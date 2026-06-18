# Security and Compliance Policy

## Security Governance

Northstar maintains a security governance program covering access control, secure development, vulnerability management, logging, incident response, supplier review, and change management. Security responsibilities are assigned to delivery, engineering, DevOps, and management roles. Security exceptions require written approval and remediation plans.

## Identity and Access Management

Administrative access follows least-privilege principles. Production access is restricted to approved personnel and reviewed periodically. Multi-factor authentication is required for administrative systems, source control, CI/CD, cloud consoles, and privileged support tooling. Role-based access control is used in client applications so users receive only the permissions needed for their role.

## Encryption

Customer data is encrypted in transit using TLS. Sensitive data at rest is encrypted using managed cloud storage and database encryption capabilities. Secrets are not stored in source code and must be managed through environment variables, secret managers, or platform-provided secret storage.

## Audit Logging

Applications should record security-relevant actions such as authentication events, administrative changes, permission changes, data export, status transitions, and privileged support activity. Logs should include actor, timestamp, action, affected entity, and request context where available. Logs should be protected from unauthorized modification.

## Vulnerability Management

Dependencies are reviewed using automated scanning where possible. Critical vulnerabilities are triaged as soon as they are identified. Remediation priority is based on exploitability, exposure, affected data, and compensating controls. Production systems are patched through the normal change and release process unless emergency change is required.

## Secure Development

Engineering teams use peer review, branch protection, secrets scanning, dependency review, and environment separation. Security-sensitive changes require additional review. Testing includes functional testing, regression testing, and security-focused checks for authentication, authorization, input validation, logging, and error handling.

## Incident Response

Security incidents are categorized by severity. The response process includes detection, triage, containment, investigation, remediation, communication, and post-incident review. Client notification timelines depend on contractual and regulatory requirements. Incident records include impact, timeline, root cause, corrective actions, and owner.

## Compliance Position

Northstar aligns many internal practices with ISO 27001 and SOC 2 control families, but certification status must be confirmed for each bid. The default response should avoid claiming formal certification unless a current certificate is available in the bid package.
