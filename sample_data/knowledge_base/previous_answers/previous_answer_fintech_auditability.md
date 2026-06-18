# Previous RFP Answer: Fintech Auditability and Case Management

## Question

How does your platform support compliance review and audit evidence?

## Answer

The platform supports compliance review through configurable workflow states, analyst work queues, role-based access, reviewer notes, decision history, document metadata, and timestamped audit events. Each status transition records the actor, time, target case, and relevant context. Reviewer decisions can be exported for audit or management reporting.

Segregation of duties is implemented through permissions so that users can be restricted from approving their own work or accessing cases outside their responsibility area. Audit logs are protected from ordinary user modification. Evidence export can include case summary, uploaded document metadata, decision timeline, reviewer comments, and integration status history.

For third-party screening providers, integration events should include correlation IDs, request status, response status, error category, and retry history. This helps analysts and technical teams reconcile onboarding outcomes against external provider records.
