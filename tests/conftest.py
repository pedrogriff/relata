"""Pytest configuration and shared fixtures for Relata test suite."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from relata.domain.cpc10_models import CPC10Grant, OptionPricingParameters
from relata.domain.enums import CorporateBody, SettlementMethod, SharePlanType, ValuationModel
from relata.domain.models import (
    BilingualText,
    FRESection8Submission,
    OrganIndividualSpread,
    OrganRemunerationBreakdown,
)


@pytest.fixture
def sample_option_params() -> OptionPricingParameters:
    return OptionPricingParameters(
        spot_price_brl=Decimal("35.50"),
        strike_price_brl=Decimal("35.00"),
        risk_free_rate=Decimal("0.105"),       # 10.5% a.a.
        annual_volatility=Decimal("0.32"),     # 32%
        dividend_yield=Decimal("0.025"),       # 2.5%
        time_to_maturity_years=Decimal("3.0"), # 3 years
    )


@pytest.fixture
def sample_cpc10_grant(sample_option_params: OptionPricingParameters) -> CPC10Grant:
    return CPC10Grant(
        grant_id="OUTORGA-2025-01",
        plan_name="Plano de Opções 2025 - Diretoria",
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        plan_type=SharePlanType.STOCK_OPTION,
        settlement_method=SettlementMethod.EQUITY,
        valuation_model=ValuationModel.BLACK_SCHOLES,
        grant_date=date(2025, 1, 15),
        vesting_start_date=date(2025, 2, 1),
        vesting_months=36,
        lock_up_months=12,
        total_shares_granted=120_000,
        pricing_parameters=sample_option_params,
        grant_date_fair_value_unit_brl=Decimal("11.4520"),
        annual_forfeiture_rate=Decimal("0.03"), # 3% forfeiture
    )


@pytest.fixture
def sample_valid_submission() -> FRESection8Submission:
    board_organ = OrganRemunerationBreakdown(
        corporate_body=CorporateBody.CONSELHO_ADMINISTRACAO,
        total_members=7,
        remunerated_members=7,
        pro_labore_or_salaries_brl=Decimal("1400000.00"),
        direct_benefits_brl=Decimal("70000.00"),
        committee_participation_brl=Decimal("140000.00"),
        other_fixed_brl=Decimal("0.00"),
        bonus_brl=Decimal("0.00"),
        profit_sharing_plr_brl=Decimal("0.00"),
        other_variable_brl=Decimal("0.00"),
        share_based_equity_brl=Decimal("0.00"),
        share_based_cash_brl=Decimal("0.00"),
        post_employment_benefits_brl=Decimal("0.00"),
        termination_severance_brl=Decimal("0.00"),
    )

    officers_organ = OrganRemunerationBreakdown(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        total_members=5,
        remunerated_members=5,
        pro_labore_or_salaries_brl=Decimal("5000000.00"),
        direct_benefits_brl=Decimal("350000.00"),
        committee_participation_brl=Decimal("0.00"),
        other_fixed_brl=Decimal("0.00"),
        bonus_brl=Decimal("3000000.00"),
        profit_sharing_plr_brl=Decimal("500000.00"),
        other_variable_brl=Decimal("0.00"),
        share_based_equity_brl=Decimal("2500000.00"),
        share_based_cash_brl=Decimal("0.00"),
        post_employment_benefits_brl=Decimal("150000.00"),
        termination_severance_brl=Decimal("0.00"),
    )

    board_spread = OrganIndividualSpread(
        corporate_body=CorporateBody.CONSELHO_ADMINISTRACAO,
        remunerated_members=7,
        min_individual_compensation_brl=Decimal("180000.00"),
        max_individual_compensation_brl=Decimal("320000.00"),
        average_individual_compensation_brl=Decimal("230000.00"),
    )

    officers_spread = OrganIndividualSpread(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        remunerated_members=5,
        min_individual_compensation_brl=Decimal("1200000.00"),
        max_individual_compensation_brl=Decimal("4500000.00"),
        average_individual_compensation_brl=Decimal("2300000.00"),
    )

    return FRESection8Submission(
        fiscal_year=2025,
        company_name="Empresa Exemplo S.A.",
        cnpj="12.345.678/0001-90",
        cvm_code="09876",
        item_8_1_policy_narrative=BilingualText(
            pt_br="A política de remuneração visa alinhar incentivos executivos à geração de valor sustentável de longo prazo.",
            en_us="The compensation policy aims to align executive incentives with sustainable long-term value generation.",
        ),
        item_8_2_organs=[board_organ, officers_organ],
        item_8_6_spreads=[board_spread, officers_spread],
    )
