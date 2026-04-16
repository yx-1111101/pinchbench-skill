# Project Alpha Summary

## 1. Project Overview

Project Alpha is a new customer-facing analytics dashboard intended to replace the legacy reporting system. It is being built as a multi-phase platform covering data ingestion, processing, APIs, and a React frontend.

### Core technology stack
- **Database and storage:** PostgreSQL with TimescaleDB for time-series metrics, Redis for caching, and S3 for raw data lake storage
- **Data pipeline:** Apache Kafka for real-time event streaming, Airflow for batch historical migration, Apache Flink for stream processing, dbt for transformations, and Great Expectations for data quality checks
- **API layer:** FastAPI (Python), OAuth2 with existing SSO, WebSocket live-metrics endpoint, report generation endpoints for PDF/CSV
- **Frontend:** React with Recharts, Storybook-based design system, responsive dashboard UI
- **Auth:** Existing SSO via OAuth2

### Budget
- **Original approved budget:** **$340K**
  - Infrastructure: $85K
  - Engineering: $220K
  - QA/testing: $35K
- **Budget risk identified:** Data volume and Kafka scaling increased projected infra costs by **$23K/month**, implying about **$92K** over 4 months and a possible total of **$432K**
- **Current approved budget:** **$410K** after cost review and optimization
- **Notable savings:** **$22K** saved via spot instances for Flink nodes
- **Phase 1 actual spend:** **$78K** versus **$85K** budgeted for infrastructure

## 2. Timeline

### Original timeline
- Phase 1, Data Pipeline: **Jan 20 - Feb 14**
- Phase 2, API Layer: **Feb 17 - Mar 14**
- Phase 3, Frontend: **Mar 17 - Apr 18**
- Beta Launch: **Apr 21**
- GA Release: **May 12**

### Changes to timeline
On Feb 18, the team formally revised the schedule because of:
- Security critical remediation work, adding about **1.5 weeks**
- Decision to build a separate **WebSocket gateway service**, adding about **2 weeks**
- Some parallelization reduced the combined slip to about **2.5 weeks**

### Current expected timeline
- Phase 2, API Layer: **Feb 17 - Apr 1**
- Phase 3, Frontend: **Apr 2 - May 3**
- Beta Launch: **May 6**
- GA Release: **May 27**

### Milestones reached so far
- **Phase 1 completed on schedule** as of Feb 12
- Frontend work began early in parallel before Phase 2 completion to reduce downstream impact

## 3. Key Risks and Issues

### Budget concerns
- Data volume was estimated at about **2TB/day**, higher than expected
- Infra costs increased by roughly **$15K/month** due to data volume
- Kafka cluster sizing likely required **6 brokers instead of 3**, adding about **$8K/month**
- CFO required ROI validation, sales confirmation, and cost optimization analysis before approving expansion
- Budget was ultimately increased, but cost pressure remains a core project risk

### Security findings
The Feb 10 security review identified serious issues:

**Critical, must fix before launch**
- Cross-tenant data exposure risk in the metrics time-series endpoint if `metric_id` is guessable
- WebSocket connections need per-message authentication, not only connection-time auth

**High priority**
- Rate limiting should be per-tenant and per-user
- Report generation endpoint may be vulnerable to SSRF if format inputs are not validated
- Audit logging is missing for dashboard creation and alert changes

**Medium priority**
- Request signing to reduce replay attacks
- Strict CORS allowlist documentation and configuration

These findings directly caused the schedule slip and made security remediation a gating item for launch.

### Technical challenges
- WebSocket architecture was unresolved because current infrastructure did not support sticky sessions
- Team chose a separate **WebSocket gateway service** for scalability, despite the timeline impact
- Frontend live metric widgets are blocked on the WebSocket API
- Custom metric builder is blocked on the metric definition API
- A **4-hour outage on Feb 8** occurred due to a Kafka rebalancing storm during broker restart, though mitigation steps and monitoring were added afterward

## 4. Client/Business Impact

### Sales pipeline and revenue outlook
- CFO requested confirmation that the original **$2.1M ARR** projection still held before approving extra spend
- By Feb 14, sales reported **5 enterprise prospects** with combined potential of **$1.85M ARR**
- Including the broader pipeline, the team was tracking toward **$2.8M ARR**, which is **ahead of plan**

### Client feedback highlights
- **Acme Corp, $500K ARR potential:** strongly wants real-time dashboards, KPI-based custom alerting, and Okta SSO support
- **GlobalTech, $350K ARR:** wants PDF/CSV exports and API access
- **Nexus Industries, $280K ARR:** likes UI direction, but raised multi-region data residency and SLA concerns
- **Summit Financial, $420K ARR:** interested in anomaly detection, requires SOC 2 Type II before signing, and wants white-labeling
- **DataFlow Inc, $300K ARR:** wants Snowflake integration and custom metric definitions; internal budget depends on a Q2 board meeting

### Top cross-client requests
1. Custom alerting and anomaly detection
2. Compliance-ready exports, PDF/CSV
3. API access
4. Multi-region and data residency support
5. White-labeling

### Business impact of the delay
- Sales confirmed no beta waitlist clients had hard deadlines before the revised **May 6** beta date
- As of the latest schedule update, client impact from the delay was considered **minimal**
- Security and compliance requirements appear important for larger prospects, so delaying for remediation likely protects revenue rather than harms it

## 5. Current Status

Based on the most recent updates, Project Alpha is **in active Phase 2 / early Phase 3 overlap**.

### What is done
- Phase 1 data pipeline is live and completed on schedule
- Kafka cluster is running with 6 brokers at around **48K events/sec average**
- Flink processing latency is under **200ms**
- TimescaleDB has 3 weeks of historical data loaded
- dbt models and Great Expectations quality checks are operating successfully
- Frontend design system, component library, dashboard layout engine, chart components, responsive layouts, and SSO integration are complete

### What is in progress
- API/security remediation work from the security review
- WebSocket gateway service for real-time streaming
- Frontend report export interface
- Alert configuration wizard
- Parallel frontend development to offset the schedule slip

### What is blocked or pending
- Live metric widgets are waiting for the WebSocket API
- Custom metric builder is waiting for the metric definition API, with Marcus's ETA noted as **Mar 10**
- A follow-up security review is still required after critical and high issues are fixed

### Overall status assessment
Project Alpha is **behind the original schedule but under controlled recovery**. The team has already completed the data foundation, secured expanded funding, and started frontend work early to reduce the impact of the API/security delay. The biggest remaining execution risks are completing the security fixes, delivering the WebSocket gateway, and ensuring the revised timeline to **beta on May 6** and **GA on May 27** holds.
