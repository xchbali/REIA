# TESTING.md: REIA Testing and Quality Assurance Plan

Status: Draft v0.1 (Phase 0.7), pending review.
Depends on: PRD.md v0.3, SRS.md v0.1, DATABASE.md v0.2, TAD.md v0.2, API.md v0.1, SECURITY.md v0.1.
Decisions applied from review: ADR-022 (break-glass), mandatory MFA for owners and admins, `POST /customers/search`. These are being added to the other documents in the Phase 0.8 patches. Until then, the requirement IDs they use are defined in section 5.3.

## 1. Purpose, scope and principles

### 1.1 Purpose

This plan defines how REIA is verified: what is tested, at which level, with which data, and which results block a release. It covers backend, frontend, database, security, AI behavior, performance, backup and restore, and accessibility.

### 1.2 Principles

1. **Requirement-based.** Every SRS requirement whose verification method is test (T) has at least one automated test. A report proves it.
2. **Tests ship with features.** A feature is not done without its tests (the project rule).
3. **Real infrastructure for what matters.** Database, Row-Level Security, roles, privileges and migrations are tested on real PostgreSQL with pgvector and the real roles. No substitute database.
4. **Deterministic first, statistical second.** Everything that can be tested deterministically is (memory rules, permissions, policy, validation). Model behavior is evaluated statistically on a fixed dataset, kept apart from deterministic tests.
5. **Safety invariants are absolute.** Isolation, evidence verification and provider policy are pass or fail. They are never averaged.
6. **Privacy-safe by construction.** All test and evaluation data is synthetic. No real customer data enters the repository, CI, staging or any evaluation run.
7. **Tests must be able to fail.** Critical security tests have negative controls (section 9.3).
8. **Honest reporting.** Results state what was run, on which versions and data, and with what sample size. A claim that tests pass is made only from an executed run.

## 2. Strategy and test pyramid

| Level | Scope | Runs on | Proposed share of tests |
|---|---|---|---|
| Unit | Pure functions and single classes, no I/O: memory update rules, permissions, provider policy decisions, normalizers, parsers, evidence verification, ranking, schema validation | Every commit | About 60% |
| Integration | Real PostgreSQL: repositories, RLS, privileges, migrations, jobs, the AI gateway with FakeProvider, retrieval queries | Every pull request | About 20% |
| API | HTTP contract through the FastAPI app against real PostgreSQL: auth, permissions, errors, pagination, idempotency, state transitions, search | Every pull request | About 12% |
| Security | Attack-oriented tests across levels (section 9) | Every pull request, plus scheduled scans | Counted within the levels above |
| End to end | Browser through proxy, frontend, API, worker and database with FakeProvider | Pull requests touching flows, nightly, pre-release | About 5% |
| AI evaluation | Model-in-the-loop evaluation on the synthetic dataset | On prompt, model, retrieval-weight or schema change, and weekly | Separate suite |
| Performance and resilience | Load, soak, restore | Nightly smoke, pre-release full | Separate suite |

The shares are proposals to keep the pyramid shape. They are not targets to hit.

## 3. Tooling

### 3.1 Backend

| Tool | Purpose |
|---|---|
| `pytest`, `pytest-asyncio` | Test runner and async support |
| `pytest-cov` | Coverage |
| `hypothesis` | Property-based tests for memory rules and normalizers |
| `schemathesis` | Contract and fuzz tests generated from the OpenAPI schema |
| `httpx` | API test client |
| `import-linter` | Architecture contracts |
| `ruff`, `mypy`, `pip-audit` | Lint, types, dependency audit |
| Secret scanner (for example `gitleaks`) | Secret detection in CI and pre-commit |
| `mutmut` (optional) | Mutation testing of critical pure modules |

### 3.2 Frontend and end to end

| Tool | Purpose |
|---|---|
| Vitest, React Testing Library | Component and hook tests |
| MSW | API mocking in component tests |
| ESLint, TypeScript compiler | Static checks |
| Playwright | End-to-end tests |
| `@axe-core/playwright` | Automated accessibility checks |

### 3.3 Other

A load tool (k6 or Locust, OPEN-TS2), a DAST baseline scanner against staging, and a container image scanner. All are development dependencies and are not part of the shipped application. Each addition needs a one-line justification (TAD 4.3).

## 4. Test infrastructure

### 4.1 Layout

```text
backend/tests/
  unit/  integration/  api/  security/  performance/  fixtures/
  evaluation/
    datasets/{en,es,pt}/     scenario files
    gold/                    annotations (same scenario ids)
    harness/                 runner, scorers, report writer
    baselines/               stored results per dataset version
    manifest.yaml            dataset version, origin, generation method
frontend/tests/              component tests
tests/e2e/                   Playwright specs
scripts/seed_synthetic.py    synthetic data generator
```

`api/`, `performance/`, `fixtures/` and `evaluation/harness`, `baselines` are additions to the Phase 0 skeleton.

### 4.2 Database for tests

- A Docker Compose test profile starts PostgreSQL with `pgvector`, `citext`, `pg_trgm` and `unaccent`.
- An init script creates the roles exactly as production: `reia_migrator`, `reia_app`, `reia_maintenance`. Alembic migrations run as `reia_migrator`.
- Application and API tests connect as `reia_app`. Maintenance tests connect as `reia_maintenance`. **No test of isolation or privileges runs as a superuser or the migrator.**
- A fixture asserts at session start that the `reia_app` connection has neither `SUPERUSER` nor `BYPASSRLS`. If it does, the whole suite fails.
- Setup and cleanup that need cross-tenant access use a separate migrator-role fixture. Tests do not reuse tenant data. Each test creates its own organizations with random ids, so tests are independent and can run in parallel.

### 4.3 Determinism

- A `Clock` interface is injected into services, jobs and token code. Tests use a controllable clock. (TAD addition: services must not call the system clock directly.)
- Random values (ids, tokens) use seeded sources in tests where reproducibility is needed.
- AI calls in non-evaluation tests use `FakeProvider`: deterministic, scriptable responses, configurable failures (timeouts, invalid JSON, wrong schema, policy-relevant behavior).
- No test calls an external network service. A guard fails any test that opens a socket to a non-local address.

### 4.4 Fixtures and factories

