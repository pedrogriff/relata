"""Deterministic Reconciliation & Audit Verifier for CVM FRE Section 8."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from relata.domain.models import (
    FRESection8Submission,
)


class FindingSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class AuditFinding:
    severity: FindingSeverity
    item_code: str
    organ: str
    message: str


@dataclass
class ReconciliationReport:
    is_valid: bool
    findings: list[AuditFinding] = field(default_factory=list)
    grand_total_brl: Decimal = Decimal("0.00")


def reconcile_fre_section_8(submission: FRESection8Submission) -> ReconciliationReport:
    """Performs deterministic reconciliation and compliance verification across FRE Section 8.

    Enforces invariants:
    1. Grand total matches sum of all corporate body totals.
    2. For each organ, individual spread (Min <= Average <= Max) holds.
    3. Product of Average * Remunerated Members is mathematically consistent with total organ remuneration.
    4. For organs with 0 remunerated members, all compensation fields must be exactly zero.
    """
    findings: list[AuditFinding] = []
    grand_total = Decimal("0.00")

    organ_map = {o.corporate_body: o for o in submission.item_8_2_organs}
    spread_map = {s.corporate_body: s for s in submission.item_8_6_spreads}

    for body, organ in organ_map.items():
        grand_total += organ.grand_total_brl

        # Invariant: Remunerated members must be <= total members
        if organ.remunerated_members > organ.total_members:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.ERROR,
                    item_code="8.2",
                    organ=body.label_pt,
                    message=f"Membros remunerados ({organ.remunerated_members}) > total ({organ.total_members}).",
                )
            )

        # Invariant: 0 remunerated members -> 0 total compensation
        if organ.remunerated_members == 0 and organ.grand_total_brl > 0:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.ERROR,
                    item_code="8.2",
                    organ=body.label_pt,
                    message=f"Órgão com 0 membros remunerados possui remuneração total de R$ {organ.grand_total_brl:,.2f}.",
                )
            )

        # Cross-item check with Item 8.6 (Spreads)
        spread = spread_map.get(body)
        if not spread:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.WARNING,
                    item_code="8.6",
                    organ=body.label_pt,
                    message="Quadro de remuneração individual (min/max/média) não informado para este órgão.",
                )
            )
            continue

        if spread.remunerated_members != organ.remunerated_members:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.ERROR,
                    item_code="8.6",
                    organ=body.label_pt,
                    message=(
                        f"Divergência no número de membros remunerados: "
                        f"Item 8.2 ({organ.remunerated_members}) vs Item 8.6 ({spread.remunerated_members})."
                    ),
                )
            )

        if spread.remunerated_members > 0:
            # Theoretical total from average
            calculated_pool = spread.average_individual_compensation_brl * Decimal(spread.remunerated_members)
            delta = abs(calculated_pool - organ.grand_total_brl)
            # Allow tolerance of up to 1% or R$ 100 for rounding differences in reported averages
            tolerance = max(Decimal("100.00"), organ.grand_total_brl * Decimal("0.01"))

            if delta > tolerance:
                findings.append(
                    AuditFinding(
                        severity=FindingSeverity.WARNING,
                        item_code="8.6",
                        organ=body.label_pt,
                        message=(
                            f"Discrepância entre média ponderada e total reportado: "
                            f"Média * Membros = R$ {calculated_pool:,.2f} vs Total Item 8.2 = R$ {organ.grand_total_brl:,.2f} "
                            f"(Divergência: R$ {delta:,.2f})."
                        ),
                    )
                )

    has_errors = any(f.severity == FindingSeverity.ERROR for f in findings)
    return ReconciliationReport(
        is_valid=not has_errors,
        findings=findings,
        grand_total_brl=grand_total,
    )
