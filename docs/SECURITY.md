# SECURITY.md: REIA Security Architecture and Controls

Status: Draft v0.1 (Phase 0.6), pending review.
Depends on: PRD.md v0.3, SRS.md v0.1, DATABASE.md v0.2, TAD.md v0.2, API.md v0.1.
Related: PRIVACY.md, TESTING.md, DEPLOYMENT.md, AI_ARCHITECTURE.md.

## 1. Purpose, scope and status of statements

This document defines the threats REIA must withstand and the controls that counter them. It covers the web application, the API, the database, background processing, the AI layer, the build and deployment pipeline, and operations.

Statements are marked as follows:
- **Required**: a control the system must implement. It traces to SRS requirements.
- **Proposed**: a design choice awaiting approval.
- **Open**: not decided.

**Security controls are not a compliance claim.** Nothing in this document states that REIA complies with UAE PDPL, GDPR or any other law. Legal obligations are assessed in the jurisdiction-specific review (PRIVACY.md). Where a control exists mainly because a law might require it, the mapping is in section 14 and is marked for legal verification.

## 2. Security objectives

| Objective | Meaning for REIA |
|---|---|
| Confidentiality | Customer conversations and facts are visible only to authorized members of the owning organization, and are sent to AI providers only as the provider policy allows |
| Integrity | Original conversations are never altered. Facts are traceable to evidence. Corrections and history are tamper-evident |
| Availability | The service stays usable under load and abuse. Provider outages degrade AI features only |
| Accountability | Security-relevant actions are attributable and auditable |
| Privacy | Personal data is minimized, deletable and not resurrected by restores |
| Safety of AI output | AI output cannot trigger actions, cannot leak data across tenants and cannot present unsupported claims as facts |

## 3. Assets and sensitivity levels

These sensitivity levels are internal handling rules. They are different from the AI data classes (`public`, `synthetic`, `anonymized`, `pseudonymized`, `identifiable`) in ADR-010.

| Level | Contents | Handling |
|---|---|---|
| S4 Restricted | Conversations, messages, translations, facts, evidence quotes, summaries, memory events, embeddings, customer identifiers, drafts, briefings, voice-profile examples, export archives, integration credentials, signing and encryption keys, password hashes, token hashes | Tenant isolation, encrypted in transit and at rest, never in logs, never in URLs, never sent to a restricted provider, erased through the erasure process |
| S3 Confidential | Organization and member data, audit logs, `ai_runs` metadata, task data without personal content, configuration | Access by role, minimal logging, retention per PRD 8.4 |
| S2 Internal | Application logs without personal data, metrics, documentation | Internal access only |
| S1 Public | Marketing pages, public API documentation (if published) | No restriction |

## 4. Trust boundaries and actors

### 4.1 Trust boundaries

1. Browser and the internet: untrusted.
2. Proxy, frontend and API: the application perimeter.
3. API and database: separate credentials per role.
4. Backend and AI providers: an external boundary. Data crossing it is governed by the provider policy.
5. Backend and email, ledger store and hosting services: external subprocessors.
6. Imported content (conversations, files): untrusted input at every stage, including after storage.

### 4.2 Actors considered

| Actor | Example |
|---|---|
| Anonymous attacker | Credential stuffing, scanning, abuse |
| Malicious member of one organization | Tries to read another organization's data or exceed role |
| Compromised account | Stolen password or token |
| Malicious customer or third party | Writes a chat message that attacks the AI or the UI |
| Malicious or compromised provider or subprocessor | Misuse of data sent to it |
| Insider (developer, operator, platform admin) | Excess access to customer content, secret leakage |
| Supply-chain attacker | Malicious dependency or image |

## 5. Threat model

The table lists the main threats by component. Test IDs refer to section 13.

### 5.1 Identity and access

