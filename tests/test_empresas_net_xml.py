"""Tests for CVM Sistema Empresas.NET XML generation."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from relata.domain.models import FRESection8Submission
from relata.filing.empresas_net_xml import generate_cvm_empresas_net_xml


def test_generate_cvm_xml_structure(sample_valid_submission: FRESection8Submission) -> None:
    xml_output = generate_cvm_empresas_net_xml(sample_valid_submission)
    assert len(xml_output) > 0

    root = ET.fromstring(xml_output)
    assert root.tag == "FormularioReferencia"
    assert root.attrib["AnoExercicio"] == "2025"
    assert root.attrib["CNPJ"] == "12.345.678/0001-90"
    assert root.attrib["CodigoCVM"] == "09876"

    # Verify Section 8 tag
    sec8 = root.find("Secao8_RemuneracaoAdministradores")
    assert sec8 is not None

    # Verify Item 8.1 narrative in PT and EN
    item81 = sec8.find("Item8_1_PoliticaRemuneracao")
    assert item81 is not None
    assert item81.find("DescricaoPolitica_PT") is not None
    assert item81.find("DescricaoPolitica_EN") is not None

    # Verify Organs in Item 8.2
    item82 = sec8.find("Item8_2_RemuneracaoTotalPorOrgao")
    assert item82 is not None
    organs = item82.findall("Orgao")
    assert len(organs) == 2

    # Verify Item 8.6 Spreads
    item86 = sec8.find("Item8_6_RemuneracaoIndividual")
    assert item86 is not None
    quadros = item86.findall("QuadroIndividual")
    assert len(quadros) == 2
