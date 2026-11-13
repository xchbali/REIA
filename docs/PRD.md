# PRD.md: REIA Product Requirements Document

Status: Draft v0.3 (Phase 0.2, updated with the Architecture Decision Addendum), pending review.
Sources: REIA Full URD, the Market Expansion Addendum and the Architecture Decision Addendum. Where documents differ, the later addendum wins.
Related documents: SRS.md (detailed requirements), TAD.md (architecture), DATABASE.md (data model), AI_ARCHITECTURE.md, MEMORY_ENGINE.md, SECURITY.md, PRIVACY.md.

## 1. Product summary

REIA (Real Estate Relationship Intelligence Agent) is an AI-powered customer relationship intelligence platform for real estate professionals. It acts as a persistent, evidence-based memory layer over every customer relationship an agent manages.

REIA helps an agent to:
- keep a structured profile for every customer;
- understand customer conversations in English, Spanish and Portuguese;
- remember what each customer wants, including how those requirements changed over time;
- search and question the full conversation history;
- prepare for calls with a sourced briefing;
- draft personalized follow-ups that the agent reviews and sends;
- track commitments and next actions.

REIA does not replace the agent, the agent's relationships, or the agent's judgment. The agent stays in control of all customer-facing communication.

## 2. Vision and strategic direction

REIA is one international, multilingual, configurable platform. It is not three separate applications. The core engine (customer memory, conversation intelligence, assistant, follow-up copilot, call briefing) is shared across all markets. Country differences are handled through configuration, localization and integration layers.

Primary engineering principle: build a reliable, evidence-based customer memory system first. Every other intelligent feature builds on top of it.

## 3. Problem statement

Real estate is relationship-driven. An agent may manage dozens or hundreds of buyers, tenants, sellers and investors at once. Each has different requirements, budgets, objections and history, spread across WhatsApp, calls, email, meetings, viewings, CRM entries and personal notes.

| ID | Problem | Consequence |
|---|---|---|
| P1 | Customer information is fragmented across channels and tools | Agent cannot see the full picture |
| P2 | Notes are written manually after conversations | Time lost; notes skipped or incomplete |
| P3 | Requirements, objections and promises are forgotten | Repeated questions, missed commitments |
| P4 | Requirements change over time (budget, area, timeline) | Old and new information get mixed up or overwritten |
| P5 | Generic follow-ups ignore context | Damages personal relationships |
| P6 | Preparing for a call means rereading old chats | Slow, inconsistent preparation |
| P7 | A CRM stores data but does not understand the history | The gap REIA targets |

Whether these problems are as significant for target users as assumed is a hypothesis to validate (see §14), not an established fact.

## 4. Product goals and non-goals

### 4.1 Goals

G1. One intelligence profile per customer, built from original conversations.
G2. Preserve every original conversation unchanged.
G3. Extract structured facts and keep their full history, with the source of each fact.
G4. Answer questions about a customer using only retrieved evidence, and say so when information is missing.
G5. Work across English, Spanish and Portuguese, including cross-language questions.
G6. Generate contextual drafts and call briefings that the agent controls.
G7. Isolate every organization's data completely.
G8. Be extensible to more countries, currencies and languages through configuration.

### 4.2 Non-goals

REIA must not become:
- a generic chatbot;
- another basic CRM;
- a mass-messaging or email-marketing tool;
- an autonomous salesperson or a system that sends scheduled generic follow-ups;
- a system that invents customer information;
- a replacement for human relationship-building.

## 5. Target markets

| Market | Country (ISO code) | Currency | Initial languages | Notes |
|---|---|---|---|---|
| Dubai | United Arab Emirates (AE) | AED | English (Arabic planned) | Dubai is a city, not a country; the jurisdiction is the UAE. Not the exclusive market |
| Spain | Spain (ES) | EUR | Spanish, English | GDPR applies |
| Portugal | Portugal (PT) | EUR | Portuguese, English | GDPR applies |

- The three markets are considered from the architecture stage. Their legal, property and communication practices are not assumed to be identical.
- A jurisdiction-specific compliance assessment is required before launching in each market (see PRIVACY.md). Technical security controls alone are not a compliance claim.
- Market research and pilot feedback are kept separately per country.

### Market sequencing (confirmed product decisions)

