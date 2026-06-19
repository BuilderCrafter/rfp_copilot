# Sample Data

This folder contains demo RFPs and a reusable company knowledge base for the hackathon MVP.

## How to use in the app

1. Create a project.
2. Upload one file from `sample_data/rfps/` as the RFP document.
3. Upload several or all files from `sample_data/knowledge_base/` as knowledge documents.
4. Extract questions from the RFP.
5. Generate draft answers and review the citations.

Knowledge documents are treated as a unified knowledge base for all proposal projects. Uploading the demo knowledge base once makes it available to later RFP projects.

## RFP files

- `rfps/01_smart_city_citizen_services_rfp.md` - public-sector portal, integrations, accessibility, operations, compliance.
- `rfps/02_fintech_kyc_aml_platform_rfp.md` - regulated fintech onboarding, auditability, APIs, fraud monitoring.
- `rfps/03_healthcare_patient_engagement_rfp.md` - healthcare portal, privacy, interoperability, reliability, support.

## Knowledge base files

The knowledge base is intentionally broader than any single RFP. This lets the team evaluate retrieval quality and see whether answers cite the right material instead of grabbing random text.

Recommended full demo upload set:

- `knowledge_base/company_profile_and_capabilities.md`
- `knowledge_base/security_and_compliance_policy.md`
- `knowledge_base/privacy_and_gdpr_policy.md`
- `knowledge_base/cloud_architecture_and_operations.md`
- `knowledge_base/implementation_methodology.md`
- `knowledge_base/support_sla_and_incident_management.md`
- `knowledge_base/disaster_recovery_and_business_continuity.md`
- `knowledge_base/integration_and_api_practices.md`
- `knowledge_base/accessibility_and_ux_standards.md`
- `knowledge_base/commercial_and_pricing_approach.md`
- `knowledge_base/rfp_intake_and_bid_qualification.md`
- files under `knowledge_base/case_studies/`
- files under `knowledge_base/previous_answers/`

## Important demo behavior

Some RFP questions are intentionally not fully answerable from the knowledge base. The system should flag those instead of inventing claims. This is useful for demonstrating responsible human-in-the-loop behavior.

The RFP assessment uses the same unified knowledge base to produce bid/no-bid guidance, missing buyer information, and a checklist of materials the proposal team must provide to the client.
