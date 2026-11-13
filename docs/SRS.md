# SRS.md: Software Requirements Specification

Status: Draft v0.1 (Phase 0.3), pending review.
Depends on: PRD.md v0.3 and DATABASE.md v0.2 (after the 0.2b patch). If the patch is not applied yet, references to PRD PROV-x, PRD section 8.4 and DATABASE sections 5.6, 6.1 and 7.2 point to text that does not exist yet.
Related: TAD.md, API.md, SECURITY.md, PRIVACY.md, AI_ARCHITECTURE.md, MEMORY_ENGINE.md, TESTING.md.

## 1. Introduction

### 1.1 Purpose

This document turns the product requirements in PRD.md into verifiable software requirements. It defines what the system shall do, the rules it shall obey and how each requirement is verified. It does not define how the system is built (see TAD.md) or the endpoint shapes (see API.md).

### 1.2 Scope

REIA is a multi-tenant web application for real estate professionals, covering the MVP in PRD.md section 9. Items marked deferred (L) in the PRD are listed in section 4.17 only as design constraints.

### 1.3 Conventions

- Requirement IDs use the form `SR-<MODULE>-<number>`. They are different from the PRD IDs (for example `AUTH-1`), which are cited in the Trace column.
- "Shall" marks a mandatory requirement.
- Verification: **T** automated test, **I** inspection (code or configuration review), **D** demonstration, **A** analysis.
- Priority is MVP unless the requirement says Deferred.
- Enumerations (statuses, categories, channels) are defined in DATABASE.md and are not repeated here.

### 1.4 Working definitions

These are working definitions for engineering. Legal definitions are verified in the privacy and legal review (PRD section 16.2).

| Term | Meaning |
|---|---|
| Organization (tenant) | One customer workspace and its isolated data |
| Fact | A structured statement about a customer, with evidence and a lifecycle |
| Current fact | The fact that holds now for a fact key and slot |
| Superseded fact | A fact replaced by a newer one; kept as history |
| Disputed fact | A fact that conflicts with another and is not yet resolved |
| Evidence quote | Verbatim text from the source message that supports a fact |
| Slot | A position within a multi-valued fact key (for example several preferred locations) |
| Data class | The sensitivity label of an AI request: `public`, `synthetic`, `anonymized`, `pseudonymized` or `identifiable` |
| Restricted provider | An AI provider that may not receive identifiable customer data by default (currently DeepSeek) |
| Deletion ledger | Append-only record of verified deletion requests, used to prevent restored backups from resurrecting deleted data |

## 2. Overall description

### 2.1 Product perspective

A modular monolith: a Next.js frontend, a FastAPI backend organized in feature modules, PostgreSQL with pgvector, background workers inside the backend, external AI providers behind an abstraction, and n8n for selected later workflows. See TAD.md.

### 2.2 User classes

Owner, admin, agent and read-only member, plus the platform admin who operates the platform (PRD section 6.3).

### 2.3 Operating environment

Modern evergreen desktop and mobile browsers; backend in Docker containers; PostgreSQL with the `pgvector`, `citext`, `pg_trgm` and `unaccent` extensions. The hosting region is not decided (PRD A5).

### 2.4 Constraints

- PostgreSQL is the source of truth; embeddings are derived data.
- No autonomous customer messaging.
- OpenAI is the primary production provider; DeepSeek is restricted (PRD PROV).
- Retention values are proposed defaults, not legally verified requirements (PRD 8.4).

### 2.5 Assumptions

The assumptions A1 to A7 in PRD.md section 12 apply.

## 3. Role and permission matrix

"Assigned" means the customer is assigned to that member. Agents and read-only members only see customers assigned to them (see OPEN-S1).

| Action | Owner | Admin | Agent | Read-only |
|---|---|---|---|---|
| Terminate or delete the workspace, export the workspace | Yes | No | No | No |
| Configure AI provider settings and approvals | Yes | No | No | No |
| Change organization settings | Yes | Yes | No | No |
| Invite and remove members, change roles (admins cannot change owners) | Yes | Yes | No | No |
| View audit log | Yes | Yes | No | No |
| Create customers | Yes | Yes | Yes | No |
| View customers and their records | All | All | Assigned | Assigned |
| Edit customers, import conversations, add notes | All | All | Assigned | No |
| Verify, reject, correct facts and resolve conflicts | All | All | Assigned | No |
| Use assistant, drafts and briefings | All | All | Assigned | No |
| Create and manage tasks and commitments | All | All | Assigned | No |
| Merge customers, reassign customers | Yes | Yes | No | No |
| Export a customer, request customer erasure | Yes | Yes | No | No |
| Manage own voice profile and own account | Yes | Yes | Yes | Account only |

## 4. Functional requirements