- First pilot market: Dubai (United Arab Emirates, country code AE). Secondary validation markets: Spain and Portugal.
- REIA remains a single international product supporting all three markets.
- No pilot customer has been secured. A Dubai realtor took part in an initial discovery discussion. This is not a pilot commitment and not a paying customer, and it must not be presented as one.
- Pilot target: 2 to 3 independent agents or small agency teams.
- Spain and Portugal are validated separately before any commercial expansion there.

## 6. Target users

### 6.1 Customer segments

Independent agents, property consultants, brokers, small and medium agencies, residential agents, luxury agents, investment consultants, and buyer, seller and rental specialists. The initial pilot prioritizes independent agents and small teams.

### 6.2 Initial ideal pilot profile

Manages many active customers, uses WhatsApp regularly, may use a CRM (for example Pipedrive), takes manual notes, values personalized communication, struggles to keep full context, and is willing to test AI-assisted workflows.

REIA must not assume that every CRM user needs another product. Workflow gaps are validated before extra features are built.

### 6.3 Roles in the product

| Role | Scope |
|---|---|
| Platform admin | Operates the platform; access is audited; no routine access to customer content |
| Organization owner | Full control of one organization, including members and settings |
| Organization admin | Manages members and organization settings |
| Agent | Manages own customers and uses all intelligence features |
| Read-only member | Views permitted records; cannot change them |

### 6.4 Core user stories

- As an agent, I paste a WhatsApp chat and see the customer's requirements extracted, with the exact message each one came from.
- As an agent, I ask "What does Ahmed want now?" and get a sourced answer that also shows his earlier budget.
- As an agent in Spain, I import a Spanish chat and read the answers in English, while the original Spanish stays untouched.
- As an agent, I open a call briefing before dialing and see promises I made and objections raised.
- As an agent, I generate a draft in the customer's language, edit it, and send it myself.
- As an agent, I correct a wrong extracted fact and the correction is recorded.

## 7. Product scope by module

Requirement IDs are used for traceability into SRS.md. Priority: **M** = MVP, **L** = later.

### 7.1 Authentication and accounts (AUTH)

| ID | Requirement | Priority |
|---|---|---|
| AUTH-1 | Registration, login, logout, token refresh with rotation | M |
| AUTH-2 | Email verification and password reset | M |
| AUTH-3 | Organization creation and membership with the five roles | M |
| AUTH-4 | Login rate limiting and secure session handling | M |
| AUTH-5 | User profile and UI language setting | M |
| AUTH-6 | Account deletion and personal data export | M |
| AUTH-7 | Customer-level permissions beyond roles | L |

### 7.2 Customer management (CUST)

| ID | Requirement | Priority |
|---|---|---|
| CUST-1 | Create, view, edit and archive customers | M |
| CUST-2 | Profile fields: name, type, status, assigned agent, preferred language, country, contact identifiers | M |
| CUST-3 | Customer types: buyer, seller, tenant, landlord, investor, other | M |
| CUST-4 | Status pipeline: new lead, contacted, qualified, active conversation, viewing scheduled, negotiation, converted, lost, dormant | M |
| CUST-5 | Normalized phone and email identifiers; duplicate detection | M |
| CUST-6 | Manual merge of duplicates with merge history; never automatic merge of uncertain identities | M |
| CUST-7 | Manual notes on a customer | M |
| CUST-8 | Search and filter customers (name search tolerant of accents) | M |

All profile fields are optional unless a specific workflow requires them.

### 7.3 Conversation management (CONV)

| ID | Requirement | Priority |
|---|---|---|
| CONV-1 | Import by pasting text, uploading TXT or CSV, adding call and meeting notes | M |
| CONV-2 | Store original content unchanged and immutable | M |
| CONV-3 | Record channel, direction, sender, timestamp, import method and processing status | M |
| CONV-4 | Detect and preserve the original language; never replace it with a translation | M |
| CONV-5 | Detect duplicate imports and avoid duplicate facts, events or messages | M |
| CONV-6 | Link a conversation to a customer, or hold it as "pending match" until confirmed | M |
| CONV-7 | Chronological history, channel filter, keyword search, view originals | M |
| CONV-8 | Reprocess a conversation | M |
| CONV-9 | Translation on request, stored separately from the original | M |
| CONV-10 | Emails, WhatsApp Business, calendar and call transcription as sources | L |

