# Project Alpha Summary

## 1. Project Overview

Project Alpha is a new customer-facing analytics dashboard intended to replace the company's legacy reporting system.

### Technology stack
- **Database / time-series storage:** PostgreSQL + TimescaleDB
- **Streaming / ingestion:** Apache Kafka
- **Batch ingestion / orchestration:** Airflow
- **Stream processing:** Apache Flink
- **Batch transforms / modeling:** dbt
- **Data quality:** Great Expectations
- **Cache:** Redis
- **Raw storage:** S3
- **API layer:** FastAPI (Python)
- **Frontend:** React + Recharts
- **Authentication:** Existing SSO via OAuth2

### Budget
- **Original approved budget:** **$340K total**
  - Infrastructure: $85K
  - Engineering: $220K
  - QA/testing: $35K
- **Revised budget discussion:** Infra projections increased by **$23K/month** due to higher data volume and larger Kafka cluster sizing.
- **CFO concern:** This implied a possible total of **$432K**, a **27% overrun** over the original 4-month plan.
- **Approved expanded budget:** **$410K**
- **Cost optimization achieved:** Team saved **$22K** using spot instances for Flink nodes.

## 2. Timeline

### Original timeline
- **Phase 1, Data Pipeline:** Jan 20 to Feb 14
- **Phase 2, API Layer:** Feb 17 to Mar 14
- **Phase 3, Frontend:** Mar 17 to Apr 18
- **Beta Launch:** Apr 21
- **GA Release:** May 12

### Status and changes
- **Phase 1 completed on schedule** as of Feb 12.
- On Feb 18, the timeline was revised due to:
  - security fixes for cross-tenant isolation and WebSocket authentication, about **1.5 weeks**
  - a new WebSocket gateway service, about **2 weeks**
  - some overlap reduced the net impact to about **2.5 weeks**

### Updated timeline
- **Phase 2, API Layer:** Feb 17 to **Apr 1**
- **Phase 3, Frontend:** Apr 2 to **May 3**
- **Beta Launch:** **May 6**
- **GA Release:** **May 27**

### Delivery adjustments made to offset delay
- Added **Alex Wong** as a 7th engineer for security work
- Moved **compliance export** feature to Phase 3
- Started some frontend work in parallel during late Phase 2

## 3. Key Risks and Issues

### Budget concerns
- Estimated data volume reached about **2TB/day**, well above initial assumptions.
- Infra cost pressure came from:
  - **$15K/month** extra from data volume growth
  - **$8K/month** extra from expanding Kafka from 3 to 6 brokers
- CFO required ROI justification, confirmation of revenue projections, and more cost optimization before approving higher spend.

### Security findings
**Critical, must fix before launch:**
- Cross-tenant data exposure risk on the time-series metrics endpoint if `metric_id` is guessable
- WebSocket connections need **per-message authentication**, not just connection-time auth

**High priority:**
- Rate limiting must be per-tenant and per-user
- Report generation format handling may allow SSRF if validation is weak
- Missing audit logging for dashboard and alert changes

**Medium priority:**
- Request signing to reduce replay attacks
- Strict CORS allowlists and documentation

A follow-up security review is required after critical and high issues are fixed.

### Technical challenges
- Real-time architecture required a decision between Redis pub/sub, a dedicated WebSocket gateway, or SSE.
- Team chose a **separate WebSocket gateway service** for scalability, but it added about **2 weeks** to Phase 2.
- Frontend remains blocked on the live WebSocket endpoint for real-time widgets.
- Custom metric builder is blocked on the metric definition API, with backend ETA noted as **Mar 10**.
- There was a **4-hour outage on Feb 8** caused by a Kafka rebalancing storm during broker restart. Mitigation was added through graceful shutdown procedures and monitoring alerts.

## 4. Client/Business Impact

### Sales pipeline and revenue outlook
- Initial revenue assumption referenced by finance: **$2.1M ARR**
- By Feb 14, sales reported:
  - **$1.85M ARR** pipeline from 5 enterprise prospects alone
  - **$2.8M ARR** total projected pipeline including existing prospects
- This put Project Alpha **ahead of plan** versus the original revenue projection.

### Client feedback highlights
- **Acme Corp, $500K ARR potential**
  - Strong interest in real-time dashboard
  - Wants custom KPI-based alerting
  - Asked about Okta SSO integration
- **GlobalTech, $350K ARR**
  - Likes low-latency pipeline
  - Needs CSV/PDF exports
  - Wants API access
- **Nexus Industries, $280K ARR**
  - Likes UI mockups
  - Concerned about GDPR and multi-region data residency
  - Asked about SLA guarantees for streaming
- **Summit Financial, $420K ARR**
  - Interested in anomaly detection
  - Requires SOC 2 Type II before signing
  - Wants white-labeling
- **DataFlow Inc, $300K ARR**
  - Wants Snowflake integration
  - Wants custom metric definitions via API
  - Budget decision depends on Q2 board meeting

### Top market-driven feature requests
1. Custom alerting and anomaly detection
2. Compliance-ready PDF/CSV export
3. API access for programmatic use
4. Multi-region and data residency support
5. White-labeling

### Business impact of the schedule slip
- Sales confirmed no beta waitlist clients had hard deadlines before **May 6**
- Leadership concluded **client impact from the delay is minimal**
- Security-first delivery was explicitly prioritized over shipping earlier

## 5. Current Status

Based on the most recent updates, Project Alpha is in a mixed but generally healthy state:

- **Phase 1 is complete and live**
  - Kafka, Flink, TimescaleDB, dbt, and data quality tooling are running
  - Throughput is averaging about **48K events/sec**
  - End-to-end latency is under **200ms**
  - Historical backfill of 3 weeks is complete
- **Budget is under better control than feared**
  - Expanded budget was approved at **$410K**, below the worst-case $432K scenario
  - Phase 1 actual infra spend was **$78K**, below the original $85K infra allocation
- **Phase 2 is in progress but delayed**
  - Delay is driven by legitimate security remediation and the WebSocket gateway build
  - Security and architecture work is now on the critical path
- **Frontend has already started early in parallel**
  - Design system, component library, dashboard layout engine, Recharts-based charts, SSO flow, and responsive layouts are done
  - Real-time streaming UI, export interface, and alert wizard are underway
  - Live widgets and custom metric builder remain partially blocked on backend APIs
- **Commercial outlook is strong**
  - Client response is positive
  - Revenue pipeline is above target
  - Several prospects are pushing feature priorities that may influence Phase 3 and post-launch roadmap

### Bottom line
Project Alpha appears to be **on solid footing strategically**, with strong client demand and a working data foundation. The main near-term concerns are **security remediation, real-time architecture completion, and keeping the revised timeline from slipping again**. As of the latest email, the project is progressing, but success now depends on executing Phase 2 cleanly and unblocking the remaining frontend dependencies.
