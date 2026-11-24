# How the audit works

## Data flow

App name and confirmed domains -> discover official docs -> fetch/hash public evidence -> extract candidates -> challenge scope and negation -> contextual review -> validate and aggregate -> render case study -> human check before submission.

The full findings were assembled with AI-assisted primary-source research. The Python code is a runnable supporting pipeline, not a claim that every contextual judgment came from unattended extraction. Vendor-source selection and semantic synthesis still need review.

## Why these controls matter

A naive extractor sees a Basic-auth example and overgeneralizes it to the whole GitHub API. Contextual review keeps Basic endpoint-scoped. A token that works for GitLab REST may be rejected by the MCP endpoint. New Relic offers a free API development path but requires paid accounts for hosted MCP. Opsgenie API docs still exist after new signup closed. A source that says API access is free may mean a sandbox, not production.

Ownership, interface scope, plan, environment and role must be recorded separately. Search snippets are leads only. Failed source retrieval stays failed even if a separate reading method can open the same page.

## What could be improved

Add a stronger search adapter, a schema-constrained semantic extraction step with paragraph-level citations, source freshness tracking, vendor-plan conflict detection, and blinded human labels for a random sample. Measure field-level precision/recall before and after actual corrections against the same independent labels. Do not score unknown labels or silently discard inaccessible sources. Account-level credential tests should be a separate opt-in step with sandbox scopes and no production writes.

## Two-minute explanation

The benchmark asks whether a toolkit can be built, not merely whether an API exists. 81 apps have free or trial credentials, but only 38 meet the ready rubric. OAuth dominates, while material plan, admin and production gates create the operations queue. Official MCP references are plentiful, but ownership alone says little about action coverage. The source-linked matrix records those distinctions. The executable pipeline preserves evidence and failures; contextual review corrected real mistakes. No numerical accuracy gain or human check is fabricated.
