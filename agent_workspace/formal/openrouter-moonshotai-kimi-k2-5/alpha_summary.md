# Project Alpha Summary

## 1. Project Overview

Project Alpha is a new customer-facing analytics dashboard intended to replace the company's legacy reporting system.

### Core technology stack
- **Database:** PostgreSQL with **TimescaleDB** for time-series data
- **Data ingestion and processing:** **Apache Kafka** for real-time event streaming, **Airflow** for batch ingestion and historical migration, **Apache Flink** for stream processing, **dbt** for transformations, and **Great Expectations** for data quality checks
- **Storage and caching:** **TimescaleDB**, **Redis** for cached aggregations, and **S3** as the raw data lake
- **API layer:** **FastAPI** (Python)
- **Frontend:** **React** with **Recharts**
- **Authentication:** Existing SSO via **OAuth2**

### Budget
- **Original approved budget:** **$340K total**
  - Infrastructure: $85K
  - Engineering (6 FTEs, 4 months): $220K
  - QA and testing: $35K
- **Primary budget pressure:** higher-than-expected data volume and Kafka scaling needs increased projected infrastructure costs by **$23K/month**
- **Revised projection raised by finance:** potential total of **$432K** over 4 months, a **27% overrun**
- **Approved expanded budget after review:** **$410K**
- **Mitigation savings achieved:** **$22K** saved using spot instances for Flink nodes
- **Phase 1 actual spend:** **$78K**, below the original $85K infrastructure budget

## 2. Timeline

### Original timeline
- **Phase 1, Data Pipeline:** Jan 20 to Feb 14
- **Phase 2, API Layer:** Feb 17 to Mar 14
- **Phase 3, Frontend:** Mar 17 to Apr 18
- **Beta Launch:** Apr 21
- **GA Release:** May 12

### Status and changes
- **Phase 1 completed on schedule** and was declared live on **Feb 12**
- On **Feb 18**, the project timeline was revised because of:
  - mandatory security fixes
  - the decision to add a separate WebSocket gateway service

### Updated/current expected timeline
- **Phase 2, API Layer:** Feb 17 to **Apr 1**
- **Phase 3, Frontend:** Apr 2 to **May 3**
- **Beta Launch:** **May 6**
- **GA Release:** **May 27**

### Net change
- Beta launch moved back by **15 days**
- GA release moved back by **15 days**
- Some schedule recovery actions were taken:
  - adding **Alex Wong** as a 7th engineer
  - moving compliance export work into Phase 3
  - starting frontend work in parallel during late Phase 2

## 3. Key Risks and Issues

### Budget concerns
- Data volume was estimated at roughly **2TB/day**, higher than planned
- This increased infrastructure costs by about **$15K/month**
- Kafka cluster sizing likely needed **6 brokers instead of 3**, adding another **$8K/month**
- Finance required a cost-benefit analysis, sales validation of projected ARR, and cost-optimization work before approving higher spend

### Security findings
Security identified multiple issues, including two critical blockers before launch:

#### Critical
1. **Cross-tenant data exposure risk** on the time-series metrics endpoint if `metric_id` is guessable, requiring tenant isolation at the query layer
2. **WebSocket authentication weakness**, requiring per-message auth tokens rather than auth only at connection time

#### High
3. Rate limiting should be per-tenant and per-user
4. Report generation format parameters could enable **SSRF** if not strictly validated
5. Missing audit logging for dashboard and alert configuration changes

#### Medium
6. Request signing to reduce replay-attack risk
7. Strict CORS allowlist documentation and configuration

A follow-up security review is required after the critical and high findings are fixed.

### Technical challenges
- WebSocket support became a major design issue because the existing infrastructure does not support sticky sessions
- The preferred solution, a **separate WebSocket gateway service**, adds about **2 weeks** to Phase 2
- Frontend work is partially blocked pending API dependencies:
  - live metric widgets need the WebSocket endpoint
  - custom metric builder needs the metric definition API
- There was also a **4-hour outage on Feb 8** caused by a Kafka rebalancing storm during broker restart, though graceful shutdown procedures and monitoring alerts have since been added

## 4. Client/Business Impact

### Sales pipeline and revenue outlook
Early beta waitlist feedback was strong:
- **Acme Corp:** $500K ARR potential
- **GlobalTech:** $350K ARR
- **Nexus Industries:** $280K ARR
- **Summit Financial:** $420K ARR
- **DataFlow Inc:** $300K ARR

### Revenue projections
- These five prospects alone represent **$1.85M ARR**
- Combined with the broader pipeline, sales reported the company is tracking toward **$2.8M ARR**, ahead of the original **$2.1M ARR** projection
- This sales validation helped support the case for the expanded project budget

### Client feedback themes
Clients responded positively to:
- the real-time dashboard concept
- low data-pipeline latency
- UI mockups

Top requested capabilities:
1. Custom alerting and anomaly detection
2. Compliance-ready exports, PDF and CSV
3. API access for programmatic use
4. Multi-region and data residency support
5. White-labeling

### Business and delivery impact of delays
- Sales confirmed that none of the beta waitlist clients had hard deadlines before **May 6**
- As a result, the project delay was assessed as having **minimal immediate client impact**
- However, some client requests point to future roadmap and go-to-market pressure, including:
  - Okta compatibility expectations
  - GDPR and multi-region data residency concerns
  - SOC 2 Type II requirements
  - SLA expectations for real-time streaming
  - Snowflake integration
  - white-label support

## 5. Current Status

Based on the most recent update from **Feb 25, 2026**, Project Alpha is in a delayed but actively progressing state.

### What is complete
- **Phase 1 is complete and live**
- Pipeline is running with:
  - 6 Kafka brokers
  - about 48K events/sec average throughput
  - under 200ms end-to-end latency
  - 3 weeks of historical data loaded into TimescaleDB
  - dbt models on hourly schedules
  - Great Expectations checks passing at 99.7%
- Frontend groundwork has started early and already includes:
  - design system and component library in Storybook
  - dashboard layout engine
  - chart components using Recharts
  - SSO authentication flow
  - responsive tablet and desktop layouts

### What is in progress
- **Phase 2 API work is underway**, but extended through **Apr 1**
- Security remediation work is part of the active API effort
- Frontend is also progressing in parallel on:
  - real-time streaming UI
  - report export interface
  - alert configuration wizard

### What is blocked or unresolved
- WebSocket gateway implementation is still needed for live metric widgets
- Metric definition API is still needed for the custom metric builder, with an ETA of **Mar 10** from Marcus
- A follow-up security review is still required before launch readiness

### Bottom line
Project Alpha appears to be **healthy but more complex and expensive than originally planned**. The project has strong commercial promise, an approved expanded budget, and a completed data platform foundation. The main factors defining current status are the **Phase 2 delay caused by security and WebSocket architecture work**, plus a still-manageable set of technical and compliance risks before the revised **May 6 beta** and **May 27 GA** milestones.
