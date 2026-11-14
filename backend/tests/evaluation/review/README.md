# Language Review Kit: README

Path: `backend/tests/evaluation/review/README.md`
Kit version: v0.2 (work in progress). Document version: 0.2.0. Date: 2026-11-14.
Workstream: OPEN-TS1 (Spanish and Portuguese language validation).
Owner: project owner. This file is written for the owner. Reviewers receive `reviewer_guide.md` instead (planned).

## 1. Purpose and scope

REIA is tested on synthetic conversations in English, Spanish and Portuguese. This workstream checks that the **text of those conversations** is natural, regionally correct, realistic and internally consistent, using AI checks first and independent native or fluent professionals second.

In scope:
- Spanish as used in Spain (locale `es-ES`).
- Portuguese as used in Portugal (locale `pt-PT`).
- English as the baseline language, including the Dubai market.
- Synthetic scenarios only: WhatsApp chats, call notes and similar texts about fictional customers.

Out of scope for this workstream:
- Measuring how well REIA extracts, remembers, retrieves or drafts. That is **technical AI evaluation** (TESTING.md section 11). It stays separate (section 2).
- Validating gold labels. That is annotation quality, a separate check.
- Reviewing REIA's generated outputs (drafts, answers, briefings) in Spanish or Portuguese. That needs its own kit later.
- Legal, tax or financial advice. Reviewers check how terms are used in language, not whether the law is applied correctly.
- Latin American Spanish and Brazilian Portuguese. They are not part of the baseline.

## 2. Human language validation and technical evaluation are different things

| | Human language validation (this kit) | Technical AI evaluation |
|---|---|---|
| Question | Is the synthetic text natural, regionally correct, realistic and consistent? | Does REIA extract, remember, retrieve and draft correctly? |
| What is checked | The **inputs**: conversations and notes | The system's **behavior and outputs** |
| Who checks | Native or fluent professionals, after AI checks | Automated scorers against gold labels, plus a small human sample |
| Result | Ratings, an issue log, corrections, scenario status | Precision, recall, history preservation, retrieval and grounding metrics |
| When | Before a scenario enters a dataset split | On every prompt, model or retrieval change |
| What it cannot show | Whether REIA performs well | Whether the test language is natural |

Rules that keep them apart:
1. Reviewer ratings are never used as AI performance metrics.
2. Evaluation reports state the validation level of the scenarios they used (section 5.3).
3. A good evaluation score on unvalidated text says nothing about real-world language quality.

## 3. Approved decisions

| # | Decision | Source |
|---|---|---|
| 1 | Hybrid approach: AI-assisted synthetic datasets, checks by several AI models, then independent review by native or fluent professionals from the owner's professional network in Spain and Portugal | OPEN-TS1 decision |
| 2 | Spanish means European Spanish (Spain, `es-ES`). Portuguese means European Portuguese (Portugal, `pt-PT`). English is the baseline | OPEN-TS1 decision |
| 3 | AI approval is never presented as independent human validation | OPEN-TS1 decision |
| 4 | No reviewer is confirmed. Nobody is assumed to have agreed | OPEN-TS1 decision |
| 5 | No freelancers and no review expenses without further approval | OPEN-TS1 decision |
| 6 | Reviewers read each scenario and answer comprehension questions (**blind comprehension**) before they see the intended meaning | Audit approval |
| 7 | First round: 5 scenarios per language | Audit approval |
| 8 | English baseline has parallel core scenarios (same designs as Spanish and Portuguese) and Dubai-specific scenarios | Audit approval |
| 9 | Planned kit files: README, reviewer guide, improved feedback form, AI-check log, corrections log, and one packet per language | Audit approval |
| 10 | Technical AI evaluation stays separate from human language validation | Audit approval |
| 11 | v0.1 files are preserved untouched. They are archived only after v0.2 is complete and verified and the owner explicitly approves | Audit approval |
| 12 | No AI language correction counts as native-validated until actual human feedback is received | Audit approval |
| 13 | REIA architecture, target markets and roadmap are unchanged | Audit approval |

## 4. Kit contents and status

Status values: **Created**, **Planned**, **Preserved** (v0.1, unchanged). This table is the record of what exists. It is updated by the owner when a file is saved, and it must never claim a file that does not exist.

### 4.1 Version 0.2