### 7.4 AI conversation intelligence (INTEL)

| ID | Requirement | Priority |
|---|---|---|
| INTEL-1 | Extract: identity, property requirements, financial context, intent, preferences, objections, commitments, events, communication preferences, uncertainties | M |
| INTEL-2 | Every extracted item carries category, value, evidence quote (original language), source conversation and message, confidence, verification status | M |
| INTEL-3 | Financial information is extracted only when explicitly stated, never inferred | M |
| INTEL-4 | Output is validated against strict schemas; unsupported facts are rejected | M |
| INTEL-5 | Sentiment and engagement signals, if shown, are labeled as AI signals and never as verified facts | M |
| INTEL-6 | Conversation summaries in the agent's UI language | M |
| INTEL-7 | Suggested next actions based on the actual conversation | M |
| INTEL-8 | Customer-provided text is treated as untrusted data; instructions inside it are never executed | M |
| INTEL-9 | Processing is retryable and idempotent, with a recorded outcome | M |

### 7.5 Persistent customer memory (MEM)

This is the highest-priority module.

| ID | Requirement | Priority |
|---|---|---|
| MEM-1 | Maintain current structured facts per customer | M |
| MEM-2 | Preserve every previous value when a fact changes (for example budget 1.5M then 1.8M), with date, source and evidence | M |
| MEM-3 | Detect conflicts; preserve both statements, mark the conflict, and ask the agent when it cannot be resolved | M |
| MEM-4 | Never assume the newest statement is permanent without an explicit change | M |
| MEM-5 | Episodic timeline of meaningful events | M |
| MEM-6 | Commitment memory: promises, deadlines, responsibilities | M |
| MEM-7 | Hybrid retrieval: structured queries, keyword search, semantic vector search, time and metadata filters | M |
| MEM-8 | Ranking considers customer identity, relevance, recency, verification status, source quality, temporal validity and query intent; never similarity alone | M |
| MEM-9 | Agents can correct, reject, verify and resolve facts; all changes are audited | M |
| MEM-10 | Outdated facts are marked historical or expired, never deleted automatically | M |
| MEM-11 | Cross-language retrieval (query in one language, evidence in another) | M |
| MEM-12 | PostgreSQL is the source of truth; vectors are a derived index | M |

### 7.6 Customer assistant (ASST)

| ID | Requirement | Priority |
|---|---|---|
| ASST-1 | Agent selects a customer and asks questions about that customer only | M |
| ASST-2 | Answers use retrieved evidence, include source references and dates, and separate current from historical information | M |
| ASST-3 | Missing information is stated as unavailable; the assistant never invents answers | M |
| ASST-4 | Uncertainty and unresolved conflicts are surfaced | M |
| ASST-5 | Answers are returned in the agent's UI language | M |
| ASST-6 | Retrieval never crosses customer or organization boundaries | M |

### 7.7 Follow-up copilot (FOLLOW)

| ID | Requirement | Priority |
|---|---|---|
| FOLLOW-1 | Drafts for WhatsApp, email, SMS, post-call, post-viewing, objection responses, re-engagement, appointment confirmation and document requests | M |
| FOLLOW-2 | Draft language follows the customer's preferred language | M |
| FOLLOW-3 | Drafts use the real history: no repeated questions, previous objections remembered, no invented prior discussions | M |
| FOLLOW-4 | Agent voice profile: tone, formality, length, languages, example messages; editable and resettable | M |
| FOLLOW-5 | Workflow: generate, review, edit, approve, agent sends manually, optional record of the sent message | M |
| FOLLOW-6 | No autonomous customer-facing messages in the MVP | M |

### 7.8 Call briefing (BRIEF)

| ID | Requirement | Priority |
|---|---|---|
| BRIEF-1 | Briefing sections: overview, current requirements, history, preferences, objections, commitments, pending actions, discussion points, suggested questions, warnings | M |
| BRIEF-2 | Every briefing item is backed by evidence and linked to its source | M |
| BRIEF-3 | Briefing is generated in the agent's UI language | M |

### 7.9 Tasks and commitments (TASK)