Factories build organizations, users, memberships, customers, conversations, facts, tasks and drafts with sensible defaults and explicit overrides. A scenario fixture builds common worlds, for example "two organizations, each with an owner, an admin, two agents and a read-only member, with customers assigned in every combination". The isolation matrix (section 10) uses it.

## 5. Requirement traceability

### 5.1 Markers and report

Every test carries the requirement it verifies:

```python
@pytest.mark.req("SR-MEM-003")
def test_explicit_replacement_supersedes_old_budget(...): ...
```

CI generates a report listing, for each SRS requirement with verification T, the tests that cover it. The build fails when an implemented requirement has no test. During the early phases, requirements of modules not yet built are excluded through an explicit allowlist that shrinks every phase.

### 5.2 Coverage of requirement groups

| SRS group | Main suites |
|---|---|
| SR-SYS | Integration (privileges, RLS), API (envelope, pagination), security |
| SR-AUTH, SR-ORG | API, security (ST-03 to ST-07, ST-23 to ST-25), unit (hashing, tokens) |
| SR-CUST | Unit (normalization), integration, API, security |
| SR-CONV | Unit (parsing, hashing), API, security (ST-11) |
| SR-INTEL | Unit (verification), integration (gateway), AI evaluation |
| SR-MEM | Unit and property tests (rules), integration (retrieval), AI evaluation |
| SR-ASST, SR-FOLLOW, SR-BRIEF | Integration with FakeProvider, AI evaluation, API |
| SR-TASK, SR-TIME, SR-DASH | Unit, API |
| SR-SRCH | API, security (ST-28 to ST-30), AI evaluation (retrieval) |
| SR-PROV | Unit (policy), integration (gateway), security (ST-13) |
| SR-PRIV, SR-AUD | Integration, API, restore tests |
| SR-I18N | Unit, frontend, E2E, AI evaluation |
| SR-NFR | Performance suite, CI checks |

### 5.3 Requirements from approved decisions (to be added to SRS v0.2)

These IDs are used by the tests below and are added to SRS.md in the Phase 0.8 patch.

| ID | Requirement |
|---|---|
| SR-AUTH-013 | Organization owners and admins shall enroll in MFA before accessing the application. Passkeys (WebAuthn) and TOTP authenticator apps are supported. SMS shall never be the only MFA method |
| SR-AUTH-014 | Single-use recovery codes shall be issued at enrollment. Account recovery shall follow a controlled process. No administrator shall disable another user's MFA outside that process |
| SR-AUTH-015 | MFA shall be enforced at login and as step-up for sensitive operations |
| SR-AUTH-016 | MFA enrollment, removal, recovery and failure events shall be audited |
| SR-AUTH-017 | MFA shall be optional for agents at launch, and the policy shall be switchable to mandatory per role without redesign |
| SR-PLAT-001 | Platform administrators shall have no standing access to customer conversations, memories, personal information or organization business data |
| SR-PLAT-002 | Break-glass access shall be allowed only for a documented operational or security emergency and shall need an explicit reason recorded before access |
| SR-PLAT-003 | Break-glass authorization shall be time-limited with automatic expiry and limited to the minimum data and duration needed |
| SR-PLAT-004 | Break-glass access shall require MFA |
| SR-PLAT-005 | Every break-glass attempt and action shall be logged in an immutable audit trail. Break-glass shall not bypass audit logging |
| SR-PLAT-006 | The security contact and, where applicable, the organization owner shall be alerted when break-glass starts |
| SR-PLAT-007 | Every break-glass event shall be reviewed after use |
| SR-PLAT-008 | Normal platform administration shall be separate from customer-content access |
| SR-SRCH-004 | `POST /customers/search` shall be read-only and shall not create, update or delete anything |
| SR-SRCH-005 | The request shall follow a validated, documented schema with explicit pagination, sorting and filtering |
| SR-SRCH-006 | Organization isolation and the assigned-customer rule shall be enforced on the server. Agents receive results for assigned customers only. Owners and admins receive organization-wide results |
| SR-SRCH-007 | Search shall not expose unauthorized customer information through counts, pagination metadata, error messages or AI retrieval. The response shall contain no total count |

## 6. Unit tests

### 6.1 Scope

Pure logic with no I/O. Priority targets:

| Area | Examples |
|---|---|
| Memory update function | Every row of the table in TAD 11.3 |
| Permissions | `can()` for every role, permission and customer visibility case |
| Provider policy | `decide()` for every provider, task, data class and configuration combination |
| Evidence verification | Quote found, quote missing, whitespace and Unicode normalization differences |
| Normalizers | Phone to E.164, email, content hash, Unicode NFC, number formats |
| Parsers | Supported chat export formats, CSV mapping, malformed input |
| Ranking | Score fusion and boosts with fixed inputs |
| Schemas | Valid and invalid request and AI output schemas |
| Token and password helpers | Hashing parameters stored, constant-time comparison, token expiry with a controlled clock |
| Money and area | Decimal handling, currency and unit requirements |

### 6.2 Property-based tests (Hypothesis)

The memory update function must satisfy these invariants for any generated sequence of statements:

| ID | Invariant |
|---|---|
| I1 | At most one `current` fact exists per customer, key and slot |
| I2 | No fact is ever removed. The number of facts never decreases |
| I3 | `supersedes_fact_id` chains contain no cycles and never cross keys or slots |
| I4 | An AI-extracted fact never supersedes or changes a `verified` fact. It can only create a conflict |
| I5 | `valid_to` is never earlier than `valid_from` |
| I6 | Applying the same extraction result twice yields the same state (idempotence) |
| I7 | A statement older than the current fact never becomes `current` |
| I8 | A `rejected` fact never appears as `current` and never takes part in conflicts |

Normalizer properties: phone normalization is idempotent. The content hash is stable under line-ending and Unicode normalization differences and changes when the content changes. Money parsing never returns a float.

## 7. Integration tests

All run on real PostgreSQL as the proper roles.

### 7.1 Migrations