| ID | Threat | Controls | Test |
|---|---|---|---|
| TH-01 | Credential stuffing and brute force | Login throttling per account and per IP with growing delay (no hard account lock, so lockout cannot be used for denial of service), generic errors, Argon2id, common-password rejection, MFA decision (OPEN-SEC1) | ST-04 |
| TH-02 | Account enumeration (login, register, reset) | Identical responses and timing. A dummy hash verification runs when the account does not exist | ST-04 |
| TH-03 | Access token theft | Short lifetime (proposed 15 minutes), kept in memory, strict CSP against XSS, `no-store` caching | ST-05 |
| TH-04 | Refresh token theft or replay | `HttpOnly`, `Secure`, `SameSite=Strict` cookie scoped to the auth path, rotation, reuse detection revokes the family | ST-06 |
| TH-05 | CSRF on cookie endpoints | `SameSite=Strict`, `Origin` check, required custom header. All other endpoints use bearer tokens | ST-07 |
| TH-06 | JWT forgery or algorithm confusion | Pinned algorithm, `none` rejected, key id, `exp`, `iat`, `iss`, `aud` validated, keys from the secret store | ST-05 |
| TH-07 | Privilege escalation through role manipulation | Roles loaded from the database on every request, admins cannot change owners, the last owner cannot be removed, role changes audited | ST-03 |
| TH-08 | Stale access after removal | Membership checked on every request, removal effective immediately, refresh tokens of the member revoked for that organization | ST-03 |

### 5.2 Tenant isolation and authorization

| ID | Threat | Controls | Test |
|---|---|---|---|
| TH-10 | Cross-tenant read or write (IDOR, broken object authorization) | Repository filters, composite foreign keys, Row-Level Security with fail-closed default, 404 for foreign and invisible resources, UUIDs are not treated as secrets | ST-01, ST-02 |
| TH-11 | Missing authorization on a new route | Every route declares a permission code. A test fails the build when one does not | ST-03 |
| TH-12 | Mass assignment | Strict per-operation request schemas, unknown fields rejected, ORM models never bound directly to input | ST-09 |
| TH-13 | Agent reads customers assigned to others | Visibility rule in the service layer and in list queries | ST-03 |
| TH-14 | RLS bypass through a privileged connection | Separate roles, `NOSUPERUSER NOBYPASSRLS`, tests run as `reia_app`, startup role check | ST-02 |
| TH-15 | Race creating inconsistent facts | Customer advisory lock, partial unique index, idempotent jobs | ST-14 |
| TH-16 | Abuse of `SECURITY DEFINER` functions (`erase_*`, `claim_next_job`) | Fixed `search_path`, `EXECUTE` revoked from `PUBLIC`, granted to named roles only, tenant check inside, tests | ST-02 |

### 5.3 Input handling and web threats

| ID | Threat | Controls | Test |
|---|---|---|---|
| TH-20 | SQL injection | Parameterized queries through the ORM. Raw SQL only in repositories and migrations with bound parameters. A lint rule blocks string-built SQL | ST-08 |
| TH-21 | Stored XSS through imported messages or AI output | All content rendered as text, never as HTML. No raw HTML rendering of messages, drafts or AI text. Strict CSP | ST-10 |
| TH-22 | Malicious file upload | Only text and CSV, size cap enforced while streaming, binary detection, no archives, UTF-8 required, file never stored or executed, filename never trusted | ST-11 |
| TH-23 | Parser resource exhaustion (huge lines, many columns, deeply repeated patterns) | Limits on line length, field count and message count, parse timeouts, no backtracking-heavy regular expressions on user input | ST-11 |
| TH-24 | CSV or formula injection in exports | Exports are JSON. If CSV is ever added, cells starting with `=`, `+`, `-` or `@` are neutralized | ST-11 |
| TH-25 | SSRF | The backend never fetches user-supplied URLs. Outbound traffic goes only to configured provider, email and ledger endpoints. Production egress is restricted to that allowlist | ST-12 |
| TH-26 | Open redirect and header injection | No user-controlled redirects. Headers are built from validated values | ST-08 |
| TH-27 | Clickjacking | `frame-ancestors 'none'` and `X-Frame-Options: DENY` | ST-07 |

### 5.4 AI-specific threats

| ID | Threat | Controls | Test |
|---|---|---|---|
| TH-30 | Direct or indirect prompt injection in imported conversations | Content delimited as data, system instructions state it is data, the model has no tools, output accepted only through strict schemas, evidence verified, references validated | ST-15 |
| TH-31 | Poisoned memory (a message plants a false fact) | Facts are `unverified` until an agent verifies them, evidence is always shown, an AI fact never replaces a verified fact, agents can reject and restore | ST-15, ST-16 |
| TH-32 | Data exfiltration through AI output (for example markdown image or link beacons) | AI text is rendered as plain text, remote resources are never auto-loaded, links in AI output are not made clickable without agent action | ST-10, ST-15 |
| TH-33 | Cross-tenant or cross-customer leakage through retrieval | Retrieval filters by organization and customer, vector queries filter by model and version, the assistant refuses other-customer questions, references validated | ST-01, ST-16 |
| TH-34 | Identifiable data sent to a restricted provider | Provider policy in code, deployment (restricted credentials not provisioned) and organization settings, `pseudonymized` treated as `identifiable`, embedding calls included, startup refusal on contradiction | ST-13 |
| TH-35 | Sensitive prompts and responses in logs | Prompt and response content not logged, content logging disabled in production, `ai_runs` holds an input hash only | ST-17 |
| TH-36 | Cost abuse and denial of wallet | Per-user and per-organization quotas, token limits, provider timeouts, interactive rate limits | ST-18 |
| TH-37 | Excessive agency | No tools, no autonomous actions, no send path to customers | ST-15 |
| TH-38 | Embedding data treated as harmless | Embeddings are classified S4, deleted with the subject, never exported to other systems | ST-13 |

