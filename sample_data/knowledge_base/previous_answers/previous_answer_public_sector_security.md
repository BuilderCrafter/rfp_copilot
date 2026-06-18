# Previous RFP Answer: Public Sector Security and Operations

## Question

Describe your information security controls and operational monitoring approach.

## Answer

Our delivery approach applies layered security controls across identity, application, infrastructure, and operations. Administrative access is limited to approved personnel and protected with multi-factor authentication. Applications use role-based access control so users only access the functions and records required by their role.

Data is encrypted in transit using TLS and protected at rest through managed database and storage encryption. Security-relevant actions such as login events, administrative changes, permission changes, and data exports are logged with actor, timestamp, action, and affected entity where available.

Production services are monitored for availability, latency, error rates, failed jobs, integration failures, and resource utilization. High-severity alerts are escalated to the support and engineering teams according to the agreed support model. Planned maintenance is communicated in advance, and releases include rollback planning.

Northstar aligns internal practices with recognized security control families, but formal certification claims must be confirmed separately for each bid.