| Test | Check |
|---|---|
| Up from empty | All migrations apply as `reia_migrator` |
| Down and up | Downgrade then upgrade works. Migrations that cannot reverse safely say so, and the test accounts for them |
| No drift | ORM metadata and the migrated schema agree (autogenerate yields no changes) |
| RLS coverage | Every table with `organization_id` has RLS enabled and forced with the tenant policy |
| Tenant keys | Child tables reference parents with composite keys that include `organization_id` |
| Privileges | `reia_app` has no `DELETE` anywhere. It cannot update `conversations.original_content` or `content_hash`. `conversation_messages`, `message_translations`, `customer_memory_events`, `fact_corrections` and `audit_logs` are insert and select only. `reia_maintenance` has no direct `DELETE` and only the documented `EXECUTE` rights |
| Functions | `SECURITY DEFINER` functions have a fixed `search_path`. `EXECUTE` is revoked from `PUBLIC` and granted only to named roles |
| Indexes | The partial unique index for current facts, the trigram and full-text indexes, and the partial HNSW index for the active embedding model and version exist |
| Extensions | Required extensions are installed |

### 7.2 Repositories and tenancy

- Queries with no tenant context return nothing, and writes fail (SR-SYS-002).
- Cross-tenant reads and writes are impossible, including through joins.
- Composite foreign keys reject a child that points to a parent of another tenant.
- The advisory lock serializes concurrent fact updates for one customer, and the unique index remains the final guard.

### 7.3 Jobs and workers

- Claiming through `claim_next_job` is cross-tenant for scheduling data only and returns nothing else.
- Leases: a job whose lease expired is claimed again. Two workers never run the same job.
- Retries with backoff, `dead` after the maximum attempts, safe error codes on the conversation.
- Handlers are idempotent: processing a conversation twice changes nothing.
- A failure before the write transaction leaves no partial data.

### 7.4 AI gateway (with FakeProvider)

| Test | Check |
|---|---|
| Policy | Restricted provider blocked for every task and for embeddings. No outbound call is made. `ai_runs` records `blocked_by_policy` |
| Data classes | `pseudonymized` is handled as `identifiable`. A missing data class is a type error caught by static checks and by a runtime guard |
| Three-way agreement | Code, deployment configuration and organization setting must all allow. An organization setting cannot widen what code or deployment forbids |
| Startup | The application refuses to start in production when configuration contradicts the policy |
| Output validation | One retry on schema failure, then failure with nothing stored |
| Timeouts and retries | Bounded retries with backoff for transient errors, none for policy and validation errors |
| Logging | `ai_runs` has no prompt or response content |
| Quota | Per-organization limits are enforced |

### 7.5 Retrieval

- Customer and organization filters are always applied (SR-MEM-017).
- The vector query filters by the active model and version and uses the partial index (checked with `EXPLAIN`).
- The query builder rejects a retrieval request without model and version filters.
- Rejected facts and archived customers never appear.
- Hybrid fusion returns deterministic results for fixed inputs.

## 8. API tests

| Area | Checks |
|---|---|
| Error envelope | Every error path returns the documented envelope with a stable `code` and a `request_id`, with no sensitive values echoed |
| Authentication | Register, verify, login, refresh rotation, logout, switch organization, password reset and change (including MFA steps, section 9) |
| Permissions | Generated from the route table and the permission registry. Every route is called by every role, and the result matches the matrix (API section 4) |
| Not found semantics | Another tenant's resource and an invisible customer return 404 with the same body as a missing resource |
| Validation | Unknown fields rejected, enumerations, lengths, money and area shapes, language and country codes |
| Pagination | Cursor rules, tampering, reuse with other filters, maximum page size, deterministic order, no duplicates or gaps across pages |
| Idempotency | Same key and body replays, same key and different body returns 422, expiry |
| Concurrency | `If-Match` mismatch returns 412 |
| State transitions | Every allowed and forbidden transition for conversations, facts, tasks, commitments, drafts and jobs (SRS section 6) |
| Immutability | `DELETE` and `PUT` on conversations and messages return 405. No API path changes `original_content` |
| No delete | `DELETE /customers/{id}` archives. `DELETE /tasks/{id}` cancels. Data remains |
| Imports | Duplicate import returns the existing conversation and creates nothing. Limits, encoding errors, unsupported formats |
| Contract | The OpenAPI schema matches `docs/openapi.json`. A breaking diff fails the build. `schemathesis` runs against the schema for crashes (5xx) and schema violations |
| Production surface | Interactive API docs are disabled when `ENVIRONMENT=production` |

## 9. Security tests

### 9.1 Required tests

ST-01 to ST-22 are defined in SECURITY.md section 13 and are all required. ST-23 to ST-30 come from the approved decisions.

| ID | Test | Requirements |
|---|---|---|
| ST-23 | **MFA enforcement and enrollment.** An owner or admin without MFA can reach only enrollment endpoints. Passkey and TOTP enrollment work. SMS cannot be the only method. Login for enrolled admins requires the second factor. The agent policy is optional at launch, and switching the policy to mandatory for agents takes effect without code changes | SR-AUTH-013, SR-AUTH-017 |
| ST-24 | **Recovery.** Recovery codes are single-use, stored hashed and regenerated only after step-up. Disabling or resetting another user's MFA is impossible through normal admin endpoints. The controlled recovery process requires its defined steps, notifies the user, is delayed as designed and is audited | SR-AUTH-014 |
| ST-25 | **Step-up.** Sensitive operations (change password or email, change MFA, change member roles to owner or admin, AI provider settings, exports, erasure requests, workspace termination, legal holds) are refused without a recent second factor | SR-AUTH-015 |
| ST-26 | **Break-glass.** No access without a recorded reason. No access without MFA. Authorization expires automatically and access stops at expiry. Scope is limited to the approved data. Every attempt, success or failure, and every action is in the audit trail. Attempts to bypass or alter audit entries fail. The security contact and, where applicable, the owner are alerted at start. An event without a post-use review raises an alert and blocks a new grant for the same requester | SR-PLAT-002 to SR-PLAT-007 |
| ST-27 | **Platform admin separation.** A platform admin without an active break-glass grant is refused on every endpoint and database path that exposes S4 data or organization business data. Normal admin operations work without any content access | SR-PLAT-001, SR-PLAT-008 |
| ST-28 | **Customer search authorization.** An agent finds only assigned customers. A read-only member finds only assigned customers. An owner or admin finds all customers in the organization. Nobody finds another organization's customers. Results change immediately after reassignment or removal | SR-SRCH-006 |
| ST-29 | **Search non-leakage.** The response has no total count. `has_more` and cursors are computed inside the visible set only. Two cursors for the same filters cannot reveal hidden records. A tampered or foreign cursor is rejected with the same error as an invalid one. Error messages and response sizes do not differ between "no such customer" and "customer you cannot see". Timing differences between hidden and nonexistent matches are within a tested bound. The AI assistant and retrieval never use records outside the visible set | SR-SRCH-007 |
| ST-30 | **Search read-only and validation.** Running any search leaves the database unchanged (row counts, `updated_at` values and audit entries other than the allowed read audit). The request schema rejects unknown fields, bad filters, oversized pages and unsupported sort fields. Sorting and pagination are deterministic | SR-SRCH-004, SR-SRCH-005 |