### 5.5 Data lifecycle and operations

| ID | Threat | Controls | Test |
|---|---|---|---|
| TH-40 | Deleted data resurrected by a restore | Deletion ledger, separate write-once store, mandatory re-apply and verification before reopening | ST-19 |
| TH-41 | Secrets committed or leaked | Secret scanning in CI and pre-commit, secrets only in environment or secret manager, rotation procedure | ST-17 |
| TH-42 | Personal data in logs, errors or URLs | Log scrubbing, generic error bodies, no query-string logging, no personal data in URLs | ST-17 |
| TH-43 | Insider or platform admin reads customer content | No standing access, time-boxed break-glass with approval and audit (ADR-022), developers have no production database access | ST-20 |
| TH-44 | Supply-chain compromise | Pinned lock files, dependency audit, minimal dependencies, review, image scanning, restricted CI tokens | ST-21 |
| TH-45 | Backup theft | Encrypted backups, restricted access, separate credentials, expiry within the proposed 35 days | ST-19 |
| TH-46 | Audit log tampering | Append-only for the application role, retention purge only by the maintenance role, alerts on gaps | ST-02 |
| TH-47 | Denial of service | Proxy and application rate limits, payload and time limits, background processing isolated from the API, pagination | ST-18 |
| TH-48 | Export archive leakage | Encrypted at rest, short expiry, creator-only download, download audited, deleted by maintenance | ST-22 |
| TH-49 | Job queue poisoning or runaway jobs | Idempotency keys, maximum attempts, leases, dead-job state, alerts | ST-14 |

## 6. Controls by domain

### 6.1 Authentication (Required, SR-AUTH-001 to 012)

**Passwords (Proposed policy):**
- Length 12 to 128 characters, all Unicode characters allowed, no composition rules, no forced periodic change.
- Rejected when found in a list of common or breached passwords. The MVP uses a local list. A breach-lookup service would receive password hash prefixes and needs a privacy review first (OPEN-SEC5).
- Argon2id with parameters at least the current OWASP minimum recommendation at implementation time (verify the figures then), tuned so that one verification takes a documented target time on the production hardware. Parameters are stored with the hash so they can be raised later.
- Passwords are never logged, returned or emailed.

**Throttling:** failed logins are counted per account and per IP. The delay grows with the count (proposed start: 5 failures in 15 minutes). The account is not locked, so an attacker cannot lock a user out.

**Timing:** when the account does not exist, a dummy Argon2 verification runs so response times match. Comparisons of tokens and hashes are constant time.

**Tokens:** as in TAD section 7 and API section 2.2. The refresh cookie is named with the `__Secure-` prefix. (The stricter `__Host-` prefix needs path `/`, which conflicts with the restricted path.) Access tokens are validated for algorithm, signature, `exp`, `iat`, `iss`, `aud` and key id.

**Email flows:** verification, reset and invitation tokens are 256-bit random values, stored as hashes, single-use and expiring. Reset revokes all sessions and notifies the user by email. Changing the email address requires the password and verification of the new address.

**Multi-factor authentication (Open, OPEN-SEC1):** the URD does not require it. Recommendation: TOTP for owners and admins before any pilot with real customer data. Needs a decision.

### 6.2 Authorization (Required, SR-ORG-002, SR-SYS-001)

- Deny by default. Permission checks live in the service layer using `core/permissions.py`.
- Object-level checks on every read and write: organization, then customer visibility, then action.
- Foreign or invisible resources return 404.
- Role changes, member removal, assignment and merges are audited.
- A test enumerates all routes and fails if one lacks a declared permission.

### 6.3 Tenant isolation (Required, SR-SYS-001, SR-SYS-002)