| Path (under `backend/tests/evaluation/review/`) | Purpose | Status |
|---|---|---|
| `README.md` | This file: process, statuses, privacy, checklists | Created |
| `reviewer_guide.md` | Instructions for reviewers: what to do, what not to do, time estimate, confidentiality, how to return feedback | Planned |
| `reviewer_feedback_form.md` | Improved feedback form: blind comprehension answers, ratings, issue log with severity, region flags, term preferences | Planned |
| `packets/packet_es-ES.md` | 5 Spanish (Spain) scenarios | Planned |
| `packets/packet_pt-PT.md` | 5 Portuguese (Portugal) scenarios | Planned |
| `packets/packet_en.md` | English baseline: parallel core scenarios and Dubai-specific scenarios | Planned |
| `provenance/ai_check_log.md` | Record of which AI models checked what, and what they found | Planned |
| `rounds/round-01/corrections_log.md` | Record of every proposed correction and what was decided | Planned |

### 4.2 Version 0.1 (preserved)

| Path | Status |
|---|---|
| `reviewer_packet_es-ES.md` | Preserved, unchanged |
| `reviewer_packet_pt-PT.md` | Preserved, unchanged |
| `reviewer_feedback_template.md` | Preserved, unchanged |

The v0.1 files are not moved, edited or deleted. They have known gaps (no blind comprehension, 3 scenarios, no process documents). They must not be sent to reviewers. Archiving into `archive/v0.1/` needs the owner's explicit approval after v0.2 is complete and verified (section 12).

## 5. Terms, statuses and validation levels

### 5.1 Terms

| Term | Meaning |
|---|---|
| Synthetic | Invented for testing. No real person, client, number, address or transaction |
| Native or fluent reviewer | A professional who speaks the target variant natively or fluently and is willing to review. Preferred order: native with real estate experience, fluent with real estate experience, native without, fluent without |
| Blind comprehension | The reviewer reads the scenario and writes what they understood (for example the budget, requirements and promises) **before** seeing the intended meaning |
| Intended meaning | The facts and intentions the scenario was written to express. Shown to the reviewer only after the blind comprehension answers are written |
| Choice item | An A/B question used where the AI is unsure which wording is more natural. The reviewer picks one or proposes another |
| Blocker | Makes the text unusable, wrong in language variant, misleading or impossible to understand |
| Major | Clearly unnatural, wrong term, or inconsistent fact |
| Minor | Style or preference |
| Required | A change the reviewer says is needed for the text to be correct or natural |
| Preference | A change the reviewer would make but the text is acceptable without |

### 5.2 Scenario status

Each scenario has exactly one status. A scenario moves forward only when the condition is met and recorded.

| Status | Meaning | Condition to reach it |
|---|---|---|
| `draft` | Written, not yet checked | Generated or written |
| `ai_checked` | Checked by AI models only | At least two different AI models checked it. Findings are logged in `ai_check_log.md` and each is fixed, declined or sent to reviewers as a choice item |
| `owner_checked` | Checked by the owner | The owner confirmed: no real data, plausible situation, facts consistent (dates, weekdays, amounts, names) |
| `native_reviewed` | Reviewed by a human native or fluent professional | At least one reviewer returned feedback, every issue is triaged in the corrections log, and accepted corrections are applied |
| `accepted` | Ready to be used in a dataset split | Acceptance criteria in section 9 are met and the owner's decision is recorded |
| `needs_rework` | Not usable yet | A blocker or an unresolved region-variant issue exists |

`native_reviewed` means that a review took place and its results were handled. It does not mean the text is perfect.

### 5.3 Validation level (used in every report)

| Level | Meaning | Wording allowed |
|---|---|---|
| L0 | Not checked | "unchecked" |
| L1 | AI-checked only | "AI-checked, not human-validated" |
| L2 | Owner-checked | "owner-checked, not native-validated" |
| L3 | Native or fluent human reviewed | "reviewed by a native or fluent professional" (never "validated" without the review) |

A report must never describe L0 to L2 text as human-validated.

### 5.4 Correction status

Used in `corrections_log.md`.

| Status | Meaning |
|---|---|
| `ai_suggested` | Proposed by an AI model (including AI audits). **Not validated** |
| `reviewer_confirmed` | A human reviewer confirmed it |
| `reviewer_proposed` | A human reviewer proposed it |
| `reviewer_rejected` | A human reviewer rejected it |
| `owner_applied` | The owner applied it to the scenario |
| `owner_declined` | The owner declined it, with a reason |

Rules:
1. Only `reviewer_confirmed` and `reviewer_proposed` corrections count as human feedback.
2. An AI correction may be applied only as provisional. The scenario stays below L3 and the log says it is unvalidated. Better, an uncertain AI correction is sent to reviewers as a choice item.
3. When a human reviewer disagrees with an AI correction, the human feedback is recorded and the owner decides. The owner may disagree with a reviewer, but the reason is recorded.
4. If several reviewers disagree with each other, both views are recorded and the owner decides. The disagreement is also noted as a variant or style difference.

