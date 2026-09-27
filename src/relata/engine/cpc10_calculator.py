"""Deterministic Fair Value & Amortization Calculator under CPC 10 (R1) / IFRS 2."""

from __future__ import annotations

import math
from decimal import Decimal

from relata.domain.cpc10_models import CPC10Grant, MonthlyVestingAccrual, OptionPricingParameters
from relata.domain.enums import SharePlanType
from relata.engine.share_distributor import distribute_integer_shares


def _normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function Phi(x) using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def calculate_black_scholes_call(params: OptionPricingParameters) -> Decimal:
    """Calculates Black-Scholes European Call option fair value per CPC 10 Item 16 / IFRS 2.

    Formula:
        d1 = [ln(S / K) + (r - q + 0.5 * sigma^2) * T] / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
        Call = S * exp(-q * T) * N(d1) - K * exp(-r * T) * N(d2)

    Returns:
        Fair value in BRL rounded to 4 decimal places.
    """
    s = float(params.spot_price_brl)
    k = float(params.strike_price_brl)
    r = float(params.risk_free_rate)
    sigma = float(params.annual_volatility)
    q = float(params.dividend_yield)
    t = float(params.time_to_maturity_years)

    if t <= 0:
        return Decimal(str(round(max(0.0, s - k), 4)))

    if k <= 0:
        return Decimal(str(round(s * math.exp(-q * t), 4)))

    sqrt_t = math.sqrt(t)
    vol_sqrt_t = sigma * sqrt_t

    d1 = (math.log(s / k) + (r - q + 0.5 * (sigma**2)) * t) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t

    call_price = (s * math.exp(-q * t) * _normal_cdf(d1)) - (k * math.exp(-r * t) * _normal_cdf(d2))
    fair_value = max(0.0, call_price)

    return Decimal(str(round(fair_value, 4)))


def generate_cpc10_accrual_schedule(grant: CPC10Grant) -> list[MonthlyVestingAccrual]:
    """Generates monthly accounting accruals recognized in P&L (DRE) over the vesting period.

    Follows CPC 10 (R1) Item 19:
    Recognizes the fair value pro-rata temporis over the vesting period,
    adjusting for estimated employee turnover/forfeitures.
    """
    total_months = grant.vesting_months
    total_shares = grant.total_shares_granted

    # Determine unit fair value
    if grant.plan_type in (SharePlanType.STOCK_OPTION, SharePlanType.SAR) and grant.pricing_parameters:
        unit_fv = calculate_black_scholes_call(grant.pricing_parameters)
    else:
        unit_fv = grant.grant_date_fair_value_unit_brl

    # Distribute shares across vesting months using Largest Remainder Method
    equal_weights = [Decimal("1.0") / Decimal(total_months)] * total_months
    monthly_shares = distribute_integer_shares(total_shares, equal_weights)

    annual_forfeiture = float(grant.annual_forfeiture_rate)
    total_grant_value = Decimal(total_shares) * unit_fv

    schedule: list[MonthlyVestingAccrual] = []
    prev_cumulative_expense = Decimal("0.00")

    curr_year = grant.vesting_start_date.year
    curr_month = grant.vesting_start_date.month

    for m in range(1, total_months + 1):
        # Time fraction of vesting completed
        progress = Decimal(m) / Decimal(total_months)

        # Forfeiture factor: (1 - annual_forfeiture)^(m / 12)
        elapsed_years = float(m) / 12.0
        survival_rate = Decimal(str(round((1.0 - annual_forfeiture) ** elapsed_years, 6)))

        # Target cumulative expense at month m
        target_cumulative = total_grant_value * progress * survival_rate
        target_cumulative = target_cumulative.quantize(Decimal("0.01"))

        # Period expense for current month
        period_expense = target_cumulative - prev_cumulative_expense
        prev_cumulative_expense = target_cumulative

        unvested_balance = max(Decimal("0.00"), (total_grant_value * survival_rate) - target_cumulative)
        active_shares = int(Decimal(total_shares) * survival_rate)

        schedule.append(
            MonthlyVestingAccrual(
                month_index=m,
                year=curr_year,
                month=curr_month,
                shares_vesting_in_month=monthly_shares[m - 1],
                period_expense_recognized_brl=period_expense,
                cumulative_expense_recognized_brl=target_cumulative,
                unvested_balance_brl=unvested_balance.quantize(Decimal("0.01")),
                active_shares_expected=active_shares,
            )
        )

        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1

    return schedule
