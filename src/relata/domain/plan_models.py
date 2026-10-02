"""Pydantic Models for CVM Resolution 80/2022 Section 8 Items 8.3, 8.4, 8.5, and 8.7.

Models variable compensation structures (8.3), share-based compensation plans (8.4),
recognized stock option balances and intrinsic values (8.5), and termination terms (8.7).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from relata.domain.common import BilingualText
from relata.domain.enums import (
    CorporateBody,
    PerformanceMetricCategory,
    SettlementMethod,
    SharePlanType,
    StrikeAdjustmentIndex,
)


class PerformanceMetric(BaseModel):
    """Performance metric/KPI governing variable compensation (Item 8.3)."""

    model_config = ConfigDict(frozen=True)

    name: BilingualText
    category: PerformanceMetricCategory
    weight_pct: Annotated[Decimal, Field(gt=0, le=100, description="Peso da métrica em percentual")]
    threshold_pct: Annotated[Decimal, Field(gt=0, description="Gatilho mínimo de atingimento (% do target)")] = Decimal("80.0")
    target_pct: Annotated[Decimal, Field(gt=0, description="Meta orçada (100%)")] = Decimal("100.0")
    max_cap_pct: Annotated[Decimal, Field(gt=0, description="Teto máximo de remuneração variável (% do target)")] = Decimal("150.0")
    actual_attainment_pct: Decimal | None = None


class VariableCompensationPolicy(BaseModel):
    """Item 8.3: Variable compensation policy, metrics, targets, and clawback mechanisms."""

    model_config = ConfigDict(frozen=True)

    corporate_body: CorporateBody
    narrative: BilingualText
    metrics: list[PerformanceMetric] = []
    has_clawback: bool = True
    clawback_description: BilingualText | None = None
    has_malus: bool = False
    deferral_period_months: Annotated[int, Field(ge=0, description="Prazo de diferimento em meses")] = 0

    @property
    def total_weight_pct(self) -> Decimal:
        return sum((m.weight_pct for m in self.metrics), Decimal("0.0"))

    @model_validator(mode="after")
    def validate_total_weight(self) -> VariableCompensationPolicy:
        if self.metrics and abs(self.total_weight_pct - Decimal("100.0")) > Decimal("0.01"):
            raise ValueError(f"Soma dos pesos das métricas ({self.total_weight_pct}%) deve ser igual a 100.0%.")
        return self


class PlanTranche(BaseModel):
    """Individual grant tranche or series within a share-based plan (Item 8.4)."""

    model_config = ConfigDict(frozen=True)

    tranche_id: str
    grant_date: date
    share_plan_type: SharePlanType
    shares_granted: Annotated[int, Field(gt=0, description="Número de opções ou ações outorgadas na série")]
    vesting_months: Annotated[int, Field(gt=0, description="Prazo de carência em meses")]
    lock_up_months: Annotated[int, Field(ge=0, description="Prazo de restrição pós-aquisição")] = 0
    exercise_strike_brl: Annotated[Decimal, Field(ge=0, description="Preço de exercício unitário em BRL")]
    strike_adjustment_index: StrikeAdjustmentIndex = StrikeAdjustmentIndex.FIXED
    settlement_method: SettlementMethod = SettlementMethod.EQUITY
    cpc10_grant_fair_value_brl: Annotated[Decimal, Field(ge=0, description="Valor justo unitário calculado pelo CPC 10")] = Decimal("0.0")

    @property
    def total_tranche_grant_value_brl(self) -> Decimal:
        return self.cpc10_grant_fair_value_brl * Decimal(self.shares_granted)


class ShareBasedPlan(BaseModel):
    """Item 8.4: Share-based compensation plan (Stock Options, RSUs, PSUs, Phantom Stock)."""

    model_config = ConfigDict(frozen=True)

    plan_id: str
    plan_name: BilingualText
    agm_approval_date: date
    plan_type: SharePlanType
    max_dilution_percentage: Annotated[Decimal, Field(ge=0, le=100, description="Limite estatutário máximo de diluição (% do capital)")]
    tranches: list[PlanTranche] = []

    @property
    def total_shares_granted(self) -> int:
        return sum(t.shares_granted for t in self.tranches)

    @property
    def weighted_average_strike_price_brl(self) -> Decimal:
        if not self.tranches or self.total_shares_granted == 0:
            return Decimal("0.0")
        total_strike_val = sum((t.exercise_strike_brl * Decimal(t.shares_granted) for t in self.tranches), Decimal("0.0"))
        return total_strike_val / Decimal(self.total_shares_granted)

    @property
    def weighted_average_vesting_months(self) -> Decimal:
        if not self.tranches or self.total_shares_granted == 0:
            return Decimal("0.0")
        total_vest_val = sum((Decimal(t.vesting_months) * Decimal(t.shares_granted) for t in self.tranches), Decimal("0.0"))
        return total_vest_val / Decimal(self.total_shares_granted)


class OptionBalancesItem85(BaseModel):
    """Item 8.5: Stock option balances, recognized expenses, exercisable units, and intrinsic value."""

    model_config = ConfigDict(frozen=True)

    corporate_body: CorporateBody
    total_options_granted: Annotated[int, Field(ge=0, description="Total acumulado de opções outorgadas")]
    unvested_options: Annotated[int, Field(ge=0, description="Opções a vencer (em carência)")]
    exercisable_options: Annotated[int, Field(ge=0, description="Opções exercíveis (já adquiridas)")]
    exercised_options: Annotated[int, Field(ge=0, description="Opções exercidas no exercício")] = 0
    forfeited_options: Annotated[int, Field(ge=0, description="Opções canceladas/expiradas")] = 0

    weighted_avg_exercise_price_brl: Annotated[Decimal, Field(ge=0, description="Preço médio ponderado de exercício total")]
    weighted_avg_unvested_strike_brl: Annotated[Decimal, Field(ge=0, description="Preço médio de exercício das opções a vencer")]
    weighted_avg_exercisable_strike_brl: Annotated[Decimal, Field(ge=0, description="Preço médio de exercício das opções exercíveis")]

    intrinsic_value_exercisable_brl: Annotated[Decimal, Field(ge=0, description="Valor intrínseco das opções exercíveis em BRL")] = Decimal("0.0")
    current_year_recognized_expense_brl: Annotated[Decimal, Field(ge=0, description="Despesa reconhecida no resultado no exercício social")] = Decimal("0.0")
    cumulative_recognized_expense_brl: Annotated[Decimal, Field(ge=0, description="Despesa acumulada reconhecida até o exercício")] = Decimal("0.0")

    @property
    def active_options(self) -> int:
        return self.unvested_options + self.exercisable_options

    @model_validator(mode="after")
    def validate_option_conservation(self) -> OptionBalancesItem85:
        reconciled_sum = self.unvested_options + self.exercisable_options + self.exercised_options + self.forfeited_options
        if reconciled_sum != self.total_options_granted:
            raise ValueError(
                f"Soma dos saldos de opções ({reconciled_sum}: {self.unvested_options} a vencer + "
                f"{self.exercisable_options} exercíveis + {self.exercised_options} exercidas + "
                f"{self.forfeited_options} canceladas) diverge do total outorgado ({self.total_options_granted})."
            )
        return self


class TerminationPackageItem87(BaseModel):
    """Item 8.7: Post-employment benefits, golden parachutes, and termination conditions."""

    model_config = ConfigDict(frozen=True)

    corporate_body: CorporateBody
    has_golden_parachute: bool = False
    golden_parachute_terms: BilingualText | None = None
    notice_period_months: Annotated[int, Field(ge=0, description="Aviso prévio contratual em meses")] = 0
    non_compete_duration_months: Annotated[int, Field(ge=0, description="Duração do pacto de não concorrência")] = 0
    non_compete_monthly_indemnity_brl: Annotated[Decimal, Field(ge=0, description="Indenização mensal por não concorrência")] = Decimal("0.0")
    statutory_severance_terms: BilingualText