## 6. Roles

| Role | Does | Does not |
|---|---|---|
| Project owner | Runs the process, checks privacy and plausibility, contacts reviewers, triages corrections, makes final decisions, keeps the private tracker | Treat AI approval as human validation |
| AI assistants | Generate scenarios, run language and consistency checks, suggest corrections | Approve scenarios, validate language, or see real data |
| Reviewers | Read scenarios, answer comprehension questions, rate, flag issues, suggest corrections, choose between variants | Judge AI performance, give legal or financial advice, share the packet publicly |

## 7. Workflow

One round follows these steps. Each step has an output. A step is not skipped.

| # | Step | Output |
|---|---|---|
| 1 | **Plan the round.** Fix the scenario list, the split of each scenario and the packet version | Scenario table in the packet |
| 2 | **Generate** scenarios with AI assistance. Prompts contain no real data. Data class is `synthetic` | Scenarios at `draft` |
| 3 | **AI check** with at least two different models. Check grammar, regional variant, real estate terminology, consistency of numbers and dates, and plausibility. Record every model, prompt and finding | `ai_check_log.md`, scenarios at `ai_checked` |
| 4 | **Owner check** for privacy, plausibility and consistency (section 8 checklist) | Scenarios at `owner_checked` |
| 5 | **Prepare packets.** Comprehension questions come first, intended meaning in a separate part. Choice items for uncertain wording | Packets |
| 6 | **Invite reviewers** individually (section 10). Nobody is assumed to agree | Private tracker updated |
| 7 | **Collect feedback** privately using the feedback form. Redact anything personal | Feedback saved without personal data |
| 8 | **Triage** every issue in the corrections log: classify, decide, give a reason | `corrections_log.md` |
| 9 | **Apply** the approved corrections. Increase the scenario revision number | Scenarios revised |
| 10 | **AI re-check** the revised text. Record it separately. It does not replace the human review | `ai_check_log.md` updated |
| 11 | **Update status.** Move scenarios to `native_reviewed` or `accepted` only when the conditions are met | Status table updated |
| 12 | **Close the round.** Write a short round report: counts, reviewer types (pseudonymous), decisions, limitations, what is still unreviewed | Round report in `rounds/round-01/` |

### 7.1 Splits and tuning

- Scenarios in the first round belong to the **development split** (TESTING.md section 11.2). They will change as reviewers give feedback, and tuning may use them.
- Held-out scenarios are reviewed in a later round. Their review corrects the language only. Findings on held-out scenarios are never used to tune prompts or parameters against those same scenarios.
- Every change to a held-out scenario is logged and creates a new dataset version.

### 7.2 Scenario identity and revisions

- Packet scenario IDs are stable: `ES-01` to `ES-05`, `PT-01` to `PT-05`, `EN-01` to `EN-05` (parallel core) and `EN-D01`, `EN-D02`, and so on (Dubai-specific).
- Every scenario text has a revision: `ES-01 r1` is the v0.1 text, `ES-01 r2` is the first v0.2 text. Feedback always refers to ID and revision.
- Each packet contains a mapping from the packet ID to the dataset scenario ID (the `scenario_id` format in TESTING.md section 11.2). The dataset files themselves are created in Phase 5. Until then, the mapping is reserved, not final.

## 8. Owner checklist per scenario (step 4)

- [ ] No real person, client, company, phone number, email address, ID number or address. Emails use only reserved domains. Names are invented
- [ ] Dates are consistent: every weekday matches the date, and every relative expression ("tomorrow", "Friday", "end of the month") resolves to the right day
- [ ] Amounts, currencies and units are consistent across messages, and the intended meaning
- [ ] The speaker of each message is clear and consistent (customer or agent), including use of singular and plural address
- [ ] The situation is plausible for the market (prices, areas, procedures, documents)
- [ ] Every promise, objection and request in the intended meaning appears in the messages
- [ ] Ambiguity is deliberate and written down (what is unclear and why)
- [ ] The text is not a near-copy of another scenario unless it is intentionally parallel
- [ ] The scenario's split and revision are written down

## 9. Acceptance criteria (proposed)

A scenario becomes `accepted` when all of these hold. These are proposals and can be changed by the owner.

1. Status is `native_reviewed`.
2. Every blocker and every required issue is resolved or declined with a recorded reason.
3. No unresolved region-variant flag (for example Latin American Spanish or Brazilian Portuguese usage).
4. Blind comprehension: the reviewer's understanding matches the intended meaning for the key facts (amounts, requirements, promises, dates), or any mismatch is explained as deliberate ambiguity or fixed by a revision.
5. The reviewer did not judge the scenario unrealistic for the market, or the concern is resolved.
6. The owner's decision and the date are recorded.

