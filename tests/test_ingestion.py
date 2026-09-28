"""Tests for unstructured document ingestion, Gemini Flash 3.8 extractor, and FRE mapping."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from relata.domain.enums import CorporateBody, SharePlanType
from relata.engine.reconciler import reconcile_fre_section_8
from relata.filing.empresas_net_xml import generate_cvm_empresas_net_xml
from relata.ingestion.document_loader import load_document
from relata.ingestion.extractor import AtaExtractor
from relata.ingestion.mapper import map_ata_to_fre_submission, map_share_plan_to_cpc10_grant
from relata.ingestion.models import (
    AtaExtractionResult,
    ExtractedShareGrantCondition,
)

SAMPLE_ATA_TEXT = """
COMPANHIA BRASILEIRA DE TECNOLOGIA S.A.
CNPJ nº 10.987.654/0001-32 - NIRE 35.300.123.456
ATA DA ASSEMBLEIA GERAL ORDINÁRIA REALIZADA EM 28 DE ABRIL DE 2025

1. DATA, HORA E LOCAL: Realizada em 28 de abril de 2025, às 10:00 horas, na sede social.
2. ORDEM DO DIA:
(a) Tomar as contas dos administradores e examinar as demonstrações financeiras do exercício findo em 31/12/2024;
(b) Fixar a remuneração global dos administradores para o exercício social de 2025, nos termos do Art. 152 da Lei 6.404/76;
(c) Deliberar sobre a outorga de opções de compra de ações para membros da Diretoria Estatutária.

3. DELIBERAÇÕES:
3.1. Foi aprovada, por unanimidade dos presentes, a fixação do montante global anual de remuneração
dos administradores no valor de até R$ 20.000.000,00 (vinte milhões de reais) para o exercício de 2025,
a ser distribuído entre os membros do Conselho de Administração e da Diretoria Estatutária.
Presentes na assembleia o acionista controlador CPF 123.456.789-00 e o Diretor Presidente CPF 987.654.321-99.

3.2. Aprovado o Plano de Opção de Compra de Ações autorizando a outorga de até 150.000 opções de ações
para a Diretoria Estatutária com prazo de carência (vesting) de 36 meses.
"""


def test_document_loader_plain_text(tmp_path: Path) -> None:
    txt_file = tmp_path / "ata_sample.txt"
    txt_file.write_text(SAMPLE_ATA_TEXT, encoding="utf-8")

    loaded_text = load_document(txt_file)
    assert "COMPANHIA BRASILEIRA DE TECNOLOGIA S.A." in loaded_text
    assert "R$ 20.000.000,00" in loaded_text


def test_document_loader_pdf_reference() -> None:
    pdf_path = Path("/home/pedrogriff/relata/docs/references/ResolutionCVM80.pdf")
    if pdf_path.exists():
        text = load_document(pdf_path)
        assert len(text) > 1000
        assert "CVM RESOLUTION" in text.upper()


def test_extractor_sanitizes_cpf_before_inference() -> None:
    extractor = AtaExtractor()
    sanitized = extractor.sanitize_text(SAMPLE_ATA_TEXT)

    # Raw CPFs must NOT appear in sanitized text
    assert "123.456.789-00" not in sanitized
    assert "987.654.321-99" not in sanitized
    assert "[SEC_CPF_" in sanitized


def test_heuristic_extraction_from_ata_text() -> None:
    extractor = AtaExtractor()
    result = extractor.extract(SAMPLE_ATA_TEXT)

    assert isinstance(result, AtaExtractionResult)
    assert result.meeting_type == "AGO"
    assert "COMPANHIA BRASILEIRA DE TECNOLOGIA S.A." in result.company_name
    assert result.cnpj == "10.987.654/0001-32"
    assert result.global_compensation_ceiling_brl == Decimal("20000000.00")

    # Verify extracted organs
    bodies = {o.corporate_body for o in result.organs_breakdown}
    assert CorporateBody.CONSELHO_ADMINISTRACAO in bodies
    assert CorporateBody.DIRETORIA_ESTATUTARIA in bodies

    # Verify extracted share plan
    assert len(result.share_plans) >= 1
    assert result.share_plans[0].plan_type == SharePlanType.STOCK_OPTION
    assert result.share_plans[0].vesting_months == 36

    # Verify bilingual policy texts
    assert len(result.qualitative_policy_summary_pt) > 10
    assert len(result.qualitative_policy_summary_en) > 10


def test_mapping_ata_to_fre_submission_and_reconciliation() -> None:
    extractor = AtaExtractor()
    extracted = extractor.extract(SAMPLE_ATA_TEXT)

    submission = map_ata_to_fre_submission(extracted, fiscal_year=2025, cvm_code="12345")
    assert submission.fiscal_year == 2025
    assert submission.company_name == extracted.company_name
    assert len(submission.item_8_2_organs) == len(extracted.organs_breakdown)

    # Run deterministic reconciler over mapped submission
    report = reconcile_fre_section_8(submission)
    assert report.is_valid is True
    assert report.grand_total_brl > Decimal("0.00")

    # Generate Sistema Empresas.NET XML from mapped submission
    xml_data = generate_cvm_empresas_net_xml(submission)
    assert "FormularioReferencia" in xml_data
    assert "Secao8_RemuneracaoAdministradores" in xml_data


def test_mapping_share_plan_to_cpc10_grant() -> None:
    plan_condition = ExtractedShareGrantCondition(
        plan_name="Plano Outorga 2025",
        plan_type=SharePlanType.STOCK_OPTION,
        corporate_body=CorporateBody.DIRETORIA_ESTATUTARIA,
        total_shares_approved=50_000,
        strike_price_brl=Decimal("28.00"),
        vesting_months=36,
        lockup_months=12,
    )

    from datetime import date
    grant = map_share_plan_to_cpc10_grant(
        plan=plan_condition,
        grant_id="OUTORGA-DIR-2025",
        grant_date=date(2025, 5, 2),
        spot_price_brl=Decimal("30.00"),
    )

    assert grant.grant_id == "OUTORGA-DIR-2025"
    assert grant.total_shares_granted == 50_000
    assert grant.vesting_months == 36
    assert grant.pricing_parameters is not None
    assert grant.pricing_parameters.strike_price_brl == Decimal("28.00")