| ID | Requirement | Priority |
|---|---|---|
| TASK-1 | Manual tasks with category, assignee, due date, priority, status | M |
| TASK-2 | AI-suggested tasks and commitments start as "suggested"; they become real only after agent approval | M |
| TASK-3 | Overdue and pending views, filter by priority | M |

### 7.10 Timeline (TIME) and search (SRCH)

| ID | Requirement | Priority |
|---|---|---|
| TIME-1 | Per-customer chronological timeline of conversations, notes, requirement changes, commitments, drafts, tasks and status changes | M |
| TIME-2 | Filter by date, channel, activity type, agent, category | M |
| SRCH-1 | Search customers, conversations, requirements, objections, tasks and commitments with keyword and semantic modes | M |
| SRCH-2 | Search respects organization and role permissions | M |

### 7.11 Dashboard (DASH)

| ID | Requirement | Priority |
|---|---|---|
| DASH-1 | Basic dashboard: recent customers and interactions, pending and overdue tasks, recent AI activity | M |
| DASH-2 | Advanced analytics, calculated only from recorded data; no unsupported revenue predictions | L |

### 7.12 Integrations (INTG)

| ID | Requirement | Priority |
|---|---|---|
| INTG-1 | Pipedrive: OAuth, import contacts and deals, selected field sync, attach approved notes | L |
| INTG-2 | WhatsApp Business Platform, only through officially supported capabilities; no scraping or personal-account access | L |
| INTG-3 | Gmail, Outlook, calendar and transcription providers with least-privilege OAuth | L |
| INTG-4 | n8n for selected workflows; core business logic stays in the backend | L |
| INTG-5 | CRM data is never overwritten without defined rules, field mapping and user-chosen sync direction | L |

The standalone memory engine is built and validated before any integration work.

### 7.13 Internationalization (I18N)

| ID | Requirement | Priority |
|---|---|---|
| I18N-1 | UI languages at launch: English, Spanish, Portuguese. Conversation processing at launch: English, Spanish, Portuguese. An Arabic UI is not required at launch | M |
| I18N-2 | UI language is a per-user setting; customer language is a per-customer setting | M |
| I18N-3 | Language detection on import | M |
| I18N-4 | Currencies AED and EUR at launch; any ISO 4217 currency supported through configuration; currency code stored separately from the amount | M |
| I18N-5 | Area in square meters or square feet with the unit stored explicitly | M |
| I18N-6 | Structured location: country, region, city, neighborhood, building or development, postal code | M |
| I18N-7 | Localized number, date and time formatting; timezone-aware dates | M |
| I18N-8 | Country configuration (currencies, languages, units, terminology) is added without changing core logic | M |
| I18N-9 | No Dubai-specific assumptions hardcoded in core logic | M |
| I18N-10 | Frontend architecture supports future right-to-left (RTL) layouts: logical CSS properties, no hardcoded left or right assumptions | M |
| I18N-11 | Unicode (UTF-8) storage and processing everywhere; no English-only assumptions in database fields or interfaces | M |
| I18N-12 | Conversation language detection is separate from UI language. Arabic conversation processing is a future capability, evaluated independently from Arabic UI localization | L |

### 7.14 AI provider governance (PROV)

| ID | Requirement | Priority |
|---|---|---|
| PROV-1 | Provider-independent interface; provider and model are selectable per task and per organization; no provider is hardcoded in business logic | M |
| PROV-2 | OpenAI is the primary production provider for conversation analysis, fact extraction, memory generation and updates, customer Q&A, summaries, follow-up drafts, call briefings and embeddings | M |
| PROV-3 | DeepSeek is restricted to development, experimentation, synthetic test data, public information and properly anonymized test content | M |
| PROV-4 | Five data classes are distinct: `public`, `synthetic`, `anonymized`, `pseudonymized`, `identifiable`. Pseudonymized data is never automatically treated as anonymized. It is handled as identifiable customer data unless a documented anonymization assessment says otherwise | M |
| PROV-5 | Restricted providers are deny-by-default for `pseudonymized` and `identifiable` data. Enabling one for real customer data requires all of: legal review of the jurisdiction, review of current contractual terms and privacy policy, assessment of international transfers and safeguards, data-processing agreements and security review, and explicit approval in the provider configuration | M |
| PROV-6 | The restriction is enforced in three independent places: backend code policy, deployment configuration (credentials of a restricted provider are not provisioned in production unless approved under PROV-5), and per-organization settings. Per-organization settings can only narrow what code and deployment allow, never widen it | M |
| PROV-7 | Every AI request, including embedding requests, passes the provider-policy check before it leaves the backend. Blocked requests are rejected and recorded | M |
| PROV-8 | Logs record provider, model, endpoint, task, data class, timestamp and processing status, without unnecessarily logging sensitive prompt content | M |
| PROV-9 | Before production, review current OpenAI API data controls, storage settings and Zero Data Retention eligibility per endpoint. Endpoints are not assumed to have identical retention behavior | M |
| PROV-10 | The design allows region-specific providers to be added later | L |

