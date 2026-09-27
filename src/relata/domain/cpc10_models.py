"""Pydantic Models for CPC 10 (R1) / IFRS 2 Share-Based Payment Valuation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from relata.domain.enums import CorporateBody, SettlementMethod, SharePlanType, ValuationModel


class OptionPricingParameters(BaseModel):
    """Parameters required for Black-Scholes / Binomial / Monte Carlo valuation under CPC 10 Item 16."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    spot_price_brl: Annotated[Decimal, Field(gt=0, description="Preço à vista da ação na data da outorga (BRL)")]
    strike_price_brl: Annotated[Decimal, Field(ge=0, description="Preço de exercício estipulado no plano (BRL)")]
    risk_free_rate: Annotated[Decimal, Field(ge=0, lt=1, description="Taxa livre de risco anualizada (ex: NTN-B / CDI projetado)")]
    annual_volatility: Annotated[Decimal, Field(gt=0, description="Volatilidade histórica/implícita anualizada do papel")]
    dividend_yield: Annotated[Decimal, Field(ge=0, lt=1, default=Decimal("0.0"), description="Taxa de dividendos anualizada esperada")]
    time_to_maturity_years: Annotated[Decimal, Field(gt=0, description="Prazo remanescente/esperado até expiração em anos")]


class CPC10Grant(BaseModel):
    """Single share-based payment award under CPC 10 (R1) / IFRS 2."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    grant_id: str
    plan_name: str
    corporate_body: CorporateBody
    plan_type: SharePlanType
    settlement_method: SettlementMethod = SettlementMethod.EQUITY
    valuation_model: ValuationModel = ValuationModel.BLACK_SCHOLES

    grant_date: date
    vesting_start_date: date
    vesting_months: Annotated[int, Field(gt=0, description="Prazo de aquisição de direitos (vesting period) em meses")]
    lock_up_months: Annotated[int, Field(ge=0, default=0, description="Período de restrição pós-vesting")]

    total_shares_granted: Annotated[int, Field(gt=0, description="Número total de opções ou ações outorgadas")]
    pricing_parameters: OptionPricingParameters | None = None
    grant_date_fair_value_unit_brl: Annotated[Decimal, Field(ge=0, description="Valor justo unitário na data da outorga")]
    annual_forfeiture_rate: Annotated[Decimal, Field(ge=0, lt=1, default=Decimal("0.0"), description="Taxa anual estimada de cancelamento/saída")]

    @model_validator(mode="after")
    def validate_pricing_consistency(self) -> CPC10Grant:
        if self.plan_type in (SharePlanType.STOCK_OPTION, SharePlanType.SAR):
            if self.pricing_parameters is None and self.grant_date_fair_value_unit_brl <= 0:
                raise ValueError("Opções de compra e SARs exigem pricing_parameters ou valor justo unitário > 0.")
        return self

    @property
    def total_grant_fair_value_brl(self) -> Decimal:
        """Total gross fair value at grant date before forfeiture adjustment."""
        return Decimal(self.total_shares_granted) * self.grant_date_fair_value_unit_brl


class MonthlyVestingAccrual(BaseModel):
    """Monthly accounting accrual schedule entry recognized in DRE / Income Statement."""

    model_config = ConfigDict(frozen=True)

    month_index: Annotated[int, Field(ge=1, description="Índice mensal (1..N)")]
    year: int
    month: int
    shares_vesting_in_month: int
    period_expense_recognized_brl: Decimal
    cumulative_expense_recognized_brl: Decimal
    unvested_balance_brl: Decimal
    active_shares_expected: int
