#!/usr/bin/env python3
"""Apply the 0.2b documentation patch to docs/PRD.md and docs/DATABASE.md.

Run from the repository root:
    python3 scripts/patch_docs_0_2b.py --dry-run [--diff]
    python3 scripts/patch_docs_0_2b.py --apply
    python3 scripts/patch_docs_0_2b.py --restore .doc_backups/<timestamp>

Safety rules:
  * Every edit must match exactly once in its file. If any edit in either file
    fails, nothing is written to either file.
  * Both originals are backed up before any write.
  * Files are written through temporary files and swapped in with os.replace.
    If the second swap or the final verification fails, both files are restored.
  * Dry-run never writes anything.
Exit codes: 0 ok, 1 validation failed, 2 write failed (restored),
            3 verification failed (restored), 4 already applied or file missing.
"""

import argparse
import difflib
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PRD_PATH = Path("docs/PRD.md")
DB_PATH = Path("docs/DATABASE.md")
BACKUP_ROOT = Path(".doc_backups")

PRD_GUARD = "Draft v0.3 (Phase 0.2, updated with the Architecture Decision Addendum)"
DB_GUARD = "Draft v0.2 (Phase 0.1, updated with the Architecture Decision Addendum and review)"
# DB_GUARD = "Draft v0.2 (Phase 0.1, updated with the Architecture Decision Addendum)"

# ---------------------------------------------------------------------------
# PRD.md edits
# ---------------------------------------------------------------------------
PRD_EDITS = []

PRD_EDITS.append((
    "P01 status line",
    """Status: Draft v0.2 (Phase 0.2), pending review.""",
    """Status: Draft v0.3 (Phase 0.2, updated with the Architecture Decision Addendum), pending review.""",
))

PRD_EDITS.append((
    "P02 sources line",
    """Sources: REIA Full URD and the Market Expansion Addendum. Where the two differ, the Addendum wins (target markets, languages, currencies).""",
    """Sources: REIA Full URD, the Market Expansion Addendum and the Architecture Decision Addendum. Where documents differ, the later addendum wins.""",
))

PRD_EDITS.append((
    "P03 market table header",
    """| Market | Country | Currency | Initial languages | Notes |""",
    """| Market | Country (ISO code) | Currency | Initial languages | Notes |""",
))

PRD_EDITS.append((
    "P04 Dubai row (city vs country)",
    """| Dubai | AE | AED | English (Arabic planned) | Not the exclusive market |""",
    """| Dubai | United Arab Emirates (AE) | AED | English (Arabic planned) | Dubai is a city, not a country; the jurisdiction is the UAE. Not the exclusive market |""",
))

PRD_EDITS.append((
    "P05 Spain row",
    """| Spain | ES | EUR | Spanish, English | GDPR applies |""",
    """| Spain | Spain (ES) | EUR | Spanish, English | GDPR applies |""",
))

PRD_EDITS.append((
    "P06 Portugal row",
    """| Portugal | PT | EUR | Portuguese, English | GDPR applies |""",
    """| Portugal | Portugal (PT) | EUR | Portuguese, English | GDPR applies |""",
))

PRD_EDITS.append((
    "P07 market sequencing",
    """- Market research and pilot feedback are kept separately per country.""",
    """- Market research and pilot feedback are kept separately per country.

### Market sequencing (confirmed product decisions)

- First pilot market: Dubai (United Arab Emirates, country code AE). Secondary validation markets: Spain and Portugal.
- REIA remains a single international product supporting all three markets.
- No pilot customer has been secured. A Dubai realtor took part in an initial discovery discussion. This is not a pilot commitment and not a paying customer, and it must not be presented as one.
- Pilot target: 2 to 3 independent agents or small agency teams.
- Spain and Portugal are validated separately before any commercial expansion there.""",
))