### 4.1 System-wide rules (SYS)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-SYS-001 | Every tenant-owned record shall belong to exactly one organization. Reads and writes shall be restricted to the authenticated user's current organization in repositories, in composite foreign keys and in Row-Level Security | G7, R2 | T |
| SR-SYS-002 | When no organization context is set, data access shall return no rows and writes shall fail (fail closed) | G7 | T |
| SR-SYS-003 | Original conversation content shall be immutable after storage, enforced by database privileges and not only by application code | G2 | T |
| SR-SYS-004 | No AI-derived fact shall exist without a source conversation, a source message and an evidence quote | G3, INTEL-2 | T |
| SR-SYS-005 | Earlier values of a fact shall be preserved. A change shall create a new version and never overwrite an old one | G3, MEM-2 | T |
| SR-SYS-006 | The system shall contain no code path that sends a message to a customer. Drafts are copied or sent by the agent outside REIA | FOLLOW-6 | I, T |
| SR-SYS-007 | Imported content shall be treated as untrusted data. Instructions inside it shall never be followed, shall never invoke tools or change policy, and shall never alter prompts | INTEL-8, R7 | T |
| SR-SYS-008 | Timestamps shall be stored in UTC and shown in the user's or organization's timezone | I18N-7 | T |
| SR-SYS-009 | All API errors shall use one error envelope containing a code, a message, details and a request id | TAD | T |
| SR-SYS-010 | AI-originated information shall be distinguishable from agent-verified information in storage, API and UI | G3, MEM-9 | T, D |
| SR-SYS-011 | The original language of imported content shall be preserved. A translation shall be stored separately and shall never replace the original | I18N, CONV-4 | T |
| SR-SYS-012 | Lists shall be paginated and ordered deterministically | 8.2 | T |

### 4.2 Authentication and accounts (AUTH)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-AUTH-001 | A person shall be able to register with an email address and a password that meets the password policy in SECURITY.md | AUTH-1 | T |
| SR-AUTH-002 | Passwords shall be stored only as memory-hard hashes (Argon2id preferred) and shall never be logged or returned | AUTH-1 | T, I |
| SR-AUTH-003 | A user shall verify the email address before accessing any organization data. Verification tokens shall be single-use, expiring and stored as hashes | AUTH-2 | T |
| SR-AUTH-004 | Login shall return a short-lived access token and a rotating refresh token. Refresh tokens shall be stored as hashes in token families | AUTH-1 | T |
| SR-AUTH-005 | Reuse of an already rotated refresh token shall revoke its whole family and create an audit entry | AUTH-1 | T |
| SR-AUTH-006 | Logout shall revoke the refresh token family of the current session | AUTH-1 | T |
| SR-AUTH-007 | Password reset shall use a single-use expiring token, shall revoke all refresh tokens of the user and shall not reveal whether an email address is registered | AUTH-2 | T |
| SR-AUTH-008 | Login attempts shall be rate limited per account and per IP address. Failure messages shall be generic | AUTH-4 | T |
| SR-AUTH-009 | A user may belong to several organizations. Each request shall operate in exactly one organization chosen explicitly and validated against active membership | AUTH-3 | T |
| SR-AUTH-010 | A user shall be able to edit their name and UI language. Changing the email address shall require re-verification | AUTH-5 | T |
| SR-AUTH-011 | A user shall be able to request deletion of their account. A sole owner of a workspace with other members shall first transfer ownership or terminate the workspace | AUTH-6 | T |
| SR-AUTH-012 | A user shall be able to export their own account data in a machine-readable format | AUTH-6 | T |

### 4.3 Organizations and roles (ORG)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-ORG-001 | A user shall be able to create an organization with country, default locale, default currency and timezone. The creator shall become the owner | AUTH-3 | T |
| SR-ORG-002 | The roles owner, admin, agent and read-only shall have the permissions in section 3 and these shall be enforced on the server for every endpoint | AUTH-3 | T |
| SR-ORG-003 | Members shall be invited by email with a single-use expiring token | AUTH-3 | T |
| SR-ORG-004 | An organization shall always have at least one active owner | AUTH-3 | T |
| SR-ORG-005 | Role changes and member removal shall be audited. Removal shall immediately revoke that member's access to the organization | AUTH-3 | T |
| SR-ORG-006 | Organization settings shall be validated by a typed schema. Unknown keys shall be rejected | I18N-8 | T |
| SR-ORG-007 | The workspace lifecycle (`active`, `dormant`, `terminated`) shall follow PRD section 8.4. A dormant workspace shall never be deleted without owner notice | 8.4 | T |
| SR-ORG-008 | Platform admins shall have no routine access to customer content. Any access path that exists shall be audited (see OPEN-S7) | 6.3 | I |

### 4.4 Customer management and identity (CUST)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-CUST-001 | An agent shall be able to create, view, edit and archive customers. Only the full name is required. Archiving shall be a soft delete | CUST-1, CUST-2 | T |
| SR-CUST-002 | Customer type and status shall use the enumerations in DATABASE.md. A status change shall create a `status_changed` memory event | CUST-3, CUST-4 | T |
| SR-CUST-003 | Contact identifiers shall be stored as received and in normalized form: emails lowercased, phone numbers in E.164. A phone number without a country code shall use the organization's country as the default region | CUST-5 | T |
| SR-CUST-004 | An active identifier shall belong to one customer only. A collision shall return the possible duplicate to the agent. The system shall never merge customers automatically | CUST-5, CUST-6 | T |
| SR-CUST-005 | A manual merge shall preserve original identifiers, store a snapshot of the source customer, move all linked records to the target, mark the source as merged and be audited | CUST-6 | T |
| SR-CUST-006 | Customer search shall support name (accent-insensitive and tolerant of small typos), identifier, status, type and assigned agent | CUST-8 | T |
| SR-CUST-007 | Manual notes shall be stored as conversations (channel `call_note`, `meeting_note` or `other`) so that they use the same processing pipeline | CUST-7 | T |
| SR-CUST-008 | Assigning or reassigning a customer shall be audited | CUST-2 | T |
| SR-CUST-009 | Archived customers shall be excluded from default lists, search, retrieval and AI context, and shall be restorable | CUST-1 | T |
| SR-CUST-010 | Preferred language and country shall be validated as BCP 47 and ISO 3166-1 alpha-2 codes | I18N-2 | T |

