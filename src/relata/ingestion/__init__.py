"""Ingestion package for unstructured corporate meeting minutes and document extraction."""

from __future__ import annotations

from relata.ingestion.document_loader import load_document
from relata.ingestion.extractor import AtaExtractor
from relata.ingestion.mapper import map_ata_to_fre_submission, map_share_plan_to_cpc10_grant
from relata.ingestion.models import (
    AtaExtractionResult,
    ExtractedClawbackProvision,
    ExtractedOrganRemuneration,
    ExtractedShareGrantCondition,
)

__all__ = [
    "AtaExtractionResult",
    "AtaExtractor",
    "ExtractedClawbackProvision",
    "ExtractedOrganRemuneration",
    "ExtractedShareGrantCondition",
    "load_document",
    "map_ata_to_fre_submission",
    "map_share_plan_to_cpc10_grant",
]
