# Evidence-first integration audit

A 100-app, primary-document benchmark of the credential, API, policy and MCP gates between an app and an agent toolkit. Researched 23 November 2026.

## Findings in one minute

- 38 apps are ready for a scoped own-account prototype, 61 are conditional and one, Opsgenie, is blocked for new onboarding.
- 81 apps have a free or trial credential path. That is not a promise of free production access.
- OAuth appears in 87 apps. Authentication-family counts overlap.
- 95 apps have an official MCP reference, but only 75 are classified as operational business-data/action interfaces. Six are read-only/limited, 11 limited/preview, three docs/developer-only and five unconfirmed. Operational does not imply unrestricted or free.
- CRM and commerce has 10 ready apps out of 20. Marketing/analytics and productivity each have 14 conditional apps out of 20.

The app set was researcher-selected after the referenced employer list was not visible. It is balanced across five categories and was approved by the candidate. It is not presented as an employer-supplied list. No production credentials or private account information are included.

## Two ways to use this repository

- **Core checkout (this git tree):** code, tests, the 100-app source data in `data/full`, docs, and the small outputs. It does not contain the large generated files (`output/final/dataset.json`, `output/report.html`, `index.html`, `output/source-verification/source-checks.json`) or the 760 source snapshots. The Quick start commands below regenerate the dataset and the report from `data/full`, so the findings can be rebuilt from this tree alone.
- **Full archive:** the exact final package (a9e8e79f) with every generated file and the 760 snapshots is attached to the [v1.0.0 release](https://github.com/Pirategrand/composio-integration-audit/releases/tag/v1.0.0) as `composio-integration-audit-final-a9e8e79f.zip` (SHA-256 292b38dd096342091f4aec6d4d78bc233675c96019f8c0266ccbb46c81b6dcdc). Use it for offline citation replay and for the shipped `source-checks.json`. The hosted report is at https://files.instinct.com/omkorwol4w3y-which-apps-are-ready-for-agents .

## Quick start

Python 3.11+, standard library only. No API key is needed for the included utilities.

```sh
python -m unittest discover -s tests -v
python src/finalize.py --input data/full/*.json --output output/final --expected-count 100
python src/build_report.py --dataset output/final/dataset.json --output output/report.html
```

Open `output/report.html` for the single-page interactive case study. It contains the findings, complete searchable matrix, methods, actual corrections and verification limits. Source evidence links open the vendor documentation. `output/final/dataset.json` is the machine-readable result.

### Reproduce citation retrieval

```sh
python src/verify_sources.py --dataset output/final/dataset.json --output output/source-verification
python src/verify_sources.py --dataset output/final/dataset.json --output output/source-verification --offline
```

The recorded full run attempted 407 unique URLs: 372 retrieved, 20 fetch errors, five robots files unavailable and 10 robots-disallowed pages. Offline replay validates the included successful snapshots; unresolved URLs become offline_cache_miss. The original failure types remain in the shipped source-checks.json, so copy that file before rerunning into the same directory. Network results will change. Lexical matches and HTTP success are not semantic accuracy.

### Run discovery, collection and candidate extraction

```sh
python src/run.py --input data/demo.json --output output/smoke
python src/discover.py --input data/discovery-demo.json --search-fixture data/github-recorded-search.json --output output/discovery-replay.json
```

`data/demo.json` is a two-app engineering smoke test, not the 100-app result. For a new input, use an object with `apps`, each containing `id`, `name`, `official_domains`, and optionally `sources` (`url`, `purpose`). The public RSS discovery adapter promotes only relevant allowlisted domains; uncertain search results remain unresolved. A recorded search fixture is replay, not live discovery. The supplied smoke search returned irrelevant GitHub results and was rejected rather than accepted as primary evidence.

`src/audit.py` collects public pages into dated content-hashed snapshots, extracts candidate auth/access/API/MCP evidence and produces a basic collector report. `synthesize.py` challenges negation, sandbox/production confusion and endpoint scope. `review.py` validates exact source quotations and hashes before applying structured review entries. `finalize.py` validates unique IDs and the 100-row schema, then derives counts and a risk-prioritized review queue. `verify_sources.py` replays all citations independently of the findings synthesis.

## What actually ran, and what did not

The 100-app findings are AI-assisted primary-document research with contextual source review. They are **not** claimed to be an unattended 100-app LLM run. The executable discovery, collector, replay, schema, aggregation, citation-check and rendering utilities were run. No Composio SDK connection or external LLM API is required or claimed. The main remaining automation gap is contextual semantic synthesis: the deterministic extractor cannot reliably infer plan entitlements from keywords alone.

No login, app install, paid account, credential signup, production API execution or application submission was performed. Fetching honors robots policies, rejects local/private addresses, uses timeouts and limits page sizes. External page instructions are never executed.

## Verification and honest error accounting

- `data/review/risk-sample.json`: 20 deliberately risk-focused app checks, four per category. Each checks one material claim. This is agent source review, not random sampling or independent human review.
- `data/full/review-ledger.jsonl`: actual source-driven corrections, including Help Scout free-vs-trial entitlement, Squarespace paid-plan gating, Ecwid aggregator-vs-vendor MCP ownership and HubSpot remote MCP read-only scope.
- `output/final/sample-queue.json`: a separate deterministic, category-stratified risk queue for a person to check.
- Tests measure code behavior, not research accuracy. Retrieval rate is not accuracy. There is no independent ground-truth reference set, so no first-pass/final accuracy percentage is reported.
- Completed independent human checks: **zero**. The assignment requests human checks and understanding of the code; the candidate must perform that step before submission. Use `HUMAN_REVIEW.md` for a short source-linked checklist.

Important unresolved or bounded evidence: Miro MCP plan documentation conflicts; Ecwid's vendor-hosted overview uses older plan names; some public pages could not be retrieved by the collector. Medium confidence and source failure records are retained. Policies and access can change after the research date.

## Verdict rubric

Ready means an own-account scoped prototype has a documented path without a material unresolved new-onboarding gate. Conditional means trial, entitlement, role, production approval, policy ambiguity or partnership work is material. Blocked means no viable new-onboarding route was established. MCP ownership and capability scope are separate fields. A docs-only server is not a billing or CRM action server.

See `METHOD.md` for the architecture, limits and a two-minute explanation. The candidate should read the code and verify every statement they intend to defend.
