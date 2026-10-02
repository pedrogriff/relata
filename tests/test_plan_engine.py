"""Unit tests for Item 8.4 and 8.5 calculation and auditing engine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from relata.domain.common import BilingualText
from relata.domain.enums import CorporateBody, SharePlanType
from relata.domain.plan_models import OptionBalancesItem85, PlanTranche, ShareBasedPlan
from relata.engine.plan_engine import (
    audit_item_8_4_dilution_limit,
    calculate_dilution,
    calculate_intrinsic_value,
    calculate_weighted_average_strike,
    reconcile_item_8_5_balances,
)


def test_calculate_dilution_standard_and_edge_cases() -> None:
    # 5,000,000 option shares out of 100,000,000 total shares = 5.0%
    dilution = calculate_dilution(5000000, 100000000)
    assert dilution == Decimal("5.0000")

    # 1,234,567 out of 50,000,000 = 2.4691%
    dilution2 = calculate_dilution(1234567, 50000000)
    assert dilution2 == Decimal("2.4691")

    # Zero plan shares = 0.0%
    assert calculate_dilution(0, 100000000) == Decimal("0.0000")

    with pytest.raises(ValueError, match="Total de ações da companhia deve ser maior que zero"):
        calculate_dilution(1000, 0)

    with pytest.raises(ValueError, match="Total de ações do plano não pode ser negativo"):
        calculate_dilution(-10, 1000000)


def test_calculate_weighted_average_strike() -> None:
    t1 = PlanTranche(
        tranche_id="T1",
        grant_date=date(2025, 1, 1),
        share_plan_type=SharePlanType.STOCK_OPTION,
        shares_granted=100000,
        vesting_months=36,
        exercise_strike_brl=Decimal("20.00"),
    )
    t2 = PlanTranche(
        tranche_id="T2",
        grant_date=date(2025, 6, 1),
        share_plan_type=SharePlanType.STOCK_OPTION,
        shares_granted=300000,
        vesting_months=36,
        exercise_strike_brl=Decimal("40.00"),
    )
    # PMPE = (100k * 20 + 300k * 40) / 400k = (2M + 12M) / 400k = 14M / 400k = 35.00
    pmpe = calculate_weighted_average_strike([t1, t2])
    assert pmpe == Decimal("35.0000")

    assert calculate_weighted_average_strike([]) == Decimal("0.0")


def test_calculate_intrinsic_value() -> None:
    # In the money: Spot 45, Strike 30, 100k shares => spread = 15 => intrinsic = 1,500,000
    val_itm = calculate_intrinsic_value(Decimal("45.00"), Decimal("30.00"), 100000)
    assert val_itm == Decimal("1500000.00")

    # Out of the money: Spot 25, Strike 30 => spread = 0 => intrinsic = 0
    val_otm = calculate_intrinsic_value(Decimal("25.00"), Decimal("30.00"), 100000)
    assert val_otm == Decimal("0.00")

    # At the money: Spot 30, Strike 30 => intrinsic = 0
    val_atm = calculate_intrinsic_value(Decimal("30.00"), Decimal("30.00"), 100000)
    assert val_atm == Decimal("0.00")

    # Zero shares
    assert calculate_intrinsic_value(Decimal("45.00"), Decimal("30.00"), 0) == Decimal("0.0")


def test_audit_item_8_4_dilution_limit() -> None:
    t = PlanTranche(
        tranche_id="T1",
        grant_date=date(2025, 1, 1),
        share_plan_type=SharePlanType.STOCK_OPTION,
        shares_granted=4000000,
        vesting_months=36,
        exercise_strike_brl=Decimal("20.00"),
    )
    plan = ShareBasedPlan(
        plan_id="SOP",
        plan_name=BilingualText(pt_br="Plano", en_us="Plan"),
        agm_approval_date=date(2025, 4, 15),
        plan_type=SharePlanType.STOCK_OPTION,
        max_dilution_percentage=Decimal("5.0"),
        tranches=[t],
    )
    # Total shares 100,000,000 => 4% dilution <= 5% cap => Compliant!
    is_ok, dilution, _ = audit_item_8_4_dilution_limit(plan, 100000000)
    assert is_ok is True
    assert dilution == Decimal("4.0000")

    # If company has only 50,000,000 shares => 8% dilution > 5% cap => Violation!
    is_ok_viol, dilution_viol, msg_viol = audit_item_8_4_dilution_limit(plan, 50000000)
    assert is_ok_viol is False
    assert dilution_viol == Decimal("8.0000")
    assert "VIOLAÇÃO DE DILUIÇÃO" in msg_viol


def test_reconcile_item_8_5_balances() -> None:
    bal = OptionBalancesItem85(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        total_options_granted=100000,
        unvested_options=60000,
        exercisable_options=40000,
        exercised_options=0,
        forfeited_options=0,
        weighted_avg_exercise_price_brl=Decimal("25.00"),
        weighted_avg_unvested_strike_brl=Decimal("25.00"),
        weighted_avg_exercisable_strike_brl=Decimal("25.00"),
        intrinsic_value_exercisable_brl=Decimal("400000.00"),  # (35 - 25) * 40k = 400k
        current_year_recognized_expense_brl=Decimal("250000.00"),
        cumulative_recognized_expense_brl=Decimal("500000.00"),
    )
    # With spot 35, intrinsic should be (35 - 25) * 40k = 400k => Clean!
    findings = reconcile_item_8_5_balances(bal, spot_price_brl=Decimal("35.00"))
    assert len(findings) == 0

    # Test when current year expense > cumulative
    bal_bad_expense = OptionBalancesItem85(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        total_options_granted=100000,
        unvested_options=60000,
        exercisable_options=40000,
        weighted_avg_exercise_price_brl=Decimal("25.00"),
        weighted_avg_unvested_strike_brl=Decimal("25.00"),
        weighted_avg_exercisable_strike_brl=Decimal("25.00"),
        current_year_recognized_expense_brl=Decimal("600000.00"),
        cumulative_recognized_expense_brl=Decimal("500000.00"),  # Bad!
    )
    findings_exp = reconcile_item_8_5_balances(bal_bad_expense)
    assert any("excede a despesa acumulada" in f for f in findings_exp)
