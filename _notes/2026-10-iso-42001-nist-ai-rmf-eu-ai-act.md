---
title: "ISO/IEC 42001, the NIST AI RMF and the EU AI Act, side by side"
slug: iso-42001-nist-ai-rmf-eu-ai-act
date: 2026-10-05
updated: 2026-10-05
status: working draft
version: "0.1"
description: >-
  A clause-by-clause map of where the three frameworks ask for the same thing,
  where they differ, and what each adds that the others do not. Written for
  someone who already runs a management system and has been told to add AI to it.
published: false
---
{% comment %}
EDITOR'S CHECKLIST. This block never renders. Delete it when the note is done.

This outline was drafted in a sandbox that could not reach nist.gov, eur-lex.europa.eu
or iso.org, so every reference below comes from memory and is marked "(verify)".
Before setting `published: true`:

  1. Check every row of the table against the texts:
       ISO/IEC 42001:2023 (clause and Annex A control titles only; the standard is
       paywalled, so do not quote its text),
       NIST AI RMF 1.0 (NIST AI 100-1, January 2023) and the Playbook,
       Regulation (EU) 2024/1689 as published in the Official Journal.
  2. Remove every "(verify)" once the cell is right, and delete cells that are wrong
     rather than softening them.
  3. Replace every "[Brian: ...]" prompt with your own text or delete it.
  4. Check the application dates in the timeline paragraph; a Commission proposal in
     late 2025 sought to change parts of the high-risk timetable.
  5. Update `updated`, bump `version`, change `status` (working draft, reviewed, final).
  6. Add an entry to _data/work.yml with kind: mapping pointing at this note's URL
     so it also appears under Framework mappings on the front page.
{% endcomment %}

## Why this table exists

Anyone who has run an ISO 27001 management system and is now asked to "add AI" meets the same three documents in the first week: a certifiable standard, a voluntary framework from a US agency, and a European regulation with fines attached. They overlap heavily, they use different words for the same things, and each contains at least one obligation the other two do not. This note lines them up so that one piece of work can be shown to satisfy, or partly satisfy, all three.

"Maps to" here means: doing the thing on the left produces evidence that is directly usable for the thing on the right. It does not mean the obligations are identical.

## Sources and scope

- **ISO/IEC 42001:2023** is referenced by clause number and by Annex A control title. The text of the standard is copyrighted and paywalled, so nothing from it is quoted.
- **NIST AI RMF 1.0** (NIST AI 100-1) is referenced by function and subcategory, for example GOVERN 1.1. The Playbook is treated as guidance, not requirement.
- **Regulation (EU) 2024/1689**, the AI Act, is referenced by article number. Unless stated, obligations are those for providers and deployers of high-risk systems under Chapter III.

This is a map, not legal advice. [Brian: add one sentence on the organisational context you had in mind when you wrote it, for example a small B2B SaaS provider that uses third-party AI APIs.]

## The shape of each document

**ISO/IEC 42001** is a management system standard with the same harmonised structure as ISO 27001: context, leadership, planning, support, operation, performance evaluation, improvement, with an Annex A of controls selected through a Statement of Applicability. If you already run an ISMS, clauses 4 to 10 are familiar in form; the new substance is in the AI risk assessment, the AI system impact assessment and the Annex A controls. (verify clause numbering against the published text)

**The NIST AI RMF** is voluntary and non-certifiable. It is organised into four functions: GOVERN, MAP, MEASURE and MANAGE, each broken into categories and numbered subcategories. GOVERN is cross-cutting; the other three follow a system through its life cycle. It is strongest on characterising impacts and on measurement, and it says little about documentation as such.

**The EU AI Act** is law. It classifies systems by risk, prohibits some uses outright, and places most of its weight on providers of high-risk systems, with a shorter list of duties for deployers. It cares about evidence of conformity, not about whether you have a management system, though Article 17 requires providers of high-risk systems to have a quality management system that looks a great deal like one.

## The map

Each row is a requirement area of ISO/IEC 42001. The other two columns name the parts of the NIST AI RMF and the AI Act that the same work serves. Every cell is marked (verify) until it has been checked against the source text.