ST-23 to ST-30 are added to SECURITY.md section 13 in the Phase 0.8 patch. The unified `POST /search` is covered by ST-28 and ST-29 as well.

### 9.2 Method notes

- ST-01 and ST-03 are generated from the route table and the fixture world in section 10. A new route is covered automatically, and a route without a declared permission fails the build.
- ST-15 (prompt injection) and ST-16 (retrieval isolation) have a fixed corpus in English, Spanish and Portuguese, including injection inside quoted text, inside names, inside file headers and spread across several messages.
- ST-17 (leakage) plants canary strings (for example unique tokens in message text, names and phone numbers) and scans logs, error bodies, metrics, audit metadata and `ai_runs` for them after exercising every endpoint.
- ST-10 uses payloads such as HTML, script tags, event handlers, markdown images and links, and Unicode tricks. The page must render them as inert text. Remote resource requests are monitored and any attempt fails the test.

### 9.3 Negative controls

A security test is only useful if it fails when the protection is missing. A nightly job runs selected tests against deliberately weakened environments and expects **failure**:

| Weakened environment | Tests that must fail |
|---|---|
| RLS disabled on a tenant table | ST-01, ST-02, CT-09 |
| `reia_app` granted `DELETE` | ST-02 privilege tests |
| `reia_app` granted `UPDATE` on `original_content` | ST-02, CT-16 |
| Restricted provider allowed by code but not by deployment, or the reverse | ST-13 |
| Permission check removed from one route | ST-03 |
| Evidence verification disabled | CT-15 |
| Audit insert skipped in a break-glass path | ST-26 |

If a negative-control run passes, the build is marked as failed, because the corresponding test cannot detect the problem.

## 10. Authorization and isolation test design

### 10.1 Fixture world

Two organizations, A and B, each with: an owner, an admin, agents A1 and A2 (B1 and B2), and a read-only member. Customers in each organization: assigned to A1, assigned to A2, assigned to the read-only member, and unassigned. One user (agent) has memberships in both organizations. Each customer has conversations, facts, a conflict, tasks, a draft and a briefing.

### 10.2 Matrix

The generated matrix covers:

- Roles: owner, admin, agent (own, other), read-only (own, other), user in the wrong organization, user with no membership, removed member, platform admin without break-glass, unauthenticated.
- Resources: customer, identifiers, conversations, messages, summaries, facts, conflicts, events, commitments, tasks, drafts, briefings, timeline, memory view, consents, exports, jobs, notifications.
- Operations: read, list, search, create, update, action endpoints, export, erasure request.
- Expected result for each cell: allowed, 403 (role lacks the permission), or 404 (not visible or another tenant).

### 10.3 Assigned-customer rules

| Rule | Test |
|---|---|
| Agents and read-only members see only assigned customers | Lists, search, timeline, assistant and exports for A1 never include A2's customers |
| Owners and admins see all customers of their organization | And nothing of organization B |
| Unassigned customers are visible to owners and admins only | Agents get 404 |
| Reassignment takes effect immediately | After moving a customer from A1 to A2, A1 gets 404 on every endpoint, including previously issued cursors and open job references. A2 gets access |
| Child records inherit visibility | Tasks, drafts, briefings, facts and conversations of an invisible customer return 404, even when the task is assigned to the requesting user |
| Removal is immediate | A removed member's existing access token fails on the next request |
| Multi-organization user | A token for organization A never grants access to B. Switching organization gives access only to B's visible data |
| Read-only | Read endpoints work on assigned customers. Write, AI and export endpoints return 403 |

### 10.4 AI path isolation

- The assistant, drafts, briefings and semantic search retrieve only records the caller may see. Tests plant a unique fact in an invisible customer and assert it never appears in any answer, draft, briefing, snippet, citation or suggestion, including when the question names that customer.
- A question about another customer than the selected one is refused (SR-ASST-009).
- Cache or reuse of AI results never crosses users with different visibility. (If a cache is ever added, it needs its own isolation test.)

## 11. AI testing and evaluation

### 11.1 Two kinds of AI tests

| Kind | Purpose | Model used | Runs |
|---|---|---|---|
| Deterministic AI tests | Everything around the model: schemas, verification, policy, memory rules, reference validation, refusal paths, prompt assembly | FakeProvider | Every pull request |
| Model evaluation | How well the real models extract, retrieve, answer and draft | Real providers, on synthetic data only | On prompt, model, retrieval or schema change, and weekly |

A change that affects model behavior cannot merge without a fresh evaluation run recorded against the baseline.

### 11.2 Dataset design

**Principle:** the dataset is synthetic, versioned, annotated by humans and split so that tuning never touches the held-out set.

**Languages:** English, Spanish and Portuguese, each with native-quality text. Spanish and Portuguese data must be written or reviewed by fluent speakers, including regional variants where they matter (Spain Spanish, Portugal Portuguese and Brazilian Portuguese expressions that agents may meet). OPEN-TS1 tracks who reviews.

**Splits and proposed starting size** (proposals, grown before the pilot):

| Split | Per language | Use |
|---|---|---|
| Development | 20 scenarios | Prompt and parameter tuning. May be inspected freely |
| Held-out test | 20 scenarios | Reported results. Never used for tuning. Changes to it are logged |
| Adversarial | 10 scenarios | Injection, ambiguity, traps. Included in gates as described in section 11.5 |

A scenario has one to five conversations for one fictional customer. With these sizes results are indicative, not statistically strong. Reports always show counts and confidence intervals, and no claim is made from a small category. The target before the pilot is at least 100 scenarios per language.

**Scenario taxonomy** (each scenario carries tags):

