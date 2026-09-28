"""Mapper from extracted unstructured data into formal CVM FRE Section 8 & CPC 10 domain models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from relata.domain.cpc10_models import CPC10Grant, OptionPricingParameters
from relata.domain.enums import SettlementMethod, ValuationModel
from relata.domain.models import (
    BilingualText,
    FRESection8Submission,
    OrganIndividualSpread,
    OrganRemunerationBreakdown,
)
from relata.ingestion.models import AtaExtractionResult, ExtractedShareGrantCondition


def map_ata_to_fre_submission(
    extraction: AtaExtractionResult,
    fiscal_year: int,
    cvm_code: str = "00000",
) -> FRESection8Submission:
    """Transforms extraction result into a validated FRESection8Submission container."""
    organs: list[OrganRemunerationBreakdown] = []
    spreads: list[OrganIndividualSpread] = []

    for item in extraction.organs_breakdown:
        # Construct Organ breakdown
        organ = OrganRemunerationBreakdown(
            corporate_body=item.corporate_body,
            total_members=max(1, item.total_members),
            remunerated_members=max(1, item.remunerated_members),
            pro_labore_or_salaries_brl=item.fixed_compensation_brl,
            direct_benefits_brl=Decimal("0.00"),
            committee_participation_brl=Decimal("0.00"),
            other_fixed_brl=Decimal("0.00"),
            bonus_brl=item.variable_compensation_brl,
            profit_sharing_plr_brl=Decimal("0.00"),
            other_variable_brl=Decimal("0.00"),
            share_based_equity_brl=item.share_based_compensation_brl,
            share_based_cash_brl=Decimal("0.00"),
            post_employment_benefits_brl=item.post_employment_brl,
            termination_severance_brl=Decimal("0.00"),
        )
        organs.append(organ)

        # Derive conservative spread boundaries for Item 8.6
        total_rem = organ.grand_total_brl
        n = Decimal(organ.remunerated_members)
        avg = total_rem / n if n > 0 else Decimal("0.00")
        min_val = (avg * Decimal("0.70")).quantize(Decimal("0.01"))
        max_val = (avg * Decimal("1.40")).quantize(Decimal("0.01"))
        # Ensure min <= avg <= max
        if min_val > avg:
            min_val = avg
        if max_val < avg:
            max_val = avg

        spread = OrganIndividualSpread(
            corporate_body=item.corporate_body,
            remunerated_members=organ.remunerated_members,
            min_individual_compensation_brl=min_val,
            max_individual_compensation_brl=max_val,
            average_individual_compensation_brl=avg.quantize(Decimal("0.01")),
        )
        spreads.append(spread)

    return FRESection8Submission(
        fiscal_year=fiscal_year,
        company_name=extraction.company_name,
        cnpj=extraction.cnpj or "00.000.000/0001-00",
        cvm_code=cvm_code,
        item_8_1_policy_narrative=BilingualText(
            pt_br=extraction.qualitative_policy_summary_pt,
            en_us=extraction.qualitative_policy_summary_en,
        ),
        item_8_2_organs=organs,
        item_8_6_spreads=spreads,
    )


def map_share_plan_to_cpc10_grant(
    plan: ExtractedShareGrantCondition,
    grant_id: str,
    grant_date: date,
    spot_price_brl: Decimal,
    annual_volatility: Decimal = Decimal("0.30"),
    risk_free_rate: Decimal = Decimal("0.105"),
    dividend_yield: Decimal = Decimal("0.02"),
) -> CPC10Grant:
    """Converts extracted share plan terms into an accounting CPC10Grant award ready for valuation."""
    time_to_maturity = Decimal(str(round(float(plan.vesting_months) / 12.0, 2)))
    pricing_params = OptionPricingParameters(
        spot_price_brl=spot_price_brl,
        strike_price_brl=plan.strike_price_brl,
        risk_free_rate=risk_free_rate,
        annual_volatility=annual_volatility,
        dividend_yield=dividend_yield,
        time_to_maturity_years=time_to_maturity,
    )

    return CPC10Grant(
        grant_id=grant_id,
        plan_name=plan.plan_name,
        corporate_body=plan.corporate_body,
        plan_type=plan.plan_type,
        settlement_method=SettlementMethod.EQUITY,
        valuation_model=ValuationModel.BLACK_SCHOLES,
        grant_date=grant_date,
        vesting_start_date=grant_date,
        vesting_months=plan.vesting_months,
        lock_up_months=plan.lockup_months,
        total_shares_granted=plan.total_shares_approved,
        pricing_parameters=pricing_params,
        grant_date_fair_value_unit_brl=Decimal("0.00"),  # Computed by calculator
        annual_forfeiture_rate=Decimal("0.03"),
    )
