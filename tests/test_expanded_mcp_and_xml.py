"""Integration tests for expanded MCP server tools and CVM Empresas.NET XML schema."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from relata.domain.common import BilingualText
from relata.domain.enums import (
    CorporateBody,
    PerformanceMetricCategory,
    SharePlanType,
    StrikeAdjustmentIndex,
)
from relata.domain.models import FRESection8Submission
from relata.domain.plan_models import (
    OptionBalancesItem85,
    PerformanceMetric,
    PlanTranche,
    ShareBasedPlan,
    TerminationPackageItem87,
    VariableCompensationPolicy,
)
from relata.filing.empresas_net_xml import generate_cvm_empresas_net_xml
from relata.mcp.server import RelataMCPServer


def test_mcp_dilution_and_intrinsic_tool() -> None:
    server = RelataMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "relata_calculate_dilution_and_intrinsic_value",
            "arguments": {
                "total_plan_shares": 5000000,
                "total_company_shares": 100000000,
                "spot_price_brl": 42.50,
                "strike_price_brl": 30.00,
                "max_dilution_cap_pct": 5.0,
            },
        },
    }
    resp = server.handle_message(req)
    assert resp is not None
    assert "result" in resp
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert content["dilution_percentage"] == 5.0
    assert content["dilution_compliant"] is True
    assert content["in_the_money"] is True
    assert content["unit_intrinsic_spread_brl"] == 12.50
    assert content["total_intrinsic_value_brl"] == 62500000.0


def test_mcp_ledger_reconcile_tool(sample_valid_submission: FRESection8Submission) -> None:
    server = RelataMCPServer()
    tb = [
        {
            "account_code": "3.1.01.001",
            "account_name": "Salários e Pró-labore",
            "balance_brl": 6960000.00,
            "component": "pro_labore",
        },
        {
            "account_code": "3.1.01.002",
            "account_name": "Bônus",
            "balance_brl": 3000000.00,
            "component": "annual_bonus",
        },
        {
            "account_code": "3.1.01.003",
            "account_name": "PLR",
            "balance_brl": 500000.00,
            "component": "profit_sharing_plr",
        },
        {
            "account_code": "3.1.01.004",
            "account_name": "Ações CPC 10",
            "balance_brl": 2500000.00,
            "component": "share_based_equity",
        },
        {
            "account_code": "3.1.01.005",
            "account_name": "Benefícios Pós-Emprego",
            "balance_brl": 150000.00,
            "component": "post_employment_pension",
        },
    ]

    req = {
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {
            "name": "relata_reconcile_ledger_trial_balance",
            "arguments": {
                "trial_balance": tb,
                "submission": sample_valid_submission.model_dump(mode="json"),
            },
        },
    }
    resp = server.handle_message(req)
    assert resp is not None
    assert "result" in resp
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert content["is_reconciled"] is True
    assert content["net_discrepancy_brl"] == 0.0


def test_mcp_audit_option_balances_tool() -> None:
    server = RelataMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 103,
        "method": "tools/call",
        "params": {
            "name": "relata_audit_option_balances_item_8_5",
            "arguments": {
                "corporate_body": "diretoria_estatutaria",
                "total_options_granted": 100000,
                "unvested_options": 60000,
                "exercisable_options": 40000,
                "exercised_options": 0,
                "forfeited_options": 0,
                "weighted_avg_exercise_price_brl": 25.0,
                "weighted_avg_unvested_strike_brl": 25.0,
                "weighted_avg_exercisable_strike_brl": 25.0,
                "intrinsic_value_exercisable_brl": 400000.0,
                "current_year_recognized_expense_brl": 250000.0,
                "cumulative_recognized_expense_brl": 500000.0,
                "spot_price_brl": 35.0,
            },
        },
    }
    resp = server.handle_message(req)
    assert resp is not None
    assert "result" in resp
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert content["is_valid"] is True
    assert len(content["findings"]) == 0


def test_expanded_xml_generation(sample_valid_submission: FRESection8Submission) -> None:
    # Enrich sample_valid_submission with Items 8.3, 8.4, 8.5, 8.7
    m1 = PerformanceMetric(
        name=BilingualText(pt_br="TSR Relativo", en_us="Relative TSR"),
        category=PerformanceMetricCategory.FINANCIAL,
        weight_pct=Decimal("100.0"),
    )
    pol = VariableCompensationPolicy(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        narrative=BilingualText(pt_br="Política Variável", en_us="Variable Policy"),
        metrics=[m1],
        has_clawback=True,
    )
    t = PlanTranche(
        tranche_id="TR-1",
        grant_date=date(2025, 3, 1),
        share_plan_type=SharePlanType.STOCK_OPTION,
        shares_granted=100000,
        vesting_months=36,
        exercise_strike_brl=Decimal("30.00"),
        strike_adjustment_index=StrikeAdjustmentIndex.IPCA,
        cpc10_grant_fair_value_brl=Decimal("12.50"),
    )
    plan = ShareBasedPlan(
        plan_id="SOP-2025",
        plan_name=BilingualText(pt_br="Plano 2025", en_us="Plan 2025"),
        agm_approval_date=date(2025, 4, 25),
        plan_type=SharePlanType.STOCK_OPTION,
        max_dilution_percentage=Decimal("5.0"),
        tranches=[t],
    )
    bal = OptionBalancesItem85(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        total_options_granted=100000,
        unvested_options=60000,
        exercisable_options=40000,
        weighted_avg_exercise_price_brl=Decimal("30.00"),
        weighted_avg_unvested_strike_brl=Decimal("30.00"),
        weighted_avg_exercisable_strike_brl=Decimal("30.00"),
    )
    pkg = TerminationPackageItem87(
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        has_golden_parachute=False,
        notice_period_months=2,
        statutory_severance_terms=BilingualText(
            pt_br="Rescisão padrão CLT",
            en_us="Standard CLT severance",
        ),
    )

    enriched_submission = FRESection8Submission(
        fiscal_year=sample_valid_submission.fiscal_year,
        company_name=sample_valid_submission.company_name,
        cnpj=sample_valid_submission.cnpj,
        cvm_code=sample_valid_submission.cvm_code,
        item_8_1_policy_narrative=sample_valid_submission.item_8_1_policy_narrative,
        item_8_2_organs=sample_valid_submission.item_8_2_organs,
        item_8_3_variable_policies=[pol],
        item_8_4_share_plans=[plan],
        item_8_5_option_balances=[bal],
        item_8_6_spreads=sample_valid_submission.item_8_6_spreads,
        item_8_7_termination_packages=[pkg],
    )

    xml_output = generate_cvm_empresas_net_xml(enriched_submission)
    assert "<Item8_3_EstruturaRemuneracaoVariavel>" in xml_output
    assert "<Item8_4_PlanosRemuneracaoBaseadaAcoes>" in xml_output
    assert "<Item8_5_SaldosOpcoesReconhecidas>" in xml_output
    assert "<Item8_7_RescisaoBeneficiosPosEmprego>" in xml_output
    assert "SOP-2025" in xml_output
    assert "TSR Relativo" in xml_output