PRD_EDITS.append((
    "P08 I18N-1",
    """| I18N-1 | Supported content languages: English, Spanish, Portuguese. Arabic and others later | M |""",
    """| I18N-1 | UI languages at launch: English, Spanish, Portuguese. Conversation processing at launch: English, Spanish, Portuguese. An Arabic UI is not required at launch | M |""",
))

PRD_EDITS.append((
    "P09 I18N-9 plus new rows",
    """| I18N-9 | No Dubai-specific assumptions hardcoded in core logic | M |""",
    """| I18N-9 | No Dubai-specific assumptions hardcoded in core logic | M |
| I18N-10 | Frontend architecture supports future right-to-left (RTL) layouts: logical CSS properties, no hardcoded left or right assumptions | M |
| I18N-11 | Unicode (UTF-8) storage and processing everywhere; no English-only assumptions in database fields or interfaces | M |
| I18N-12 | Conversation language detection is separate from UI language. Arabic conversation processing is a future capability, evaluated independently from Arabic UI localization | L |""",
))

PRD_EDITS.append((
    "P10 section 7.14 AI provider governance",
    """## 8. Cross-cutting requirements""",
    """### 7.14 AI provider governance (PROV)

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

## 8. Cross-cutting requirements""",
))

PRD_EDITS.append((
    "P11 section 8.4 retention, deletion and ledger",
    """## 9. MVP definition""",
    """### 8.4 Data retention, deletion and subject rights (proposed defaults)

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

## 9. MVP definition""",
))

PRD_EDITS.append((
    "P12 pilot target (section 14)",
    """Pilot target: 3 to 5 authorized real estate professionals. Nothing in this document counts as market validation.""",
    """Pilot target: 2 to 3 independent agents or small agency teams, starting in Dubai. No pilot customer is confirmed; a Dubai discovery discussion has taken place, which is not a pilot commitment. Spain and Portugal are validated separately before commercial expansion. Nothing in this document counts as market validation.""",
))

PRD_EDITS.append((
    "P13 assumption A5 hosting region",
    """| A5 | EU-region hosting is acceptable for all three markets | Reviewed in compliance assessment |""",
    """| A5 | The chosen hosting region is acceptable for each market. The Dubai pilot comes first, so UAE PDPL cross-border transfer rules must be assessed before a region is chosen | Reviewed in the compliance assessment; no hosting region is assumed in DATABASE.md or TAD.md |""",
))

PRD_EDITS.append((
    "P14 assumption A7",
    """| A6 | Official WhatsApp and Pipedrive APIs permit the planned use | Investigated in Phase 11 before any commitment |""",
    """| A6 | Official WhatsApp and Pipedrive APIs permit the planned use | Investigated in Phase 11 before any commitment |
| A7 | OpenAI API data controls and retention settings are acceptable for customer conversations | Reviewed before production, including Zero Data Retention eligibility (PROV-9, ADR-010) |""",
))

PRD_EDITS.append((
    "P15 section 16 decision log",
    """## 16. Open questions

1. Which pilot market goes first, and are pilot agents already identified?
2. Final retention periods per country (PRIVACY.md).
3. Which LLM provider handles which task, and is DeepSeek acceptable for customer data under each jurisdiction's rules?
4. Is Arabic needed in the UI at launch, or only later?
5. Embedding model and dimension (ADR-007).""",
    """## 16. Decision log and open questions

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
7. The separate append-only store for the deletion ledger and the restore runbook (defined in TAD.md and DEPLOYMENT.md, tested in Phase 12).""",
))
# ---------------------------------------------------------------------------
# DATABASE.md edits
# ---------------------------------------------------------------------------
DB_EDITS = []

DB_EDITS.append((
    "D01 status line",
    """Status: Draft v0.1 (Phase 0.1), pending review.""",
    """Status: Draft v0.2 (Phase 0.1, updated with the Architecture Decision Addendum and review), pending review.""",
))

DB_EDITS.append((
    "D02 ER diagram provider settings",
    """  organizations ||--o{ ai_runs : records""",
    """  organizations ||--o{ ai_runs : records
  organizations ||--o{ organization_provider_settings : configures""",
))

