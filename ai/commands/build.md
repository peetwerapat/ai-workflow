---
description: Implement a feature per its spec with tests — supports incremental mode and resume
argument-hint: [task-id] [--repo <name>] [--incremental | --no-test | --resume]
---

# /build — Implement Feature

> **Language**: always talk to the dev in **Thai** (technical terms may stay English). This file is written in English only to save tokens — render every message/report below in Thai.

Implement per the spec file and write tests alongside
Default: code + test + run tests in one go

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
  - `--no-test` — skip tests (prototype only)
  - `--resume` — continue from existing state
  - `--repo <name>` — cross-repo spec: build only this repo (default: every repo not yet ✅, in build order)

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
| ⚠️ Done (untested) | proceed — focus on writing tests |
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

---

## Step 2: Announce Plan

```
## Build Plan: {Task ID} — {Feature Name}

**Mode**: default | incremental | resume
**Skip tests**: yes | no

### Files to create
- `{path}` — {purpose}

### Files to modify
- `{path}` — {what changes}

### Test coverage plan
- Unit: {count} tests
- Integration: {count} (if critical flow)
- Focus: happy path, rule violations, tenant isolation

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

## Step 5: Test (unless `--no-test`)

### 5.1 Generate Tests

Cover 4 categories for every business method:
1. **Happy path** — valid input, correct output
2. **Business rule violation** — throws/returns the expected error
3. **Edge cases** — null, empty, boundary
4. **Tenant isolation** (if multi-tenant) — queries don't leak across tenants

### 5.2 Run Tests

Use the project's real command (from Step 1.5) — scope as narrowly as still covers the change, e.g. filter by module/path

### 5.3 Handle Failures

- **Attempt 1**: analyze error → fix code or test → rerun
- **Attempt 2**: analyze deeper (may be a wrong assumption in the spec) → fix → rerun
- **Attempt 3**: **stop**
  ```
  ⚠️ Tests still failing after 3 attempts

  Latest error: {error}
  Analysis: {what I think is wrong}

  Status remains 🚧 (not marked done)
  ```

### 5.4 Lint / Typecheck

After tests pass → run the project's lint + typecheck and make them pass too, before the build counts as done

---

## Step 6: Update Spec File

### 6.1 Status
- tests pass → `✅ Done`
- `--no-test` → `⚠️ Done (untested)`
- tests fail → keep `🚧 In Progress`

### 6.2 Implementation Status

Replace `_(TBD — pending /build)_`:
```markdown
## Implementation Status

**Files**:
- `{path}`
- ... (every file created / modified in this build)

**Tests**: {N passing} / {N failing}
**Coverage**: {if measurable}
```

### 6.3 Changelog
```markdown
- **{YYYY-MM-DD}** BUILT — Implemented {brief summary} + {N} tests
```
(`--no-test` → state explicitly "no tests written — --no-test flag used")

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
- repos to build = every repo in Implementation Status not yet ✅ (or only `--repo <name>`)
- check that files can be written in every repo to be built — if not (e.g. session opened in another repo / sandbox) → stop, recommend:
  `cd <project>` and open a new session, or `/build {task-id} --repo <name>` from a session in that repo
- any repo without `.ai/` → warn (no ARCHITECTURE to follow), recommend `/ai-init` first

**Plan** (Step 2) shown once for all repos: build order, files per repo, test command per repo, contracts the next repo will depend on

**Per repo** (in order):
1. Read memory file + `ARCHITECTURE.md` + module rule **of that repo** — do not load context of repos not yet reached
2. Implement only the `### {repo}` section in Proposed Design — paths relative to the project root
3. Test with that repo's command (Step 1.5 per repo) — different repos may use different runners
4. Update that repo's row in Implementation Status (Status / Files / Tests) + Changelog `BUILT [{repo}]`
5. Recompute **Overall Status** (AI.md › Cross-repo Task), then update `**Status**:` + Last Updated
6. Pass the actually implemented contract (path, shape) on to the next repo

**Save context**: runtime supports subagents → delegate steps 1-4 of each repo to a subagent, one at a time (in order, never parallel — later repos depend on earlier repos' contracts)
send input: spec path + repo name + contract summary from the previous repo / receive back: files, tests, actual contract, gotchas

**Failure**: a repo's tests fail all 3 attempts → stop at that repo (row stays 🚧), **do not build the next repos**
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

```
## ✅ Build Complete: {Task ID}

### Summary
{1-2 sentences}

### Files Changed
Created:
- `{path}` (+X lines)
Modified:
- `{path}` (+X / -Y lines)

### Tests
- Unit: X added ({all passing | Y passing, Z failing})
- Lint / Typecheck: ✅ | ⚠️
{or "⚠️ Tests skipped — --no-test used"}

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
- **Write tests alongside code** (except `--no-test`)
- **Make tests + lint + typecheck pass** before marking ✅
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
- ❌ **Install dependencies without confirm**
- ❌ **Auto commit / push**
- ❌ **Cross-repo: build the next repo while a previous repo (that it depends on) still has failing tests**
- ❌ **Cross-repo: mark Overall ✅ if any repo is not yet ✅**

### Flag-specific Rules

- **`--no-test`**: only for prototype/exploration — if it is production work → warn the dev first
- **`--incremental`**: use when the feature is complex or the dev wants to tune along the way
- **`--resume`**: never overwrite existing code without confirm

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
AI: [implement only → status ⚠️ → warn that it should be tested before production]
```
