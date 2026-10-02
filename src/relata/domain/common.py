"""Common domain primitives for Relata CVM reporting platform."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class BilingualText(BaseModel):
    """Bilingual statutory text container ensuring synchronized disclosures without translation drift."""

    model_config = ConfigDict(frozen=True)

    pt_br: Annotated[str, Field(min_length=1, description="Texto estatutário oficial em português (CVM)")]
    en_us: Annotated[str, Field(min_length=1, description="Tradução oficial em inglês para investidores/ADRs")]
