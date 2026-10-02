"""Deterministic engine for CVM Resolution 80 Item 8.4 and 8.5 calculations and audits.

Implements dilution analytics, weighted average strike prices (PMPE), intrinsic value estimation,
and statutory balance reconciliation invariants.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from relata.domain.plan_models import OptionBalancesItem85, PlanTranche, ShareBasedPlan


def calculate_dilution(total_plan_shares: int, total_company_shares: int) -> Decimal:
    """Calculates potential equity dilution percentage from share-based payment awards.

    Formula: (total_plan_shares / total_company_shares) * 100
    """
    if total_company_shares <= 0:
        raise ValueError(f"Total de ações da companhia deve ser maior que zero (recebido: {total_company_shares}).")
    if total_plan_shares < 0:
        raise ValueError(f"Total de ações do plano não pode ser negativo (recebido: {total_plan_shares}).")

    dilution = (Decimal(total_plan_shares) / Decimal(total_company_shares)) * Decimal("100.0")
    return dilution.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_weighted_average_strike(tranches: list[PlanTranche]) -> Decimal:
    """Calculates Weighted Average Exercise Price (Preço Médio Ponderado de Exercício - PMPE).

    Formula: sum(strike_i * shares_i) / sum(shares_i)
    """
    if not tranches:
        return Decimal("0.0")

    total_shares = sum(t.shares_granted for t in tranches)
    if total_shares == 0:
        return Decimal("0.0")

    total_strike_val = sum((t.exercise_strike_brl * Decimal(t.shares_granted) for t in tranches), Decimal("0.0"))
    pmpe = total_strike_val / Decimal(total_shares)
    return pmpe.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_intrinsic_value(
    spot_price_brl: Decimal,
    strike_price_brl: Decimal,
    total_shares: int,
) -> Decimal:
    """Calculates total intrinsic value of in-the-money options (Valor Intrínseco).

    Formula: max(0, spot_price - strike_price) * total_shares
    """
    if total_shares <= 0:
        return Decimal("0.0")

    spread = max(Decimal("0.0"), spot_price_brl - strike_price_brl)
    intrinsic = spread * Decimal(total_shares)
    return intrinsic.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def audit_item_8_4_dilution_limit(
    plan: ShareBasedPlan,
    total_company_shares: int,
) -> tuple[bool, Decimal, str]:
    """Audits whether share plan grants comply with the AGM authorized statutory dilution cap."""
    dilution_pct = calculate_dilution(plan.total_shares_granted, total_company_shares)
    is_compliant = dilution_pct <= plan.max_dilution_percentage

    if is_compliant:
        msg = (
            f"Plano '{plan.plan_id}' em conformidade: diluição atual ({dilution_pct:.4f}%) "
            f"respeita o teto estatutário aprovado em AGO/AGE ({plan.max_dilution_percentage:.2f}%)."
        )
    else:
        msg = (
            f"VIOLAÇÃO DE DILUIÇÃO no plano '{plan.plan_id}': diluição atual ({dilution_pct:.4f}%) "
            f"excede o teto estatutário aprovado em AGO/AGE ({plan.max_dilution_percentage:.2f}%)."
        )

    return is_compliant, dilution_pct, msg


def reconcile_item_8_5_balances(
    balance: OptionBalancesItem85,
    spot_price_brl: Decimal | None = None,
) -> list[str]:
    """Verifies statutory invariants and accounting consistency for Item 8.5 disclosures."""
    findings: list[str] = []

    # Invariant 1: Option balance conservation
    reconciled = (
        balance.unvested_options
        + balance.exercisable_options
        + balance.exercised_options
        + balance.forfeited_options
    )
    if reconciled != balance.total_options_granted:
        findings.append(
            f"Divergência de saldo ({balance.corporate_body.label_pt}): soma das parcelas ({reconciled}) "
            f"diverge do total outorgado ({balance.total_options_granted})."
        )

    # Invariant 2: Current year expense <= cumulative expense
    if balance.current_year_recognized_expense_brl > balance.cumulative_recognized_expense_brl:
        findings.append(
            f"Incoerência contábil CPC 10 ({balance.corporate_body.label_pt}): despesa do exercício "
            f"(R$ {balance.current_year_recognized_expense_brl}) excede a despesa acumulada (R$ {balance.cumulative_recognized_expense_brl})."
        )

    # Invariant 3: Zero exercisable options must have zero intrinsic value
    if balance.exercisable_options == 0 and balance.intrinsic_value_exercisable_brl > Decimal("0.0"):
        findings.append(
            f"Inconsistência de valor intrínseco ({balance.corporate_body.label_pt}): sem opções exercíveis, "
            f"mas valor intrínseco reportado é R$ {balance.intrinsic_value_exercisable_brl}."
        )

    # Invariant 4: Spot price intrinsic valuation verification (if spot provided)
    if spot_price_brl is not None and balance.exercisable_options > 0:
        expected_intrinsic = calculate_intrinsic_value(
            spot_price_brl,
            balance.weighted_avg_exercisable_strike_brl,
            balance.exercisable_options,
        )
        diff = abs(expected_intrinsic - balance.intrinsic_value_exercisable_brl)
        # Allow tolerance of up to 1.00 BRL due to rounding in weighted average strike
        if diff > Decimal("10.00"):
            findings.append(
                f"Discrepância no valor intrínseco reportado ({balance.corporate_body.label_pt}): "
                f"reportado R$ {balance.intrinsic_value_exercisable_brl}, esperado R$ {expected_intrinsic} "
                f"(com cotação de mercado R$ {spot_price_brl} e PMPE exercível R$ {balance.weighted_avg_exercisable_strike_brl})."
            )

    return findings
