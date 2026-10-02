"""Unit tests for CVM Resolution 80 Section 8 Items 8.3, 8.4, 8.5, and 8.7 domain models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from relata.domain.common import BilingualText
from relata.domain.enums import (
    CorporateBody,
    PerformanceMetricCategory,
    SettlementMethod,
    SharePlanType,
    StrikeAdjustmentIndex,
)
from relata.domain.plan_models import (
    OptionBalancesItem85,
    PerformanceMetric,
    PlanTranche,
    ShareBasedPlan,
    TerminationPackageItem87,
    VariableCompensationPolicy,
)


def test_performance_metric_and_variable_policy() -> None:
    m1 = PerformanceMetric(
        name=BilingualText(pt_br="TSR Relativo ao IBOV", en_us="Relative TSR vs IBOVESPA"),
        category=PerformanceMetricCategory.FINANCIAL,
        weight_pct=Decimal("40.0"),
        threshold_pct=Decimal("80.0"),
        target_pct=Decimal("100.0"),
        max_cap_pct=Decimal("150.0"),
    )
    m2 = PerformanceMetric(
        name=BilingualText(pt_br="EBITDA Ajustado", en_us="Adjusted EBITDA"),
        category=PerformanceMetricCategory.FINANCIAL,
        weight_pct=Decimal("40.0"),
    )
    m3 = PerformanceMetric(
        name=BilingualText(pt_br="Redução de Emissões CO2", en_us="CO2 Reduction ESG"),
        category=PerformanceMetricCategory.ESG_SUSTAINABILITY,
        weight_pct=Decimal("20.0"),
    )

    policy = VariableCompensationPolicy(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        narrative=BilingualText(pt_br="Política variável alinhada ao plano trienal", en_us="Variable policy aligned with 3-year plan"),
        metrics=[m1, m2, m3],
        has_clawback=True,
        has_malus=True,
        deferral_period_months=12,
    )
    assert policy.total_weight_pct == Decimal("100.0")
    assert policy.deferral_period_months == 12


def test_variable_policy_rejects_invalid_weights_sum() -> None:
    m1 = PerformanceMetric(
        name=BilingualText(pt_br="Meta 1", en_us="Goal 1"),
        category=PerformanceMetricCategory.FINANCIAL,
        weight_pct=Decimal("50.0"),
    )
    m2 = PerformanceMetric(
        name=BilingualText(pt_br="Meta 2", en_us="Goal 2"),
        category=PerformanceMetricCategory.OPERATIONAL,
        weight_pct=Decimal("40.0"),  # Total = 90% != 100%
    )
    with pytest.raises(ValidationError, match="Soma dos pesos das métricas"):
        VariableCompensationPolicy(
            corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
            narrative=BilingualText(pt_br="Política", en_us="Policy"),
            metrics=[m1, m2],
        )


def test_share_based_plan_properties() -> None:
    t1 = PlanTranche(
        tranche_id="2025-S1",
        grant_date=date(2025, 3, 15),
        share_plan_type=SharePlanType.STOCK_OPTION,
        shares_granted=100000,
        vesting_months=36,
        lock_up_months=12,
        exercise_strike_brl=Decimal("25.00"),
        strike_adjustment_index=StrikeAdjustmentIndex.IPCA,
        settlement_method=SettlementMethod.EQUITY,
        cpc10_grant_fair_value_brl=Decimal("10.50"),
    )
    t2 = PlanTranche(
        tranche_id="2025-S2",
        grant_date=date(2025, 8, 1),
        share_plan_type=SharePlanType.STOCK_OPTION,
        shares_granted=100000,
        vesting_months=48,
        exercise_strike_brl=Decimal("35.00"),
        cpc10_grant_fair_value_brl=Decimal("12.00"),
    )

    plan = ShareBasedPlan(
        plan_id="SOP-2025",
        plan_name=BilingualText(pt_br="Plano de Opções 2025", en_us="Stock Option Plan 2025"),
        agm_approval_date=date(2025, 4, 30),
        plan_type=SharePlanType.STOCK_OPTION,
        max_dilution_percentage=Decimal("5.0"),
        tranches=[t1, t2],
    )

    assert plan.total_shares_granted == 200000
    assert plan.weighted_average_strike_price_brl == Decimal("30.00")
    assert plan.weighted_average_vesting_months == Decimal("42.0")
    assert t1.total_tranche_grant_value_brl == Decimal("1050000.00")


def test_option_balances_item_8_5_valid() -> None:
    bal = OptionBalancesItem85(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        total_options_granted=500000,
        unvested_options=300000,
        exercisable_options=150000,
        exercised_options=40000,
        forfeited_options=10000,
        weighted_avg_exercise_price_brl=Decimal("28.50"),
        weighted_avg_unvested_strike_brl=Decimal("30.00"),
        weighted_avg_exercisable_strike_brl=Decimal("25.00"),
        intrinsic_value_exercisable_brl=Decimal("1500000.00"),
        current_year_recognized_expense_brl=Decimal("850000.00"),
        cumulative_recognized_expense_brl=Decimal("1650000.00"),
    )
    assert bal.active_options == 450000


def test_option_balances_item_8_5_rejects_divergent_sum() -> None:
    with pytest.raises(ValidationError, match="Soma dos saldos de opções"):
        OptionBalancesItem85(
            corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
            total_options_granted=500000,
            unvested_options=300000,
            exercisable_options=100000,
            exercised_options=50000,
            forfeited_options=10000,  # 300k + 100k + 50k + 10k = 460k != 500k
            weighted_avg_exercise_price_brl=Decimal("28.00"),
            weighted_avg_unvested_strike_brl=Decimal("28.00"),
            weighted_avg_exercisable_strike_brl=Decimal("28.00"),
        )


def test_termination_package_item_8_7() -> None:
    pkg = TerminationPackageItem87(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        has_golden_parachute=True,
        golden_parachute_terms=BilingualText(
            pt_br="Indenização equivalente a 12 remunerações mensais em caso de alienação de controle",
            en_us="Severance indemnity equal to 12 months compensation in case of change of control",
        ),
        notice_period_months=3,
        non_compete_duration_months=12,
        non_compete_monthly_indemnity_brl=Decimal("80000.00"),
        statutory_severance_terms=BilingualText(
            pt_br="Rescisão sem justa causa nos termos do Art. 477 da CLT e estatuto social",
            en_us="Dismissal without cause under Brazilian CLT Art. 477 and corporate bylaws",
        ),
    )
    assert pkg.has_golden_parachute is True
    assert pkg.non_compete_monthly_indemnity_brl == Decimal("80000.00")