### 4.5 Conversation management (CONV)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-CONV-001 | The system shall import conversations by pasted text, TXT file, CSV file and manual note | CONV-1 | T |
| SR-CONV-002 | Imports shall be validated: UTF-8 text, a configurable maximum size, file type detected from content, filenames never trusted and uploaded content never executed or rendered as markup | CONV-1 | T |
| SR-CONV-003 | A CSV import shall show a column mapping (sender, timestamp, message) for the user to confirm before processing | CONV-1 | D |
| SR-CONV-004 | The original content shall be stored exactly as received after decoding. A separately normalized form (Unicode NFC, unified line endings, trimmed trailing whitespace) shall be used only for hashing and comparison | CONV-2 | T |
| SR-CONV-005 | A duplicate import (same normalized content hash in the organization) shall return the existing conversation and create no new messages, facts, events or jobs | CONV-5 | T |
| SR-CONV-006 | Messages shall be parsed into sender, timestamp and text for the documented export formats. Content in any other format shall be stored as a single message with an unknown sender, and the import shall tell the user | CONV-3 | T |
| SR-CONV-007 | Language shall be detected per conversation and per message and stored. It shall be independent of the user's UI language and the customer's preferred language | CONV-4, I18N-12 | T |
| SR-CONV-008 | A conversation shall be linked to a customer on import or held as `pending_customer_match`. When identifiers match more than one customer or are ambiguous, the agent shall confirm the link | CONV-6, CUST-6 | T |
| SR-CONV-009 | The system shall show a customer's conversations in chronological order, filter by channel, show the original messages and show the processing status | CONV-7 | T, D |
| SR-CONV-010 | Reprocessing shall create a new summary version and shall not create duplicate facts or events | CONV-8 | T |
| SR-CONV-011 | A translation of a message shall be generated only on request, stored in `message_translations` and labelled as an AI translation | CONV-9 | T |
| SR-CONV-012 | A failed processing shall show a failure reason that contains no message content | CONV-3 | T |
| SR-CONV-013 | The API shall not delete conversations. Removal shall happen only through the erasure process in 4.14 | G2 | T, I |
| SR-CONV-014 | Keyword search over messages shall use a language-aware text search configuration chosen from the detected language | SRCH-1 | T |

### 4.6 AI conversation intelligence (INTEL)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-INTEL-001 | Conversation processing shall run as a background job with an idempotency key (conversation id and pipeline version), a maximum number of attempts and a recorded status | INTEL-9 | T |
| SR-INTEL-002 | Only conversations linked to a customer shall be processed | R9 | T |
| SR-INTEL-003 | Every AI call shall pass the provider-policy check in 4.13 before it leaves the backend | PROV-7 | T |
| SR-INTEL-004 | Model output shall be validated against strict typed schemas. Invalid output shall be retried once. If it is still invalid, the job shall fail and store nothing from it | INTEL-4 | T |
| SR-INTEL-005 | Extraction shall cover identity, property requirements, financial context, intent, preferences, objections, commitments, events, communication preferences and uncertainties | INTEL-1 | T |
| SR-INTEL-006 | Each extracted item shall carry a category, a fact key from the registry, a typed value, an evidence quote in the original language, the source message, a confidence value and a change signal (`explicit_replacement`, `addition`, `restatement` or `unclear`) | INTEL-2 | T |
| SR-INTEL-007 | The backend shall verify that every evidence quote appears in the source message text (after whitespace and Unicode normalization). A fact whose quote cannot be found shall be rejected and logged | SYS-004, R1 | T |
| SR-INTEL-008 | A fact key that is not in the registry shall be rejected and logged | INTEL-4 | T |
| SR-INTEL-009 | Financial facts shall be extracted only when explicitly stated. A money fact shall carry an explicitly stated ISO 4217 currency. An amount without a stated currency shall not be stored as a money fact (see OPEN-S3) | INTEL-3 | T |
| SR-INTEL-010 | AI-extracted facts shall be stored with origin `ai_extracted` and verification status `unverified` | MEM-9 | T |
| SR-INTEL-011 | AI-suggested commitments and tasks shall be stored with status `suggested` | TASK-2 | T |
| SR-INTEL-012 | Facts, memory events and the summary of one conversation shall be committed in one transaction. The conversation shall become `processed` only after that commit | INTEL-9 | T |
| SR-INTEL-013 | Embeddings shall be generated by a separate retryable job after the commit. Their failure shall not undo the facts | MEM-7 | T |
| SR-INTEL-014 | Summaries shall be written in the language of the user who started processing, or the organization's default language, and the language shall be stored | INTEL-6, I18N-2 | T |
| SR-INTEL-015 | Free-text values shall keep the customer's own wording. Canonical English shall be used only for fact keys and enumerated values | I18N | T |
| SR-INTEL-016 | Sentiment and engagement signals shall not be stored as customer facts. If shown in a summary they shall be labelled as an AI impression | INTEL-5 | T, I |
| SR-INTEL-017 | Prompts shall include only the data needed for the task (data minimization) | 8.1 | I |
| SR-INTEL-018 | Prompts shall instruct the model to treat conversation text as data. Output shall be accepted only through the typed schema, so no output can trigger an action | INTEL-8 | T |