As specified in DATABASE.md section 4 and TAD section 8: composite foreign keys, Row-Level Security with `FORCE`, transaction-local `app.current_org_id`, separate roles, tests run as the application role, a startup check that the role is neither superuser nor `BYPASSRLS`. The tenant setting is applied by one helper only. Raw database sessions are not available to modules.

**Platform administration (Proposed, ADR-022):**
- No role grants standing access to customer content. `users.platform_role = 'platform_admin'` gives access to operational endpoints only (organization lifecycle, health, billing metadata), never to S4 data.
- Access to customer content for support or incident response is **break-glass**: it needs the organization owner's documented approval, or a documented security incident approved by two people. It uses time-limited credentials (proposed maximum 4 hours) through the maintenance role with a tenant context. Every query session is recorded in `audit_logs` with the approver and the reason, and the owner is notified afterwards.
- Developers have no access to production data. Debugging uses synthetic or anonymized data.

### 6.4 Input validation and output encoding (Required)

- Every request is validated by strict Pydantic schemas: types, lengths, ranges, enumerations. Unknown fields are rejected.
- Text input is normalized to Unicode NFC for comparison. Control characters other than line breaks and tabs are rejected in names and identifiers. Maximum lengths apply to every string.
- Identifiers use parsers: phone numbers through `phonenumbers`, emails through a validated email type.
- Output: the frontend renders imported and AI text as text. It never uses raw HTML insertion for such content.
- Errors never echo sensitive input values.

### 6.5 File and import handling (Required, SR-CONV-002)

- Accepted: pasted text, `.txt`, `.csv`. Everything else returns 415.
- The size limit is enforced while streaming (proposed 5 MB), before the content is held in memory.
- The content must be valid UTF-8 text without NUL bytes. A byte-order mark is stripped.
- The file type is decided from the content, never from the name or declared type alone.
- Archives, spreadsheets and documents are not accepted in the MVP.
- Uploaded files are not stored. Only the decoded text is stored.
- CSV parsing limits: maximum columns, maximum cell length and maximum rows, with a parse time limit.

### 6.6 Web application security (Required)

| Control | Value |
|---|---|
| TLS | TLS 1.2 minimum, 1.3 preferred, modern cipher suites, certificate renewal automated |
| HSTS | `Strict-Transport-Security: max-age=31536000; includeSubDomains` (preload only after review) |
| Content Security Policy | Strict, with per-response nonces (example below) |
| Other headers | `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` with unused features disabled, `X-Frame-Options: DENY`, `Cache-Control: no-store` on authenticated responses |
| CORS | Same-origin deployment. The API allows only configured origins, never `*`, and credentials only for the exact frontend origin |
| Cookies | `HttpOnly`, `Secure`, `SameSite=Strict`, minimal path, `__Secure-` prefix |
| URLs | No personal data, tokens or secrets in URLs or query strings |
| API docs | Swagger UI and OpenAPI browser disabled in production |

Example policy (nonce supplied per response by the frontend middleware):

```text
default-src 'self';
script-src 'self' 'nonce-<random>';
style-src 'self' 'nonce-<random>';
img-src 'self' data:;
font-src 'self';
connect-src 'self';
object-src 'none';
base-uri 'self';
form-action 'self';
frame-ancestors 'none';
upgrade-insecure-requests
```

The final policy is verified against the real build, because framework requirements can force changes. Any relaxation needs an entry in the decision log.

### 6.7 Secrets and key management (Required, SR-PROV-010, SR-NFR-008)

- Secrets exist only in environment variables injected at runtime or in the platform secret manager. They are never in the repository, images, logs, error messages or the frontend bundle.
- One set of secrets per environment. Production secrets are not available to CI or staging.
- Keys are versioned with key ids: JWT signing keys and credential encryption keys can be rotated without downtime (new key signs or encrypts, old keys verify or decrypt until retired).
- Integration credentials and export archives use authenticated encryption (AES-256-GCM or equivalent) with a key id.
- Rotation: scheduled (proposed at least yearly) and immediate on suspicion. A key compromise runbook (section 11) lists every secret and how to rotate it.
- `.env` is git-ignored. `.env.example` has names only. A secret scanner runs in pre-commit and CI.
- Restricted provider credentials (DeepSeek) are not provisioned in production unless approved under PROV-5.

### 6.8 Data protection (Required)

