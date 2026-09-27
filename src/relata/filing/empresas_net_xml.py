"""CVM Sistema Empresas.NET XML Schema Generator for Formulário de Referência (FRE).

Produces official statutory XML document formatted for upload into CVM's electronic filing system.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

from relata.domain.models import FRESection8Submission


def generate_cvm_empresas_net_xml(submission: FRESection8Submission) -> str:
    """Generates standardized XML string for CVM Sistema Empresas.NET Section 8."""
    root = ET.Element(
        "FormularioReferencia",
        attrib={
            "Versao": "2.0",
            "AnoExercicio": str(submission.fiscal_year),
            "CNPJ": submission.cnpj,
            "CodigoCVM": submission.cvm_code,
            "NomeCompanhia": submission.company_name,
        },
    )

    sec8 = ET.SubElement(root, "Secao8_RemuneracaoAdministradores")

    # Item 8.1 - Politica de Remuneracao
    item81 = ET.SubElement(sec8, "Item8_1_PoliticaRemuneracao")
    p_desc_pt = ET.SubElement(item81, "DescricaoPolitica_PT")
    p_desc_pt.text = submission.item_8_1_policy_narrative.pt_br
    p_desc_en = ET.SubElement(item81, "DescricaoPolitica_EN")
    p_desc_en.text = submission.item_8_1_policy_narrative.en_us

    # Item 8.2 - Remuneracao Total por Orgao
    item82 = ET.SubElement(sec8, "Item8_2_RemuneracaoTotalPorOrgao")
    for organ in submission.item_8_2_organs:
        node = ET.SubElement(
            item82,
            "Orgao",
            attrib={
                "Tipo": organ.corporate_body.value,
                "TotalMembros": str(organ.total_members),
                "MembrosRemunerados": str(organ.remunerated_members),
            },
        )
        # Fixed
        fixed = ET.SubElement(node, "RemuneracaoFixa")
        ET.SubElement(fixed, "ProLaboreSalarios").text = f"{organ.pro_labore_or_salaries_brl:.2f}"
        ET.SubElement(fixed, "BeneficiosDiretos").text = f"{organ.direct_benefits_brl:.2f}"
        ET.SubElement(fixed, "ParticipacaoComites").text = f"{organ.committee_participation_brl:.2f}"
        ET.SubElement(fixed, "OutrosFixos").text = f"{organ.other_fixed_brl:.2f}"
        ET.SubElement(fixed, "TotalFixo").text = f"{organ.total_fixed_brl:.2f}"

        # Variable
        variable = ET.SubElement(node, "RemuneracaoVariavel")
        ET.SubElement(variable, "Bonus").text = f"{organ.bonus_brl:.2f}"
        ET.SubElement(variable, "PLR").text = f"{organ.profit_sharing_plr_brl:.2f}"
        ET.SubElement(variable, "OutrosVariaveis").text = f"{organ.other_variable_brl:.2f}"
        ET.SubElement(variable, "TotalVariavel").text = f"{organ.total_variable_brl:.2f}"

        # Share-based
        shares = ET.SubElement(node, "RemuneracaoBaseadaAcoes")
        ET.SubElement(shares, "LiquidacaoAcoes").text = f"{organ.share_based_equity_brl:.2f}"
        ET.SubElement(shares, "LiquidacaoCaixa").text = f"{organ.share_based_cash_brl:.2f}"
        ET.SubElement(shares, "TotalAcoes").text = f"{organ.total_share_based_brl:.2f}"

        # Post-employment & Severance
        ET.SubElement(node, "BeneficiosPosEmprego").text = f"{organ.post_employment_benefits_brl:.2f}"
        ET.SubElement(node, "IndenizacaoCessacaoCargo").text = f"{organ.termination_severance_brl:.2f}"

        # Grand Total
        ET.SubElement(node, "TotalGeralOrgao").text = f"{organ.grand_total_brl:.2f}"

    # Item 8.6 - Remuneracao Min, Max e Media
    item86 = ET.SubElement(sec8, "Item8_6_RemuneracaoIndividual")
    for spread in submission.item_8_6_spreads:
        ET.SubElement(
            item86,
            "QuadroIndividual",
            attrib={
                "Orgao": spread.corporate_body.value,
                "MembrosRemunerados": str(spread.remunerated_members),
                "Minimo": f"{spread.min_individual_compensation_brl:.2f}",
                "Maximo": f"{spread.max_individual_compensation_brl:.2f}",
                "Media": f"{spread.average_individual_compensation_brl:.2f}",
            },
        )

    # Pretty print XML
    raw_xml = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(raw_xml)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
