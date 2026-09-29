"""Comprehensive Test Suite for Relata Model Context Protocol (MCP) Server.

Tests JSON-RPC 2.0 handshake, all 6 exposed tools, resources, error handling,
and stdio transport loop.
"""

from __future__ import annotations

import io
import json

import pytest

from relata.domain.models import FRESection8Submission
from relata.mcp.protocol import INVALID_PARAMS, METHOD_NOT_FOUND
from relata.mcp.server import RelataMCPServer
from relata.mcp.stdio import run_stdio_server


@pytest.fixture
def mcp_server() -> RelataMCPServer:
    return RelataMCPServer()


def test_mcp_handshake_and_ping(mcp_server: RelataMCPServer) -> None:
    # 1. Initialize
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "cursor-agent", "version": "1.0.0"},
        },
    }
    resp = mcp_server.handle_message(init_msg)
    assert resp is not None
    assert resp["id"] == 1
    assert resp["result"]["protocolVersion"] == "2024-11-05"
    assert "tools" in resp["result"]["capabilities"]
    assert "resources" in resp["result"]["capabilities"]
    assert resp["result"]["serverInfo"]["name"] == "relata-mcp"

    # 2. Notification (no response expected)
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    assert mcp_server.handle_message(notif) is None

    # 3. Ping
    ping_msg = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
    ping_resp = mcp_server.handle_message(ping_msg)
    assert ping_resp is not None
    assert ping_resp["id"] == 2
    assert ping_resp["result"] == {}


def test_mcp_tools_list(mcp_server: RelataMCPServer) -> None:
    msg = {"jsonrpc": "2.0", "id": 10, "method": "tools/list"}
    resp = mcp_server.handle_message(msg)
    assert resp is not None
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    expected = [
        "relata_calculate_cpc10_fair_value",
        "relata_generate_cpc10_accruals",
        "relata_distribute_shares",
        "relata_reconcile_fre_section_8",
        "relata_ingest_corporate_minutes",
        "relata_generate_empresas_net_xml",
    ]
    for exp in expected:
        assert exp in tool_names


def test_tool_call_calculate_cpc10_fair_value(mcp_server: RelataMCPServer) -> None:
    call_msg = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": "relata_calculate_cpc10_fair_value",
            "arguments": {
                "spot_price_brl": 35.50,
                "strike_price_brl": 35.00,
                "risk_free_rate": 0.105,
                "annual_volatility": 0.32,
                "dividend_yield": 0.025,
                "time_to_maturity_years": 3.0,
            },
        },
    }
    resp = mcp_server.handle_message(call_msg)
    assert resp is not None
    assert resp["id"] == 20
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert content["unit_fair_value_brl"] > 10.0


def test_tool_call_generate_cpc10_accruals(mcp_server: RelataMCPServer) -> None:
    call_msg = {
        "jsonrpc": "2.0",
        "id": 21,
        "method": "tools/call",
        "params": {
            "name": "relata_generate_cpc10_accruals",
            "arguments": {
                "total_shares_granted": 120000,
                "vesting_months": 36,
                "unit_fair_value_brl": 12.50,
                "annual_forfeiture_rate": 0.03,
                "grant_date": "2025-01-15",
            },
        },
    }
    resp = mcp_server.handle_message(call_msg)
    assert resp is not None
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert len(content["schedule"]) == 36
    assert content["total_recognized_expense_brl"] > 0


def test_tool_call_distribute_shares(mcp_server: RelataMCPServer) -> None:
    call_msg = {
        "jsonrpc": "2.0",
        "id": 22,
        "method": "tools/call",
        "params": {
            "name": "relata_distribute_shares",
            "arguments": {
                "total_shares": 1000,
                "weights": [0.33, 0.33, 0.22, 0.12],
            },
        },
    }
    resp = mcp_server.handle_message(call_msg)
    assert resp is not None
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert content["total_shares_allocated"] == 1000
    assert content["exact_conservation"] is True