DB_EDITS.append((
    "D03 role reia_migrator and reia_maintenance",
    """- `reia_migrator`: owns all tables, runs Alembic migrations. Never used by the running application.""",
    """- `reia_migrator`: owns all tables and runs Alembic migrations and nothing else. Used only by the deployment pipeline. Never used by the running application or by scheduled jobs.
- `reia_maintenance`: used only by the scheduled retention and deletion jobs. `NOSUPERUSER NOBYPASSRLS`, not a table owner. It has no direct `DELETE` on any table. It executes the controlled functions in section 7.2 and works per tenant through `app.current_org_id`, like the application.""",
))

DB_EDITS.append((
    "D04 role reia_app",
    """- `reia_app`: used by FastAPI. `NOSUPERUSER NOBYPASSRLS`. Not the table owner. Has only the privileges listed in §7.""",
    """- `reia_app`: used by FastAPI. `NOSUPERUSER NOBYPASSRLS`. Not the table owner. Has only the privileges listed in section 7 and no `DELETE` on any table.""",
))

DB_EDITS.append((
    "D05 organizations lifecycle status",
    """- settings* jsonb default `'{}'` (country-config overrides, validated by Pydantic)""",
    """- settings* jsonb default `'{}'` (country-config overrides, retention overrides; validated by Pydantic)
- lifecycle_status* (`active`, `dormant`, `terminated`; default `active`), terminated_at, export_window_ends_at""",
))

DB_EDITS.append((
    "D06 embedding columns",
    """- embedding* `vector(1536)` (dimension set by ADR-007), embedding_model*, embedding_dimension*""",
    """- embedding* `vector(1536)` (fixed by ADR-007), embedding_provider*, embedding_model*, embedding_model_version*, embedding_dimension* (CHECK = 1536)
- embedding_model_version is a configured label (setting `EMBEDDING_MODEL_VERSION`, initial value `v1`), because a provider's model name can stay the same when its behavior changes""",
))

DB_EDITS.append((
    "D07 embedding uniqueness",
    """- UNIQUE (source_type, source_id, chunk_index, embedding_model)""",
    """- UNIQUE (source_type, source_id, chunk_index, embedding_model, embedding_model_version)
- A different model or dimension never shares this column or its index. A model change follows the procedure in section 6.1.""",
))

DB_EDITS.append((
    "D08 ai_runs data class",
    """- provider*, model*, prompt_name*, prompt_version*, input_hash* (no raw prompt text by default)""",
    """- provider*, model*, endpoint (API endpoint used), data_class* (`public`, `synthetic`, `anonymized`, `pseudonymized`, `identifiable`), prompt_name*, prompt_version*, input_hash* (no raw prompt text by default)""",
))

DB_EDITS.append((
    "D09 ai_runs status",
    """- status* (`succeeded`, `schema_invalid`, `provider_error`, `timeout`), error_code, error_details, created_at*""",
    """- status* (`succeeded`, `schema_invalid`, `provider_error`, `timeout`, `blocked_by_policy`), error_code, error_details, created_at*""",
))