### 4.7 Customer memory (MEM)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-MEM-001 | A fact-key registry in code shall define for each key the value type, the allowed units and whether it is single-valued or multi-valued | MEM-1 | I, T |
| SR-MEM-002 | When a new fact has the same key and slot as a current fact and the same value, no duplicate current fact shall be created (see OPEN-S2) | MEM-2 | T |
| SR-MEM-003 | When the value differs and the change signal is `explicit_replacement`, the old fact shall become `superseded` with `valid_to` set, the new fact shall become `current` and link to the old one, and a memory event shall be created | MEM-2, MEM-4 | T |
| SR-MEM-004 | When the value differs and the change signal is not `explicit_replacement`, both facts shall become `disputed` and an open conflict shall be created. The newest statement shall not be assumed to be a permanent change | MEM-3, MEM-4 | T |
| SR-MEM-005 | For multi-valued keys, an `addition` shall create a new slot and shall not replace existing values | MEM-1 | T |
| SR-MEM-006 | `valid_from` shall be the time of the source conversation, not the time of extraction. An older statement imported later shall be stored as historical and shall not replace a newer current fact | MEM-2 | T |
| SR-MEM-007 | At most one current fact shall exist per organization, customer, key and slot, enforced by the database | MEM-1 | T |
| SR-MEM-008 | An AI-extracted fact that contradicts a verified fact shall create a conflict. It shall never replace the verified fact | MEM-9 | T |
| SR-MEM-009 | An agent shall be able to verify, reject, correct and restore facts and resolve conflicts. A correction shall create a new manual verified fact that supersedes the old one. Each action shall be recorded in `fact_corrections` and the audit log | MEM-9 | T |
| SR-MEM-010 | Resolving a conflict as "both valid" shall require the agent to assign different slots so the one-current-fact rule still holds | MEM-3 | T |
| SR-MEM-011 | Restoring a rejected fact shall return it to `disputed` if a current fact exists in its slot, otherwise to `current` | MEM-9 | T |
| SR-MEM-012 | Rejected facts shall be excluded from retrieval, the assistant, briefings and drafts. Their embeddings shall be removed by a cleanup job | MEM-9 | T |
| SR-MEM-013 | Outdated facts shall be marked `superseded` or `expired` and shall never be deleted automatically | MEM-10 | T |
| SR-MEM-014 | Memory events shall be append-only | MEM-5 | T |
| SR-MEM-015 | Hybrid retrieval shall combine structured queries, language-aware keyword search and vector search, with customer, time and metadata filters | MEM-7 | T |
| SR-MEM-016 | Retrieval ranking shall consider customer identity, relevance, recency, verification status, source quality, temporal validity and query intent. Similarity alone shall not decide the ranking | MEM-8 | T, A |
| SR-MEM-017 | Retrieval shall never return records of another customer or organization, enforced by query filters and Row-Level Security | ASST-6 | T |
| SR-MEM-018 | Vector queries shall filter by the active embedding model and version and shall use the partial index (DATABASE.md 6.1) | MEM-7 | T |
| SR-MEM-019 | Cross-language retrieval shall work: a query in one launch language shall find evidence in another. Evidence shall be shown in its original language with an optional translation | MEM-11 | T |
| SR-MEM-020 | Every retrieved item shall include its type, id, date, language, lifecycle status and verification status | MEM-12, ASST-2 | T |
| SR-MEM-021 | After a customer merge, facts of both customers shall be reconciled through the same conflict rules | CUST-6 | T |
| SR-MEM-022 | Embeddings shall be treated as derived data that can be deleted and rebuilt at any time. PostgreSQL records remain the source of truth | MEM-12 | I, T |

### 4.8 Customer assistant (ASST)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-ASST-001 | Each assistant query shall be bound to one customer. The user's access to that customer shall be validated first | ASST-1 | T |
| SR-ASST-002 | The answer shall be generated only from retrieved context. Each claim shall reference at least one source (fact, message or event) | ASST-2 | T |
| SR-ASST-003 | The backend shall validate every reference: it must exist, belong to the same customer and organization and not be rejected. A claim with an invalid reference shall be removed from the answer | ASST-2 | T |
| SR-ASST-004 | If no supported claim remains, or retrieval finds nothing relevant, the assistant shall state that the information is not available and shall not invent an answer. This response may be produced without calling a model | ASST-3 | T |
| SR-ASST-005 | Answers shall separate current, historical, disputed and unverified information and shall show dates | ASST-2, ASST-4 | T, D |
| SR-ASST-006 | Answers shall list missing information and unresolved conflicts that are relevant to the question | ASST-4 | T |
| SR-ASST-007 | Answers shall be written in the requester's UI language. Evidence quotes shall stay in their original language | ASST-5 | T |
| SR-ASST-008 | Suggested next actions shall be labelled as suggestions and shall not be presented as facts | ASST-2 | D |
| SR-ASST-009 | A question about a different customer than the selected one shall be refused with an explanation, even if the text names another customer | ASST-6 | T |
| SR-ASST-010 | The assistant shall be rate limited and cost limited per organization. The limits shall be configurable | 8.2 | T |
| SR-ASST-011 | The MVP shall not store assistant questions and answers beyond `ai_runs` metadata (see OPEN-S4) | 8.1 | I |

