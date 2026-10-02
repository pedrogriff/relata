"""Unit tests for General Ledger Trial Balance Reconciler (Balancete vs. FRE Section 8)."""

from __future__ import annotations

from decimal import Decimal

from relata.domain.enums import CompensationComponent
from relata.domain.models import FRESection8Submission
from relata.engine.ledger_reconciler import TrialBalanceAccount, reconcile_ledger_trial_balance


def test_reconcile_ledger_trial_balance_clean(sample_valid_submission: FRESection8Submission) -> None:
    # In sample_valid_submission:
    # Board fixed: 1,610,000 | Officers fixed: 5,350,000 => Total fixed = 6,960,000
    # Officers bonus: 3,000,000
    # Officers PLR: 500,000
    # Officers share_based_equity: 2,500,000
    # Officers post_employment: 150,000
    tb = [
        TrialBalanceAccount(
            account_code="3.1.01.001",
            account_name="Despesa de Honorários e Pró-labore",
            balance_brl=Decimal("6960000.00"),
            component=CompensationComponent.PRO_LABORE,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.002",
            account_name="Despesa de Bônus Executivo",
            balance_brl=Decimal("3000000.00"),
            component=CompensationComponent.ANNUAL_BONUS,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.003",
            account_name="Participação nos Lucros e Resultados (PLR)",
            balance_brl=Decimal("500000.00"),
            component=CompensationComponent.PROFIT_SHARING_PLR,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.004",
            account_name="Despesa com Pagamento Baseado em Ações (CPC 10)",
            balance_brl=Decimal("2500000.00"),
            component=CompensationComponent.SHARE_BASED_EQUITY,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.005",
            account_name="Provisão de Benefícios Pós-Emprego",
            balance_brl=Decimal("150000.00"),
            component=CompensationComponent.POST_EMPLOYMENT_PENSION,
        ),
    ]

    report = reconcile_ledger_trial_balance(tb, sample_valid_submission)
    assert report.is_reconciled is True
    assert report.net_discrepancy_brl == Decimal("0.00")
    assert report.total_ledger_expense_brl == Decimal("13110000.00")
    assert report.total_fre_reported_brl == Decimal("13110000.00")
    assert not any(f.is_material for f in report.findings)


def test_reconcile_ledger_trial_balance_flags_material_discrepancy(
    sample_valid_submission: FRESection8Submission,
) -> None:
    # Introduce discrepancy: General ledger recorded R$ 3,700,000 in bonus, but FRE reported R$ 3,000,000
    tb_mismatched = [
        TrialBalanceAccount(
            account_code="3.1.01.001",
            account_name="Despesa de Honorários e Pró-labore",
            balance_brl=Decimal("6960000.00"),
            component=CompensationComponent.PRO_LABORE,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.002",
            account_name="Despesa de Bônus Executivo",
            balance_brl=Decimal("3700000.00"),  # Discrepancy of +R$ 700k!
            component=CompensationComponent.ANNUAL_BONUS,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.003",
            account_name="Participação nos Lucros e Resultados (PLR)",
            balance_brl=Decimal("500000.00"),
            component=CompensationComponent.PROFIT_SHARING_PLR,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.004",
            account_name="Despesa com Pagamento Baseado em Ações (CPC 10)",
            balance_brl=Decimal("2500000.00"),
            component=CompensationComponent.SHARE_BASED_EQUITY,
        ),
        TrialBalanceAccount(
            account_code="3.1.01.005",
            account_name="Provisão de Benefícios Pós-Emprego",
            balance_brl=Decimal("150000.00"),
            component=CompensationComponent.POST_EMPLOYMENT_PENSION,
        ),
    ]

    report = reconcile_ledger_trial_balance(tb_mismatched, sample_valid_submission)
    assert report.is_reconciled is False
    assert report.net_discrepancy_brl == Decimal("700000.00")
    bonus_finding = next(f for f in report.findings if f.component == CompensationComponent.ANNUAL_BONUS)
    assert bonus_finding.is_material is True
    assert bonus_finding.discrepancy_brl == Decimal("700000.00")
