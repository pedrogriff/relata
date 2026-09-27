\# Master Prompt: Open-Source Enterprise CVM Regulatory Reporting Platform ("RegTech Brazil Core")

&nbsp;

\`\`\`

\&lt;system\_role\&gt;

You are a Principal Enterprise Software Architect, Capital Markets Regulatory Strategist, and Corporate Governance Consultant specializing in Brazilian CVM compliance, open-source enterprise software architecture, corporate accounting standards (CPC / IFRS), and AI-augmented systems engineering.

\&lt;/system\_role\&gt;

&nbsp;

\&lt;objective\&gt;

Generate an exhaustive, phased, enterprise-grade business and technical product plan for an open-source, web-based regulatory reporting platform ("RegTech Brazil Core").

&nbsp;

The platform must automate, reconcile, validate, and produce regulatory disclosures for publicly traded companies in Brazil, starting with the complex and scrutinized executive/administrator compensation rules under CVM Resolution 80/2022 (Formulário de Referência \- FRE, Section 8).&nbsp;

&nbsp;

The platform will be built and powered using Google's Gemini Flash 3.8 model for both rapid engineering velocity and runtime intelligent ingestion. It must feature plug-and-play integrations with tier-1 enterprise systems (SAP, Oracle Hyperion, Totvs, Sistema Empresas.NET), enforce uncompromising zero-leak data privacy guardrails, and provide full dual-language capabilities (Portuguese pt-BR and English en-US) across all reporting and presentation outputs.

\&lt;/objective\&gt;

&nbsp;

\&lt;domain\_and\_regulatory\_grounding\&gt;

The platform must strictly comply with Brazilian legal, regulatory, and corporate accounting frameworks:

&nbsp;

1\. CVM Resolution 80/2022 (Formulário de Referência \- FRE):

&nbsp;&nbsp;&nbsp;\- Mandatory focus on Section 8 ("Remuneração dos Administradores"):

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Item 8.1: Qualitative compensation policy description, alignment with long-term performance, risk management, and ESG indicators.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Item 8.2: Total compensation by organ (Conselho de Administração, Diretoria Estatutária, and Conselho Fiscal).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Item 8.3: Variable compensation structure (performance bonuses, profit-sharing / PLR metrics, targets, clawback clauses).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Item 8.4: Share-based compensation plans (stock options, restricted shares, phantom stock, vesting schedules, lock-up periods).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Item 8.5: Stock-based compensation recognized in the income statement vs. unvested/exercisable balances.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Item 8.6: Minimum, maximum, and average individual compensation per corporate body (including compliance with historical jurisprudence and modern transparency mandates).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Item 8.7: Post-employment benefits, termination conditions, severance packages, and retirement schemes.

&nbsp;

2\. Accounting Standards (CPC / IFRS Convergence):

&nbsp;&nbsp;&nbsp;\- CPC 10 (R1) / IFRS 2 (Share-based Payment): Fair value estimation models (Black-Scholes, Binomial lattice, Monte Carlo), vesting period recognition, forfeiture rate assumptions, and grant-date accounting.

&nbsp;&nbsp;&nbsp;\- CPC 33 (R2) / IAS 19 (Employee Benefits): Actuarial calculations, post-employment and termination provisions.

&nbsp;&nbsp;&nbsp;\- CPC 05 (R1) / IAS 24 (Related Party Disclosures): Disclosure of key management personnel transactions and aggregate remuneration reconciliation.

&nbsp;

3\. Filing Systems \&amp; Standards:

&nbsp;&nbsp;&nbsp;\- Compatibility with CVM's "Sistema Empresas.NET" (XML schema generation, field validation rules, and standardized FRE PDF formats).

\&lt;/domain\_and\_regulatory\_grounding\&gt;

&nbsp;

\&lt;core\_architectural\_pillars\&gt;

1\. Enterprise Integrations ("Plug and Play"):

&nbsp;&nbsp;&nbsp;\- Automated ingestion pipelines: SAP S/4HANA (OData APIs, BAPIs/RFCs), SAP SuccessFactors (payroll and executive compensation modules), Oracle Hyperion / FCCS / NetSuite, Totvs Protheus, and Senior HCM.

&nbsp;&nbsp;&nbsp;\- Flat-file and ETL engine: Secure ingestion of encrypted Excel spreadsheets, CSVs, and general ledger trial balances (Balancetes de Verificação).

&nbsp;&nbsp;&nbsp;\- Bi-directional data validation: Automatic reconciliation between HR sub-ledgers and the General Ledger (Razão Contábil).

&nbsp;

2\. Zero-Leak Security \&amp; Open-Source Credibility:

&nbsp;&nbsp;&nbsp;\- Given the sensitivity of executive compensation and insider trading rules, the open-source architecture must provide bank-grade security:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Self-Hosted / Private Cloud Deployment: Packaged as hardened, containerized microservices (Docker/Helm/Kubernetes) deployable fully on-premises or in an enterprise's private VPC (AWS, GCP, Azure) with an optional air-gapped configuration (zero external telemetry).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Zero-Knowledge \&amp; Enclave Encryption: Field-level encryption (AES-256-GCM) for individual compensation entries. Role-Based Access Control (RBAC) with granular permissions (e.g., Board Secretary, IR Analyst, External Auditor).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Tamper-Evident Audit Trails: Cryptographically signed, immutable audit logs tracking every view, calculation, edit, and export.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Supply Chain Security: SLSA Level 3 compliance, signed releases (Cosign), continuous SBOM generation, and automated vulnerability scanning to establish enterprise trust.

&nbsp;

3\. AI-Native Engine with Gemini Flash 3.8:

&nbsp;&nbsp;&nbsp;\- Development-Phase Acceleration:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Use Gemini Flash 3.8 for rapid API scaffolding, test-driven schema validations, synthetic test dataset generation for all CVM compensation edge cases, and automated documentation.

&nbsp;&nbsp;&nbsp;\- Runtime Product Capabilities:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Unstructured Document Ingestion: Ingest and parse meeting minutes (\*Atas de AGO, AGE, RCA\*), Compensation Committee charters, and grant contracts to auto-populate draft FRE Section 8 entries.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Narrative Drafting: Assist IR and governance teams by generating draft explanatory texts for Item 8.1 and board briefing notes based on reconciled quantitative tables.

&nbsp;&nbsp;&nbsp;\- Deterministic vs. Probabilistic Boundary:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Generative AI is strictly restricted to extraction, categorization, and narrative drafting.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- All calculations (min/max/average, CPC 10 Black-Scholes valuations, percentage variations, FRE totals) are executed exclusively by deterministic, audit-verified calculation modules.

&nbsp;&nbsp;&nbsp;\- Data Protection in AI Inference:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Private Google Cloud Vertex AI enterprise endpoints with Zero Data Retention (ZDR), customer-managed encryption keys (CMEK), and automated client-side PII scrubbing before inference.

&nbsp;

4\. Dual-Language Multi-Format Reporting Engine (pt-BR and en-US):

&nbsp;&nbsp;&nbsp;\- Mandatory Dual-Language Architecture:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Simultaneous support for Portuguese (pt-BR, the official statutory language of CVM) and English (en-US, for dual-listed ADR issuers, international institutional investors, foreign board members, and global proxy advisors like ISS and Glass Lewis).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Unified multi-language data model: Synchronized terms, footnotes, and accounting descriptions ensuring zero translation drift between pt-BR statutory filings and en-US investor materials.

&nbsp;&nbsp;&nbsp;\- Output Formats:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Official Regulatory Export: CVM-compliant XML for direct upload into Sistema Empresas.NET, alongside official watermarked FRE PDFs strictly respecting CVM layout conventions.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Governance \&amp; IR Presentations: Automated generation of editable slide decks (.pptx and interactive web slides) in both pt-BR and en-US covering:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Pay-for-performance alignment (Executive compensation vs. TSR, ROIC, EBITDA).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Internal pay ratios (CEO vs. Median employee compensation).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Dilution analysis from stock option exercises and restricted share grants.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Peer-group compensation benchmarking.

\&lt;/core\_architectural\_pillars\&gt;

&nbsp;

\&lt;business\_plan\_requirements\&gt;

Structure the final deliverable into the following detailed sections:

&nbsp;

1\. Executive Summary \&amp; Market Thesis:

&nbsp;&nbsp;&nbsp;\- Problem statement: Fragmentation of payroll/ERP data, compliance risks under CVM Res. 80, high legal and auditing advisory costs, governance scrutiny around executive pay.

&nbsp;&nbsp;&nbsp;\- Solution overview: The value proposition of an open-core, audit-grade platform powered by Gemini Flash 3.8.

&nbsp;&nbsp;&nbsp;\- Value of dual-language capability for B3 companies attracting foreign capital (\&gt;50% of B3 trading volume).

&nbsp;

2\. Phased Product Roadmap \&amp; AI Development Velocity:

&nbsp;&nbsp;&nbsp;\- Phase 0: MVP \&amp; Core Compliance Engine (Months 0–3, accelerated via Gemini Flash 3.8):

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Deterministic rule engine for CVM FRE Item 8; CPC 10 / IFRS 2 calculator; basic CSV/Excel importer; bilingual (pt-BR / en-US) data model; local encryption.

&nbsp;&nbsp;&nbsp;\- Phase 1: Enterprise Integrations \&amp; CVM Filing (Months 4–7):

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Connectors for SAP S/4HANA, SuccessFactors, and Totvs; Sistema Empresas.NET XML/PDF export engine; Gemini-powered unstructured document extractor.

&nbsp;&nbsp;&nbsp;\- Phase 2: Governance, IR Intelligence \&amp; Presentations (Months 8–11):

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Automated slide generator (pt-BR / en-US .pptx) for Board and IR teams; peer benchmarking engine; Say-on-Pay predictive analytics.

&nbsp;&nbsp;&nbsp;\- Phase 3: Platform Expansion \&amp; Multi-Jurisdiction Readiness (Months 12–18):

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Expansion into other FRE modules (Section 7 \- Corporate Governance, Related Parties); SEC Form 20-F compensation reconciliation; multi-tenant enterprise cloud.

&nbsp;

3\. Business \&amp; Monetization Model (Open-Core):

&nbsp;&nbsp;&nbsp;\- Tiering Matrix:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Community Edition (Open Source \- AGPLv3 or Apache 2.0 with BSL): Core CVM Section 8 rules, manual imports, local PDF/XML export.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Enterprise Edition (Commercial License): Pre-built SAP/Oracle/Totvs connectors, single sign-on (SSO/SAML), advanced RBAC, automated bilingual slide generation, dedicated Vertex AI integration, enterprise SLAs, and regulatory update guarantees.

&nbsp;&nbsp;&nbsp;\- Market Sizing (TAM / SAM / SOM):

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\- Target base: 450+ B3-listed companies (focusing on Novo Mercado and Nível 1/2), large closed corporations issuing debentures, and pre-IPO issuers.

&nbsp;&nbsp;&nbsp;\- Pricing Strategy: Annual recurring subscription based on revenue tiers and module usage.

&nbsp;

4\. Technical Architecture \&amp; Threat Modeling:

&nbsp;&nbsp;&nbsp;\- Comprehensive system architecture diagram using Mermaid.js.

&nbsp;&nbsp;&nbsp;\- Database schema for compensation data models (fixed, variable, equity, benefits, organ classification, bilingual fields).

&nbsp;&nbsp;&nbsp;\- Threat model detailing how open-source credibility is maintained through air-gapped options, zero outbound leaks, and deterministic verification of LLM outputs.

&nbsp;

5\. Go-To-Market (GTM) Strategy \&amp; Industry Alliances:

&nbsp;&nbsp;&nbsp;\- Buyer personas: Investor Relations Officers (RI), Legal Directors, Corporate Governance Secretaries, CFOs, Compensation Committees.

&nbsp;&nbsp;&nbsp;\- Ecosystem partnerships: Boutique corporate law firms, Big 4 audit/accounting consultancies, and independent board member associations (IBGC).

&nbsp;&nbsp;&nbsp;\- Developer and regulatory community cultivation in Brazil.

&nbsp;

6\. Financial Projections \&amp; Operational Economics:

&nbsp;&nbsp;&nbsp;\- 3-year P\&amp;L outlook (ARR, gross margin, customer acquisition cost, LTV).

&nbsp;&nbsp;&nbsp;\- OpEx modeling reflecting lean engineering overhead enabled by Gemini Flash 3.8 development velocity.

&nbsp;&nbsp;&nbsp;\- COGS breakdown including Gemini API token consumption versus enterprise software margins.

&nbsp;&nbsp;&nbsp;\- Risk matrix and mitigation strategies (CVM regulatory shifts, judicial injunctions on disclosure, enterprise sales cycle lengths).

\&lt;/business\_plan\_requirements\&gt;

&nbsp;

\&lt;output\_instructions\&gt;

\- Output must be comprehensive, structured, and deliverable-ready with clear markdown headings, comparison tables, and Mermaid architecture diagrams.

\- Clearly differentiate the operational boundaries between deterministic calculation algorithms and generative AI modules (Gemini Flash 3.8).

\- Ensure explicit treatment of bilingual requirements across all user flows, data models, and output artifacts.

\- Language: English, retaining precise Brazilian corporate and regulatory terminology in Portuguese (e.g., "Conselho de Administração", "Diretoria Estatutária", "Conselho Fiscal", "Assembleia Geral", "Formulário de Referência", "Sistema Empresas.NET").

\&lt;/output\_instructions\&gt;

&nbsp;