### 4.9 Follow-up copilot (FOLLOW)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-FOLLOW-001 | The agent shall be able to generate a draft for the purposes and channels listed in PRD FOLLOW-1, using current facts, recent messages, pending commitments and the agent's voice profile | FOLLOW-1 | T |
| SR-FOLLOW-002 | The draft language shall be the customer's preferred language. If it is not set, the language of the customer's latest messages shall be used. If neither is known, the organization's default language shall be used and the draft shall be flagged | FOLLOW-2 | T |
| SR-FOLLOW-003 | A draft shall not state facts that are absent from the retrieved context. The references used shall be stored with the draft | FOLLOW-3 | T |
| SR-FOLLOW-004 | Drafts shall exclude rejected facts and shall flag disputed ones for the agent | FOLLOW-3 | T |
| SR-FOLLOW-005 | The generated text shall be preserved when the agent edits. The edit shall be stored separately | FOLLOW-5 | T |
| SR-FOLLOW-006 | Draft statuses shall follow section 6. Editing an approved draft shall return it to `edited` and shall require approval again | FOLLOW-5 | T |
| SR-FOLLOW-007 | Only the agent can mark a draft as `sent_manually`. The agent may record the sent message as an outbound conversation, which then goes through the normal pipeline | FOLLOW-5 | T |
| SR-FOLLOW-008 | The agent shall be able to create, edit, reset and delete their voice profile. Example messages shall be treated as `identifiable` data in provider checks | FOLLOW-4 | T |

### 4.10 Call briefing (BRIEF)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-BRIEF-001 | The agent shall be able to generate a briefing on demand with the ten sections in PRD BRIEF-1 | BRIEF-1 | T |
| SR-BRIEF-002 | Every briefing item shall reference its source. A section without evidence shall say that no information is recorded and shall not be filled with guesses | BRIEF-2 | T |
| SR-BRIEF-003 | A briefing shall be written in the requester's UI language | BRIEF-3 | T |
| SR-BRIEF-004 | A briefing shall be stored, shall keep earlier briefings and shall indicate when newer conversations exist since it was generated | BRIEF-1 | T |
| SR-BRIEF-005 | The warnings section shall include open conflicts, overdue commitments and unverified AI facts that affect the discussion | BRIEF-1 | T |

### 4.11 Tasks and commitments (TASK)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-TASK-001 | An agent shall be able to create, edit, assign and complete tasks with category, priority and due date | TASK-1 | T |
| SR-TASK-002 | AI-suggested tasks and commitments shall start as `suggested`. They shall become `open` only after an agent approves them and `cancelled` when dismissed. They shall never become confirmed automatically | TASK-2 | T |
| SR-TASK-003 | A task shall be overdue when its status is `open` or `in_progress` and its due time has passed | TASK-3 | T |
| SR-TASK-004 | The system shall provide pending and overdue views and filters by priority, assignee and customer | TASK-3 | T |
| SR-TASK-005 | Commitments shall record the responsible party (`agent` or `customer`), due time, status and source, and tasks may reference a commitment | MEM-6 | T |
| SR-TASK-006 | Because the application role has no `DELETE` privilege, removing a task shall set its status to `cancelled`. The API shall document this (see OPEN-S8) | 7.9 | T |

### 4.12 Timeline, search and dashboard (TIME, SRCH, DASH)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-TIME-001 | The customer timeline shall show conversations, notes, requirement changes, commitments, drafts, tasks and status changes in chronological order with cursor pagination | TIME-1 | T |
| SR-TIME-002 | The timeline shall be filterable by date, channel, activity type, agent and event category | TIME-2 | T |
| SR-SRCH-001 | Unified search shall cover customers, conversations, requirements, objections, tasks and commitments in exact, keyword, semantic and hybrid modes with date and customer filters | SRCH-1 | T |
| SR-SRCH-002 | Search shall respect organization and role permissions and shall show the type and source of each result | SRCH-2 | T |
| SR-SRCH-003 | Search query text sent to an embedding provider shall be classified `identifiable` and shall pass the provider-policy check | PROV-7 | T |
| SR-DASH-001 | The dashboard shall show recent customers and interactions, pending and overdue tasks and recent AI activity, calculated only from recorded data | DASH-1 | T |

