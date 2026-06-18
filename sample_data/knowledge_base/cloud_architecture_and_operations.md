# Cloud Architecture and Operations

## Hosting Model

Northstar typically deploys customer platforms on managed cloud infrastructure using separate environments for development, test, staging, and production. Deployments can be hosted in a customer-approved cloud region. Network, compute, storage, database, monitoring, and backup choices are documented in a solution architecture document.

## Application Architecture

A common architecture includes a web frontend, backend API, relational database, object storage for documents, background worker for long-running jobs, identity provider integration, monitoring, and logging. For integration-heavy systems, Northstar uses an API layer and event processing components to decouple external systems from user-facing workflows.

## Monitoring and Alerting

Production systems are monitored for availability, latency, error rates, resource utilization, queue depth, failed jobs, integration failures, and security-relevant events. Alerts are routed to the support or DevOps team according to severity and support agreement.

## Release Management

Releases follow a controlled process with change description, tested build, deployment checklist, rollback plan, and release notes. Maintenance windows are agreed with the customer when downtime or user impact is expected. Critical fixes may follow an emergency change process.

## Rollback

Rollback plans depend on the type of change. Application-only releases can usually be rolled back by redeploying a previous version. Database schema changes require forward/backward compatibility planning, backups, and migration validation.

## Data Residency

Northstar can deploy services in customer-approved cloud regions when technically feasible. Data residency requirements must be confirmed during discovery because third-party integrations, analytics tools, notification providers, and support processes may affect data location.