| ISO/IEC 42001 | NIST AI RMF 1.0 | EU AI Act (Reg. 2024/1689) |
|---|---|---|
| 4 Context of the organisation: 4.1 to 4.4, scope of the AIMS | MAP 1.1 to 1.6: intended purpose, context, and system scope established; GOVERN 1.1: legal and regulatory requirements understood (verify) | Art. 2 scope; Art. 3 definitions, including who is a provider and who is a deployer; Art. 6 and Annex III, whether any system is high-risk (verify) |
| 5 Leadership: 5.2 AI policy, 5.3 roles, responsibilities and authorities | GOVERN 1.1 to 1.2: policies and procedures; GOVERN 2.1 to 2.2: roles, responsibilities and training; GOVERN 4.1: risk culture (verify) | Art. 17(1): quality management system including a strategy for regulatory compliance and an accountability framework; Art. 26(2): deployers assign human oversight to competent persons (verify) |
| 6.1.2 and 8.2 AI risk assessment, with Annex C risk sources | MAP 5.1: likelihood and magnitude of impacts; MEASURE 1 and 2: methods, metrics and evaluation; MANAGE 1.1 to 1.2: risks prioritised (verify) | Art. 9: risk management system, continuous and iterative across the life cycle (providers of high-risk systems) (verify) |
| 6.1.3 and 8.3 AI risk treatment | MANAGE 1.3 to 1.4: responses to risks; MANAGE 2.1 to 2.3: resources and plans for benefits and residual risk (verify) | Art. 9(4) to (5): risk mitigation, testing, residual risk judged acceptable; Art. 20: corrective actions (verify) |
| 6.1.4 and 8.4 AI system impact assessment; Annex A.5 Assessing impacts of AI systems | MAP 5.1 to 5.2: impacts on individuals, groups, communities, organisations and society characterised; MEASURE 2.6 to 2.12: trustworthy characteristics evaluated (verify) | Art. 27: fundamental rights impact assessment for certain deployers; Art. 9(2)(a): risks to health, safety and fundamental rights identified (verify) |
| 6.2 AI objectives and planning to achieve them | GOVERN 1.3: level of risk management activity set from risk tolerance; MAP 1.3: organisational goals and mission (verify) | No direct equivalent (verify) |
| 7.2 Competence and 7.3 Awareness | GOVERN 2.2: personnel and partners trained; GOVERN 3.1 to 3.2: workforce and diverse perspectives (verify) | Art. 4: AI literacy for staff of providers and deployers (verify) |
| 7.5 Documented information | GOVERN 1.4: transparent documentation of policies and processes; MAP and MEASURE subcategories that call for documentation (verify) | Art. 11 and Annex IV: technical documentation; Art. 12: record-keeping and logging; Art. 18: documentation retention (verify) |
| 8.1 Operational planning and control; Annex A.6 AI system life cycle | MAP 2.1 to 2.3 and MAP 3.1 to 3.5: system tasks, methods, capabilities and limits; MEASURE 2.1 to 2.5: testing and evaluation; MANAGE 2.4 and 4.1: deployment and monitoring (verify) | Art. 13: transparency and instructions for deployers; Art. 14: human oversight designed in; Art. 15: accuracy, robustness and cybersecurity (verify) |
| Annex A.7 Data for AI systems | MAP 2.3: scientific integrity and data provenance; MEASURE 2.1 to 2.2: test sets and metrics documented, evaluations involving human subjects (verify) | Art. 10: data and data governance for training, validation and testing data (verify) |
| Annex A.8 Information for interested parties of AI systems | GOVERN 5.1 to 5.2: engagement and feedback from AI actors; MEASURE 3.3: end-user feedback; MAP 5.2: feedback channels (verify) | Art. 13: information to deployers; Art. 50: transparency obligations for systems interacting with people and for synthetic content; Art. 26(7) and (11): informing workers and affected persons; Art. 86: right to an explanation (verify) |
| Annex A.9 Use of AI systems, including intended use and responsible use | MAP 1.1: intended purposes and contexts of use; MAP 3.1 to 3.4: benefits, costs and application scope (verify) | Art. 5: prohibited practices; Art. 26: deployers use systems in accordance with instructions and monitor them (verify) |
| Annex A.10 Third-party and customer relationships | GOVERN 6.1 to 6.2: third-party risks and contingency; MAP 4.1 to 4.2: third-party components mapped; MANAGE 3.1 to 3.2: third-party risks managed (verify) | Art. 25: responsibilities along the AI value chain; Art. 17: supplier and component controls within the quality management system (verify) |
| 9 Performance evaluation: 9.1 monitoring and measurement, 9.2 internal audit, 9.3 management review | MEASURE 3.1 to 3.3: risks tracked over time; MEASURE 4.1 to 4.3: efficacy of measurement; MANAGE 4.1: post-deployment monitoring (verify) | Art. 72: post-market monitoring by providers; Art. 26(5): deployers monitor operation; Art. 17(1)(h) and (i): procedures for post-market monitoring and incident reporting (verify) |
| 10 Improvement: 10.1 continual improvement, 10.2 nonconformity and corrective action | MANAGE 4.3: incident response and recovery; MANAGE 2.4: mechanisms to deactivate or disengage (verify) | Art. 20: corrective actions and duty of information; Art. 73: reporting of serious incidents (verify) |
| Annex A.2 Policies related to AI; Annex A.3 Internal organisation, including reporting of concerns | GOVERN 1.1 to 1.2; GOVERN 2.1; GOVERN 4.3: incident information shared (verify) | Art. 17: quality management system; Art. 87: reporting of infringements and protection of reporting persons (verify) |
| Annex A.4 Resources for AI systems: data, tooling, systems and computing, human resources | MAP 1.6: system requirements; MAP 2.1: tasks and methods; GOVERN 1.7: decommissioning (verify) | Art. 11 and Annex IV: description of development resources and computational resources in the technical documentation (verify) |