## 8. Cross-cutting requirements

### 8.1 Security and privacy (summary)

- Strict organization isolation, role-based access, protected endpoints.
- Encryption in transit; encrypted integration credentials; no secrets in code; no sensitive data in ordinary logs.
- Minimal personal data sent to AI providers; no training on customer data without explicit authorization; provider keys server-side only.
- Audit logging of security-relevant events and fact corrections.
- Data export, deletion and retention policies, defined per jurisdiction (PRIVACY.md).
- Consent and authorization for imports, recordings, transcription and third-party integrations.

### 8.2 Reliability and performance targets

These are engineering targets, not guarantees. They are measured under a defined MVP test load.

- Dashboard API: under 500 ms at p95.
- Customer search: under 1 s at p95.
- AI latency is measured separately because it depends on external providers.
- Pagination on all lists; retries and idempotent processing; structured logs; backup and restore tested before the pilot.

### 8.3 Accessibility and UX principles

Simple navigation, responsive layout, clear information hierarchy, accessible controls, consistent components, loading, error and empty states, and confirmation dialogs for sensitive actions. The interface is built to support additional languages and right-to-left scripts later.

### 8.4 Data retention, deletion and subject rights (proposed defaults)

The values below are **proposed REIA product-policy defaults** applied across the UAE (Dubai), Spain and Portugal. They are **not statutory retention periods** under UAE PDPL or GDPR, and REIA does not claim that those laws require these durations. **Legally verified requirements: none yet.** This section is updated with verified requirements only after a qualified, jurisdiction-specific privacy and legal review, which is required before production launch. PRIVACY.md is the authoritative document.

| Data category | Proposed default | Status |
|---|---|---|
| Customer records and conversations | Kept while the customer workspace remains active, subject to purpose limitation and user controls | Proposed |
| Production deletion after a verified deletion request | Within 30 days | Proposed |
| Backup expiration after deletion | Within 35 additional days | Proposed |
| Security and audit logs | 12 months | Proposed |
| Legal hold | Only where legally required, documented and access-restricted | Proposed |

#### Workspace lifecycle (proposed)

- `active`: normal operation.
- `dormant`: no member activity for a configurable inactivity period (the length is not set here and is decided with the legal review). The owner is notified. A dormant workspace is never deleted automatically without owner notice. Deletion starts only on the owner's confirmation or on termination. Whether continued retention of dormant data is justified is a legal review item.
- `terminated`: the owner closes the workspace or the contract ends. Data export is available during a configurable export window (length not set yet). When the window ends, the deletion process starts as for a verified deletion request, unless a documented legal hold applies.

#### Deletion requests, backups and the deletion ledger

1. A deletion request (customer erasure or workspace deletion) is verified, then recorded in the deletion ledger before anything is deleted.
2. Production data, including embeddings and other derived data, is erased within 30 days through the controlled erase functions (DATABASE.md section 7.2).
3. Backups are immutable and are not edited per customer. Backup copies expire within 35 further days under the normal backup rotation.
4. The deletion ledger records identifiers only, never personal data: subject type and id, organization id, verification and execution timestamps, and the date after which no backup can still hold the data. It is append-only and is also exported to a store separate from the database backups, so restoring a backup cannot roll it back.
5. After any restore, the restore procedure must re-apply every ledger entry executed after the backup's snapshot time before the system is reopened to users. Restored data of a deleted subject must never become visible. Phase 12 tests this procedure.
6. Ledger entries are kept at least until the last backup that could contain the subject has expired, plus a safety margin. Proposed: 12 months, the same as audit logs.
7. Data held by AI providers is reviewed under PROV-9, and the deletion process documents what each provider retains.

