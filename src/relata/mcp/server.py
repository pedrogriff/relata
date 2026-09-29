"""Relata Model Context Protocol (MCP) Server.

Exposes CVM Resolution 80/2022 regulatory tools, CPC 10 (R1) / IFRS 2 equity accounting
calculators, and unstructured document ingestion to Cursor, Claude Desktop, and AI agents.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

from relata.domain.cpc10_models import CPC10Grant, OptionPricingParameters
from relata.domain.enums import CorporateBody, SettlementMethod, SharePlanType, ValuationModel
from relata.domain.models import FRESection8Submission
from relata.engine.cpc10_calculator import (
    calculate_black_scholes_call,
    generate_cpc10_accrual_schedule,
)
from relata.engine.reconciler import reconcile_fre_section_8
from relata.engine.share_distributor import distribute_integer_shares
from relata.filing.empresas_net_xml import generate_cvm_empresas_net_xml
from relata.ingestion.extractor import AtaExtractor
from relata.mcp.protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    LATEST_PROTOCOL_VERSION,
    METHOD_NOT_FOUND,
    ResourceContent,
    ResourceDefinition,
    ToolCallResult,
    ToolDefinition,
)


class RelataMCPServer:
    """Enterprise MCP Server for CVM Regulatory Reporting & Executive Compensation."""

    SERVER_NAME = "relata-mcp"
    SERVER_VERSION = "0.1.0"

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = self._register_tools()
        self._resources: dict[str, ResourceDefinition] = self._register_resources()

    def _register_tools(self) -> dict[str, ToolDefinition]:
        tools = [
            ToolDefinition(
                name="relata_calculate_cpc10_fair_value",
                description=(
                    "Calculates European Call Option fair value under CPC 10 (R1) Item 16 / IFRS 2 "
                    "using continuous dividend Black-Scholes formula."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "spot_price_brl": {"type": "number", "description": "Spot stock price on B3 (BRL)"},
                        "strike_price_brl": {"type": "number", "description": "Strike / exercise price (BRL)"},
                        "risk_free_rate": {"type": "number", "description": "Annual risk-free rate (e.g. 0.105 for 10.5%)"},
                        "annual_volatility": {"type": "number", "description": "Annualized historical or implied volatility (e.g. 0.32)"},
                        "dividend_yield": {"type": "number", "default": 0.0, "description": "Expected annual dividend yield (e.g. 0.025)"},
                        "time_to_maturity_years": {"type": "number", "description": "Expected term to maturity in years (e.g. 3.0)"},
                    },
                    "required": ["spot_price_brl", "strike_price_brl", "risk_free_rate", "annual_volatility", "time_to_maturity_years"],
                },
            ),
            ToolDefinition(
                name="relata_generate_cpc10_accruals",
                description=(
                    "Generates straight-line monthly P&L accrual schedules under CPC 10 (R1) Item 19, "
                    "incorporating annual forfeiture/turnover rates and exact share vesting distributions."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "total_shares_granted": {"type": "integer", "description": "Total options or shares granted"},
                        "vesting_months": {"type": "integer", "description": "Vesting duration in months (e.g. 36 or 48)"},
                        "unit_fair_value_brl": {"type": "number", "description": "Unit fair value at grant date (BRL)"},
                        "annual_forfeiture_rate": {"type": "number", "default": 0.0, "description": "Estimated annual exit/forfeiture rate (e.g. 0.03)"},
                        "grant_date": {"type": "string", "description": "Grant date YYYY-MM-DD (defaults to today)"},
                    },
                    "required": ["total_shares_granted", "vesting_months", "unit_fair_value_brl"],
                },
            ),
            ToolDefinition(
                name="relata_distribute_shares",
                description=(
                    "Distributes integer shares across fractional vesting weights using the Largest Remainder Method, "
                    "guaranteeing the mathematical invariant: sum(allocated_shares) == total_shares."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "total_shares": {"type": "integer", "description": "Total integer shares to conserve"},
                        "weights": {"type": "array", "items": {"type": "number"}, "description": "List of fractional weights"},
                    },
                    "required": ["total_shares", "weights"],
                },
            ),
            ToolDefinition(
                name="relata_reconcile_fre_section_8",
                description=(
                    "Deterministically reconciles CVM Resolution 80 Section 8 statutory reports, "
                    "verifying corporate body sums, individual spread invariants (Min <= Avg <= Max), and pool consistency."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "submission": {"type": "object", "description": "Full FRESection8Submission JSON object"},
                    },
                    "required": ["submission"],
                },
            ),
            ToolDefinition(
                name="relata_ingest_corporate_minutes",
                description=(
                    "Parses unstructured Brazilian corporate minutes (Atas de AGO/AGE/RCA) using Gemini Flash 3.8 "
                    "and LGPD Art. 18 zero-retention CPF tokenization, producing structured CVM compensation data."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_text": {"type": "string", "description": "Raw text or extracted PDF text of the Ata"},
                        "gemini_api_key": {"type": "string", "description": "Optional Gemini API Key for live inference"},
                    },
                    "required": ["document_text"],
                },
            ),
            ToolDefinition(
                name="relata_generate_empresas_net_xml",
                description=(
                    "Generates official CVM Sistema Empresas.NET XML document from a validated "
                    "FRE Section 8 submission for direct regulatory filing."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "submission": {"type": "object", "description": "Validated FRESection8Submission JSON object"},
                    },
                    "required": ["submission"],
                },
            ),
        ]
        return {t.name: t for t in tools}

    def _register_resources(self) -> dict[str, ResourceDefinition]:
        resources = [
            ResourceDefinition(
                uri="relata://regulations/cvm-resolution-80",
                name="CVM Resolution 80/2022 Reference",
                description="Statutory guidelines for Formulário de Referência (FRE) Section 8 (Remuneração dos Administradores).",
                mimeType="text/markdown",
            ),
            ResourceDefinition(
                uri="relata://accounting/cpc-10-r1",
                name="CPC 10 (R1) / IFRS 2 Accounting Guide",
                description="Accounting standard for Share-based Payment (Pagamento Baseado em Ações) fair value and amortization.",
                mimeType="text/markdown",
            ),
        ]
        return {r.uri: r for r in resources}

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Processes an incoming JSON-RPC 2.0 message."""
        if not isinstance(message, dict):
            return {"jsonrpc": "2.0", "id": None, "error": {"code": INVALID_REQUEST, "message": "Invalid request."}}

        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {}) or {}

        # Handle notifications (no response expected)
        if method and method.startswith("notifications/"):
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": LATEST_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": {
                        "name": self.SERVER_NAME,
                        "version": self.SERVER_VERSION,
                    },
                },
            }

        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": [t.model_dump() for t in self._tools.values()]},
            }

        if method == "tools/call":
            return self._handle_tool_call(msg_id, params)

        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"resources": [r.model_dump() for r in self._resources.values()]},
            }

        if method == "resources/read":
            return self._handle_resource_read(msg_id, params)

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": METHOD_NOT_FOUND, "message": f"Method '{method}' not recognized."},
        }

    def _handle_tool_call(self, msg_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}

        if tool_name not in self._tools:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": INVALID_PARAMS, "message": f"Unknown tool: '{tool_name}'."},
            }

        try:
            if tool_name == "relata_calculate_cpc10_fair_value":
                result = self._exec_calculate_fair_value(arguments)
            elif tool_name == "relata_generate_cpc10_accruals":
                result = self._exec_generate_accruals(arguments)
            elif tool_name == "relata_distribute_shares":
                result = self._exec_distribute_shares(arguments)
            elif tool_name == "relata_reconcile_fre_section_8":
                result = self._exec_reconcile_fre(arguments)
            elif tool_name == "relata_ingest_corporate_minutes":
                result = self._exec_ingest_minutes(arguments)
            elif tool_name == "relata_generate_empresas_net_xml":
                result = self._exec_generate_xml(arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": METHOD_NOT_FOUND, "message": f"Tool '{tool_name}' not implemented."},
                }

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": ToolCallResult(
                    content=[{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]
                ).model_dump(),
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": INTERNAL_ERROR, "message": f"Tool execution failed: {exc}"},
            }

    def _exec_calculate_fair_value(self, args: dict[str, Any]) -> dict[str, Any]:
        params = OptionPricingParameters(
            spot_price_brl=Decimal(str(args["spot_price_brl"])),
            strike_price_brl=Decimal(str(args["strike_price_brl"])),
            risk_free_rate=Decimal(str(args["risk_free_rate"])),
            annual_volatility=Decimal(str(args["annual_volatility"])),
            dividend_yield=Decimal(str(args.get("dividend_yield", 0.0))),
            time_to_maturity_years=Decimal(str(args["time_to_maturity_years"])),
        )
        fv = calculate_black_scholes_call(params)
        return {
            "status": "success",
            "model": "Black-Scholes (CPC 10 / IFRS 2)",
            "unit_fair_value_brl": float(fv),
            "spot_price_brl": float(params.spot_price_brl),
            "strike_price_brl": float(params.strike_price_brl),
            "time_to_maturity_years": float(params.time_to_maturity_years),
        }

    def _exec_generate_accruals(self, args: dict[str, Any]) -> dict[str, Any]:
        grant_date_val = date.fromisoformat(args["grant_date"]) if "grant_date" in args else date.today()
        grant = CPC10Grant(
            grant_id="MCP-GRANT",
            plan_name="Plano de Opções Outorgado",
            corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
            plan_type=SharePlanType.STOCK_OPTION,
            settlement_method=SettlementMethod.EQUITY,
            valuation_model=ValuationModel.BLACK_SCHOLES,
            grant_date=grant_date_val,
            vesting_start_date=grant_date_val,
            vesting_months=int(args["vesting_months"]),
            total_shares_granted=int(args["total_shares_granted"]),
            grant_date_fair_value_unit_brl=Decimal(str(args["unit_fair_value_brl"])),
            annual_forfeiture_rate=Decimal(str(args.get("annual_forfeiture_rate", 0.0))),
        )
        schedule = generate_cpc10_accrual_schedule(grant)
        return {
            "status": "success",
            "total_shares": grant.total_shares_granted,
            "total_months": grant.vesting_months,
            "total_recognized_expense_brl": float(schedule[-1].cumulative_expense_recognized_brl),
            "schedule": [s.model_dump(mode="json") for s in schedule],
        }

    def _exec_distribute_shares(self, args: dict[str, Any]) -> dict[str, Any]:
        total = int(args["total_shares"])
        weights = [Decimal(str(w)) for w in args["weights"]]
        shares = distribute_integer_shares(total, weights)
        return {
            "status": "success",
            "total_shares_input": total,
            "total_shares_allocated": sum(shares),
            "shares_per_tranche": shares,
            "exact_conservation": sum(shares) == total,
        }

    def _exec_reconcile_fre(self, args: dict[str, Any]) -> dict[str, Any]:
        sub_data = args["submission"]
        submission = FRESection8Submission.model_validate(sub_data)
        report = reconcile_fre_section_8(submission)
        return {
            "status": "success",
            "is_valid": report.is_valid,
            "grand_total_brl": float(report.grand_total_brl),
            "findings": [
                {
                    "severity": f.severity.value,
                    "item_code": f.item_code,
                    "organ": f.organ,
                    "message": f.message,
                }
                for f in report.findings
            ],
        }

    def _exec_ingest_minutes(self, args: dict[str, Any]) -> dict[str, Any]:
        doc_text = args["document_text"]
        api_key = args.get("gemini_api_key")
        extractor = AtaExtractor(api_key=api_key)
        extracted = extractor.extract(doc_text)
        return {
            "status": "success",
            "extraction": extracted.model_dump(mode="json"),
        }

    def _exec_generate_xml(self, args: dict[str, Any]) -> dict[str, Any]:
        sub_data = args["submission"]
        submission = FRESection8Submission.model_validate(sub_data)
        xml_str = generate_cvm_empresas_net_xml(submission)
        return {
            "status": "success",
            "xml_length_bytes": len(xml_str.encode("utf-8")),
            "xml_content": xml_str,
        }

    def _handle_resource_read(self, msg_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        uri = params.get("uri")
        if uri == "relata://regulations/cvm-resolution-80":
            text = (
                "# CVM Resolution 80/2022 — Formulário de Referência (FRE) Section 8\n\n"
                "Focuses on 'Remuneração dos Administradores' across Brazilian corporate bodies:\n"
                "- Item 8.1: Qualitative compensation policy description & ESG alignment.\n"
                "- Item 8.2: Total compensation by organ (Conselho de Administração, Diretoria, Conselho Fiscal).\n"
                "- Item 8.3: Variable compensation structure & performance targets.\n"
                "- Item 8.4 & 8.5: Share-based compensation plans and accounting recognition (CPC 10).\n"
                "- Item 8.6: Minimum, maximum, and average individual compensation per body.\n"
                "- Item 8.7: Post-employment benefits and termination severance.\n"
            )
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"contents": [ResourceContent(uri=uri, text=text, mimeType="text/markdown").model_dump()]},
            }

        if uri == "relata://accounting/cpc-10-r1":
            text = (
                "# CPC 10 (R1) / IFRS 2 — Share-Based Payment (Pagamento Baseado em Ações)\n\n"
                "Key Accounting Mandates:\n"
                "- Item 16: Fair value estimation at grant date via Black-Scholes, Binomial Lattice, or Monte Carlo.\n"
                "- Item 19: Straight-line recognition over vesting duration (pro-rata temporis).\n"
                "- Adjustment for expected annual forfeiture/turnover rates without reversing market condition impacts.\n"
                "- Exact share conservation across tranche schedules.\n"
            )
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"contents": [ResourceContent(uri=uri, text=text, mimeType="text/markdown").model_dump()]},
            }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": INVALID_PARAMS, "message": f"Resource URI '{uri}' not found."},
        }