DB_EDITS.append((
    "D10 provider settings and deletion ledger tables",
    """**integrations**""",
    """**organization_provider_settings** (AI provider policy per organization and task)
- id*, organization_id*
- task* (`extract`, `summarize`, `compare_facts`, `answer`, `draft`, `briefing`, `translate`, `embed`)
- provider*, model*, enabled* (default true)
- allowed_data_classes* (`text[]`, subset of `public`, `synthetic`, `anonymized`, `pseudonymized`, `identifiable`)
- approval_reference, approved_by, approved_at (required when `allowed_data_classes` includes `pseudonymized` or `identifiable` and the provider is flagged restricted in code)
- created_at*, updated_at*
- UNIQUE (organization_id, task)
- The restricted-provider list lives in code (`app/ai/provider_policy.py`). Restricted providers are deny-by-default for `pseudonymized` and `identifiable` data. A request is sent only when all three agree: (1) the code policy, (2) the deployment configuration (`AI_RESTRICTED_PROVIDERS_ALLOWED_FOR_CUSTOMER_DATA`, empty by default; credentials of a restricted provider are not provisioned in production unless approved), and (3) this row. This row can only narrow what code and deployment allow, never widen it.
- Pseudonymized data is never treated as anonymized automatically. It is handled as `identifiable` unless a documented anonymization assessment says otherwise.
- Every AI call, including embedding calls, is checked before sending. The result is recorded in `ai_runs` (`provider`, `model`, `endpoint`, `data_class`). Blocked calls are recorded with `status = 'blocked_by_policy'`.

**deletion_ledger** (append-only; identifiers only; no foreign key to organizations, so deleting a workspace cannot delete its ledger rows)
- id*, organization_id* (plain uuid)
- subject_type* (`customer`, `workspace`), subject_id*
- request_reference*, requested_by, verified_by*, verified_at*
- status* (`verified`, `executing`, `executed`, `failed`), executed_at
- backup_expiry_at (the earliest date after which no backup can contain the subject, computed from the backup rotation)
- created_at*
- No personal data is stored. Rows are also exported to an append-only store that is separate from the database backups (ADR-011), so a restore cannot roll the ledger back.
- RLS: `reia_app` sees only its current organization. A dedicated policy lets `reia_maintenance` list pending entries across organizations, because the table holds identifiers only. Every other table stays tenant-scoped for it.

**integrations**""",
))

DB_EDITS.append((
    "D11 embedding index definition",
    """- memory_embeddings: btree `(organization_id, customer_id)` plus HNSW `USING hnsw (embedding vector_cosine_ops)`.""",
    """- memory_embeddings: btree `(organization_id, customer_id)` plus a partial HNSW index for the active model and version: `USING hnsw (embedding vector_cosine_ops) WHERE embedding_model = 'text-embedding-3-small' AND embedding_model_version = 'v1'`. The predicate uses the real configured values, never a placeholder. Retrieval queries always filter on the active model and version with inline literals taken from an allowlist in configuration, because a parameterized predicate can stop the planner from using a partial index. A test checks the plan with EXPLAIN.""",
))

DB_EDITS.append((
    "D12 section 6.1 re-embedding procedure",
    """## 7. Immutability, privileges and retention""",
    """### 6.1 Embedding model versions, re-embedding and index migration

Configuration: `EMBEDDING_PROVIDER=openai`, `EMBEDDING_MODEL=text-embedding-3-small`, `EMBEDDING_DIMENSION=1536`, `EMBEDDING_MODEL_VERSION=v1`. The label `v1` is a REIA-maintained label for the initial configuration, and the partial index in section 6 uses these same literal values. At startup the application checks that the partial index for the active label exists and refuses to serve retrieval if it does not.

Procedure for changing the model, dimension or version label:
1. Record a new ADR that supersedes ADR-007, with the reason and the quality thresholds the new model must meet.
2. Add the new label to configuration as inactive. A different dimension needs a new column or table, never the existing `vector(1536)` column.
3. Add an Alembic migration that creates the new partial HNSW index (`CREATE INDEX CONCURRENTLY`, run outside a transaction block).
4. Run the idempotent `re_embed` job in batches. It is rate limited, passes the provider-policy check (ADR-010) and records cost in `ai_runs`. The unique key includes model and version, so reruns never duplicate rows.
5. Run the evaluation set (English, Spanish, Portuguese, including cross-language queries) against the new label and compare with the recorded baseline. The switch is blocked unless the thresholds from step 1 are met.
6. Switch the active label through configuration in a normal deployment.
7. Keep the old vectors and index for a rollback window. Rollback means setting the previous label active again.
8. After verification, a later migration drops the old index and the old vectors.

Tests (listed in TESTING.md):
- Inserting a vector with a wrong dimension is rejected by the database.
- A query without the active model and version filter fails a unit test of the query builder.
- EXPLAIN shows the partial index is used for the retrieval query.
- The `re_embed` job is idempotent.
- The retrieval-quality regression test runs on every model or label change and compares the results with the stored baseline.

## 7. Immutability, privileges and retention""",
))

