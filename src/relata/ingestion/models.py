"""Pydantic schemas for unstructured corporate document extraction (Atas de AGO/AGE/RCA)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from relata.domain.enums import CorporateBody, SharePlanType


class ExtractedOrganRemuneration(BaseModel):
    """Extracted remuneration proposal or approved budget per corporate body."""

    model_config = ConfigDict(frozen=True)

    corporate_body: CorporateBody
    total_members: Annotated[int, Field(ge=0, default=0)] = 0
    remunerated_members: Annotated[int, Field(ge=0, default=0)] = 0
    approved_cap_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))] = Decimal("0.0")
    fixed_compensation_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))] = Decimal("0.0")
    variable_compensation_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))] = Decimal("0.0")
    share_based_compensation_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))] = Decimal("0.0")
    post_employment_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))] = Decimal("0.0")


class ExtractedShareGrantCondition(BaseModel):
    """Extracted share-based incentive grant terms from board/shareholder resolutions."""

    model_config = ConfigDict(frozen=True)

    plan_name: str
    plan_type: SharePlanType
    corporate_body: CorporateBody
    total_shares_approved: Annotated[int, Field(gt=0)]
    strike_price_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))] = Decimal("0.0")
    vesting_months: Annotated[int, Field(gt=0, default=36)] = 36
    lockup_months: Annotated[int, Field(ge=0, default=0)] = 0
    performance_conditions: list[str] = Field(default_factory=list)


class ExtractedClawbackProvision(BaseModel):
    """Extracted clawback and risk mitigation clause for variable compensation."""

    model_config = ConfigDict(frozen=True)

    corporate_body: CorporateBody
    trigger_events: list[str] = Field(default_factory=list)
    recovery_window_years: Annotated[int, Field(ge=0, default=2)] = 2


class AtaExtractionResult(BaseModel):
    """Structured extraction payload produced from corporate meeting minutes (*Atas*)."""

    model_config = ConfigDict(frozen=True)

    document_title: str
    meeting_type: str  # e.g., "AGO", "AGE", "RCA", "Assembleia Geral Ordinária"
    meeting_date: date | None = None
    company_name: str
    cnpj: str | None = None

    # Global annual remuneration cap approved under Lei 6.404/76 Art. 152
    global_compensation_ceiling_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]

    organs_breakdown: list[ExtractedOrganRemuneration] = Field(default_factory=list)
    share_plans: list[ExtractedShareGrantCondition] = Field(default_factory=list)
    clawbacks: list[ExtractedClawbackProvision] = Field(default_factory=list)

    # Narrative justifications for CVM Item 8.1
    qualitative_policy_summary_pt: str
    qualitative_policy_summary_en: str
