"""Pydantic Models for CVM Resolution 80/2022 (Formulário de Referência - Section 8).

Strictly structured to generate valid CVM Sistema Empresas.NET regulatory tables
with synchronized Portuguese (pt-BR) and English (en-US) bilingual fields.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from relata.domain.enums import CorporateBody


class BilingualText(BaseModel):
    """Bilingual statutory text container ensuring synchronized disclosures without translation drift."""

    model_config = ConfigDict(frozen=True)

    pt_br: Annotated[str, Field(min_length=1, description="Texto estatutário oficial em português (CVM)")]
    en_us: Annotated[str, Field(min_length=1, description="Tradução oficial em inglês para investidores/ADRs")]


class OrganRemunerationBreakdown(BaseModel):
    """Item 8.2: Detailed remuneration breakdown by statutory organ."""

    model_config = ConfigDict(frozen=True)

    corporate_body: CorporateBody
    total_members: Annotated[int, Field(ge=0, description="Número total de membros do órgão")]
    remunerated_members: Annotated[int, Field(ge=0, description="Número de membros remunerados")]

    # Remuneração Fixa
    pro_labore_or_salaries_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]
    direct_benefits_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]
    committee_participation_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]
    other_fixed_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]

    # Remuneração Variável
    bonus_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]
    profit_sharing_plr_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]
    other_variable_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]

    # Remuneração Baseada em Ações (CPC 10)
    share_based_equity_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]
    share_based_cash_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]

    # Pós-Emprego e Rescisão
    post_employment_benefits_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]
    termination_severance_brl: Annotated[Decimal, Field(ge=0, default=Decimal("0.0"))]

    @property
    def total_fixed_brl(self) -> Decimal:
        return (
            self.pro_labore_or_salaries_brl
            + self.direct_benefits_brl
            + self.committee_participation_brl
            + self.other_fixed_brl
        )

    @property
    def total_variable_brl(self) -> Decimal:
        return self.bonus_brl + self.profit_sharing_plr_brl + self.other_variable_brl

    @property
    def total_share_based_brl(self) -> Decimal:
        return self.share_based_equity_brl + self.share_based_cash_brl

    @property
    def grand_total_brl(self) -> Decimal:
        return (
            self.total_fixed_brl
            + self.total_variable_brl
            + self.total_share_based_brl
            + self.post_employment_benefits_brl
            + self.termination_severance_brl
        )

    @model_validator(mode="after")
    def validate_member_counts(self) -> OrganRemunerationBreakdown:
        if self.remunerated_members > self.total_members:
            raise ValueError(
                f"Membros remunerados ({self.remunerated_members}) não podem exceder total de membros ({self.total_members})."
            )
        return self


class OrganIndividualSpread(BaseModel):
    """Item 8.6: Minimum, maximum, and average individual compensation per organ."""

    model_config = ConfigDict(frozen=True)

    corporate_body: CorporateBody
    remunerated_members: Annotated[int, Field(ge=0)]
    min_individual_compensation_brl: Annotated[Decimal, Field(ge=0)]
    max_individual_compensation_brl: Annotated[Decimal, Field(ge=0)]
    average_individual_compensation_brl: Annotated[Decimal, Field(ge=0)]

    @model_validator(mode="after")
    def validate_spread_invariants(self) -> OrganIndividualSpread:
        if self.remunerated_members == 0:
            if not (
                self.min_individual_compensation_brl
                == self.max_individual_compensation_brl
                == self.average_individual_compensation_brl
                == Decimal("0.0")
            ):
                raise ValueError("Órgão sem membros remunerados deve ter min, max e média iguais a zero.")
            return self

        if self.min_individual_compensation_brl > self.max_individual_compensation_brl:
            raise ValueError(
                f"Min ({self.min_individual_compensation_brl}) não pode exceder Max ({self.max_individual_compensation_brl})."
            )

        if not (
            self.min_individual_compensation_brl
            <= self.average_individual_compensation_brl
            <= self.max_individual_compensation_brl
        ):
            raise ValueError(
                f"Média ({self.average_individual_compensation_brl}) deve estar entre Min ({self.min_individual_compensation_brl}) e Max ({self.max_individual_compensation_brl})."
            )
        return self


class FRESection8Submission(BaseModel):
    """Complete Formulário de Referência (FRE) Section 8 Statutory Report."""

    model_config = ConfigDict(frozen=True)

    fiscal_year: Annotated[int, Field(ge=2020, le=2050, description="Exercício social de referência")]
    company_name: str
    cnpj: str
    cvm_code: str

    item_8_1_policy_narrative: BilingualText
    item_8_2_organs: list[OrganRemunerationBreakdown]
    item_8_6_spreads: list[OrganIndividualSpread]

    @property
    def grand_total_compensation_brl(self) -> Decimal:
        return sum((organ.grand_total_brl for organ in self.item_8_2_organs), Decimal("0.0"))

    def get_organ_breakdown(self, body: CorporateBody) -> OrganRemunerationBreakdown | None:
        for organ in self.item_8_2_organs:
            if organ.corporate_body == body:
                return organ
        return None

    def get_organ_spread(self, body: CorporateBody) -> OrganIndividualSpread | None:
        for spread in self.item_8_6_spreads:
            if spread.corporate_body == body:
                return spread
        return None