### 4.13 AI provider governance (PROV)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-PROV-001 | The backend shall define a provider-independent interface with at least structured generation and embedding. Business logic shall not import a provider SDK directly | PROV-1 | I |
| SR-PROV-002 | The provider and model shall be selectable per task and per organization, with defaults from deployment configuration | PROV-1 | T |
| SR-PROV-003 | Every AI request shall carry a data class set by the calling service. The class shall not come from user input or from the model. Content originating from customers, contact details, requirements and transaction details shall default to `identifiable` | PROV-4 | T |
| SR-PROV-004 | `pseudonymized` data shall be treated as `identifiable` for policy decisions. Only a documented anonymization assessment and an approved anonymization component can produce `anonymized` data | PROV-4 | T, I |
| SR-PROV-005 | Restricted providers shall be denied by default for `pseudonymized` and `identifiable` data. A request shall be sent only when the code policy, the deployment configuration and the organization setting all allow it. The organization setting can only narrow what code and deployment allow | PROV-5, PROV-6 | T |
| SR-PROV-006 | In production, the application shall refuse to start if configuration enables a restricted provider for customer data without a recorded approval reference | PROV-6 | T |
| SR-PROV-007 | A blocked request shall make no outbound call, shall be recorded in `ai_runs` with status `blocked_by_policy` and shall not fall back to another provider unless that provider is also allowed for the data class | PROV-7 | T |
| SR-PROV-008 | Embedding requests shall follow the same policy checks as all other AI requests | PROV-7 | T |
| SR-PROV-009 | Logs shall record provider, model, endpoint, task, data class, status, tokens, cost and latency. Raw prompts and responses shall not be logged by default, and content logging shall be disabled in production | PROV-8 | T, I |
| SR-PROV-010 | Provider credentials shall be read from environment variables or a secret manager, kept server-side and never exposed to the frontend or logs | 8.1 | T, I |
| SR-PROV-011 | Provider calls shall have timeouts and bounded retries with backoff | 8.2 | T |
| SR-PROV-012 | Usage and cost shall be tracked per organization, with configurable limits | 11 | T |
| SR-PROV-013 | Before production, the data-retention behavior of every endpoint in use shall be reviewed and recorded, including Zero Data Retention eligibility for OpenAI | PROV-9 | I |
| SR-PROV-014 | The REIA application shall not use customer data to train models. Provider settings shall be chosen and verified so that providers do not train on customer data either (see PRIVACY.md) | 8.1 | I |

### 4.14 Privacy, retention and deletion (PRIV)

All retention values here are proposed defaults (PRD 8.4), not legally verified requirements.

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-PRIV-001 | The system shall export a customer, a user account and a workspace in a machine-readable format. A customer export shall include original conversations and facts with their sources | AUTH-6, 8.4 | T |
| SR-PRIV-002 | Customer identity fields shall be correctable, and facts shall be correctable through SR-MEM-009 | 8.4 | T |
| SR-PRIV-003 | A verified deletion request shall be written to the deletion ledger before any data is deleted | 8.4 | T |
| SR-PRIV-004 | Production data, including embeddings and other derived data, shall be erased within the proposed 30 days through the controlled erase functions, run by the maintenance role | 8.4 | T |
| SR-PRIV-005 | The deletion ledger shall be append-only, shall hold identifiers only and shall be exported to a store separate from the database backups | 8.4 | T, I |
| SR-PRIV-006 | After a restore, every ledger entry executed after the snapshot time shall be re-applied before users get access again. Restored data of a deleted subject shall never be visible | 8.4 | T |
| SR-PRIV-007 | Backups shall expire within the proposed 35 further days. Backups shall not be edited per customer | 8.4 | I |
| SR-PRIV-008 | Retention periods shall be configurable per organization within limits defined in PRIVACY.md | 8.4 | T |
| SR-PRIV-009 | A legal hold shall block deletion jobs for the held subject until released. Holds shall be documented, access-restricted and audited (see OPEN-S5) | 8.4 | T |
| SR-PRIV-010 | The system shall record consent and lawful-basis information per customer and purpose where applicable. The product shall not claim legal compliance | 14 | T, I |
| SR-PRIV-011 | Technical logs and audit metadata shall contain identifiers only. Message content and contact details shall never appear in them | 8.4 | T |
| SR-PRIV-012 | The data handled by each provider and subprocessor and the international transfers shall be documented in PRIVACY.md before the pilot | 8.4, 16.2 | I |

### 4.15 Audit (AUD)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-AUD-001 | The system shall write an audit entry for: login success and failure, refresh token reuse, password reset, role and membership changes, customer merge, customer reassignment, fact verify, reject, correct and restore, data export, deletion requests, legal hold changes, provider settings changes and integration connections | 8.1 | T |
| SR-AUD-002 | An audit entry shall contain the user, organization, action, resource type and id, IP address, time and request id. It shall contain no content | 8.1 | T |
| SR-AUD-003 | Audit entries shall be append-only. Only owners and admins can read them | 8.1 | T |
| SR-AUD-004 | Audit logs shall be kept for 12 months as a proposed default. Purging shall be done only by the maintenance role | 8.4 | T |

### 4.16 Internationalization (I18N)

| ID | Requirement | Trace | Verify |
|---|---|---|---|
| SR-I18N-001 | The UI shall support English, Spanish and Portuguese through locale resources, with English as the fallback | I18N-1 | T |
| SR-I18N-002 | UI language (per user), customer preferred language (per customer) and detected conversation language (per conversation and message) shall be independent | I18N-2, I18N-12 | T |
| SR-I18N-003 | Numbers, dates, times and currencies shall be formatted by locale and timezone | I18N-7 | T |
| SR-I18N-004 | Money shall be stored as an amount plus an ISO 4217 currency code, and area as a value plus the unit `sqm` or `sqft`. No implicit conversion shall change stored values | I18N-4, I18N-5 | T |
| SR-I18N-005 | Location shall be stored in structured form: country, region, city, neighborhood, building or development and postal code | I18N-6 | T |
| SR-I18N-006 | Country configuration shall come from YAML defaults and per-organization overrides. Adding a country shall need configuration and localization resources only, not changes to core logic | I18N-8, I18N-9 | T, I |
| SR-I18N-007 | The system shall use UTF-8 throughout, compare text in Unicode NFC and support accent-insensitive search for names | I18N-11 | T |
| SR-I18N-008 | The frontend shall use logical CSS properties and avoid hardcoded left or right assumptions so that right-to-left layouts can be added later. An Arabic UI is not part of the launch | I18N-10 | I |
| SR-I18N-009 | Spanish and Portuguese conversations shall be processed with the same quality gates as English, and original content shall be preserved | I18N-1 | T |