- In transit: TLS everywhere, including database connections and calls to providers and subprocessors.
- At rest: storage encryption provided by the hosting platform for database volumes and backups (to be confirmed with the hosting choice, OPEN-T1), plus application-level encryption for integration credentials and export archives.
- Field-level encryption of conversation text is not part of the MVP. It would conflict with keyword search and retrieval. The risk is accepted for the MVP and noted in section 12.
- Backups are encrypted, access is restricted and separate, and they expire within the proposed 35 days.
- Data minimization: prompts include only what the task needs (TAD 10.4). Contact details are not sent to providers unless a task requires them.
- Personal data never appears in logs, metrics, traces, error bodies or URLs.

### 6.9 AI security (Required, SR-INTEL-018, SR-PROV)

1. **Provider policy:** three independent enforcement points (code, deployment, organization settings). Restricted providers are denied by default for `pseudonymized` and `identifiable` data. Embedding requests follow the same policy. Blocked calls make no outbound request and are recorded.
2. **Data classes** are assigned by the calling service and never by user input or model output.
3. **Prompt injection:** customer text is placed in a delimited data section. The system prompt says it is data and not instructions. The model has no tools and cannot trigger actions. Output is accepted only through strict schemas.
4. **Verification:** every evidence quote must appear in the source message. Every claim in an answer needs a valid reference. Facts without verifiable evidence are rejected.
5. **Output handling:** AI text is rendered as text. No automatic loading of remote content. Drafts are text the agent copies.
6. **Memory trust:** AI facts are unverified until an agent verifies them. A conflicting AI fact never replaces a verified fact.
7. **Provider terms:** before production, each provider endpoint's data retention, training use, subprocessors and region are reviewed and recorded (SR-PROV-013). OpenAI Zero Data Retention eligibility is checked per endpoint.
8. **No training:** REIA does not use customer data to train models, and provider settings are chosen so that providers do not either (SR-PROV-014).
9. **Logging:** `ai_runs` records provider, model, endpoint, data class, tokens, cost, latency and status. It does not record prompt or response content.
10. **Evaluation:** a prompt-injection and leakage suite runs in CI against the FakeProvider and against real providers on synthetic data.

### 6.10 Logging, audit and monitoring (Required, SR-AUD, SR-PRIV-011)

**Application logs:** structured JSON with request id, organization id, user id, route, status, latency. A scrubbing filter removes fields that look like content, body, message, email or phone. Query strings are not logged by the application or the proxy.

**Audit log:** append-only for the application role. Events listed in SR-AUD-001, plus: break-glass sessions, provider setting changes, export downloads, legal hold changes, failed authorization on object access (counted, not detailed). Entries hold identifiers, never content. Retention 12 months (proposed).

**Alerts (proposed):**

| Signal | Why |
|---|---|
| Spike in failed logins or reset requests | Credential attacks |
| Refresh token reuse | Token theft |
| Repeated 404 or permission errors on object ids by one user | Enumeration or IDOR probing |
| `blocked_by_policy` events | Provider policy tests or misconfiguration |
| Database permission errors for the application role | Bug or attack |
| Dead jobs, queue age growth | Processing failures |
| Ledger export lag or failure | Resurrection risk |
| Backup failure | Recovery risk |
| Break-glass session started | Must always be reviewed |
| Cost anomalies | Denial of wallet |

Alert content carries identifiers only.

### 6.11 Infrastructure and container security (Required, SR-NFR-007)

- Containers run as non-root, with minimal base images, no privileged mode, a read-only root filesystem where possible and dropped capabilities.
- The database is never exposed to the internet. Only the `api`, `worker` and `maintenance` containers can reach it. Connections require TLS.
- Network segmentation: the proxy is the only public component. n8n runs on a separate network with a scoped API credential.
- Production egress is limited to the configured provider, email and ledger endpoints.
- Images are scanned in CI and before deployment. Base images are updated on a schedule.
- `pg_hba` allows only the required roles from the application network. The migration and maintenance roles are reachable only from their own containers.
- Host and platform patching follows the hosting provider's process, with documented responsibility (DEPLOYMENT.md).

### 6.12 Supply chain and development process (Required, SR-NFR-009)

- Lock files for Python and Node dependencies. Dependencies are pinned and reviewed. A new dependency needs a justification (TAD 4.3).
- `pip-audit` and an `npm audit` equivalent run in CI. Automated update pull requests are reviewed, not auto-merged.
- Static analysis: `ruff` with security rules and `mypy`. A SAST tool and a container scanner are added in Phase 1 (tool choice by CI setup, OPEN-T10).
- Branch protection: pull requests require passing checks and review. CI tokens have the minimum scope. Secrets in CI are limited to what each job needs.
- No production access from developer machines. Deployments go through the pipeline.
- Third-party scripts are not loaded in the frontend. Fonts and assets are self-hosted.

