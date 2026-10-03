---
description: Modify an existing feature — bug fix / requirement change / refactor with impact analysis
argument-hint: <task-id> "<description>" [--quick | --dry-run | --cancel <reason> | --deprecate <reason>]
---

# /change — Modify Existing Feature

> **Language**: always talk to the dev in **Thai** (technical terms may stay English). This file is written in English only to save tokens — render every message/report below in Thai.

Modify an existing feature — covers 3 use cases in one command:
- **Bug fix** — code behaved wrongly → fix it to match the spec
- **Requirement change** — spec changes → code follows
- **Refactor** — internal change, behavior unchanged

AI classifies the type automatically from the description.

## Context Files

- shared project context (if any — see `~/.ai/AI.md` › Context Resolution): `PROJECT.md` + files in the context map relevant to the task
  - Touches a contract in `integrations.md` → flag consumer-side repos in risk + propose a shared update (do not edit it yourself)
- project memory file at root + `.ai/context/MEMORY.md` (if any — the team's wins on conflict)
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/specs/{task-id}.md` (or `CLOSED-TASK-{id}.md`) — **source of truth**

## Runtime Info

```bash
git config user.name
date "+%Y-%m-%d"
```

---

## Input

**$ARGUMENTS**

Format: `<task-id> "<description>" [flags]`

- **task-id** (required, first token): `TASK-YYYYMMDD-HHMM` or legacy `{MODULE}-{NNN}`
- **description** (required): may include a prefix to force the type — `"refactor: ..."`, `"fix: ..."`, `"change: ..."`
- **Flags**:
  - `--quick` — skip impact analysis (only for small, clear changes)
  - `--dry-run` — show impact analysis only, no real edits
  - `--cancel <reason>` — Status → ❌, Changelog `CANCELLED`
  - `--deprecate <reason>` — Status → 📦, Changelog `DEPRECATED`

**Missing args** → show the correct format + stop

---

## Step 1: Parse & Validate

```
input: TASK-20260501-1430 "login ค้างเมื่อ Redis down" --quick
→ task-id: TASK-20260501-1430
→ description: login ค้างเมื่อ Redis down
→ flags: [--quick]
```

task-id does not match the pattern → stop:
```
❌ "{input}" is not a valid task-id
Format: TASK-YYYYMMDD-HHMM or {MODULE}-{NNN}
Search: /status <keyword>
```

---

## Step 2: Pre-flight Check

### 2.1 Find the spec file

Try in order:
1. `.ai/context/specs/TASK-{id}.md` (active)
2. `.ai/context/specs/CLOSED-TASK-{id}.md` (closed)
3. multi-repo project → `<project>/.ai/context/specs/` (active, then closed) — see AI.md › Cross-repo Task

**Neither found**:
```
❌ No spec file found for {task-id}

- Is the Task ID correct? → `/status {task-id}`
- If this is a new feature → use `/spec`, not `/change`
```

### 2.2 Reopen check (if it is a CLOSED file)

Rename back to active first: `git mv CLOSED-TASK-{id}.md TASK-{id}.md`
(the next `/reindex` will append the `REOPENED` Changelog entry)

### 2.3 Check Status

| Status | Action |
|---|---|
| ✅ Done | ✅ proceed |
| ⚠️ Done (untested) | ⚠️ warn + proceed (tests may already have issues) |
| 🚧 In Progress | ⚠️ ask: build not finished yet — better to edit the spec then `/build --resume`? |
| 📋 Planned | ❌ stop — not built yet, edit the spec file directly or cancel + new `/spec` |
| 🔴 Blocked | ⚠️ ask about the blocker first |
| ❌ Cancelled / 📦 Deprecated | ❌ stop (to revive → reopen first) |

---

### 2.4 Cross-repo spec (`**Scope**: cross-repo`)

- Impact analysis covers **every repo in `**Repos**:`** + other repos that `integrations.md` says consume the contract being changed
- Change must touch a repo not yet in `**Repos**:` → show it in the Change Plan + ask for confirm, then add it to Repos / Design / Implementation Status
- Execute (Step 7) one repo at a time in build order — test with each repo's own command
- Changelog names the repos touched: `{TYPE} [{repo}, {repo}]` / update rows in Implementation Status + Overall Status
- Open the session at the project root if writing to multiple repos (same as `/build`)
- Original spec is repo-level but the change spreads to another repo → propose a new cross-repo `/spec` for the cross-repo part (referencing the original task) instead of stuffing it into a single repo's spec

---

## Step 3: Detect Change Type

**Priority 1 — explicit prefix**
```
"refactor: ..." → REFACTORED
"fix: ..." / "bug: ..." / "bugfix: ..." → FIXED
"change: ..." → CHANGED
```

**Priority 2 — keyword inference**
```
FIXED:      bug, broken, error, ค้าง, พัง, ไม่ทำงาน, ผิด
REFACTORED: refactor, cleanup, extract, rename, move, reorganize, simplify, ปรับโครงสร้าง, แยก
Default:    CHANGED
```

**Priority 3 — confirm** if confidence is low:
```
Guessed change type: {TYPE}
A) {TYPE} — as guessed
B) Override (FIXED / CHANGED / REFACTORED)
```

---

## Step 4: Impact Analysis

**`--quick` → skip to Step 6**

> ⚠️ `--quick` is only for small, clear changes
> **Never use for**: auth, payment, money calculation, multi-tenant, data migration
> If the dev passes `--quick` for these → warn and do the full analysis anyway

### Normal → Delegate to impact-analyzer

**Input:**
```
Task ID: {task-id}
Current spec path: .ai/context/specs/{task-id}.md
Current code files: {list from Implementation Status}
Change description: {description}
Change type (detected): {FIXED | CHANGED | REFACTORED}
```

**Expect output:**
- **Conflict check** (most important)
- Risk level (🔴 / 🟡 / 🟢) + reasoning
- Affected files (direct + indirect)
- Test impact (existing / new)
- Proposed approach (1-2 options if there is a trade-off)
- Confidence assessment

**If the runtime does not support subagents** → read `~/.ai/agents/impact-analyzer.md` and follow that process yourself

---

## Step 5: Handle Conflict (if any)

Conflict with an existing business rule → **stop immediately**:

```
⚠️ Business Rule Conflict Detected