Reviewer coverage targets:
- First round: at least 1 reviewer per language.
- Before the pilot (TESTING.md): all held-out scenarios reviewed by at least 1 reviewer, with 2 reviewers preferred where available. At least 25% of development scenarios and half of the adversarial scenarios reviewed.
- If no reviewer is available, scenarios stay at `owner_checked` and every report states that limitation. They are not promoted.

## 10. Privacy and conduct rules

### 10.1 Data

1. Everything in the kit is synthetic. No real client data in packets, feedback, logs or the repository.
2. Reviewers are asked not to include real client information in feedback. If they do, it is redacted and the original is deleted. It is never committed.
3. Reviewers are identified by pseudonymous IDs: `R-ES-01`, `R-PT-01`, `R-EN-01`, and so on.
4. Names, emails, LinkedIn addresses, employers and any contact details are kept in the owner's **private tracker outside the repository**. They never appear in the repository, the manifest, reports or logs.
5. Only minimal information about reviewers is recorded: pseudonymous ID, language and variant, background category (native or fluent, real estate experience yes or no), region they know best, time spent, status of the invitation.
6. A reviewer may be named only with their written permission, and the owner confirms the exact wording first.
7. A legal check of how reviewer data is handled has not been done. If reviewers are ever paid or contracted, that needs separate approval and a privacy review first.

### 10.2 AI use

1. AI models are used only on synthetic text. DeepSeek is allowed only for synthetic or properly anonymized data (ADR-010).
2. Every AI check is recorded in `ai_check_log.md`: model and provider, date, what was asked, findings, what was done.
3. AI suggestions are `ai_suggested` until a human reviews them (section 5.4).
4. AI approval is never described as native-language validation.

### 10.3 Contacting reviewers

1. Nobody is assumed to agree. As of this version, **no reviewer is confirmed**.
2. Invite each person individually and personally. No mass or automated messages.
3. The first message says: the data is entirely fictional, taking part is voluntary, the estimated time, there is no payment, and they can decline or stop at any time without explanation.
4. No pressure. At most one polite reminder (proposed).
5. No freelancers and no expenses without further approval.
6. Reviewers are asked not to publish or share the packets, so the test data stays uncontaminated.
7. A person who declines or does not answer is recorded in the private tracker only.

## 11. Relationship to other documents

| Document | Relationship |
|---|---|
| TESTING.md section 11.2 | Defines dataset design, splits and scenario format. It has not yet been updated with the language decision. The update belongs to milestone 0.8. Until then, this README governs the review process |
| ADR-010 and SECURITY.md | Provider rules for AI use on test data |
| ADR-013 | Arabic is not part of this workstream |
| `datasets/` and `gold/` (Phase 5) | The dataset files that packet scenarios map to |

When TESTING.md is updated, it must refer to this README and use the statuses and validation levels defined here.

## 12. Verification before v0.2 is called complete

v0.2 is complete when all of the following are true. Only then may the owner approve archiving v0.1.

- [ ] Every file in section 4.1 exists, and the status table is updated
- [ ] Every packet shows the blind comprehension questions **before** the intended meaning
- [ ] Every packet has five scenarios per language (English: five parallel core plus the Dubai-specific ones), each with ID, revision, split and dataset mapping
- [ ] No scenario contains real data. A text search finds no email addresses outside reserved domains and no real-looking phone numbers
- [ ] All weekdays and relative dates are checked
- [ ] The AI-check log lists at least two different models per scenario, and no entry claims human validation
- [ ] The feedback form includes severity, required or preference, region flags, term preferences and reviewer confidence
- [ ] No names, emails or LinkedIn addresses of reviewers exist anywhere in the repository
- [ ] The v0.1 files are unchanged
- [ ] The owner has read every file

## 13. Open items

| # | Item | Decide in |
|---|---|---|
| 1 | Number of Dubai-specific English scenarios (proposal: 3) | `packet_en.md` step |
| 2 | Export format for reviewers: Word, PDF or form. Markdown stays the source | `reviewer_guide.md` step |
| 3 | Location and format of the owner's private tracker | Owner |
| 4 | Whether a second reviewer per language is available for the first round | Owner |
| 5 | Later kit for reviewing REIA's generated outputs in Spanish and Portuguese | Phase 8 |
| 6 | Optional robustness sets for Latin American Spanish and Brazilian Portuguese | After the pilot plan |
| 7 | Update of TESTING.md with the language decision and reference to this README | Milestone 0.8 |

## 14. Document control

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-11-14 | First version of the v0.2 README. Defines process, statuses, privacy rules and checklists. Other v0.2 files are planned and not yet created |