### 4.17 Deferred integrations (INTG, constraints only)

| ID | Requirement | Trace | Priority |
|---|---|---|---|
| SR-INTG-001 | Integrations shall use OAuth with least-privilege scopes, shall store credentials encrypted and shall write sync logs | INTG-1 to INTG-3 | Deferred |
| SR-INTG-002 | An integration shall never overwrite CRM data without defined rules, field mapping and a user-chosen sync direction | INTG-5 | Deferred |
| SR-INTG-003 | WhatsApp access shall use only officially supported platform capabilities. No scraping or personal-account access shall be built | INTG-2 | Deferred |
| SR-INTG-004 | n8n workflows shall call the public API with a scoped service credential. Core business logic shall stay in the backend | INTG-4 | Deferred |

## 5. External interfaces

| Interface | Notes |
|---|---|
| REST API | `/api/v1`, JSON, JWT bearer authentication. Defined in API.md |
| AI providers | Through the provider interface. OpenAI primary, DeepSeek restricted. Calls are subject to SR-PROV |
| Email delivery | Needed for verification, reset and invitation messages. The sending service is a configuration choice made in TAD.md |
| PostgreSQL | Application role, migration role and maintenance role (DATABASE.md 4.1) |
| Deletion ledger store | An append-only store separate from database backups (TAD.md, DEPLOYMENT.md) |
| Deferred | Pipedrive, WhatsApp Business Platform, Gmail, Outlook, calendars, n8n |

## 6. State models

### 6.1 Conversation processing

| From | Event | To |
|---|---|---|
| (new) | Imported without a confirmed customer | `pending_customer_match` |
| (new) or `pending_customer_match` | Linked to a customer | `pending` |
| `pending` | Job started | `processing` |
| `processing` | Commit succeeded | `processed` |
| `processing` | Attempts exhausted or unrecoverable error | `failed` |
| `failed` or `processed` | Retry or reprocess requested | `pending` |

### 6.2 Fact lifecycle

| From | Event | To |
|---|---|---|
| (new) | Extracted or entered, no existing current fact in the slot | `current` |
| `current` | Explicit replacement, correction or newer fact | `superseded` |
| (new) | Older statement imported after a newer current fact | `superseded` |
| `current` and new fact | Conflict without explicit replacement | both `disputed` |
| `disputed` | Conflict resolved | `current` or `superseded` |
| `current` or `disputed` | Agent rejects | `rejected` |
| `rejected` | Agent restores | `disputed` or `current` (SR-MEM-011) |
| `current` | Agent or rule marks outdated | `expired` |

### 6.3 Draft, task, commitment, job and workspace

| Entity | Transitions |
|---|---|
| Draft | `draft` to `edited` to `approved` to `sent_manually`. `approved` back to `edited` on edit. `draft`, `edited` or `approved` to `discarded` |
| Task | `suggested` to `open` (approve) or `cancelled` (dismiss). `open` to `in_progress` to `done`. `open` or `in_progress` to `cancelled`. `done` to `open` (reopen) |
| Commitment | `suggested` to `open` or `cancelled`. `open` to `fulfilled` or `cancelled` |
| Processing job | `queued` to `running` to `succeeded` or `failed`. `failed` to `queued` while attempts remain, otherwise `dead` |
| Workspace | `active` to `dormant` and back to `active` on activity. `active` or `dormant` to `terminated`, then the deletion process |

## 7. Data requirements

The data model is defined in DATABASE.md. The following rules are repeated here because they are requirements.

- Money is `numeric(18,2)` with a separate ISO 4217 code, never a float.
- Facts, memory events, fact corrections, audit logs, messages and translations are append-only or immutable for the application role.
- Every child table references its parent with a composite key that includes `organization_id`.
- Embeddings store provider, model, model version label and dimension, and the dimension is fixed at 1536 (ADR-007).

## 8. Non-functional requirements

| ID | Requirement | Verify |
|---|---|---|
| SR-NFR-001 | The dashboard API shall respond in under 500 ms at p95 and customer search in under 1 s at p95, under the MVP test load defined in TESTING.md. These are targets, not guarantees | T |
| SR-NFR-002 | AI latency shall be measured and reported separately from API latency | T |
| SR-NFR-003 | All list endpoints shall be paginated | T |
| SR-NFR-004 | Background jobs shall be idempotent and retryable. Failures shall not leave partial facts | T |
| SR-NFR-005 | Backup and restore shall be tested before the pilot, including the deletion-ledger re-apply step | T, D |
| SR-NFR-006 | Logs shall be structured and contain a request id and organization id, and never message content | T |
| SR-NFR-007 | All traffic shall use TLS. The frontend shall send security headers and the backend shall use a strict CORS allowlist | I, T |
| SR-NFR-008 | Secrets shall never be committed. Configuration shall come from environment variables. A secret-scanning check shall run in CI | I, T |
| SR-NFR-009 | Dependencies shall be kept minimal and scanned for known vulnerabilities in CI | I |
| SR-NFR-010 | The code shall use type hints. Migrations, linting, type checks and tests shall run in CI | I |
| SR-NFR-011 | The UI shall target WCAG 2.2 level AA, be responsive and provide loading, error and empty states and confirmation for sensitive actions | I, D |
| SR-NFR-012 | AI features shall be testable offline with a deterministic fake provider and a fixed evaluation dataset in English, Spanish and Portuguese | T |
| SR-NFR-013 | Availability targets and capacity limits for the pilot shall be defined before the pilot. They are not set in this version | A |