Other rules:
- Retention is configurable where customer contracts or applicable law require different periods.
- The product provides data export, correction, deletion and retention-management capabilities.
- Personal data in technical logs is minimized.
- Exceptions and legal holds are documented.

## 9. MVP definition

Central proposition to prove: **REIA can understand and remember a customer's complete conversation history and provide reliable contextual assistance.**

### 9.1 In MVP

Authentication and organizations; customer management and profiles; manual conversation import; original conversation storage; summarization; structured fact extraction with evidence; persistent memory with history and conflict handling; hybrid retrieval; customer-specific assistant with source-backed answers; follow-up drafts; call briefings; basic tasks; basic dashboard; English, Spanish and Portuguese support; testing and security.

### 9.2 Excluded from MVP

Autonomous messaging or calling, AI voice agents, complex multi-agent orchestration, full WhatsApp integration, full CRM synchronization, advanced analytics, enterprise billing, complex team management, mobile apps.

## 10. Success metrics

### 10.1 AI quality (measured on a fixed evaluation set in English, Spanish and Portuguese)

Fact extraction precision and recall; budget-change detection; historical preservation; conflict detection; retrieval precision and recall; cross-language retrieval accuracy; source attribution accuracy; unsupported-answer refusal rate; hallucination rate; follow-up personalization and briefing quality (human-rated).

Numeric targets are set in Phase 5 after the first evaluation baseline. They are not invented here.

### 10.2 Operational

Time to process a conversation; time spent on notes and call preparation; share of imports processed successfully; customers managed per agent.

### 10.3 Business and pilot

Weekly active users, retention, processed conversations, free-to-paid conversion, acquisition cost, recurring revenue, lifetime value. Pilot questions: does it save time, prevent information loss, is the memory trusted, are briefings and drafts useful, would the user pay, which feature would be missed most.

## 11. Business model hypotheses

B2B SaaS subscription. The plans and prices below are pricing experiments only. They are not validated market prices.

| Plan | Scope | Hypothetical price |
|---|---|---|
| Individual | One user, limited processing, memory, assistant, drafts | $29 to $49 per month |
| Professional | Higher limits, advanced memory, CRM integration, briefings | $79 to $149 per month |
| Team | Multiple users, shared records, permissions, admin | $199 to $399 per month |

AI cost per processed conversation must be measured (`ai_runs.cost_usd`) before any price is finalized.

 ## 12. Assumptions and dependencies

| ID | Assumption or dependency | How it is handled |
|---|---|---|
| A1 | Agents will paste or upload conversations manually in the MVP | Validated in the pilot |
| A2 | A multilingual embedding model gives acceptable cross-language retrieval for EN, ES and PT | ADR-007; measured in Phase 6 |
| A3 | LLM providers return schema-valid structured output reliably enough with retries | Measured in Phase 5; fallbacks documented |
| A4 | The pilot agents hold the right to process their customers' conversations | Consent and terms; PRIVACY.md |
| A5 | The chosen hosting region is acceptable for each market. The Dubai pilot comes first, so UAE PDPL cross-border transfer rules must be assessed before a region is chosen | Reviewed in the compliance assessment; no hosting region is assumed in DATABASE.md or TAD.md |
| A6 | Official WhatsApp and Pipedrive APIs permit the planned use | Investigated in Phase 11 before any commitment |
| A7 | OpenAI API data controls and retention settings are acceptable for customer conversations | Reviewed before production, including Zero Data Retention eligibility (PROV-9, ADR-010) |

## 13. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Hallucinated or wrongly attributed facts | Strict schemas, mandatory evidence, agent verification, evaluation set |
| R2 | Cross-tenant data exposure | Composite FKs, Row-Level Security, repository filters, isolation tests |
| R3 | Wrong "current" value after requirements change | Versioned facts, conflict handling, explicit-change detection |
| R4 | Poor extraction quality in Spanish or Portuguese | Multilingual evaluation set from Phase 5 |
| R5 | Privacy and legal exposure (UAE PDPL, GDPR, provider transfers) | Per-jurisdiction assessment before each launch; data minimization |
| R6 | Provider outage, cost spikes or policy changes | Provider abstraction, retries, cost tracking |
| R7 | Prompt injection through imported messages | Untrusted-data handling, no tool execution from content, injection tests |
| R8 | Building features nobody needs | Pilot validation before expansion |
| R9 | Wrong customer matching | Manual confirmation for ambiguous identities |
| R10 | Platform policy limits on WhatsApp and CRM access | Official APIs only; MVP does not depend on them |

