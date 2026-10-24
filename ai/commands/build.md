---
description: Implement an existing recorded spec when the dev explicitly invokes /build or asks to build a task ID; ordinary coding requests do not require a spec
argument-hint: [task-id] [--repo <name>] [--incremental | --no-test | --resume] [--validation flow|tests]
---

# /build — Implement Feature

> **Language**: always talk to the dev in **Thai** (technical terms may stay English). This file is written in English only to save tokens — render every message/report below in Thai.

Implement the recorded spec, exercise a practical flow, and check completeness.
Read `~/.ai/workflows/implementation.md` for helper routing, validation, and feedback. Default validation is `flow`; `tests` is opt-in unless team rules require it.

## Context Files

Always read before starting:
- shared project context (if any — see `~/.ai/AI.md` › Context Resolution): `PROJECT.md` + files in the context map relevant to the task
- project memory file at root + `.ai/context/MEMORY.md` (if any — the team's file wins on conflict)
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/specs/{task-id}.md` — **source of truth for this build**
- module rule file of the module to be changed (if any)

`features.md` is read as overview only — details live in the spec file

## Input

**$ARGUMENTS**

- **task-id** (optional): `TASK-YYYYMMDD-HHMM` or legacy `{MODULE}-{NNN}`
  - not given → use the latest feature with status 📋 or 🚧
- **Flags**:
  - `--incremental` — stop for dev review after every layer
  - `--no-test` — skip automated tests; still exercise the practical flow where available
  - `--validation flow|tests` — choose practical flow (default) or relevant automated tests
  - `--resume` — continue from existing state
  - `--repo <name>` — cross-repo spec: build only this repo (default: unfinished rows in build order; tests mode also selects ⚠️ rows needing automated evidence)

---

## Step 1: Pre-flight Check

**1.1 Find spec file**

- task-id given → read `.ai/context/specs/{task-id}.md` (or `CLOSED-TASK-{id}.md`)
  not found + inside a multi-repo project → continue searching `<project>/.ai/context/specs/` (see AI.md › Cross-repo Task)
- no task-id → scan `specs/TASK-*.md` for files whose `**Status**:` = 📋 or 🚧 (latest first)
  (including cross-repo specs whose `**Repos**:` contains the current repo)
- **Not found**:
  ```
  ❌ Spec file not found

  This feature has not gone through /spec — please run:
    /spec <requirement>
  ```
  → **stop immediately**

**1.2 Check status**

| Status | Action |
|---|---|
| 📋 Planned | ✅ proceed |
| 🚧 In Progress (no `--resume`) | ask: start over or resume? |
| ✅ Done (no `--resume`) | warn + ask: really re-build? (must reopen first) |
| ⚠️ Done (untested) | inspect existing work; follow the requested validation mode without rebuilding completed code |
| 🔴 Blocked | ask about the blocker first |
| ❌ / 📦 | stop — feature is closed, must reopen first |

**1.3 Load module context** — find the module from the spec → read that module's rule file if any

**1.4 Scan existing code** — survey the area the spec will touch:
- existing file structure
- patterns in use (follow them)
- conflicts with the code to be written

**1.4b Cross-repo spec** (`**Scope**: cross-repo`) → follow [Cross-repo Build](#cross-repo-build) instead of Steps 2-6 per repo

**1.5 Detect project commands** — read the project's manifest/scripts to find the real test / lint / typecheck / migration commands
**Never hardcode `npm test`** if the project uses something else

**1.6 Validation readiness** — identify an available local UI, CLI, API, or runtime flow. Use the shared implementation protocol. If the environment is unavailable, continue authorized implementation and report the unexercised flow with concise steps for the developer. Missing test infrastructure does not require a workflow confirmation. In `tests` mode, report missing tools and offer an existing flow; dependencies still need approval before installation. Mandatory team checks remain required.

---

## Step 2: Announce Plan

```
## Build Plan: {Task ID} — {Feature Name}

**Mode**: default | incremental | resume
**Validation**: flow | tests (record actual evidence)

### Files to create
- `{path}` — {purpose}

### Files to modify
- `{path}` — {what changes}

### Validation plan
- Flow: {entry point, input, expected output, available environment}
- Automated checks: {relevant existing command if selected/required; otherwise not selected}
- Review: {helper trigger or main-assistant completeness check}

### Dependencies
- Existing: {what will be imported}
- New: {package} — ⚠️ must confirm before installing

### Approach
{1-2 sentence strategy summary}
```

**`--incremental`** → wait for confirm before proceeding
**Otherwise** → proceed immediately

---

## Step 3: Update Status to In Progress

Edit the spec file:
- `**Status**:` → `🚧 In Progress`
- `**Last Updated**:` → `{now}` by `{git user}`

(`--resume` → status is already 🚧, only update Last Updated)

> Do not touch `features.md` — `/reindex` handles it

---

## Step 4: Implement

### Default Mode

Implement in dependency order (adapt to the project's actual architecture):

1. **Data model / Entity / Schema**
2. **Migration** (if schema changes)
   - ❌ **Never create migration files / set timestamps yourself** — always generate via the project's CLI
   - then write the `up()` / `down()` body into the CLI-generated file
   - multiple migrations in one task → generate one file at a time, in the order they must actually run
3. **Data access layer** (repository / DAO / query module)
4. **Business logic layer** (service / usecase / handler)
5. **Input/Output contract** (DTO / schema / validator)
6. **Transport layer** (controller / route / resolver / CLI)
7. **Wiring** (module registration / DI container / route table)

### Incremental Mode (`--incremental`)

After each layer → **stop**:
```
✅ Completed: {layer}
Files:
- `{path}` (+45 lines)

Preview:
{key signatures}

Review first? (reply anything to proceed)
```

### Resume Mode (`--resume`)

Read HANDOFF.md if it exists; compare task identity, HEAD, branch, and current diff before trusting it. Earlier tests cover only the recorded code state. Report stale validation and re-run relevant checks after subsequent code changes. Consult only confirmed, scoped lessons with current evidence.

1. Read existing code in the feature's area
2. Diff against the spec → find gaps
3. Implement only the gaps (do not overwrite existing code)
4. Code that conflicts with the spec → flag for dev confirm before changing

### Implementation Rules

- ✅ Follow conventions in `ARCHITECTURE.md` + module rule
- ✅ Use the same patterns as existing code
- ✅ Separate layers as the project defines — never bypass (e.g. querying the DB directly from the transport layer)
- ✅ Error handling as the project already does — never throw raw errors if the project has custom exceptions
- ✅ Multi-tenant → filter by tenant key on every query, from the authenticated context
- ❌ Never hardcode secrets — read from config/env
- ❌ Never use `setTimeout` / `setInterval` for background work — use the project's queue/scheduler

---

## Step 5: Validate and Review

### 5.1 Practical flow (default)

Use `~/.ai/workflows/implementation.md` to exercise the changed user path and a nearby unaffected case. Record inputs/steps, environment, expected and observed results, and the code state covered. If the environment is unavailable, finish the authorized implementation and report `flow not run` with developer steps; do not install a testing framework or claim a pass.

### 5.2 Automated checks (when selected or required)

In `--validation tests` mode, use the real relevant project command from Step 1.5. Prefer existing checks. Add a targeted regression only for a recurring bug or behavior that benefits from an executable check; do not generate tests for every method automatically. Follow mandatory team checks and approval rules for dependencies. `--no-test` skips optional automated checks; it cannot waive a mandatory team check silently.

### 5.3 Handle failures

For the same demonstrated failure: inspect evidence and correct once; if the first correction does not fix the symptom, use debugger before another speculative edit. Stop after three failed attempts, keep status 🚧, and report what failed and what evidence is missing. Do not bypass a failed check by changing validation mode.

### 5.4 Completeness and review

Inspect reachability, wiring, config names, exports, callers, contracts, and every requested outcome using the shared protocol. Use code-reviewer for a behavior change, multi-file work, or a sensitive path. Verify findings, fix supported issues within scope, and report remaining limits. Review alone never proves a runtime pass. Run lint/typecheck/build only when relevant to the change or required by the team.

### 5.5 Fix-loop Budget

Keep at most three attempts for the same failure and eight fix → rerun cycles per repo overall. A new helper does not reset the budget. Reached budget → stop with 🚧 and a concrete remaining-work report.

### Command Output Budget

Command output stays in context and is resent on every later request — keep it small:
- **Scope first**: run only the tests / lint / typecheck for changed files or the module; full-project run once at the end
- **Short output**: use a summary / dot / failures-only reporter if the runner has one, and/or pipe through `2>&1 | tail -n 80`
- **On failure**: rerun only the failing test / file to see details — never rerun the whole suite to read one error
- ❌ Never dump full build / install / test logs into the conversation (`npm install`, `build`, verbose reporters)
- Don't re-read a large file already read in this session unless it changed

---

## Step 6: Update Spec File

### 6.1 Status
- current relevant automated checks pass and no observed failure remains → `✅ Done`
- implemented without automated-test evidence → `⚠️ Done (untested)`; record flow passed/not run separately
- any demonstrated unresolved failure → keep `🚧 In Progress`

### 6.2 Implementation Status

Replace `_(TBD — pending /build)_`:
```markdown
## Implementation Status

**Files**:
- `{path}`
- ... (every file created / modified in this build)

**Validation**: {flow steps/input, expected/observed result, environment, code state; or not run with reason}
**Tests**: {actual command and result, or not run}
**Coverage**: {if measurable}
```

### 6.3 Changelog
```markdown
- **{YYYY-MM-DD}** BUILT — Implemented {brief summary}; validation: {actual flow/check and result, or not run}
```
(Record automated tests as not run when absent; do not attribute that to a flag the developer did not use.)

### 6.4 Last Updated
```markdown
**Last Updated**: {now} by {git user.name} \<{git user.email}\>
```

### 6.5 Known Gotchas (if any)
Found a pitfall the next maintainer should know → add to `## Known Gotchas`

---

## Cross-repo Build

One spec, many repos — do Steps 1.3-6 **one repo at a time, following `**Repos**:` (build order)**

**Pre-flight**
- repos to build = unfinished rows (📋 / 🚧 / 🔴), or explicit `--repo <name>`; `--validation tests` also selects ⚠️ rows needing automated evidence. Do not rebuild flow-verified implementation merely because it has no automated tests.
- check that files can be written in every repo to be built — if not (e.g. session opened in another repo / sandbox) → stop, recommend:
  `cd <project>` and open a new session, or `/build {task-id} --repo <name>` from a session in that repo
- any repo without `.ai/` → warn (no ARCHITECTURE to follow), recommend `/ai-init` first
- identify the available validation flow per repo (1.6); missing test setup alone does not block implementation

**Plan** (Step 2) shown once for all repos: build order, files per repo, validation flow/mode per repo, contracts the next repo will depend on

**Per repo** (in order):
1. Read memory file + `ARCHITECTURE.md` + module rule **of that repo** — do not load context of repos not yet reached
2. Implement only the `### {repo}` section in Proposed Design — paths relative to the project root
3. Validate with that repo's selected flow or checks, and record actual evidence and unavailable environments
4. Update that repo's row in Implementation Status (Status / Files / Tests) + Changelog `BUILT [{repo}]`
5. Recompute **Overall Status** (AI.md › Cross-repo Task), then update `**Status**:` + Last Updated
6. Pass the actually implemented contract (path, shape) on to the next repo

**Save context**: the main assistant implements one repo at a time, preserving the actual provider contract for the next repo. Use read-only helpers only at the shared protocol's triggers; never assign implementation to the five analysis helpers. Keep a compact checkpoint with files, flow/check evidence, contract, and gotchas rather than rereading unrelated repos.

**Failure**: a repo has a demonstrated unresolved flow/check failure after 3 attempts → stop at that repo (row stays 🚧), **do not build the next repos**
that depend on it — for repos that don't depend on it (no shared Contract Changes), ask the dev whether to continue

**Contract drift**: actual implementation differs from the spec's Contract Changes → stop, let the dev choose: fix code to match the spec, or `/change`

**Final Report** (Step 7) adds:
- Implementation Status table per repo + Overall Status
- proposed diff for `<project>/.ai/context/integrations.md` (if the contract changed — wait for dev confirm before writing)
- suggested commit **separately per repo**:
  ```
  cd {repo} && git commit -m "feat({scope}): {description}

  Task: {task-id}"
  ```

---

## Step 7: Final Report

For substantial work with an existing `.ai/context/`, update the current task's HANDOFF.md checkpoint using the handoff template. Preserve unrelated work. Include actual validation commands and code state; never invent test evidence. If the directory does not exist, include remaining work in the response instead of initializing context. Suggest lessons for review; only /learn persists confirmed entries.

```
## {actual status icon} Build Result: {Task ID}

### Summary
{1-2 sentences}

### Files Changed
Created:
- `{path}` (+X lines)
Modified:
- `{path}` (+X / -Y lines)

### Validation
- Mode: flow | tests
- Steps/input/environment: {actually exercised}
- Expected / observed: {result, or not run with reason}
- Automated checks: {actual command and result, or not run}
- Review/completeness: {resolved findings, requested outcomes covered, and remaining limits}

### ⚠️ Assumptions
{every assumption made where the spec was unclear}
1. ...

### 🔍 Points to Review
{points that need human judgment}
1. ...

### ⚠️ Anti-patterns Detected (if any)
{patterns that conflict with ARCHITECTURE.md but were implemented because the spec required them}

### 📘 API / Interface added or changed
For every endpoint/public interface built this round — so consumers can use it immediately without reading code:

**`{METHOD} {path}`** — {short purpose}
- **Auth**: {scheme}
- **Path params** / **Query params**: table `name | type | default | desc`
- **Request body**: shape + key fields + validation
- **Response 2xx**: example JSON + key fields (use real field names, e.g. `pageSize` not `limit`)
- **Error cases**: table `status | error key | when`
- **Important edge cases / behaviors**
- **Example calls**: 1-3 examples (default / with filter / edge)

> No new public interface (internal changes only) → skip this section

### Next Steps
1. Review code + tests
2. `git diff` to see all changes
3. `/reindex` to update features.md (terminal status will be auto-closed)
4. Commit + push
```

---

## Rules

### Must Do
- **Read spec + ARCHITECTURE.md + module rule** before writing code, every time
- **Follow existing pattern** — do not create new styles
- **Exercise the selected practical flow**, or report unavailable validation honestly; automated tests are targeted/opt-in unless team rules require them
- **Require current relevant automated-test evidence for ✅**; record practical flow evidence separately
- **Update spec file** (Status / Implementation Status / Changelog / Last Updated) every time
- **Report assumptions + review points** always
- **Document every public interface built** in the Final Report

### Must Not
- ❌ **Build without a spec file**
- ❌ **Edit spec content (Business Rules / Design)** — if the spec is unclear → stop, ask the dev to run `/change`
  (Status / Implementation Status / Changelog / Last Updated / Known Gotchas may be edited — they are build state)
- ❌ **Touch `features.md`**
- ❌ **Bypass architecture rules**
- ❌ **Mark ✅ while tests still fail** — leaving 🚧 is better
- ❌ **Install dependencies without confirm** — includes test libraries (see 1.6)
- ❌ **Exceed the fix-loop budget (5.5) without the dev's OK**
- ❌ **Dump full command logs into context** (see Command Output Budget)
- ❌ **Auto commit / push**
- ❌ **Cross-repo: build the next repo while a previous repo (that it depends on) still has failing tests**
- ❌ **Cross-repo: mark Overall ✅ if any repo is not yet ✅**

### Flag-specific Rules

- **`--no-test`**: skip optional automated checks; still exercise the practical flow when available and report validation limits
- **`--incremental`**: use when the feature is complex or the dev wants to tune along the way
- **`--resume`**: inspect current work and preserve unrelated edits; continue already-authorized remaining work without asking again

---

## Output Language

- Reply to the dev in **Thai**
- Code / code comments / commit messages → **English**
- Commit message format: `feat({module}): {description}`

---

## Examples

```
dev: /build TASK-20260501-1430
AI: [pre-flight → plan → implement → test → update spec → report]

dev: /build --resume
AI: [find latest 🚧 feature → diff against spec → continue only the gaps]

dev: /build TASK-20260501-1430 --incremental
AI: [implement layer → stop → confirm → next layer → ...]

dev: /build --no-test
AI: [implement → exercise available practical flow → status ⚠️ with actual flow result; automated tests not run]
```
