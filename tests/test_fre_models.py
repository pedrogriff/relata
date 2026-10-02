"""Tests for CVM Resolution 80 Section 8 domain models and schema validations."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from relata.domain.common import BilingualText
from relata.domain.enums import CorporateBody, SharePlanType
from relata.domain.models import (
    FRESection8Submission,
    OrganIndividualSpread,
    OrganRemunerationBreakdown,
)
from relata.domain.plan_models import (
    OptionBalancesItem85,
    TerminationPackageItem87,
    VariableCompensationPolicy,
)


def test_valid_submission_constructs_correctly(sample_valid_submission: FRESection8Submission) -> None:
    assert sample_valid_submission.fiscal_year == 2025
    assert sample_valid_submission.grand_total_compensation_brl > Decimal("0.00")
    board = sample_valid_submission.get_organ_breakdown(CorporateBody.CONSELHO_ADMINISTRACAO)
    assert board is not None
    assert board.total_members == 7
    assert board.total_fixed_brl == Decimal("1610000.00")
    assert board.total_variable_brl == Decimal("0.00")
    assert board.total_share_based_brl == Decimal("0.00")

    # Spread getter
    board_spread = sample_valid_submission.get_organ_spread(CorporateBody.CONSELHO_ADMINISTRACAO)
    assert board_spread is not None
    assert board_spread.min_individual_compensation_brl == Decimal("180000.00")

    # Non-existent organ getter returns None
    assert sample_valid_submission.get_organ_breakdown(CorporateBody.COMITE_AUDITORIA) is None
    assert sample_valid_submission.get_organ_spread(CorporateBody.COMITE_AUDITORIA) is None


def test_submission_helpers_for_expanded_items(sample_valid_submission: FRESection8Submission) -> None:
    bal = OptionBalancesItem85(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        total_options_granted=100000,
        unvested_options=60000,
        exercisable_options=40000,
        weighted_avg_exercise_price_brl=Decimal("25.00"),
        weighted_avg_unvested_strike_brl=Decimal("25.00"),
        weighted_avg_exercisable_strike_brl=Decimal("25.00"),
    )
    pol = VariableCompensationPolicy(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        narrative=BilingualText(pt_br="Política", en_us="Policy"),
    )
    pkg = TerminationPackageItem87(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        statutory_severance_terms=BilingualText(pt_br="Rescisão", en_us="Severance"),
    )

    sub = FRESection8Submission(
        fiscal_year=sample_valid_submission.fiscal_year,
        company_name=sample_valid_submission.company_name,
        cnpj=sample_valid_submission.cnpj,
        cvm_code=sample_valid_submission.cvm_code,
        item_8_1_policy_narrative=sample_valid_submission.item_8_1_policy_narrative,
        item_8_2_organs=sample_valid_submission.item_8_2_organs,
        item_8_3_variable_policies=[pol],
        item_8_5_option_balances=[bal],
        item_8_6_spreads=sample_valid_submission.item_8_6_spreads,
        item_8_7_termination_packages=[pkg],
    )

    assert sub.get_option_balance(CorporateBody.DIRETORIA_ESTATUTARIA) == bal
    assert sub.get_option_balance(CorporateBody.CONSELHO_ADMINISTRACAO) is None

    assert sub.get_variable_policy(CorporateBody.DIRETORIA_ESTATUTARIA) == pol
    assert sub.get_variable_policy(CorporateBody.CONSELHO_ADMINISTRACAO) is None

    assert sub.get_termination_package(CorporateBody.DIRETORIA_ESTATUTARIA) == pkg
    assert sub.get_termination_package(CorporateBody.CONSELHO_ADMINISTRACAO) is None


def test_organ_breakdown_rejects_more_remunerated_than_total() -> None:
    with pytest.raises(ValidationError, match="Membros remunerados"):
        OrganRemunerationBreakdown(
            corporate_body=CorporateBody.CONSELHO_ADMINISTRACAO,
            total_members=5,
            remunerated_members=6,  # Invalid!
        )


def test_individual_spread_rejects_min_greater_than_max() -> None:
    with pytest.raises(ValidationError, match="não pode exceder Max"):
        OrganIndividualSpread(
            corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
            remunerated_members=3,
            min_individual_compensation_brl=Decimal("500000.00"),
            max_individual_compensation_brl=Decimal("300000.00"),  # Min > Max!
            average_individual_compensation_brl=Decimal("400000.00"),
        )


def test_individual_spread_rejects_average_out_of_bounds() -> None:
    with pytest.raises(ValidationError, match="deve estar entre Min"):
        OrganIndividualSpread(
            corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
            remunerated_members=3,
            min_individual_compensation_brl=Decimal("200000.00"),
            max_individual_compensation_brl=Decimal("500000.00"),
            average_individual_compensation_brl=Decimal("600000.00"),  # Average > Max!
        )


def test_zero_remunerated_members_spread() -> None:
    # Zero remunerated with zeros is valid
    spread = OrganIndividualSpread(
        corporate_body=CorporateBody.CONSELHO_FISCAL,
        remunerated_members=0,
        min_individual_compensation_brl=Decimal("0.0"),
        max_individual_compensation_brl=Decimal("0.0"),
        average_individual_compensation_brl=Decimal("0.0"),
    )
    assert spread.remunerated_members == 0

    # Zero remunerated with non-zero is rejected
    with pytest.raises(ValidationError, match="Órgão sem membros remunerados deve ter min, max e média iguais a zero"):
        OrganIndividualSpread(
            corporate_body=CorporateBody.CONSELHO_FISCAL,
            remunerated_members=0,
            min_individual_compensation_brl=Decimal("1000.0"),
            max_individual_compensation_brl=Decimal("1000.0"),
            average_individual_compensation_brl=Decimal("1000.0"),
        )


def test_enums_bilingual_labels() -> None:
    assert CorporateBody.CONSELHO_ADMINISTRACAO.label_pt == "Conselho de Administração"
    assert CorporateBody.CONSELHO_ADMINISTRACAO.label_en == "Board of Directors"
    assert CorporateBody.DIRETORIA_ESTATUTARIA.label_en == "Statutory Executive Board"

    assert SharePlanType.STOCK_OPTION.label_pt == "Opções de Compra de Ações (Stock Options)"
    assert SharePlanType.STOCK_OPTION.label_en == "Stock Options"
    assert SharePlanType.RESTRICTED_SHARES.label_pt == "Ações Restritas (RSUs)"
    assert SharePlanType.RESTRICTED_SHARES.label_en == "Restricted Share Units (RSUs)"
