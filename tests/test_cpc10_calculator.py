"""Tests for CPC 10 (R1) / IFRS 2 Black-Scholes valuation and accrual schedule generation."""

from __future__ import annotations

from decimal import Decimal

from relata.domain.cpc10_models import CPC10Grant, OptionPricingParameters
from relata.engine.cpc10_calculator import (
    calculate_black_scholes_call,
    generate_cpc10_accrual_schedule,
)


def test_black_scholes_call_pricing(sample_option_params: OptionPricingParameters) -> None:
    """Verifies Black-Scholes Call pricing returns consistent non-zero value for standard parameters."""
    fv = calculate_black_scholes_call(sample_option_params)
    assert fv > Decimal("0.00")
    # For S=35.5, K=35, r=10.5%, vol=32%, div=2.5%, T=3, call should be around R$ 11 - R$ 14
    assert Decimal("10.00") <= fv <= Decimal("15.00")


def test_black_scholes_deep_in_the_money() -> None:
    params = OptionPricingParameters(
        spot_price_brl=Decimal("100.00"),
        strike_price_brl=Decimal("1.00"),
        risk_free_rate=Decimal("0.05"),
        annual_volatility=Decimal("0.20"),
        dividend_yield=Decimal("0.00"),
        time_to_maturity_years=Decimal("1.0"),
    )
    fv = calculate_black_scholes_call(params)
    # Call value should be very close to S - K * exp(-rT) ~ 100 - 0.9512 ~ 99.05
    assert Decimal("98.00") <= fv <= Decimal("100.00")


def test_generate_cpc10_accrual_schedule(sample_cpc10_grant: CPC10Grant) -> None:
    """Verifies that accrual schedule spans exact vesting months and recognizes cumulative expenses."""
    schedule = generate_cpc10_accrual_schedule(sample_cpc10_grant)

    assert len(schedule) == sample_cpc10_grant.vesting_months
    # First month index should be 1, last should be 36
    assert schedule[0].month_index == 1
    assert schedule[-1].month_index == 36

    # Invariant: sum of shares vesting across schedule equals total grant shares
    total_shares_vested = sum(entry.shares_vesting_in_month for entry in schedule)
    assert total_shares_vested == sample_cpc10_grant.total_shares_granted

    # Cumulative expense must be monotonically increasing
    for i in range(1, len(schedule)):
        assert schedule[i].cumulative_expense_recognized_brl >= schedule[i - 1].cumulative_expense_recognized_brl

    # In month 36, unvested balance should reach 0.00
    assert schedule[-1].unvested_balance_brl == Decimal("0.00")