def test_tool_call_reconcile_and_generate_xml(
    mcp_server: RelataMCPServer,
    sample_valid_submission: FRESection8Submission,
) -> None:
    sub_dict = sample_valid_submission.model_dump(mode="json")

    # 1. Reconcile
    reconcile_msg = {
        "jsonrpc": "2.0",
        "id": 23,
        "method": "tools/call",
        "params": {
            "name": "relata_reconcile_fre_section_8",
            "arguments": {"submission": sub_dict},
        },
    }
    resp = mcp_server.handle_message(reconcile_msg)
    assert resp is not None
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert content["is_valid"] is True

    # 2. XML Generation
    xml_msg = {
        "jsonrpc": "2.0",
        "id": 24,
        "method": "tools/call",
        "params": {
            "name": "relata_generate_empresas_net_xml",
            "arguments": {"submission": sub_dict},
        },
    }
    resp_xml = mcp_server.handle_message(xml_msg)
    assert resp_xml is not None
    xml_content = json.loads(resp_xml["result"]["content"][0]["text"])
    assert xml_content["status"] == "success"
    assert "<FormularioReferencia" in xml_content["xml_content"]


def test_tool_call_ingest_corporate_minutes(mcp_server: RelataMCPServer) -> None:
    sample_text = (
        "COMPANHIA ABC S.A. - CNPJ 12.345.678/0001-99\n"
        "ATA DA ASSEMBLEIA GERAL ORDINÁRIA DE 30 DE ABRIL DE 2025\n"
        "Aprovado o montante global de R$ 10.000.000,00 para remuneração dos administradores."
    )
    ingest_msg = {
        "jsonrpc": "2.0",
        "id": 25,
        "method": "tools/call",
        "params": {
            "name": "relata_ingest_corporate_minutes",
            "arguments": {"document_text": sample_text},
        },
    }
    resp = mcp_server.handle_message(ingest_msg)
    assert resp is not None
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert "extraction" in content
    assert content["extraction"]["global_compensation_ceiling_brl"] == "10000000.00"


def test_mcp_resources(mcp_server: RelataMCPServer) -> None:
    list_msg = {"jsonrpc": "2.0", "id": 30, "method": "resources/list"}
    list_resp = mcp_server.handle_message(list_msg)
    assert list_resp is not None
    uris = [r["uri"] for r in list_resp["result"]["resources"]]
    assert "relata://regulations/cvm-resolution-80" in uris
    assert "relata://accounting/cpc-10-r1" in uris

    # Read resource
    read_msg = {
        "jsonrpc": "2.0",
        "id": 31,
        "method": "resources/read",
        "params": {"uri": "relata://regulations/cvm-resolution-80"},
    }
    read_resp = mcp_server.handle_message(read_msg)
    assert read_resp is not None
    assert "Remuneração dos Administradores" in read_resp["result"]["contents"][0]["text"]


def test_mcp_error_handling(mcp_server: RelataMCPServer) -> None:
    # 1. Method not found
    bad_method = {"jsonrpc": "2.0", "id": 99, "method": "unknown/method"}
    resp = mcp_server.handle_message(bad_method)
    assert resp is not None
    assert resp["error"]["code"] == METHOD_NOT_FOUND

    # 2. Unknown tool
    bad_tool = {
        "jsonrpc": "2.0",
        "id": 100,
        "method": "tools/call",
        "params": {"name": "non_existent_tool"},
    }
    resp2 = mcp_server.handle_message(bad_tool)
    assert resp2 is not None
    assert resp2["error"]["code"] == INVALID_PARAMS


def test_mcp_stdio_transport() -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    input_stream = io.StringIO(json.dumps(req) + "\n")
    output_stream = io.StringIO()
    err_stream = io.StringIO()

    run_stdio_server(stdin=input_stream, stdout=output_stream, stderr=err_stream)

    out_lines = [json.loads(line) for line in output_stream.getvalue().splitlines() if line.strip()]
    assert len(out_lines) == 1
    assert out_lines[0]["id"] == 1
    assert out_lines[0]["result"]["serverInfo"]["name"] == "relata-mcp"