| Tag | What it tests |
|---|---|
| `budget_change_explicit` | Customer clearly replaces an earlier budget |
| `budget_change_implicit` | A different figure appears without saying it replaces the old one (must become a conflict) |
| `restatement` | The same requirement repeated (no duplicate current fact) |
| `multi_valued` | Several preferred locations, several property types |
| `out_of_order` | Older conversation imported after a newer one |
| `retraction` | "Forget what I said about Marina" |
| `negation` | "I do not want ground floor" |
| `financial_no_currency` | Amount without a stated currency (must not become a money fact) |
| `number_formats` | `1.800.000`, `1,8 millones`, `1,8 milhões`, `AED 1.8M`, `350 mil euros`, `€350k` |
| `units` | m² and sqft, with the unit stated or not |
| `terminology` | "T2" in Portugal (two-bedroom), "dormitorios" and "habitaciones" in Spain, "studio" variants |
| `relative_dates` | "next Friday", "en dos semanas", "na próxima semana" |
| `code_switching` | English and Spanish or Portuguese within one chat |
| `short_messages` | Emoji, one-word replies, voice-note transcripts |
| `commitments` | Agent and customer promises with deadlines |
| `objections` | Price, location, financing, timing |
| `long_conversation` | Longer than one model context window (chunking) |
| `no_information` | Questions about things never mentioned |
| `near_duplicate` | Same chat with small edits |
| `injection` | Instructions inside customer messages |
| `other_customer` | Another customer's data present in the corpus to catch leakage |

**Annotation record** (YAML, one file per scenario in `datasets/<lang>/` and its gold in `gold/`). Fact keys and the schema are illustrative until MEMORY_ENGINE.md fixes the registry.

```yaml
scenario_id: es-budget-change-explicit-001
language: es
split: test
tags: [budget_change_explicit, number_formats]
customer: { ref: C1, full_name: "Ahmed Rahimi" }   # fictional
conversations:
  - id: es-bce-001-a
    channel: whatsapp
    occurred_at: "2026-09-21T10:12:00Z"
    messages:
      - { idx: 0, sender_role: customer, sender_label: "Ahmed", text: "Hola Sara, busco un apartamento de 2 dormitorios en Dubai Marina. Mi presupuesto es de 1,5 millones de dirhams." }
      - { idx: 1, sender_role: agent, sender_label: "Sara", text: "Perfecto, Ahmed. Te envío opciones esta semana." }
  - id: es-bce-001-b
    channel: whatsapp
    occurred_at: "2026-10-02T14:05:00Z"
    messages:
      - { idx: 0, sender_role: customer, sender_label: "Ahmed", text: "Lo hemos hablado en familia y subimos el presupuesto a 1,8 millones de dirhams." }
gold:
  facts:
    - { conversation: es-bce-001-a, message_idx: 0, key: budget, value_type: money, min: "1500000.00", currency: AED,
        quote: "Mi presupuesto es de 1,5 millones de dirhams", change_signal: addition }
    - { conversation: es-bce-001-a, message_idx: 0, key: bedrooms, value_type: integer, min: 2,
        quote: "apartamento de 2 dormitorios", change_signal: addition }
    - { conversation: es-bce-001-a, message_idx: 0, key: preferred_location, value_type: location, city: Dubai, neighborhood: "Dubai Marina",
        quote: "en Dubai Marina", change_signal: addition }
    - { conversation: es-bce-001-b, message_idx: 0, key: budget, value_type: money, min: "1800000.00", currency: AED,
        quote: "subimos el presupuesto a 1,8 millones de dirhams", change_signal: explicit_replacement }
  state_after_replay:
    - { key: budget, current: "1800000.00 AED", superseded: ["1500000.00 AED"], open_conflicts: 0 }
  events: [ { type: budget_changed, conversation: es-bce-001-b } ]
questions:
  - id: q1
    text: "¿Cuál es el presupuesto actual de Ahmed?"
    answer_language: es
    expected_available: true
    expected_claims:
      - { status: current, fact: "budget 1800000.00 AED", source: { conversation: es-bce-001-b, message_idx: 0 } }
      - { status: historical, fact: "budget 1500000.00 AED", source: { conversation: es-bce-001-a, message_idx: 0 } }
  - id: q2
    text: "¿Cuántos baños quiere Ahmed?"
    expected_available: false
```

Every dataset file also has a `manifest.yaml` entry: dataset version, origin (`synthetic`), generation method (human-written, or model-assisted with human review) and reviewer names or ids for each language.

**Versioning:** the dataset has a semantic version and a content hash recorded in every result. Changing the held-out set creates a new version and a new baseline. Gold corrections are logged with a reason.

**Annotation quality:** every scenario is reviewed by a second person. For Spanish and Portuguese the reviewer is a fluent speaker. Disagreements are resolved and the resolution is recorded. A sample is re-annotated to estimate agreement.

### 11.3 What is measured

**Definitions**

| Term | Meaning |
|---|---|
| Fact match | Same key, same normalized value (amount and currency, unit, location parts) and the evidence points to the gold message |
| Fabricated evidence | Evidence quote that is not in the source message (should be rejected by the backend) |
| Fabricated fact | Extracted fact that the source text does not support |
| Unsupported claim | Answer claim whose cited sources do not support it, or that has no valid source |
| False available | An answer was given when the gold says the information is not available |
| False unavailable | The assistant says the information is not available when it is |
| Leak | Any content from another customer, organization or invisible record in an output |

**Extraction (EV-EXT)** per language, category and tag: precision, recall and F1 of facts, value accuracy (right key, wrong value), `change_signal` accuracy, share of model quotes rejected by verification (fabrication signal), fabricated fact rate, financial rule compliance (no money fact without currency), and handling of chunked long conversations.

**Memory and history (EV-MEM)**

Run in two ways so that causes can be separated:
1. *Rules in isolation:* feed the gold facts to the memory update function. Expected state must match exactly. This is deterministic and is a normal test, not an evaluation.
2. *End to end:* real extraction, then memory update, replayed over the scenario's conversations. Compare the final state with `state_after_replay`.

Metrics: current-value accuracy, history preservation (every earlier value present with the right lifecycle, `valid_from` and source), correct supersede versus conflict decisions, correct handling of out-of-order imports, retraction and verified-fact protection, duplicate suppression for restatements and near-duplicates.

**Conflicts (EV-CON)**: precision and recall of conflict creation, wrongly auto-resolved conflicts (should be zero for non-explicit changes), unresolved-conflict surfacing in answers.

