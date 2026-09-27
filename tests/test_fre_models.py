"""Tests for CVM Resolution 80 Section 8 domain models and schema validations."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from relata.domain.enums import CorporateBody
from relata.domain.models import (
    FRESection8Submission,
    OrganIndividualSpread,
    OrganRemunerationBreakdown,
)


def test_valid_submission_constructs_correctly(sample_valid_submission: FRESection8Submission) -> None:
    assert sample_valid_submission.fiscal_year == 2025
    assert sample_valid_submission.grand_total_compensation_brl > Decimal("0.00")
    board = sample_valid_submission.get_organ_breakdown(CorporateBody.CONSELHO_ADMINISTRACAO)
    assert board is not None
    assert board.total_members == 7
    assert board.total_fixed_brl == Decimal("1610000.00")


def test_organ_breakdown_rejects_more_remunerated_than_total() -> None:
    with pytest.raises(ValidationError, match="Membros remunerados"):
        OrganRemunerationBreakdown(
            corporate_body=CorporateBody.CONSELHO_ADMINISTRACAO,
            total_members=5,
            remunerated_members=6, # Invalid!
        )


def test_individual_spread_rejects_min_greater_than_max() -> None:
    with pytest.raises(ValidationError, match="não pode exceder Max"):
        OrganIndividualSpread(
            corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
            remunerated_members=3,
            min_individual_compensation_brl=Decimal("500000.00"),
            max_individual_compensation_brl=Decimal("300000.00"), # Min > Max!
            average_individual_compensation_brl=Decimal("400000.00"),
        )


def test_individual_spread_rejects_average_out_of_bounds() -> None:
    with pytest.raises(ValidationError, match="deve estar entre Min"):
        OrganIndividualSpread(
            corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
            remunerated_members=3,
            min_individual_compensation_brl=Decimal("200000.00"),
            max_individual_compensation_brl=Decimal("500000.00"),
            average_individual_compensation_brl=Decimal("600000.00"), # Average > Max!
        )