## What ISO/IEC 42001 adds that ISO 27001 does not

If you already run an ISMS, clauses 4 to 10 of 42001 are the same machinery pointed at a different subject, and most of the documentation can be shared or cross-referenced. The genuinely new obligations are:

1. **The AI system impact assessment** (6.1.4, 8.4, Annex A.5). This is the one with no counterpart in 27001. The nearest existing instrument is a data protection impact assessment under GDPR Article 35, and the two can share a method, but the questions are different: an impact assessment asks what the system does to people and groups who are not its users. (verify clause numbers)
2. **AI-specific risk sources** (Annex C), which widen the risk assessment beyond confidentiality, integrity and availability to fairness, transparency, safety and environmental impact. (verify)
3. **Life-cycle, data and use controls** (Annex A.6, A.7, A.9) that assume you build or operate the system, not just protect it.
4. **Information for interested parties** (Annex A.8), which is a disclosure duty rather than a security one.

[Brian: this is where the finding from your own cross-framework work belongs, that the impact assessment was the main new obligation not covered by existing 27001 controls. Say how you handled it.]

## What the AI Act adds that neither framework does

- A legal classification that decides whether most of this applies at all (Art. 6 and Annex III), and a list of practices that are simply prohibited (Art. 5). (verify)
- A fundamental rights impact assessment for public bodies and for private deployers in a few named sectors (Art. 27), which is a duty on the deployer rather than the provider. (verify)
- AI literacy for everyone who operates or uses systems on an organisation's behalf (Art. 4). (verify)
- Serious incident reporting to market surveillance authorities (Art. 73), registration in the EU database (Art. 49) and conformity assessment and CE marking for high-risk systems (Arts. 43 and 48). (verify)
- Separate obligations for providers of general-purpose AI models (Arts. 53 to 55), which neither 42001 nor the RMF address directly. (verify)

**Timeline.** The Act entered into force on 1 August 2024. The prohibitions and the AI literacy duty applied from 2 February 2025, the general-purpose AI obligations from 2 August 2025, and most of the remaining obligations, including those for high-risk systems listed in Annex III, from 2 August 2026, with product-embedded high-risk systems under Annex I following on 2 August 2027. (verify all dates; check the status of the Commission's late-2025 proposal to change parts of the high-risk timetable)

## How I use this

[Brian: four or five sentences in the first person. Suggested points: using the table as the AI equivalent of a Statement of Applicability; using it to answer customer security and procurement questionnaires that now ask about AI; deciding whether a customer-facing feature crosses the line from internal productivity tool to deployed AI system; briefing a leadership team that has heard of all three documents and read none of them.]

## Related documents

- NIST AI 100-1, Artificial Intelligence Risk Management Framework (AI RMF 1.0), January 2023. (verify)
- NIST AI 600-1, the Generative AI Profile, July 2024. (verify)
- NIST IR 8596, Cybersecurity Framework Profile for Artificial Intelligence, initial public draft. [Brian: confirm the title, status and date, and say in one sentence why it matters for someone who already has an ISMS.] (verify)
- ISO/IEC 23894:2023, guidance on AI risk management, which 42001's risk assessment leans on. (verify)