**Retrieval (EV-RET)**: for questions with gold relevant sources, recall@k, MRR and nDCG@k, reported per language and for cross-language pairs (query in English with evidence in Spanish or Portuguese, and every other pairing). Also: leakage count (must be zero), effect of filters (time, customer), ablations (keyword only, vector only, hybrid with and without boosts) to justify the ranking weights.

**Answers, grounding and hallucination (EV-ANS, EV-HAL)**: claim support rate, unsupported claim rate, citation precision and recall, false available and false unavailable rates, correct current versus historical labeling, correct uncertainty and conflict surfacing, answer language correctness, evidence shown in the original language.

**Drafts (EV-DRF)**: language correct, uses customer history, no repeated already-answered questions, no facts outside the context (claims extracted from the draft and checked against context), disputed facts flagged, voice profile adherence (human rubric on a sample).

**Briefings (EV-BRF)**: section completeness against gold, every item sourced, empty sections stated honestly, warnings include open conflicts and overdue commitments.

**Injection and isolation (EV-INJ, EV-ISO)**: attack success rate (an injected instruction changing output, schema or behavior), cross-customer leak count.

**Language handling (EV-LANG)**: results per language and per tag, to find language-specific weaknesses.

### 11.4 Harness and procedure

1. Pick the dataset version and split. The manifest must say `synthetic`.
2. Configure the run: provider, model, prompt versions, retrieval weights, temperature (zero where supported), number of repeats (proposed 3, to report variance).
3. The harness runs every scenario through the real pipeline in an isolated test database, with the gateway in place and the data class set to `synthetic`.
4. Scorers compute the metrics. A judge model may score open-ended criteria (section 11.6).
5. The report is written as machine-readable JSON plus a readable summary. It contains the dataset version and hash, provider and model versions, prompt versions, parameters, repeats, per-language and per-tag results with counts, confidence intervals (for proportions, Wilson intervals) and the list of failures with scenario ids (no real data exists, so the text can be stored).
6. The result is compared with the stored baseline. Differences use paired comparison over the same scenarios, with a bootstrap interval, so small noise is not mistaken for change.
7. Failures are reviewed by category. A change is accepted, fixed or rejected, and the decision is recorded.
8. A new baseline is stored only through an approved change with a written reason.

Every run costs money. Runs are triggered by the events in 11.1 and by schedule, not on every commit. A cost budget per run is configured and the harness stops when it is exceeded.

### 11.5 Gates

| Gate | Type | Rule |
|---|---|---|
| Cross-customer and cross-tenant leakage in evaluation and tests | Absolute | Zero. Any leak blocks release |
| Accepted fact with evidence not present in its source message | Absolute | Zero. Enforced by code and tested by CT-15 and its negative control |
| Provider policy violations (identifiable data to a restricted provider, including embeddings) | Absolute | Zero |
| Memory update invariants I1 to I8 | Absolute | Property tests pass |
| Injection attack success on the adversarial set | Absolute for schema and action effects, thresholded for content influence | No schema break, no action. Content influence rate has a threshold set from the baseline |
| Extraction, retrieval, grounding, refusal and draft quality metrics | Thresholded | Thresholds are set after the first baseline in Phase 5 (and Phase 6 and 7 for retrieval and assistant), proposed from the data and approved by the product owner in an ADR. Until then the gate is "no statistically meaningful regression against the stored baseline" |
| Language parity | Thresholded | No language may fall below a set margin of the best language on the main metrics. The margin is set from the baseline |

No numeric quality target is invented in this document. Targets come from measured baselines and a recorded decision.

### 11.6 Judge models

- Used only on synthetic data, and only for criteria that cannot be scored by rules.
- The judge prompt is versioned and kept stable. Where possible the judge model differs from the generating model.
- Before use, the judge is calibrated against human labels on a sample per language. Agreement is reported. A judge with poor agreement is not used for gating.
- The judge sees only the source text and the claim, not the gold.
- Human review of a sample is part of every release evaluation.

## 12. Frontend, end-to-end, accessibility and localization tests
### 12.1 Component tests

Forms and validation messages, loading, error and empty states, permission-dependent rendering, the display of AI statements with status labels and source links, the original-language display with optional translation, confirmation dialogs for sensitive actions, rendering of imported text as inert text, and the MFA enrollment and step-up flows.

### 12.2 End-to-end scenarios (Playwright, FakeProvider)

| ID | Scenario |
|---|---|
| E2E-01 | Register, verify, enroll MFA as an admin, log in with the second factor |
| E2E-02 | Create a customer, handle a duplicate identifier suggestion |
| E2E-03 | Import a conversation, watch processing finish, see extracted facts with their evidence |
| E2E-04 | Verify, reject and correct a fact. See the history preserved |
| E2E-05 | Resolve a conflict, including "both valid" with slot assignment |
| E2E-06 | Ask the assistant a question and see sources. Ask a question with no data and see "not available" |
| E2E-07 | Generate a draft in the customer's language, edit, approve, mark as sent |
| E2E-08 | Generate a call briefing and see sourced sections |
| E2E-09 | AI-suggested tasks: approve one, dismiss another |
| E2E-10 | Search customers and conversations as an agent (assigned only) and as an admin (all) |
| E2E-11 | Two agents: reassignment removes access for the first and grants it to the second |
| E2E-12 | Request an export and erasure as an admin. Confirm the erased customer is gone |
| E2E-13 | Switch UI language between English, Spanish and Portuguese |
| E2E-14 | Session expiry and refresh. Logout clears access |

A small nightly **live smoke test** runs a few synthetic scenarios against the real OpenAI provider in staging, to catch provider-side changes. It uses synthetic data only and the `synthetic` data class.

### 12.3 Accessibility

- Axe checks on every main page and dialog, run in Playwright. Serious and critical violations fail the build.
- Keyboard-only walkthrough of the main flows is automated where possible and checked manually before the pilot.
- A manual screen-reader review of the main flows before the pilot. Target: WCAG 2.2 AA (SR-NFR-011).
- Color contrast and focus visibility are checked in component tests and in review.

### 12.4 Localization

- A test checks that locale files for `en`, `es` and `pt` have the same keys, with no missing or unused keys.
- Pseudo-localization (long and accented strings) is used to find layout breaks.
- Dates, numbers and currencies are tested for each locale and timezone, including daylight-saving boundaries for the organization timezone.
- RTL readiness: a test renders key pages with `dir="rtl"` and checks that no layout uses physical left or right properties. No Arabic UI is shipped (ADR-013).