DB_EDITS.append((
    "D13 least privilege for DELETE",
    """- Other tables: normal `SELECT, INSERT, UPDATE`. `DELETE` only where listed in §7.3.""",
    """- Other tables: `SELECT, INSERT, UPDATE` as the module needs. `reia_app` has no `DELETE` on any table. Expired or consumed rows, such as tokens, are removed by the maintenance functions in section 7.2.
- `deletion_ledger`: `reia_app` has `INSERT` and `SELECT` only (it records verified deletion requests and cannot change or delete them). `reia_maintenance` has `SELECT` and column-level `UPDATE (status, executed_at, backup_expiry_at)`.
- `reia_maintenance` has `EXECUTE` on `erase_customer`, `erase_workspace`, `purge_expired_audit_logs` and `purge_expired_tokens`, and no other write privilege.""",
))

DB_EDITS.append((
    "D14 erase functions",
    """Hard deletion of a customer's data (data-subject erasure request, account deletion) runs through a single `SECURITY DEFINER` function, `erase_customer(org_id, customer_id)`, owned by `reia_migrator`. It:""",
    """Hard deletion runs only through `SECURITY DEFINER` functions owned by `reia_migrator`: `erase_customer(org_id, customer_id)` for one customer and `erase_workspace(org_id)` for a whole workspace. The deletion job calls them under `reia_maintenance`. `EXECUTE` is revoked from `PUBLIC` and granted to `reia_maintenance` only, and each function sets a fixed `search_path`. `erase_customer`:""",
))

DB_EDITS.append((
    "D15 erase step 2",
    """2. Writes an `audit_logs` row (ids only).""",
    """2. Writes an `audit_logs` row (ids only) and marks the matching `deletion_ledger` entry executed.""",
))

DB_EDITS.append((
    "D16 erase step 3",
    """3. Cannot be called for a customer outside the current tenant.""",
    """3. Raises an error unless `app.current_org_id` equals `org_id`, so it cannot act outside the tenant context set by the job. `erase_workspace` performs the same check and also removes the organization's members, integrations and settings. Neither function touches `deletion_ledger` rows except to mark them executed.""",
))

DB_EDITS.append((
    "D17 retention section 7.3",
    """- Retention periods per jurisdiction are defined in PRIVACY.md and are not guessed here.""",
    """- Proposed product defaults (PRD.md section 8.4 and PRIVACY.md are authoritative; these are NOT statutory periods under UAE PDPL or GDPR, and no legally verified retention requirement exists yet): customer records and conversations are kept while the workspace is active; production deletion within 30 days of a verified deletion request; backups expire within a further 35 days; security and audit logs are kept for 12 months; legal holds apply only where legally required, documented and access-restricted.
- Workspace lifecycle is stored in `organizations.lifecycle_status`: `active`, `dormant` (inactive for a configurable period, owner notified, never deleted automatically) and `terminated` (export window, then the deletion process). The dormant period and the export window are not set yet.
- Deletion ledger: every verified deletion request is written to `deletion_ledger` before anything is deleted, and the ledger is exported to an append-only store separate from the database backups. Backups are immutable and are not edited per customer; they expire within 35 days under normal rotation. After any restore, the restore procedure re-applies every ledger entry executed after the snapshot time before users are let back in, so a restored backup cannot bring deleted data back. Phase 12 tests this.
- Retention is configurable per organization through `organizations.settings` (validated by Pydantic) where a contract or law requires different periods.
- Audit log retention (12 months) is enforced by `purge_expired_audit_logs`, run by `reia_maintenance`. `reia_app` has no `DELETE` on `audit_logs`.
- Technical logs and `audit_logs.metadata` contain identifiers only, never message content or contact details.""",
))

