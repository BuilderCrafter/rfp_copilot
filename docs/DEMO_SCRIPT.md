# Demo Script

Use this script to keep the final demo focused and understandable.

## Recommended demo data

RFP:

```text
sample_data/rfps/01_smart_city_citizen_services_rfp.md
```

Knowledge base:

```text
sample_data/knowledge_base/
```

Upload all knowledge-base Markdown files for the richest demo.

## Demo story

The buyer is a city government that published a complex RFP for a citizen services portal. The vendor already has useful knowledge spread across policies, previous answers, case studies, and delivery methodology documents.

The product turns that scattered knowledge into source-backed first drafts that a human reviewer can approve, edit, or flag.

## Steps

1. Create a project named `Northbridge Smart City RFP`.
2. Upload `01_smart_city_citizen_services_rfp.md` as the RFP.
3. Upload the knowledge-base documents.
4. Extract RFP questions.
5. Select a security/privacy question.
6. Generate a draft answer.
7. Show the citation panel and explain that the reviewer can verify the source.
8. Edit the final answer slightly.
9. Approve it.
10. Select a question that has weaker source support and show that it is flagged instead of invented.
11. Export the reviewed answers to PDF.

## What to emphasize

- The tool does not replace the human reviewer.
- The AI answer is only a draft.
- The source citations are the key trust feature.
- The tool saves time by reusing past answers and company knowledge.
- Unsupported claims are flagged instead of hallucinated.

## Strong questions to demo

From the smart city RFP:

- `Describe your information security controls, including encryption, identity and access management, audit logging, and vulnerability management.`
- `Provide your proposed implementation methodology, including discovery, design, configuration, integration, testing, deployment, and handover.`
- `Describe your approach to integrating with existing CRM, GIS, document management, and payment systems.`
- `Describe your accessibility approach and whether you support WCAG 2.2 AA requirements.`

## Responsible AI example

Use the ISO/SOC certification question to show that the system should not invent formal certifications. The knowledge base says Northstar aligns with common controls but does not claim certification by default.