## 13. Performance and resilience tests

### 13.1 Load model (proposed, to confirm)

The load model for SR-NFR-001 is proposed for pilot scale:

| Item | Proposed value |
|---|---|
| Organizations | 3 |
| Members per organization | up to 5 |
| Customers per agent | 300 |
| Conversations per customer | 5 |
| Messages per conversation | 30 |
| Concurrent active users | 20 |
| Growth check | The same tests at 10 times the data volume |

Data is produced by `scripts/seed_synthetic.py` directly in the database. Embedding vectors for performance tests are random vectors of the right dimension. They test index and query speed only, never semantic quality.

### 13.2 Tests

| Test | Target |
|---|---|
| Dashboard API latency | p95 under 500 ms (SR-NFR-001) |
| Customer search latency | p95 under 1 s (SR-NFR-001) |
| Retrieval query plan | The partial HNSW index is used. Latency measured with iterative scan settings |
| Query count | Key endpoints have a maximum number of queries per request (no N+1) |
| Import and processing throughput | Queue depth and time to process under load (AI calls faked with realistic delays) |
| Rate limits and quotas | Limits trigger as designed |
| Soak | A multi-hour run with steady load shows no memory growth, connection leaks or stuck jobs |
| Provider failure | Slow, failing and rate-limited provider responses: the API stays responsive, jobs retry and end `dead` correctly |
| Worker crash | Killing a worker mid-job leaves no partial data and the job is retried |

The targets are engineering goals under the stated model. They are not guarantees.

## 14. Backup, restore and deletion tests

| ID | Test |
|---|---|
| BR-01 | Erasure of a customer removes data from all tables, embeddings and derived data in the production database, writes the ledger entry and an audit entry, and returns 404 afterwards |
| BR-02 | The ledger entry is exported to the separate store, and a failed export is retried and alerted |
| BR-03 | Restore a backup taken before an erasure into an isolated environment. Apply the restore procedure. Verify that the erased customer does not exist before the system opens |
| BR-04 | The restore procedure refuses to open the system if the ledger store is unreachable or a ledger entry could not be applied |
| BR-05 | A legal hold blocks erasure and workspace deletion. Releasing it allows them |
| BR-06 | Workspace termination: export window, then deletion, including members, integrations and settings |
| BR-07 | Backup retention is enforced (no backup older than the configured maximum remains) |
| BR-08 | Restore time and data-loss window are measured and recorded (feeds OPEN-SEC2) |

All of these use synthetic data in staging.

## 15. CI quality gates

### 15.1 Pipeline

| Stage | Checks | Blocks merge |
|---|---|---|
| Pre-commit (local) | Formatting, lint, secret scan | Advisory locally, repeated in CI |
| Pull request: static | `ruff`, `mypy`, `import-linter`, ESLint, TypeScript, secret scan, dependency audits, license check | Yes |
| Pull request: backend tests | Unit, integration, API, security (ST), migration tests, requirement traceability report | Yes |
| Pull request: contract | OpenAPI export and diff, generated frontend types up to date | Yes |
| Pull request: frontend | Component tests, accessibility checks, locale key parity | Yes |
| Pull request: build | Container images build, image scan | Yes |
| Pull request: E2E | Relevant Playwright specs for changed flows | Yes |
| Nightly | Full E2E, negative controls, `schemathesis` fuzz, DAST baseline on staging, performance smoke, live provider smoke, mutation tests on critical modules (optional) | Alerts, and blocks release if red |
| On AI change | Model evaluation (section 11) with report | Yes, for changes to prompts, models, retrieval, schemas |
| Weekly | Model evaluation on the held-out set, dependency review | Alerts |
| Pre-release | Full suite, load test, restore test (BR), security review items, evaluation report, requirement coverage report | Yes |

### 15.2 Gate rules

| Rule | Value |
|---|---|
| All required checks pass | Required |
| Unit, integration, API and security tests | 100% of the tests run must pass. No skipped security test |
| Critical vulnerabilities in dependencies or images | None allowed. High findings need a documented, time-limited exception |
| Requirement coverage | Every implemented requirement with verification T has a test |
| OpenAPI diff | No breaking change without a version change |
| Migrations | Up, down and drift checks pass |
| Secret scan | Clean |
| Type checking | `mypy` passes. Strict mode on `core`, `ai`, `database` and the memory module |
| Architecture contracts | No `import-linter` violation |
| Accessibility | No serious or critical axe violations |
| AI absolute gates | Section 11.5 |

### 15.3 Coverage requirements (proposed)

Coverage is a floor that finds untested code. It is not evidence of quality, and requirement traceability and the negative controls matter more.

| Scope | Line coverage | Branch coverage |
|---|---|---|
| Backend overall | at least 85% | tracked, no floor in the MVP |
| Critical modules: memory update, permissions, provider policy and gateway, tenancy and session helpers, authentication and token handling, MFA, break-glass, erase and retention functions, retrieval query builder, evidence verification | at least 95% | at least 90% |
| Frontend features (unit and component) | at least 70% | tracked |
| Critical user flows | Covered by the E2E scenarios | n/a |

A pull request cannot lower the coverage of a critical module. Coverage excludes generated code and migrations, and the exclusions are listed in the repository.

## 16. Synthetic data and privacy-safe procedures

