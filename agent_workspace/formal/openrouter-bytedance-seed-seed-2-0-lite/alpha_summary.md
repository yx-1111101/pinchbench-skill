# Project Alpha Summary

## 1. Project Overview

Project Alpha is a new customer-facing analytics dashboard intended to replace the legacy reporting system.

### Core technology stack
- **Database and time-series storage:** PostgreSQL with TimescaleDB
- **Streaming and ingestion:** Apache Kafka for real-time events, Airflow for batch ingestion
- **Processing and transformation:** Apache Flink, dbt, Great Expectations
- **Caching and storage:** Redis for cached aggregations, S3 as the raw data lake
- **API layer:** FastAPI (Python)
- **Frontend:** React with Recharts
- **Authentication:** OAuth2 integrated with the company’s existing SSO

### Budget
- **Original approved budget:** **$340K**
  - Infrastructure: $85K
  - Engineering (6 FTEs over 4 months): $220K
  - QA and testing: $35K
- **Budget pressure identified early:** pipeline scale estimates added about **$23K/month** in cloud costs, implying about **$92K** extra over four months
- **Revised approved budget:** **$410K**
- **Savings already found:** about **$22K** via spot instances for Flink nodes
- **Phase 1 actual spend:** **$78K**, below the original $85K infrastructure allocation

## 2. Timeline

### Original timeline
- **Phase 1, Data Pipeline:** Jan 20 to Feb 14
- **Phase 2, API Layer:** Feb 17 to Mar 14
- **Phase 3, Frontend:** Mar 17 to Apr 18
- **Beta launch:** Apr 21
- **GA release:** May 12

### Actual changes
- Phase 1 completed **on schedule** by Feb 12
- On Feb 18, the project timeline was revised because of:
  - security-critical remediation work, about **1.5 weeks**
  - a dedicated WebSocket gateway service, about **2 additional weeks**
  - some work could run in parallel, so the combined slip was held to about **2.5 weeks**

### Updated timeline
- **Phase 2, API Layer:** Feb 17 to **Apr 1**
- **Phase 3, Frontend:** Apr 2 to **May 3**
- **Beta launch:** **May 6**
- **GA release:** **May 27**

### Schedule mitigation steps
- Added **Alex Wong** as a 7th engineer for security work
- Moved **compliance export** to Phase 3 to reduce Phase 2 scope
- Started frontend component work in parallel before API work fully finished

## 3. Key Risks and Issues

### Budget concerns
- Data volume was estimated at about **2TB/day**, higher than expected
- This raised infrastructure cost projections by:
  - **$15K/month** from data volume growth
  - **$8K/month** from increasing Kafka brokers from 3 to 6
- CFO flagged this as a possible **27% overrun** versus the original plan
- Finance required ROI validation, confirmation of revenue assumptions, and cost optimization options before approving expansion

### Security findings
**Critical, must fix before launch:**
- Cross-tenant data exposure risk on the metrics timeseries endpoint if `metric_id` is guessable
- WebSocket connections require per-message authentication, not just connection-time auth

**High priority:**
- Rate limiting should be per-tenant and per-user
- Report generation could expose SSRF risk if format validation is weak
- Audit logging is missing for dashboard creation and alert changes

**Medium priority:**
- Request signing to reduce replay risk
- Strict CORS documentation and allowlists

These security findings were a primary driver of the launch delay.

### Technical challenges
- WebSocket architecture was not ready for sticky-session requirements
- Team chose a **separate WebSocket gateway service** for scalability, but this added time
- Frontend progress is partially blocked on API deliverables:
  - live metric widgets are waiting on the WebSocket endpoint
  - custom metric builder is waiting on the metric definition API
- A **4-hour outage** occurred on Feb 8 due to a Kafka rebalancing storm during broker restart
  - mitigation already added: graceful shutdown procedures and monitoring alerts

## 4. Client/Business Impact

### Sales pipeline and revenue outlook
- Original revenue assumption under budget review: **$2.1M ARR**
- Sales later confirmed the broader pipeline is now tracking toward **$2.8M ARR**, ahead of plan
- The five highlighted enterprise prospects alone represent **$1.85M ARR**:
  - Acme Corp: $500K
  - GlobalTech: $350K
  - Nexus Industries: $280K
  - Summit Financial: $420K
  - DataFlow Inc: $300K

### Client feedback themes
Prospects responded positively to the product direction, especially:
- real-time dashboards
- low-latency pipeline performance
- UI mockups

Top requested capabilities:
1. Custom alerting and anomaly detection
2. Compliance-ready PDF and CSV exports
3. API access for programmatic integrations
4. Multi-region and data residency support
5. White-labeling

### Notable client-specific concerns
- **Acme Corp:** wants KPI-based alerting and Okta SSO support
- **GlobalTech:** needs CSV/PDF exports and API access
- **Nexus Industries:** raised GDPR and data residency concerns
- **Summit Financial:** requires SOC 2 Type II and wants white-labeling
- **DataFlow Inc:** wants Snowflake integration and custom metric definitions

### Business impact of the delay
- Sales confirmed no beta waitlist clients have hard deadlines before **May 6**
- Leadership assessed the customer impact of the revised schedule as **minimal**
- The stronger-than-expected pipeline likely helped justify keeping the project moving despite cost and schedule pressure

## 5. Current Status

Based on the most recent updates, Project Alpha is **active and progressing, but with a revised schedule**.

### What is complete
- **Phase 1 is done** and the data pipeline is live
- Current production-like pipeline indicators:
  - 6-broker Kafka cluster
  - about 48K events/sec average throughput
  - under 200ms end-to-end latency in Flink
  - 3 weeks of historical data loaded into TimescaleDB
  - dbt models running hourly
  - Great Expectations checks passing at 99.7%

### What is underway
- **Phase 2 is in progress**, with a focus on:
  - API implementation
  - tenant isolation fixes
  - WebSocket authentication hardening
  - building the separate WebSocket gateway service
- **Frontend work has started early in parallel**

### Frontend progress as of Feb 25
Completed:
- design system and component library
- dashboard layout engine
- Recharts-based chart components
- SSO authentication flow
- responsive tablet and desktop layouts

In progress:
- real-time streaming UI
- report export interface
- alert configuration wizard

Blocked:
- live metric widgets, pending WebSocket API
- custom metric builder, pending metric definition API, ETA Mar 10

### Overall assessment
Project Alpha appears to be in a healthy but constrained state:
- infrastructure and Phase 1 delivery are stronger than expected
- business demand is strong
- the biggest current constraints are security remediation and the WebSocket/API dependencies
- the most current official targets are **May 6 beta** and **May 27 GA**