### 6.13 Availability, abuse and resilience (Required)

- Rate limits as in API section 2.9. Payload, parse and provider timeouts everywhere.
- AI work runs in the worker process, so a provider outage or slow model does not block the API.
- Pagination and query limits protect the database. Statement timeouts are set for the application role.
- Backups and restore are tested, including the deletion ledger step. Recovery time and recovery point targets are not set yet (OPEN-SEC2).

## 7. Subprocessor and provider security

A due-diligence checklist applies to every subprocessor before it receives S4 data. The result is recorded in PRIVACY.md. Nothing is assumed from marketing claims.

| Check | Question |
|---|---|
| Data processing agreement | Is a processing agreement available and signed? |
| Retention | How long does the provider keep inputs and outputs, and can this be disabled (for example Zero Data Retention eligibility)? |
| Training | Is customer data used for training? Can it be excluded by contract or settings? |
| Region and transfers | Where is data processed and stored? Which transfer mechanism applies? |
| Subprocessors | Who else receives the data? |
| Security attestations | Which independent security reports exist? Are they current? |
| Incident notification | How and when does the provider notify customers? |
| Deletion | Can data be deleted on request and how is it confirmed? |
| Access controls | Is there access logging and is staff access restricted? |

| Subprocessor | Intended use | Status |
|---|---|---|
| OpenAI | Primary AI provider: analysis, extraction, Q&A, summaries, drafts, briefings, embeddings | Review per endpoint before production (PROV-9) |
| DeepSeek | Development, synthetic and anonymized test data only. Its published privacy policy describes processing and storage in China, which is treated as a material transfer consideration (decision addendum). To be re-verified against the current policy | Blocked for identifiable customer data |
| Email service | Verification, reset, invitation emails (the only personal data is the address) | Not chosen (OPEN-T4) |
| Hosting and database | Runtime and storage | Not chosen (OPEN-T1) |
| Ledger store | Write-once store for deletion ledger entries (identifiers only) | Not chosen (OPEN-T7) |
| Error tracking | Error reports | Not chosen, needs review and scrubbing (OPEN-T5) |

## 8. Privacy-protective security measures

These controls support the privacy design in PRD 8.4 and PRIVACY.md.

- Deletion and retention run in the maintenance process under a least-privilege role (ADR-014, ADR-020).
- The deletion ledger prevents backup resurrection (SR-PRIV-005, SR-PRIV-006).
- Exports are encrypted, short-lived and audited.
- Consent and legal hold records are append-only.
- Logs and audit entries are minimized to identifiers.
- Retention values are proposed defaults and remain subject to legal review.

## 9. Security requirements traceability

| Area | SRS requirements |
|---|---|
| Authentication | SR-AUTH-001 to 012 |
| Authorization and tenancy | SR-ORG-002, SR-ORG-005, SR-ORG-008, SR-SYS-001, SR-SYS-002, SR-CUST-004, SR-ASST-001, SR-ASST-009, SR-MEM-017 |
| Integrity | SR-SYS-003, SR-SYS-004, SR-SYS-005, SR-INTEL-007, SR-MEM-008, SR-MEM-009 |
| Input and content | SR-SYS-007, SR-CONV-002, SR-INTEL-018 |
| AI governance | SR-PROV-001 to 014 |
| Privacy mechanics | SR-PRIV-003 to 007, SR-PRIV-011 |
| Audit | SR-AUD-001 to 004 |
| Non-functional | SR-NFR-005 to 009 |

## 10. Security architecture decisions

| ID | Decision | Status |
|---|---|---|
| ADR-022 | No standing platform-admin access to customer content. Access only through time-boxed, approved, audited break-glass sessions. Developers have no production data access | Proposed |
| ADR-023 | Login throttling with growing delay instead of account lockout; dummy hash verification to equalize timing | Proposed |
| ADR-024 | Imported and AI text is always rendered as text, and a strict nonce-based CSP is mandatory | Proposed |
| ADR-025 | No field-level encryption of conversation text in the MVP, because it blocks keyword and semantic retrieval. Risk accepted and revisited after the pilot | Proposed |
## 11. Incident response

### 11.1 Severity

