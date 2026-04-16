# Project Alpha Summary

## 1. Project Overview

Project Alpha is a new customer-facing analytics dashboard intended to replace the company's legacy reporting system.

### Core technology stack
- **Database:** PostgreSQL with **TimescaleDB** for time-series data
- **Data ingestion and processing:** **Apache Kafka** for real-time event streaming, **Airflow** for batch historical migration, **Apache Flink** for stream processing, **dbt** for transformations, and **Great Expectations** for data quality checks
- **Storage and caching:** **S3** for raw data lake storage, **Redis** for caching aggregations
- **API layer:** **FastAPI (Python)**
- **Frontend:** **React** with **Recharts**
- **Auth:** Existing SSO via **OAuth2**
- **Realtime delivery:** A separate **WebSocket gateway service** was chosen for scalability

### Budget
- **Original approved budget:** **$340K total**
  - Infrastructure: $85K
  - Engineering: $220K
  - QA/testing: $35K
- **Risk identified:** infrastructure costs were projected to increase by **$23K/month** due to higher data volume and larger Kafka cluster needs, implying a potential total of **$432K** over 4 months
- **Updated approved budget:** **$410K**
- **Cost mitigation:** team saved **$22K** by using spot instances for Flink nodes
- **Phase 1 actual infra spend:** **$78K**, below the original $85K infrastructure budget line for that phase

## 2. Timeline

### Original timeline
- **Phase 1, Data Pipeline:** Jan 20 to Feb 14
- **Phase 2, API Layer:** Feb 17 to Mar 14
- **Phase 3, Frontend:** Mar 17 to Apr 18
- **Beta launch:** Apr 21
- **GA release:** May 12

### Status of timeline changes
- **Phase 1** finished **on schedule** by Feb 12
- On Feb 18, the project timeline was revised because of:
  - Security remediation work, especially tenant isolation and WebSocket auth
  - Decision to add a separate WebSocket gateway service

### Updated timeline
- **Phase 2, API Layer:** Feb 17 to **Apr 1**
- **Phase 3, Frontend:** Apr 2 to **May 3**
- **Beta launch:** **May 6**
- **GA release:** **May 27**

### Net impact
- Beta launch slipped by **15 days**
- Some delay was offset by:
  - adding **Alex Wong** as a 7th engineer
  - keeping Phase 2 focused by moving compliance export deeper into the plan
  - starting frontend component work in parallel during late Phase 2

## 3. Key Risks and Issues

### Budget concerns
- Data volume was estimated at **~2TB/day**, much higher than first assumed
- This drove projected extra infrastructure spend of:
  - **$15K/month** from data volume growth
  - **$8K/month** from increasing Kafka from 3 to 6 brokers
- CFO flagged a potential **27% budget overrun** before approving revised funding
- Finance required ROI confirmation, validation of revenue assumptions, and cost optimization options

### Security findings
Security review on Feb 10 identified several important issues.

#### Critical, must fix before launch
1. **Cross-tenant data exposure risk** on `/api/v1/metrics/{metric_id}/timeseries` if `metric_id` is guessable. Tenant isolation must be enforced at the query layer.
2. **WebSocket authentication weakness**. Long-lived connections require per-message auth tokens, not only connection-time auth.

#### High priority
3. Rate limiting should be per-tenant and per-user
4. Report generation format handling could permit **SSRF** if not validated
5. Missing audit logging for dashboard and alert configuration changes

#### Medium priority
6. Request signing to reduce replay attacks
7. Strict CORS allowlist documentation and enforcement

These security issues directly caused the Phase 2 extension.

### Technical challenges
- Current infrastructure did not support sticky sessions for WebSockets
- Team considered Redis pub/sub, a separate WebSocket gateway, or SSE
- They chose the **separate WebSocket gateway**, which improved scalability but added about **2 weeks** to Phase 2
- Frontend progress is partially blocked by backend delivery of:
  - WebSocket API endpoint for live metrics
  - Metric definition API for the custom metric builder
- Phase 1 had a **4-hour outage on Feb 8** due to a Kafka rebalancing storm during broker restart, though mitigations were implemented afterward

## 4. Client/Business Impact

### Revenue and sales pipeline
- Finance originally wanted confirmation that projected **$2.1M ARR** still held under the higher spend scenario
- By Feb 14, sales reported:
  - **$1.85M ARR** pipeline from 5 enterprise prospects alone
  - **$2.8M ARR** total projected pipeline including existing prospects
- This means the commercial outlook had improved beyond the original projection

### Specific client feedback
- **Acme Corp, $500K ARR potential**
  - Strong interest in real-time dashboard
  - Wants KPI-based custom alerting
  - Asked about Okta SSO integration
- **GlobalTech, $350K ARR**
  - Positive on latency numbers
  - Needs CSV/PDF export for compliance
  - Wants API access
- **Nexus Industries, $280K ARR**
  - Likes UI mockups
  - Concerned about multi-region data residency and GDPR
  - Asked about real-time streaming SLAs
- **Summit Financial, $420K ARR**
  - Interested in anomaly detection
  - Needs SOC 2 Type II before signing
  - Wants white-labeling
- **DataFlow Inc, $300K ARR**
  - Wants Snowflake integration
  - Asked for custom metric definitions via API
  - Budget approval depends on Q2 board timing

### Most common feature requests
1. Custom alerting and anomaly detection
2. Compliance-ready export, PDF and CSV
3. API access for programmatic use
4. Multi-region and data residency support
5. White-labeling

### Business impact of the schedule slip
- Sales confirmed no beta waitlist clients had hard deadlines before **May 6**
- Leadership considered client impact from the delay **minimal**
- Security-first delivery was explicitly prioritized over speed

## 5. Current Status

Based on the most recent update from Feb 25:

### Overall state
Project Alpha is **active and progressing**, but still in the middle of **Phase 2 and early Phase 3 parallel work**.

### What is complete
- **Phase 1 Data Pipeline is live and complete**
- Kafka, Flink, TimescaleDB ingestion, dbt models, and data quality checks are running
- Frontend foundation work is already underway ahead of schedule for some components:
  - design system and Storybook setup
  - dashboard layout engine
  - core chart components in Recharts
  - SSO integration
  - responsive tablet and desktop layouts

### What is in progress
- API layer work, including security fixes and WebSocket gateway implementation
- Frontend work on:
  - real-time streaming UI
  - report export interface
  - alert configuration wizard

### What is blocked
- Live metric widgets are blocked on the WebSocket API endpoint
- Custom metric builder is blocked on the metric definition API, with backend ETA noted as **Mar 10**

### Best current read
The project appears to be in a **controlled delay, not a crisis**:
- budget was re-baselined and approved
- Phase 1 delivered successfully
- major security issues were identified before launch rather than after
- sales outlook remains strong
- frontend is making useful progress in parallel

The main things determining success from here are finishing the Phase 2 security and realtime backend work, then keeping the revised schedule to reach **beta on May 6** and **GA on May 27**.