DB_EDITS.append((
    "D18 ADR-007",
    """- ADR-007 (pending): embedding model and dimension. Default `text-embedding-3-small` at 1536. Confirm current options in Phase 6.""",
    """- ADR-007 (confirmed): OpenAI `text-embedding-3-small`, 1536 dimensions, pgvector, cosine similarity. Model, dimension and version label are stored with every embedding, and re-embedding follows section 6.1. Retrieval quality for English, Spanish and Portuguese is measured in Phase 6. Changing the model requires a new ADR.""",
))

DB_EDITS.append((
    "D19 ADR-010, ADR-011, ADR-014",
    """- ADR-009: Identity: one active identifier belongs to one customer. Merges are manual and recorded.""",
    """- ADR-009: Identity: one active identifier belongs to one customer. Merges are manual and recorded.
- ADR-010 (confirmed): AI provider policy. Five distinct data classes; restricted providers are deny-by-default for `pseudonymized` and `identifiable` data; enforced in backend code, deployment configuration and per-organization settings; embedding requests are included.
- ADR-011 (proposed defaults, legal review required): retention defaults, workspace lifecycle, deletion ledger and backup propagation (sections 5.6 and 7.3).
- ADR-014 (proposed): database roles `reia_migrator`, `reia_app` and `reia_maintenance`; the application role has no `DELETE` (sections 4.1 and 7).""",
))

DB_EDITS.append((
    "D20 change table rows",
    """| Added country, locale, currency, timezone to organizations | International configuration |""",
    """| Added country, locale, currency, timezone to organizations | International configuration |
| Added `organization_provider_settings`; added `endpoint` and `data_class` to `ai_runs`; added `blocked_by_policy` status | Provider restrictions and logging (ADR-010) |
| Added `deletion_ledger` and `organizations.lifecycle_status`; added the `reia_maintenance` role; removed `DELETE` from `reia_app` | Deletion propagation to backups and least privilege (ADR-011, ADR-014) |
| Added `embedding_provider` and `embedding_model_version`; partial HNSW index per model and version | ADR-007; safe re-embedding |""",
))

DB_EDITS.append((
    "D21 open items",
    """- Final retention periods per country (PRIVACY.md).""",
    """- Legal verification of the retention defaults per country (PRIVACY.md). The values in section 7.3 are proposals. The dormant-workspace period and the export window are not set yet.
- Storage location of the separate append-only deletion ledger copy and the restore runbook (TAD.md, DEPLOYMENT.md).""",
))
# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
def read_text(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def analyse(text, edits):
    results = []
    for number, (label, old, new) in enumerate(edits, start=1):
        count = text.count(old)
        position = text.find(old) if count == 1 else -1
        results.append(
            {"n": number, "label": label, "old": old, "new": new, "count": count, "pos": position}
        )
    problems = [f"edit {r['n']} ({r['label']}) matched {r['count']} times, expected 1"
                for r in results if r["count"] != 1]
    if not problems:
        spans = sorted((r["pos"], r["pos"] + len(r["old"]), r["label"]) for r in results)
        for (_, end_a, label_a), (start_b, _, label_b) in zip(spans, spans[1:]):
            if end_a > start_b:
                problems.append(f"edits '{label_a}' and '{label_b}' overlap")
    return results, problems


def build(text, results):
    out = text
    for r in sorted(results, key=lambda item: item["pos"], reverse=True):
        out = out[: r["pos"]] + r["new"] + out[r["pos"] + len(r["old"]):]
    return out


def verify(text, results, guard):
    if guard not in text:
        return False
    return all(r["new"] in text for r in results)


def report(name, results, problems):
    print(f"=== {name} ===")
    for r in results:
        status = "OK  " if r["count"] == 1 else "FAIL"
        removed = r["old"].count("\n") + 1
        added = r["new"].count("\n") + 1
        print(f"[{status}] {r['n']:02d} {r['label']} (matches: {r['count']}; "
              f"replaces {removed} line(s) with {added})")
    for p in problems:
        print(f"  PROBLEM: {p}")
    print(f"  Safe to update: {'YES' if not problems else 'NO'}\n")


def show_diff(name, before, after):
    diff = difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile=f"{name} (current)", tofile=f"{name} (proposed)", lineterm="",
    )
    print("\n".join(diff))
    print()


