"""Tests for CVM FRE Section 8 deterministic reconciler and audit verifier."""

from __future__ import annotations

from decimal import Decimal

from relata.domain.enums import CorporateBody
from relata.domain.models import (
    FRESection8Submission,
    OrganIndividualSpread,
)
from relata.engine.reconciler import FindingSeverity, reconcile_fre_section_8


def test_reconcile_sample_valid_submission(sample_valid_submission: FRESection8Submission) -> None:
    report = reconcile_fre_section_8(sample_valid_submission)
    assert report.is_valid is True
    # Grand total should match sum of board + officers
    board = sample_valid_submission.get_organ_breakdown(CorporateBody.CONSELHO_ADMINISTRACAO)
    officers = sample_valid_submission.get_organ_breakdown(CorporateBody.DIRETORIA_ESTATUTARIA)
    assert board is not None
    assert officers is not None
    assert report.grand_total_brl == board.grand_total_brl + officers.grand_total_brl


def test_reconcile_flags_mismatched_remunerated_members(sample_valid_submission: FRESection8Submission) -> None:
    # Introduce mismatch: Item 8.6 reports 4 remunerated officers, but Item 8.2 reports 5
    mismatched_spread = OrganIndividualSpread(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        remunerated_members=4, # Mismatched!
        min_individual_compensation_brl=Decimal("1200000.00"),
        max_individual_compensation_brl=Decimal("4500000.00"),
        average_individual_compensation_brl=Decimal("2300000.00"),
    )

    bad_submission = sample_valid_submission.model_copy(
        update={
            "item_8_6_spreads": [
                sample_valid_submission.item_8_6_spreads[0],
                mismatched_spread,
            ]
        }
    )

    report = reconcile_fre_section_8(bad_submission)
    assert report.is_valid is False
    errors = [f for f in report.findings if f.severity == FindingSeverity.ERROR]
    assert any("Divergência no número de membros remunerados" in e.message for e in errors)