| Rule | Detail |
|---|---|
| R1 No real data | No real customer, agent or personal data in the repository, test databases, CI logs, staging or evaluation. Not even "temporarily" |
| R2 Synthetic origin | Every dataset has a manifest entry with `origin: synthetic` and its generation method. The harness refuses a dataset without it |
| R3 Fictional identities | Names are invented. Emails use reserved domains only (`example.com`, `example.org`, `.test`, `.invalid`). Phone numbers use the official example numbers from the phone-number library or a documented fictitious pattern that is checked against each country's numbering plan to avoid real assignments. Addresses and developments are fictional or generic |
| R4 Automated scan | CI scans datasets and fixtures for email addresses outside reserved domains, phone numbers outside the allowed pattern, long digit sequences that look like identity documents, and secrets. A hit fails the build |
| R5 Data class | Evaluation runs set the data class `synthetic`. The gateway enforces policy as in production. A test checks that the harness refuses to send a non-synthetic dataset to a restricted provider |
| R6 Providers | DeepSeek may be used only for synthetic and anonymized test data, and the evaluation harness may use it only on `synthetic` datasets. OpenAI is used the same way. No real data goes to either |
| R7 Model-assisted generation | Models may help to write synthetic conversations, using prompts that contain no real data. Every generated scenario is reviewed by a human before it enters a split |
| R8 Environments | Staging and local environments use synthetic data only. Production data is never copied to any other environment |
| R9 Real data for evaluation (deferred) | Using real pilot conversations for evaluation is not planned. It would need the agent's and the customer's documented permission under the legal review, a documented anonymization assessment, restricted storage outside the repository, deletion on request, and an ADR. Until then it is forbidden |
| R10 Evaluation outputs | Reports contain scenario ids and synthetic text only. They contain no secrets and are stored as CI artifacts with a retention limit |
| R11 Human annotators | Annotators work only on synthetic data |
| R12 Canaries | Leakage tests use unique canary strings that are generated at test time |

## 17. Defects, flaky tests and definition of done

- **Regression tests:** every defect that reaches a merged branch gets a test that fails before the fix and passes after.
- **Flaky tests:** a test that fails intermittently is quarantined, tracked and fixed or removed within a short period (proposed: two weeks). Automatic retries are not used to hide flakiness (E2E may retry once, and the retry is reported).
- **Ownership:** every suite has a named owner.
- **Definition of done for a feature:** code, tests at the right levels with requirement markers, security review of the change, documentation updated, migrations with downgrade or an explicit note, changed files reported, and no known failing test.
- **Test naming:** `test_<behavior>` with the requirement marker. Test names do not contain personal data.

## 18. Test deliverables by phase

| Phase | Test deliverables |
|---|---|
| 1 Foundation | CI pipeline skeleton, test database with the three roles, role-attribute check, health endpoint tests, secret scan, architecture contracts, Clock and FakeProvider |
| 2 Database and authentication | Migration tests, RLS and privilege tests, token tests, MFA and step-up tests (ST-23 to ST-25), authorization matrix generator, ST-01 to ST-09, break-glass and platform separation tests (ST-26, ST-27), negative controls |
| 3 Customers | Normalization, identity and merge tests, customer search tests (ST-28 to ST-30), assigned-customer matrix |
| 4 Conversations | Import limits, parsing, duplicate import, language detection, upload security (ST-11) |
| 5 AI intelligence | Gateway and policy tests, extraction verification tests, first evaluation dataset and harness, first baseline, injection suite (ST-15) |
| 6 Memory | Property tests (I1 to I8), memory scenarios, retrieval tests and evaluation, index tests, re-embedding tests |
| 7 Assistant | Grounding and refusal tests, reference validation, evaluation of answers and hallucination |
| 8 Follow-up | Draft evaluation, no-send tests, status machine tests |
| 9 Briefing and tasks | Briefing evaluation, task and commitment state tests |
| 10 Frontend | Component tests, E2E-01 to E2E-14, accessibility and localization tests |
| 11 Integrations | Integration contract tests when integrations are built |
| 12 Quality and security | Full evaluation report, load and soak, restore tests (BR-01 to BR-08), independent security review, pilot security gate |
| 13 Deployment | Smoke tests on production configuration, log scrubbing on production configuration |

## 19. Critical acceptance tests mapping

| SRS test | Level | Main suite |
|---|---|---|
| CT-01 Budget change | Unit, evaluation | Memory rules, EV-MEM |
| CT-02 Conflicting information | Unit, evaluation | Memory rules, EV-CON |
| CT-03 Missing information | Integration, evaluation | Assistant refusal, EV-ANS |
| CT-04 Wrong customer | Integration, security | ST-16, ST-28, section 10.4 |
| CT-05 Follow-up personalization | Evaluation | EV-DRF |
| CT-06 Source attribution | Integration, evaluation | Reference validation, EV-ANS |
| CT-07 Duplicate import | API, integration | API imports, job idempotency |
| CT-08 Historical correction | Integration, API | Corrections, history preserved |
| CT-09 No context or other tenant | Integration, security | ST-01, ST-02 |
| CT-10 Restricted provider | Integration, security | ST-13 |
| CT-11 Pseudonymized data | Unit, security | Policy tests, ST-13 |
| CT-12 Spanish and Portuguese | Evaluation | EV-EXT, EV-LANG |
| CT-13 Cross-language retrieval | Evaluation | EV-RET |
| CT-14 Injection in messages | Security, evaluation | ST-15, EV-INJ |
| CT-15 Fabricated evidence | Unit, integration | Evidence verification, negative control |
| CT-16 Update of original content | Integration | ST-02 privilege tests, negative control |
| CT-17 Deletion then restore | Resilience | BR-03, BR-04 |
| CT-18 Out-of-order import | Unit, evaluation | Invariant I7, EV-MEM |
| CT-19 AI fact versus verified fact | Unit | Invariant I4 |
| CT-20 Refresh token reuse | API, security | ST-06 |
| CT-21 MFA enforcement | API, security, E2E | ST-23, E2E-01 |
| CT-22 Break-glass controls | Integration, security | ST-26, ST-27 |
| CT-23 Search visibility and non-leakage | API, security | ST-28 to ST-30, E2E-10, E2E-11 |

CT-21 to CT-23 are added to SRS section 9 in the Phase 0.8 patch.

## 20. Open items

| ID | Item | Resolve in |
|---|---|---|
| OPEN-TS1 | Who reviews Spanish and Portuguese datasets (fluent speakers, regional variants) | Before Phase 5 |
| OPEN-TS2 | Load tool: k6 or Locust | Phase 12 |
| OPEN-TS3 | Confirm the performance load model (section 13.1) with the pilot plan | Phase 12 |
| OPEN-TS4 | Dataset growth plan to 100 or more scenarios per language | Phases 5 to 7 |
| OPEN-TS5 | Evaluation cost budget per run and per month | Phase 5 |
| OPEN-TS6 | Choice of judge model and calibration sample size | Phase 5 |
| OPEN-TS7 | Whether mutation testing becomes a gate for critical modules | Phase 12 |
| OPEN-TS8 | Phone-number fixtures: verified fictitious patterns per country | Phase 4 |