def write_tmp(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())

def restore_from(directory):
    for path in (PRD_PATH, DB_PATH):
        source = directory / path.name
        if not source.is_file():
            raise FileNotFoundError(f"backup file missing: {source}")
    for path in (PRD_PATH, DB_PATH):
        shutil.copy2(directory / path.name, path)


def main():
    parser = argparse.ArgumentParser(description="Apply the 0.2b documentation patch.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="report only (default)")
    mode.add_argument("--apply", action="store_true", help="validate, back up, then write")
    mode.add_argument("--restore", metavar="DIR", help="restore both files from a backup directory")
    parser.add_argument("--diff", action="store_true", help="print the full proposed diff")
    args = parser.parse_args()

    if args.restore:
        try:
            restore_from(Path(args.restore))
        except Exception as error:
            print(f"Restore failed: {error}")
            return 4
        print(f"Restored {PRD_PATH} and {DB_PATH} from {args.restore}")
        return 0

    for path in (PRD_PATH, DB_PATH):
        if not path.is_file():
            print(f"Missing file: {path}. Run this script from the repository root.")
            return 4

    prd_text = read_text(PRD_PATH)
    db_text = read_text(DB_PATH)

    if PRD_GUARD in prd_text or DB_GUARD in db_text:
        print("This patch looks already applied (version marker found). Nothing to do.")
        return 4

    prd_results, prd_problems = analyse(prd_text, PRD_EDITS)
    db_results, db_problems = analyse(db_text, DB_EDITS)
    report(str(PRD_PATH), prd_results, prd_problems)
    report(str(DB_PATH), db_results, db_problems)
    safe = not prd_problems and not db_problems
    print(f"BOTH FILES SAFE TO UPDATE: {'YES' if safe else 'NO'}\n")

    if not safe:
        print("Nothing was written to either file.")
        return 1

    prd_new = build(prd_text, prd_results)
    db_new = build(db_text, db_results)

    if args.diff:
        show_diff(str(PRD_PATH), prd_text, prd_new)
        show_diff(str(DB_PATH), db_text, db_new)

    if not args.apply:
        print("Dry run only. Nothing was written. Use --apply to update both files.")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = BACKUP_ROOT / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(PRD_PATH, backup_dir / PRD_PATH.name)
    shutil.copy2(DB_PATH, backup_dir / DB_PATH.name)
    print(f"Backups written to {backup_dir}")

    pid = os.getpid()
    prd_tmp = PRD_PATH.with_name(f"{PRD_PATH.name}.tmp{pid}")
    db_tmp = DB_PATH.with_name(f"{DB_PATH.name}.tmp{pid}")
    try:
        write_tmp(prd_tmp, prd_new)
        write_tmp(db_tmp, db_new)
        os.replace(prd_tmp, PRD_PATH)
        os.replace(db_tmp, DB_PATH)
    except Exception as error:
        print(f"Write failed: {error}. Restoring both files from {backup_dir}")
        for tmp in (prd_tmp, db_tmp):
            if tmp.exists():
                tmp.unlink()
        restore_from(backup_dir)
        return 2

    if not (verify(read_text(PRD_PATH), prd_results, PRD_GUARD)
            and verify(read_text(DB_PATH), db_results, DB_GUARD)):
        print(f"Verification failed. Restoring both files from {backup_dir}")
        restore_from(backup_dir)
        return 3

    print("Both files updated and verified.")
    print(f"To undo: python3 scripts/patch_docs_0_2b.py --restore {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())