### Task: {task-id}

| | Original (spec) | New (requested) |
|---|---|---|
| Rule | {original rule} | {new behavior} |

### Consequences if Changed
- {what will be removed/modified}
- {side effects}

### Needs confirmation from BA/PO
1. Do you really want to change this business rule?
2. Reason? (will be recorded permanently in the Changelog)

Type "confirm: <reason>" to continue / "cancel" to stop
```

**No confirm + reason → do not proceed**

---

## Step 6: Show Analysis + Confirm

```
## Change Plan: {task-id}

**Type**: {FIXED | CHANGED | REFACTORED}
**Description**: {description}
**Risk Level**: 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW — {why}

### 📁 Direct Impact
- `{path}` — {what changes}

### 🔗 Indirect Impact
{cross-module impact or "Isolated — no impact on other modules"}

### 🧪 Affected Tests
- `{test file}` — test "{name}" (may need edits)

### 💡 Approach
{single approach, if clear}

{or if there is a trade-off:}
Option A: {name} — Pros / Cons
Option B: {name} — Pros / Cons
Choose A or B?

### ⚠️ Pre-execution Checklist
- [ ] Risk level understood
- [ ] Test coverage exists for the files to be edited
- [ ] Breaking change has a migration path (if any)

Type "confirm" to execute / "cancel" to stop
```

### `--dry-run` → stop here
```
✅ Dry-run complete — no files changed
To execute for real → run the same command **without** --dry-run
```

---

## Step 7: Execute

### 7.1 Generate Revision ID

Find the latest revision in the spec file's Changelog:
```
{task-id}-R02 (latest) → next R03
no R → R01
```
Format: `{task-id}-R{NN}` (2 digits, zero-padded)

### 7.1b Test Readiness + Budgets

Same rules as `/build` (read `~/.ai/commands/build.md` › 1.6, 5.5, Command Output Budget if not loaded):
- **Test readiness**: the repo cannot test the kind of code being changed (no runner / missing library) → stop and ask:
  A) apply the change without tests → status ⚠️, Changelog notes it (recommended) · B) set up test infra first (new dependencies, more work) · C) stop
  ❌ never install test dependencies as a side effect of a change
- **Fix-loop budget**: 3 attempts per failure **and** at most 8 fix → rerun cycles in total per repo → then stop, status 🚧, report
- **Command output**: scoped runs, summary reporters / `2>&1 | tail -n 80`, rerun only the failing test, full-project check once at the end — never dump full logs

### 7.2 Edit Files One-by-One

**Never edit multiple files at once**

```
For each file:
  1. Read current content
  2. Apply change
  3. Run related tests
  4. fail → analyze + fix (max 3 attempts)
  5. still failing → rollback this file + report to dev
  6. next file