| Level | Examples |
|---|---|
| SEV-1 | Confirmed cross-tenant exposure, identifiable data sent to a restricted provider, leaked production secret, restored backup exposing deleted data |
| SEV-2 | Compromised user or admin account, suspected data access by an unauthorized party, sustained attack |
| SEV-3 | Vulnerability found without evidence of exploitation, policy blocks caused by misconfiguration |
| SEV-4 | Minor findings |

### 11.2 Procedure

1. **Detect and triage:** assign an incident lead, classify severity, open a private incident record.
2. **Contain:** revoke sessions and tokens, rotate affected keys and secrets, disable the affected feature or provider setting, isolate the affected tenant if needed.
3. **Preserve evidence:** keep audit logs, `ai_runs` metadata and infrastructure logs. No evidence is deleted.
4. **Eradicate and recover:** fix the cause, redeploy, verify with the relevant tests, restore data through the verified restore procedure if needed.
5. **Notify:** affected customers, and authorities where required. Statutory deadlines and recipients differ by jurisdiction and are set in the legal review. The runbook records them once verified. This document does not state them.
6. **Review:** a written post-incident review with corrective actions within a defined period, and an update of the threat model and tests.

### 11.3 Key and secret compromise runbook

The runbook lists each secret (JWT signing keys, credential encryption keys, database role passwords, provider keys, ledger store credentials, email credentials, CI tokens), who owns it, how to rotate it, what breaks during rotation and how to verify. It is written in DEPLOYMENT.md and rehearsed before the pilot.

## 12. Accepted and residual risks

| ID | Risk | Position |
|---|---|---|
| RR-1 | Conversation text is not encrypted at field level | Accepted for the MVP (ADR-025). Storage encryption and access control apply |
| RR-2 | AI providers process identifiable data outside REIA's control | Mitigated by the provider policy, contracts and review. Not eliminated |
| RR-3 | An AI model may still produce wrong content that passes validation | Mitigated by evidence checks and agent verification. Not eliminated |
| RR-4 | Single-instance in-process rate limiting | Valid only for one `api` instance (TAD 21) |
| RR-5 | No MFA until decided | Open decision OPEN-SEC1 |
| RR-6 | Third-party services not chosen yet | Each needs due diligence before use |

## 13. Security test plan

The full plan is in TESTING.md. These tests are required and run in CI unless marked.

| ID | Test | Covers |
|---|---|---|
| ST-01 | Cross-tenant matrix: every endpoint with another tenant's ids returns 404 and changes nothing | TH-10, TH-33 |
| ST-02 | Database level: queries as `reia_app` with no context return nothing, foreign inserts are rejected, `original_content` update and all `DELETE` are denied, `SECURITY DEFINER` functions enforce the tenant | TH-10, TH-14, TH-16, TH-46 |
| ST-03 | Authorization matrix: each role against each permission, route coverage test, visibility rule for agents, removed member loses access immediately | TH-07, TH-08, TH-11, TH-13 |
| ST-04 | Authentication: throttling, generic errors, timing parity, reset and verification token rules | TH-01, TH-02 |
| ST-05 | JWT: tampered, expired, wrong algorithm, wrong audience and `none` tokens are rejected | TH-03, TH-06 |
| ST-06 | Refresh rotation, reuse detection and family revocation, logout | TH-04 |
| ST-07 | Headers, CSP, cookie attributes, CORS, CSRF checks, framing | TH-05, TH-27 |
| ST-08 | Injection: SQL, header and parameter tampering fuzz on all inputs | TH-20, TH-26 |
| ST-09 | Mass assignment and unknown field rejection | TH-12 |
| ST-10 | Rendering: messages and AI text containing HTML, scripts and markdown beacons render as inert text | TH-21, TH-32 |
| ST-11 | Upload and parser limits: oversize, binary, wrong encoding, huge lines, many columns, archives | TH-22, TH-23, TH-24 |
| ST-12 | Egress: no code path fetches user-supplied URLs. Production egress allowlist verified (staging) | TH-25 |
| ST-13 | Provider policy: restricted provider blocked for every task and for embeddings, `pseudonymized` treated as `identifiable`, startup refusal on contradictory configuration | TH-34, TH-38 |
| ST-14 | Concurrency and idempotency: parallel imports, duplicate jobs, advisory lock, unique index retry | TH-15, TH-49 |
| ST-15 | Prompt injection suite in English, Spanish and Portuguese: injected instructions are ignored, no action, no schema break | TH-30, TH-31, TH-32, TH-37 |
| ST-16 | Retrieval and assistant: other-customer questions refused, no cross-customer evidence, invalid references removed | TH-31, TH-33 |
| ST-17 | Leakage: log and error output scanned for message text, contact details, keys and tokens, with seeded canary values | TH-35, TH-41, TH-42 |
| ST-18 | Rate limits, quotas and timeouts | TH-01, TH-36, TH-47 |
| ST-19 | Backup restore with deletion ledger re-apply and verification (staging) | TH-40, TH-45 |
| ST-20 | Break-glass: access without an approval record fails, sessions expire, every session is audited | TH-43 |
| ST-21 | Dependency, secret and container scans pass | TH-41, TH-44 |
| ST-22 | Export: encrypted, expires, only the creator downloads, download audited | TH-48 |