## 14. Market validation plan

Do not assume Dubai, Spain and Portugal agents share workflows. For each country, research and record separately: CRM usage, WhatsApp usage, email patterns, relationship management practices, manual note-taking, follow-up workflows, language needs, willingness to pay, competing products and integration requirements. Pilot target: 2 to 3 independent agents or small agency teams, starting in Dubai. No pilot customer is confirmed; a Dubai discovery discussion has taken place, which is not a pilot commitment. Spain and Portugal are validated separately before commercial expansion. Nothing in this document counts as market validation.

## 15. Acceptance criteria for a controlled pilot

REIA is ready for a pilot only when all of these hold:

1. Users can register and log in securely, and organizations have isolated data.
2. Agents can create and manage customers and import conversations; originals stay accessible.
3. AI extracts structured information with source references; memory persists across sessions.
4. Historical requirements are preserved; conflicts are identified; duplicate imports are handled.
5. Agents can ask customer-specific questions; answers are grounded in evidence; missing information is handled honestly.
6. Spanish and Portuguese conversations are processed correctly and answered in the agent's language.
7. Personalized drafts and call briefings can be generated, reviewed and edited; nothing is sent automatically.
8. Tasks and commitments can be managed.
9. Critical automated tests, tenant-isolation tests and security tests pass; AI evaluation results are documented.
10. Deployment and backup procedures are documented and tested; a jurisdiction-specific compliance assessment is complete for the pilot's market.

## 16. Decision log and open questions

### 16.1 Decisions (Architecture Decision Addendum and review)

| # | Decision | Status |
|---|---|---|
| 1 | Pilot market: Dubai (UAE) first; Spain and Portugal are secondary validation markets (ADR-012) | Confirmed |
| 2 | Pilot size: 2 to 3 agents or small teams; none confirmed yet | Confirmed as a target only |
| 3 | AI providers: OpenAI primary in production; DeepSeek restricted; five data classes; enforcement in code, deployment and organization settings (PROV-2 to PROV-7, ADR-010) | Confirmed |
| 4 | Arabic: no Arabic UI at launch; RTL-ready frontend; Arabic conversation processing evaluated later (ADR-013) | Confirmed |
| 5 | Embeddings: OpenAI `text-embedding-3-small`, 1536 dimensions, pgvector, cosine similarity (ADR-007) | Confirmed |
| 6 | Retention values, workspace lifecycle, deletion ledger and backup propagation in section 8.4 (ADR-011) | Proposed defaults and design; legal review required |
| 7 | Database roles `reia_migrator`, `reia_app`, `reia_maintenance`; no `DELETE` for the application role (ADR-014) | Proposed design |

### 16.2 Still open

1. Hosting region for each market, including the UAE PDPL cross-border transfer analysis for the Dubai pilot (A5).
2. Qualified privacy and legal review of retention defaults, lawful basis, subprocessors, processor agreements, consent and international transfers, per jurisdiction.
3. OpenAI endpoint data-retention settings and Zero Data Retention eligibility (A7, PROV-9).
4. Whether DeepSeek is ever enabled for real customer data (requires all conditions in PROV-5).
5. The conversation languages of the Dubai pilot agents (English only, or mixed with Arabic), and whether Arabic conversation processing must be evaluated sooner.
6. The dormant-workspace inactivity period and the export window length (section 8.4).
7. The separate append-only store for the deletion ledger and the restore runbook (defined in TAD.md and DEPLOYMENT.md, tested in Phase 12).

## 17. Glossary

- **Fact:** a structured statement about a customer, extracted or entered, with evidence and a lifecycle.
- **Supersede:** a newer fact replaces an older one as current while the older stays in history.
- **Conflict:** two statements that disagree without an explicit replacement.
- **Evidence quote:** the verbatim text in the original language that supports a fact.
- **Tenant:** one organization and its isolated data.
- **Hybrid retrieval:** combined structured, keyword and vector search.