```

### 7.3 Test Strategy per Type

**FIXED**
- Write a regression test **before** the fix (TDD-ish) — must fail before, pass after
- No existing test found → write a new one

**CHANGED**
- Update existing tests to match the new spec
- Add test cases arising from the new rule

**REFACTORED**
- Existing tests must **pass unchanged** — do not edit tests
- Tests break = not a refactor but a change → stop + confirm
- Do not add new tests

### 7.4 Handle Test Failures

**FIXED / CHANGED**: attempt 1 → 2 → 3 then stop (leave edited files, mark 🚧)

**REFACTORED**:
```
⚠️ Existing tests fail after refactor
This may not be a true refactor — behavior changed

A) Rollback (don't refactor here)
B) Change type to CHANGED (update tests to the new behavior)
```

---

## Step 8: Update Spec File

### 8.1 Append Changelog

```markdown
- **{date}** {TYPE} — {description}
  - **Reason**: {reason — required for CHANGED / FIXED / CANCELLED / DEPRECATED}
  - **Files**: {affected files}
  - **Revision**: {revision-id}
```
`{TYPE}` ∈ `CHANGED` / `FIXED` / `REFACTORED` / `CANCELLED` / `DEPRECATED`

### 8.2 Update other sections (by type)

**CHANGED + business rule changed** → update `## Business Rules`, `## Ambiguity Resolutions`
**`--cancel` / `--deprecate`** → update `**Status**:` to ❌ / 📦

### 8.3 Last Updated
```markdown
**Last Updated**: {now} by {git user.name} \<{git user.email}\>
```

### 8.4 Status
Usually unchanged (stays ✅) except:
- tests fail 3 attempts → 🚧
- major change needing lots of re-testing → may downgrade to ⚠️

---

## Step 9: Final Report

```
## ✅ Change Complete: {revision-id}

**Type**: {TYPE} | **Description**: {description}

### Files Modified
- `{path}` (+X / -Y lines)

### Tests
- Updated: X | Added: X (regression)
- All passing ✅ | Some failing ⚠️

### Doc Updates
- spec file: appended Changelog + updated Last Updated
- features.md: not updated yet — run `/reindex`

### ⚠️ Assumptions Made
1. ...

### 🔍 Points to Review
1. ...

### Next Steps
- `git diff` review
- `/reindex` to update features.md
- Commit (suggested — cross-repo: separate commit per repo with the same Task):
  ```
  {type}({module}): {description}

  Task: {task-id} / {revision-id}
  ```
```

---

## Rules

### Must Do
- **Validate task-id before analyzing**
- **Delegate impact analysis** — don't analyze yourself (unless the runtime doesn't support it)
- **Stop on conflict** — wait for dev confirmation + reason
- **Test after every file** — detect regressions early
- **Record reason in Changelog** for FIXED and CHANGED

### Must Not
- ❌ **Edit multiple files at once**
- ❌ **Skip impact analysis** for auth / payment / money / multi-tenant / migration even with `--quick`
- ❌ **Mark ✅ if tests fail**
- ❌ **Edit tests in REFACTORED**
- ❌ **Commit automatically**
- ❌ **Touch `features.md`**

---

## Edge Cases

**Description vague**
```
dev: /change TASK-XXX "แก้ตรง login"
AI: Description unclear — what bug? / which requirement changed? / or just a refactor?
```

**Feature not built yet (📋)**
```
⚠️ {task-id} is not built yet — /change is for features that are already built
A) Edit the spec file directly → then run /build
B) Cancel + new /spec
```

**Multiple changes in one command**
```
dev: /change TASK-XXX "fix login + add rate limit + change UI"
AI: Detected 3 changes — better as 3 separate commands (each gets its own revision + audit)
```

**Rollback**
```
dev: cancel (after tests fail 3 attempts)
AI: 1. `git checkout .` revert working tree
    2. Check new files created by AI
    3. spec file not edited yet (Step 8 not reached)
    → state returns to before /change
```

---

## Output Language

- Reply in **Thai**
- Technical terms, code, paths, task-id, revision-id, commit message → **English**

---

## Examples

```
dev: /change TASK-20260424-1430 "login ค้างเมื่อ Redis down"
AI: [FIXED → impact → propose timeout vs circuit breaker → dev picks A → implement + regression test]
    ✅ Change Complete: TASK-20260424-1430-R01 (FIXED)

dev: /change TASK-20260424-1445 "comment ต้องมี captcha + rate limit 3/hr"
AI: ⚠️ Conflict: original spec states "no rate limit" — reason?
dev: confirm: โดน spam ยิงจริง
AI: ✅ Change Complete: TASK-20260424-1445-R01 (CHANGED)

dev: /change AUTH-001 "refactor: แยก JWT validation เป็น guard"
AI: [REFACTORED → low risk → implement → existing tests pass, tests not edited]
    ✅ Change Complete: AUTH-001-R01 (REFACTORED)
```
