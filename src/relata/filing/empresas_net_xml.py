"""CVM Sistema Empresas.NET XML Schema Generator for Formulário de Referência (FRE).

Produces official statutory XML document formatted for upload into CVM's electronic filing system,
supporting Section 8 Items 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, and 8.7.
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

    # Item 8.3 - Estrutura de Remuneração Variável
    if submission.item_8_3_variable_policies:
        item83 = ET.SubElement(sec8, "Item8_3_EstruturaRemuneracaoVariavel")
        for policy in submission.item_8_3_variable_policies:
            pol_node = ET.SubElement(
                item83,
                "PoliticaVariavel",
                attrib={
                    "Orgao": policy.corporate_body.value,
                    "PossuiClawback": "true" if policy.has_clawback else "false",
                    "PossuiMalus": "true" if policy.has_malus else "false",
                    "MesesDiferimento": str(policy.deferral_period_months),
                },
            )
            ET.SubElement(pol_node, "DescricaoPolitica_PT").text = policy.narrative.pt_br
            ET.SubElement(pol_node, "DescricaoPolitica_EN").text = policy.narrative.en_us
            if policy.clawback_description:
                ET.SubElement(pol_node, "TermosClawback_PT").text = policy.clawback_description.pt_br
                ET.SubElement(pol_node, "TermosClawback_EN").text = policy.clawback_description.en_us

            metrics_node = ET.SubElement(pol_node, "MetricasDesempenho")
            for metric in policy.metrics:
                ET.SubElement(
                    metrics_node,
                    "Metrica",
                    attrib={
                        "Nome_PT": metric.name.pt_br,
                        "Nome_EN": metric.name.en_us,
                        "Categoria": metric.category.value,
                        "PesoPercentual": f"{metric.weight_pct:.2f}",
                        "GatilhoMinimo": f"{metric.threshold_pct:.2f}",
                        "MetaTarget": f"{metric.target_pct:.2f}",
                        "TetoMaximo": f"{metric.max_cap_pct:.2f}",
                    },
                )

    # Item 8.4 - Planos de Opção e Ações
    if submission.item_8_4_share_plans:
        item84 = ET.SubElement(sec8, "Item8_4_PlanosRemuneracaoBaseadaAcoes")
        for plan in submission.item_8_4_share_plans:
            plan_node = ET.SubElement(
                item84,
                "PlanoAcoes",
                attrib={
                    "IdPlano": plan.plan_id,
                    "TipoPlano": plan.plan_type.value,
                    "DataAprovacaoAGO": plan.agm_approval_date.isoformat(),
                    "LimiteDiluicaoMax": f"{plan.max_dilution_percentage:.4f}",
                    "TotalAcoesOutorgadas": str(plan.total_shares_granted),
                    "PMPE_PrecoMedio": f"{plan.weighted_average_strike_price_brl:.4f}",
                },
            )
            ET.SubElement(plan_node, "NomePlano_PT").text = plan.plan_name.pt_br
            ET.SubElement(plan_node, "NomePlano_EN").text = plan.plan_name.en_us

            tranches_node = ET.SubElement(plan_node, "SeriesOutorgas")
            for tranche in plan.tranches:
                ET.SubElement(
                    tranches_node,
                    "Tranche",
                    attrib={
                        "IdTranche": tranche.tranche_id,
                        "DataOutorga": tranche.grant_date.isoformat(),
                        "AcoesOutorgadas": str(tranche.shares_granted),
                        "MesesCarencia": str(tranche.vesting_months),
                        "PrecoExercicio": f"{tranche.exercise_strike_brl:.4f}",
                        "IndiceCorrecao": tranche.strike_adjustment_index.value,
                        "ValorJustoCPC10": f"{tranche.cpc10_grant_fair_value_brl:.4f}",
                    },
                )

    # Item 8.5 - Saldos de Opções Reconhecidas
    if submission.item_8_5_option_balances:
        item85 = ET.SubElement(sec8, "Item8_5_SaldosOpcoesReconhecidas")
        for bal in submission.item_8_5_option_balances:
            ET.SubElement(
                item85,
                "QuadroSaldos",
                attrib={
                    "Orgao": bal.corporate_body.value,
                    "TotalOutorgado": str(bal.total_options_granted),
                    "OpcoesAVencer": str(bal.unvested_options),
                    "OpcoesExerciveis": str(bal.exercisable_options),
                    "OpcoesExercidas": str(bal.exercised_options),
                    "OpcoesCanceladas": str(bal.forfeited_options),
                    "PMPE_Total": f"{bal.weighted_avg_exercise_price_brl:.4f}",
                    "PMPE_AVencer": f"{bal.weighted_avg_unvested_strike_brl:.4f}",
                    "PMPE_Exerciveis": f"{bal.weighted_avg_exercisable_strike_brl:.4f}",
                    "ValorIntrinsecoExerciveis": f"{bal.intrinsic_value_exercisable_brl:.2f}",
                    "DespesaReconhecidaExercicio": f"{bal.current_year_recognized_expense_brl:.2f}",
                    "DespesaReconhecidaAcumulada": f"{bal.cumulative_recognized_expense_brl:.2f}",
                },
            )

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

    # Item 8.7 - Rescisão e Pós-Emprego
    if submission.item_8_7_termination_packages:
        item87 = ET.SubElement(sec8, "Item8_7_RescisaoBeneficiosPosEmprego")
        for pkg in submission.item_8_7_termination_packages:
            pkg_node = ET.SubElement(
                item87,
                "TermosRescisao",
                attrib={
                    "Orgao": pkg.corporate_body.value,
                    "PossuiGoldenParachute": "true" if pkg.has_golden_parachute else "false",
                    "MesesAvisoPrevio": str(pkg.notice_period_months),
                    "MesesNaoConcorrencia": str(pkg.non_compete_duration_months),
                    "IndenizacaoMensalNaoConcorrencia": f"{pkg.non_compete_monthly_indemnity_brl:.2f}",
                },
            )
            ET.SubElement(pkg_node, "PoliticaIndenizacao_PT").text = pkg.statutory_severance_terms.pt_br
            ET.SubElement(pkg_node, "PoliticaIndenizacao_EN").text = pkg.statutory_severance_terms.en_us
            if pkg.golden_parachute_terms:
                ET.SubElement(pkg_node, "TermosGoldenParachute_PT").text = pkg.golden_parachute_terms.pt_br
                ET.SubElement(pkg_node, "TermosGoldenParachute_EN").text = pkg.golden_parachute_terms.en_us

    # Pretty print XML
    raw_xml = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(raw_xml)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
