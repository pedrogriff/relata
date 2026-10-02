"""Domain Enums for Brazilian CVM Resolution 80/2022 & CPC 10 (R1) / IFRS 2."""

from __future__ import annotations

from enum import StrEnum


class CorporateBody(StrEnum):
    """Statutory corporate bodies under Brazilian Corporate Law (Lei 6.404/76) & CVM Res. 80."""

    CONSELHO_ADMINISTRACAO = "conselho_administracao"
    DIRETORIA_ESTATUTARIA = "diretoria_estatutaria"
    CONSELHO_FISCAL = "conselho_fiscal"
    COMITE_AUDITORIA = "comite_auditoria"
    COMITE_REMUNERACAO = "comite_remuneracao"

    @property
    def label_pt(self) -> str:
        labels = {
            CorporateBody.CONSELHO_ADMINISTRACAO: "Conselho de Administração",
            CorporateBody.DIRETORIA_ESTATUTARIA: "Diretoria Estatutária",
            CorporateBody.CONSELHO_FISCAL: "Conselho Fiscal",
            CorporateBody.COMITE_AUDITORIA: "Comitê de Auditoria Estatutário",
            CorporateBody.COMITE_REMUNERACAO: "Comitê de Remuneração",
        }
        return labels[self]

    @property
    def label_en(self) -> str:
        labels = {
            CorporateBody.CONSELHO_ADMINISTRACAO: "Board of Directors",
            CorporateBody.DIRETORIA_ESTATUTARIA: "Statutory Executive Board",
            CorporateBody.CONSELHO_FISCAL: "Fiscal Council",
            CorporateBody.COMITE_AUDITORIA: "Statutory Audit Committee",
            CorporateBody.COMITE_REMUNERACAO: "Compensation Committee",
        }
        return labels[self]


class CompensationComponent(StrEnum):
    """Compensation components classified under CVM Resolution 80 Section 8 (Item 8.2)."""

    PRO_LABORE = "pro_labore"
    SALARY = "salary"
    DIRECT_BENEFITS = "direct_benefits"
    COMMITTEE_PARTICIPATION = "committee_participation"
    OTHER_FIXED = "other_fixed"
    ANNUAL_BONUS = "annual_bonus"
    PROFIT_SHARING_PLR = "profit_sharing_plr"
    OTHER_VARIABLE = "other_variable"
    SHARE_BASED_EQUITY = "share_based_equity"
    SHARE_BASED_CASH = "share_based_cash"
    POST_EMPLOYMENT_PENSION = "post_employment_pension"
    TERMINATION_INDEMNITY = "termination_indemnity"


class SharePlanType(StrEnum):
    """Share-based payment plans governed by CPC 10 (R1) / IFRS 2 & CVM Res. 80 Items 8.4-8.6."""

    STOCK_OPTION = "stock_option"
    RESTRICTED_SHARES = "restricted_shares"
    PERFORMANCE_SHARES = "performance_shares"
    PHANTOM_STOCK = "phantom_stock"
    SAR = "sar"

    @property
    def label_pt(self) -> str:
        labels = {
            SharePlanType.STOCK_OPTION: "Opções de Compra de Ações (Stock Options)",
            SharePlanType.RESTRICTED_SHARES: "Ações Restritas (RSUs)",
            SharePlanType.PERFORMANCE_SHARES: "Ações de Performance (PSUs)",
            SharePlanType.PHANTOM_STOCK: "Ações Fantasma (Phantom Stock)",
            SharePlanType.SAR: "Direito de Valorização de Ações (SAR)",
        }
        return labels[self]

    @property
    def label_en(self) -> str:
        labels = {
            SharePlanType.STOCK_OPTION: "Stock Options",
            SharePlanType.RESTRICTED_SHARES: "Restricted Share Units (RSUs)",
            SharePlanType.PERFORMANCE_SHARES: "Performance Share Units (PSUs)",
            SharePlanType.PHANTOM_STOCK: "Phantom Stock",
            SharePlanType.SAR: "Stock Appreciation Rights (SARs)",
        }
        return labels[self]


class SettlementMethod(StrEnum):
    """Settlement method under CPC 10 / IFRS 2 (Equity-Settled vs. Cash-Settled)."""

    EQUITY = "equity"  # Liquidação em Ações (Patrimônio Líquido)
    CASH = "cash"      # Liquidação em Caixa (Passivo Circulante/Não Circulante)


class ValuationModel(StrEnum):
    """Valuation models recognized under CPC 10 (R1) / IFRS 2 Item 16."""

    BLACK_SCHOLES = "black_scholes"
    BINOMIAL_LATTICE = "binomial_lattice"
    MONTE_CARLO = "monte_carlo"
    GRANT_DATE_MARKET_PRICE = "grant_date_market_price"


class PerformanceMetricCategory(StrEnum):
    """Categories of performance metrics for variable compensation under CVM Item 8.3."""

    FINANCIAL = "financial"          # TSR, ROIC, EBITDA, Lucro Líquido, FCF
    OPERATIONAL = "operational"      # Eficiência, Churn, NPS, SLAs
    ESG_SUSTAINABILITY = "esg"       # Descarbonização, Diversidade, Saúde e Segurança
    STRATEGIC = "strategic"          # M&A, Inovação, Transformação Digital


class StrikeAdjustmentIndex(StrEnum):
    """Monetary index used for strike price adjustments in Brazilian share plans (Item 8.4)."""

    FIXED = "fixed"                  # Preço fixo nominal sem correção
    IPCA = "ipca"                    # Índice Nacional de Preços ao Consumidor Amplo (IBGE)
    IGPM = "igpm"                    # Índice Geral de Preços do Mercado (FGV)
    CDI = "cdi"                      # Taxa de Depósito Interfinanceiro (B3)
    TR = "tr"                        # Taxa Referencial


class OptionStatus(StrEnum):
    """Status lifecycle of options and restricted share awards under CVM Item 8.5."""

    UNVESTED = "unvested"            # A Vencer (em período de carência/vesting)
    EXERCISABLE = "exercisable"      # Exercíveis (já adquiridas / vested mas não exercidas)
    EXERCISED = "exercised"          # Exercidas no exercício social
    FORFEITED = "forfeited"          # Canceladas por desligamento ou expiração


class TerminationType(StrEnum):
    """Termination conditions and severance classifications under CVM Item 8.7."""

    DISMISSAL_WITHOUT_CAUSE = "dismissal_without_cause"  # Rescisão sem justa causa (CLT Art. 477)
    DISMISSAL_WITH_CAUSE = "dismissal_with_cause"        # Rescisão com justa causa (CLT Art. 482)
    RESIGNATION = "resignation"                          # Renúncia / Pedido de demissão
    RETIREMENT = "retirement"                            # Aposentadoria estatutária
    CHANGE_OF_CONTROL = "change_of_control"              # Cláusula de mudança de controle (Golden Parachute)