## 9. Critical acceptance tests

| ID | Scenario | Expected result | Requirements |
|---|---|---|---|
| CT-01 | Budget AED 1.5M, later conversation says it is now AED 1.8M | New current budget 1.8M. 1.5M is superseded and preserved with date and source. A `budget_changed` event exists | SR-MEM-003 |
| CT-02 | Two conversations give different requirements, no explicit change | Both facts disputed, open conflict, agent asked | SR-MEM-004 |
| CT-03 | Agent asks about something never mentioned | The assistant says it is not available | SR-ASST-004 |
| CT-04 | Question about customer A | No data of customer B or another organization appears | SR-MEM-017, SR-ASST-009 |
| CT-05 | Draft for a customer | Uses the real history, not a template; references stored | SR-FOLLOW-003 |
| CT-06 | Any factual claim in an answer | Traceable to a valid source | SR-ASST-002, SR-ASST-003 |
| CT-07 | Same conversation imported twice | No new messages, facts, events or jobs | SR-CONV-005 |
| CT-08 | Agent corrects a wrong fact | Correction recorded, original source still available | SR-MEM-009 |
| CT-09 | Request without organization context, or for another tenant's id | No rows, or not found. Direct database access without the setting returns nothing | SR-SYS-001, SR-SYS-002 |
| CT-10 | Restricted provider asked to process `identifiable` data, including an embedding request | Blocked, no outbound call, `blocked_by_policy` recorded | SR-PROV-005, SR-PROV-007, SR-PROV-008 |
| CT-11 | `pseudonymized` data sent to a restricted provider | Treated as `identifiable` and blocked | SR-PROV-004 |
| CT-12 | Spanish and Portuguese conversations | Facts extracted, original preserved, answers in the agent's UI language | SR-I18N-009, SR-ASST-007 |
| CT-13 | English question, Spanish evidence | Evidence found and shown in Spanish with optional translation | SR-MEM-019 |
| CT-14 | Imported message contains instructions to the AI | Instructions ignored, no action triggered | SR-SYS-007, SR-INTEL-018 |
| CT-15 | Model returns a fact whose evidence quote is not in the message | Fact rejected and logged | SR-INTEL-007 |
| CT-16 | UPDATE of `original_content` through the application role | Denied by the database | SR-SYS-003 |
| CT-17 | Deletion request followed by a backup restore | Ledger entries re-applied, deleted subject not visible | SR-PRIV-006 |
| CT-18 | Older conversation imported after a newer one | Older fact stored as historical, newer fact stays current | SR-MEM-006 |
| CT-19 | AI fact conflicts with a verified fact | Conflict created, verified fact unchanged | SR-MEM-008 |
| CT-20 | Refresh token reused after rotation | Family revoked and audit entry created | SR-AUTH-005 |

## 10. Traceability summary

| PRD module | SRS modules |
|---|---|
| AUTH (7.1) | SR-AUTH, SR-ORG |
| CUST (7.2) | SR-CUST |
| CONV (7.3) | SR-CONV |
| INTEL (7.4) | SR-INTEL |
| MEM (7.5) | SR-MEM |
| ASST (7.6) | SR-ASST |
| FOLLOW (7.7) | SR-FOLLOW |
| BRIEF (7.8) | SR-BRIEF |
| TASK (7.9) | SR-TASK |
| TIME, SRCH (7.10), DASH (7.11) | SR-TIME, SR-SRCH, SR-DASH |
| INTG (7.12) | SR-INTG (deferred) |
| I18N (7.13) | SR-I18N |
| PROV (7.14) | SR-PROV |
| Retention and subject rights (8.4), security and privacy (8.1) | SR-PRIV, SR-AUD, SR-SYS |
| Reliability and performance (8.2), UX (8.3) | SR-NFR |

## 11. Open items

| ID | Item | Where it will be resolved |
|---|---|---|
| OPEN-S1 | Confirm the visibility rule: agents and read-only members see only assigned customers; owners and admins see all | Before Phase 2 (authorization) |
| OPEN-S2 | A restated fact has nowhere to record the additional conversation. Decide on a `fact_evidence` table for corroborating mentions | Phase 6, DATABASE.md revision |
| OPEN-S3 | Representation of uncertainties, such as an amount without a currency (for example an `extraction_uncertainties` table) | Phase 5, DATABASE.md revision |
| OPEN-S4 | Whether to persist assistant questions and answers, and the privacy impact | Phase 7 |
| OPEN-S5 | A `legal_holds` table is needed for SR-PRIV-009 and is not in DATABASE.md yet | DATABASE.md revision before Phase 2 |
| OPEN-S6 | Whether a customer merge can be undone. The snapshot is kept, but unmerge is not defined | Phase 3 |
| OPEN-S7 | Audited access path for platform admins | SECURITY.md |
| OPEN-S8 | API semantics for `DELETE /tasks` (cancel) and `DELETE /customers` (archive), because the application role has no `DELETE` | API.md |
| OPEN-S9 | Concrete limits: import size, page sizes, rate limits, token lifetimes | TAD.md and SECURITY.md |