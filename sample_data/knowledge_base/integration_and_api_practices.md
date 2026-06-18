# Integration and API Practices

## API Design

Northstar designs APIs around stable business resources, clear versioning, consistent error responses, authentication, authorization, request validation, and observability. API contracts are documented before implementation when external teams depend on them.

## Authentication and Authorization

API integrations can use OAuth 2.0, signed tokens, mTLS, API keys, or customer-approved integration credentials depending on risk and platform constraints. Authorization is scoped so integrations can access only required operations and data.

## Idempotency and Retry

For operations that may be retried, Northstar uses idempotency keys or deduplication logic to avoid duplicate business transactions. Retry behavior uses bounded retries, exponential backoff where appropriate, and clear dead-letter or failure handling.

## Error Handling

Integration errors are logged with correlation IDs and actionable error categories. User-facing workflows should distinguish between validation errors, temporary external failures, authorization failures, and permanent integration errors.

## Event-Driven Integrations

When near-real-time updates are required, Northstar can use event-driven patterns such as message queues, webhooks, or event streams. Events include identifiers, timestamps, event type, payload version, and correlation data.

## Reconciliation

For critical integrations, Northstar recommends reconciliation jobs or reports that compare source and target systems. Reconciliation helps detect missed events, duplicate processing, stale status values, and partial failures.

## Integration Monitoring

Integration monitoring covers latency, error rate, timeout rate, retry count, dead-letter messages, queue depth, and business-level failure counts. Alerts are routed according to operational severity.

## Standards

Northstar can integrate with REST APIs, message queues, SFTP, database exports, webhooks, and customer-specific APIs. Healthcare interoperability such as HL7 or FHIR requires project-specific assessment and may involve specialist integration partners if the buyer has strict conformance requirements.