Further activities before the pilot: a threat model review, a DAST baseline scan against staging, and an independent penetration test or security review by a party that did not build the system. The threat model is reviewed at the end of every phase that changes a trust boundary.

## 14. Compliance mapping (for legal verification, not a compliance claim)

| Topic | Where it is addressed | Legal verification needed |
|---|---|---|
| Security of processing | This document, TAD, DATABASE | Whether the controls meet each jurisdiction's expected standard |
| Data subject rights (access, correction, deletion, export) | API sections 6.11, 6.14, PRIVACY.md | Scope, deadlines and exceptions per jurisdiction |
| Retention and erasure | PRD 8.4, DATABASE 7.3 | The 30 and 35 day and 12 month values are proposed defaults |
| Processors and subprocessors | Section 7, PRIVACY.md | Agreements, roles of REIA and its customers |
| International transfers | Section 7, PRD A5 | Mechanism per route, UAE PDPL and GDPR |
| Consent and lawful basis | `consent_records`, API 6.12 | Which basis applies to each processing purpose |
| Breach notification | Section 11 | Deadlines and recipients |
| Impact assessment | Not done | Whether a data protection impact assessment is needed (OPEN-SEC8) |
| Records of processing | PRIVACY.md | Required content and format |

## 15. Pilot security gate

The pilot with real customer data does not start until all of these are true:

1. All tests ST-01 to ST-22 pass, and the results are stored.
2. An independent penetration test or security review is complete, and every high or critical finding is fixed.
3. Production secrets are generated, stored in the secret manager and rotated once as a rehearsal. No DeepSeek credentials exist in production.
4. Backup and restore, including the deletion ledger step, is tested and timed.
5. Provider and subprocessor due diligence is complete and recorded. Processing agreements are in place.
6. The legal and privacy review is complete for the pilot market, including hosting region and transfers.
7. The MFA decision is made and implemented as decided.
8. The incident runbook is written and rehearsed once.
9. The log scrubbing test passes on the production configuration.
10. Monitoring and alerts from section 6.10 are active and tested.

## 16. Changes this document requires elsewhere

| Document | Change |
|---|---|
| API.md v0.2 | Resolve OPEN-A2: remove the `q` parameter from `GET /customers` and add `POST /customers/search` with the same filters and a body, so personal data stays out of URLs. Add `POST /organizations/current/...` break-glass has no API (it is an operational procedure) |
| DATABASE.md v0.3 | DB-13: `break_glass_sessions` (organization, approver, requester, reason, approval reference, starts, expires, ended, query summary reference). DB-14: define `audit_logs.action` catalog and the `platform_role` semantics. DB-15: statement timeout setting for `reia_app` |
| TAD.md | Add `__Secure-` cookie naming and the CSP requirement to sections 7 and 13 |
| SRS.md | Resolve OPEN-S7 as ADR-022 |

## 17. Open items

| ID | Item | Resolve in |
|---|---|---|
| OPEN-SEC1 | MFA for owners and admins (TOTP recommended before the pilot) | Before Phase 2 |
| OPEN-SEC2 | Recovery time and recovery point targets | DEPLOYMENT.md |
| OPEN-SEC3 | Who performs the independent security review | Before the pilot |
| OPEN-SEC4 | Statutory breach notification deadlines and recipients | Legal review |
| OPEN-SEC5 | Breached-password check method (local list or a privacy-reviewed lookup) | Phase 2 |
| OPEN-SEC6 | Web application firewall or CDN at the proxy | DEPLOYMENT.md |
| OPEN-SEC7 | Where logs are shipped and how long they are kept apart from the 12 month audit logs | DEPLOYMENT.md |
| OPEN-SEC8 | Whether a data protection impact assessment is needed | Legal review |