"""Enterprise General Ledger Trial Balance Reconciler (Balancete Contábil vs. CVM FRE Seção 8).

Reconciles ERP trial balance accounts (SAP S/4HANA, Totvs, Oracle Hyperion)
against CVM Resolution 80 Item 8.2 reported compensation totals and CPC 10 P&L reserves.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from relata.domain.enums import CompensationComponent
from relata.domain.models import FRESection8Submission


class TrialBalanceAccount(BaseModel):
    """General Ledger account entry from ERP trial balance (Balancete de Verificação)."""

    model_config = ConfigDict(frozen=True)

    account_code: str
    account_name: str
    balance_brl: Annotated[Decimal, Field(ge=0, description="Saldo devedor acumulado no exercício em BRL")]
    component: CompensationComponent


class LedgerReconciliationFinding(BaseModel):
    """Finding identifying parity or discrepancy for a specific compensation component."""

    model_config = ConfigDict(frozen=True)

    component: CompensationComponent
    ledger_amount_brl: Decimal
    fre_reported_brl: Decimal
    discrepancy_brl: Decimal
    is_material: bool


class LedgerReconciliationReport(BaseModel):
    """Comprehensive audit report matching GL trial balance against CVM FRE Section 8 filing."""

    model_config = ConfigDict(frozen=True)

    fiscal_year: int
    is_reconciled: bool
    total_ledger_expense_brl: Decimal
    total_fre_reported_brl: Decimal
    net_discrepancy_brl: Decimal
    findings: list[LedgerReconciliationFinding]


def reconcile_ledger_trial_balance(
    trial_balance: list[TrialBalanceAccount],
    submission: FRESection8Submission,
    material_threshold_brl: Decimal = Decimal("1.00"),
) -> LedgerReconciliationReport:
    """Reconciles ERP Trial Balance ledger entries against FRE Section 8 reported components.

    Asserts that expenses booked in the accounting ledger match the regulatory figures
    disclosed to the market and CVM, flagging any discrepancies.
    """
    # Group ledger entries by component
    ledger_totals: dict[CompensationComponent, Decimal] = {}
    for entry in trial_balance:
        ledger_totals[entry.component] = ledger_totals.get(entry.component, Decimal("0.0")) + entry.balance_brl

    # Aggregate FRE reported figures across all organs
    fre_fixed = sum((o.total_fixed_brl for o in submission.item_8_2_organs), Decimal("0.0"))
    fre_bonus = sum((o.bonus_brl for o in submission.item_8_2_organs), Decimal("0.0"))
    fre_plr = sum((o.profit_sharing_plr_brl for o in submission.item_8_2_organs), Decimal("0.0"))
    fre_equity = sum((o.share_based_equity_brl for o in submission.item_8_2_organs), Decimal("0.0"))
    fre_cash_shares = sum((o.share_based_cash_brl for o in submission.item_8_2_organs), Decimal("0.0"))
    fre_post_emp = sum((o.post_employment_benefits_brl for o in submission.item_8_2_organs), Decimal("0.0"))
    fre_severance = sum((o.termination_severance_brl for o in submission.item_8_2_organs), Decimal("0.0"))

    fre_component_map: dict[CompensationComponent, Decimal] = {
        CompensationComponent.PRO_LABORE: fre_fixed,
        CompensationComponent.ANNUAL_BONUS: fre_bonus,
        CompensationComponent.PROFIT_SHARING_PLR: fre_plr,
        CompensationComponent.SHARE_BASED_EQUITY: fre_equity,
        CompensationComponent.SHARE_BASED_CASH: fre_cash_shares,
        CompensationComponent.POST_EMPLOYMENT_PENSION: fre_post_emp,
        CompensationComponent.TERMINATION_INDEMNITY: fre_severance,
    }

    findings: list[LedgerReconciliationFinding] = []
    all_components = set(ledger_totals.keys()).union(set(fre_component_map.keys()))

    total_ledger = sum(ledger_totals.values(), Decimal("0.0"))
    total_fre = sum(fre_component_map.values(), Decimal("0.0"))
    has_material_discrepancy = False

    for comp in sorted(all_components, key=lambda c: c.value):
        ledger_val = ledger_totals.get(comp, Decimal("0.0"))
        fre_val = fre_component_map.get(comp, Decimal("0.0"))
        discrepancy = ledger_val - fre_val
        is_material = abs(discrepancy) > material_threshold_brl

        if is_material:
            has_material_discrepancy = True

        findings.append(
            LedgerReconciliationFinding(
                component=comp,
                ledger_amount_brl=ledger_val,
                fre_reported_brl=fre_val,
                discrepancy_brl=discrepancy,
                is_material=is_material,
            )
        )

    net_discrepancy = total_ledger - total_fre
    is_reconciled = not has_material_discrepancy and abs(net_discrepancy) <= material_threshold_brl

    return LedgerReconciliationReport(
        fiscal_year=submission.fiscal_year,
        is_reconciled=is_reconciled,
        total_ledger_expense_brl=total_ledger,
        total_fre_reported_brl=total_fre,
        net_discrepancy_brl=net_discrepancy,
        findings=findings,
    )
