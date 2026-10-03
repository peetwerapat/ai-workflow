---
description: Detect drift between spec files ↔ actual code (does not check features.md — that is /reindex's job)
argument-hint: [--fix]
---

# /sync — Detect & Fix Spec ↔ Code Drift

> **Language**: always talk to the dev in **Thai** (technical terms may stay English). This file is written in English only to save tokens — render every message/report below in Thai.

Check whether specs in `.ai/context/specs/` still match the actual code
— report only (default) or interactive fix (`--fix`)

**Scope**: does not check `features.md` drift — that is a derived view, fixed with `/reindex`
**End of run**: `--fix` mode auto-chains `/reindex` (because specs were modified)

## Context Files

- project memory file at root + `.ai/context/MEMORY.md` (if present — the team's wins on conflict)
- `.ai/context/features.md` (overview only — not a detection source)
- `.ai/context/untracked.md` (whitelist)

## Runtime Info

```bash
git log --oneline -10
git status --short
```

## Input

**$ARGUMENTS**

- **Empty** → Detection mode (report only)
- **`--fix`** → Interactive fix (detect → propose → confirm one item at a time)

---

## Step 1: Scan Sources

### Source A — spec files (source of truth)

Read every file in `.ai/context/specs/` (both `TASK-*.md` and `CLOSED-TASK-*.md`)

Parse: Task ID, Module, Status, and **Implementation Status > Files**

Multi-repo project → also read `<project>/.ai/context/specs/`, only specs whose `**Repos**:` includes this repo — use only this repo's rows in Implementation Status
(files listed there = tracked, not orphan) / `--fix` may edit only this repo's rows

### Source B — source code

Find the project's actual source root (do not assume `src/`), then list:
- module/package directories that actually exist
- all source files (excluding generated / vendor / build output)
- migration files

---

## Step 2: Detect Drift Categories

### 🔴 Category 1: Orphan Code
**Code file exists but does not appear in any spec's Files list** (written without going through `/spec`)

Skip: files listed in `untracked.md`, test files paired with already-tracked source, config/generated files

```
🔴 {path}
   Created: {commit} "{msg}" ({relative time} by {author})
   Not referenced by any spec
```

### 🔴 Category 2: Stale Files
**Spec says file X exists but the filesystem does not have it**

```
🔴 CLOSED-TASK-{id}.md ({Module})
   Lists: {path}
   File missing (possibly renamed in {commit}, {relative time})
```

### 🟡 Category 3: Module Orphan
**Module directory exists but no spec has `Module` = that name**

### 🟡 Category 4: Status Lie
- ✅ but Files list is empty
- ✅ but all files in Files list are missing
- 📋 but code actually exists (built but forgot to flip status)

### 🟡 Category 5: Post-BUILT Activity (heuristic)
**Files in a spec were modified after the latest Changelog entry**

- Find the date of the latest Changelog entry (BUILT / CHANGED / FIXED / REFACTORED — take the max)
- `git log --since="{date}" -- {files}`
- Commits after that which don't match the Changelog → flag

> ⚠️ **Heuristic only** — a commit may be a typo / comment update, dev must judge

---

## Step 3: Report

```
## Doc Drift Report (Spec ↔ Code)

Scanned: {X} spec files | {Y} modules | {Z} source files

---

### 🔴 Critical Drift ({count})

**Orphan Code ({count})**
- `{path}` — created {commit} "{msg}" ({time} by {author}), not referenced by any spec

**Stale Files ({count})**
- {task-id}: `{path}` not found — last commit {commit} ({time})

---

### 🟡 Warning Drift ({count})

**Module Orphan ({count})**
- `{module path}` — no spec with Module = {name}

**Status Lie ({count})**
- {task-id}: status ✅ but Files list empty
- {task-id}: status 📋 but code already exists

**Post-BUILT Activity ({count})**
- {task-id} ✅ (last entry {date}) — `{file}` modified on {date}
  Check whether it is a bug fix, refactor, or requirement change

---

### ✅ In Sync
{X} specs with no drift
```

**No drift at all:**
```
## ✅ Spec ↔ Code in Sync
Scanned {X} specs, {Y} modules, {Z} files — no drift detected
(features.md sync is /reindex's job)
```

---

## Step 4: Fix Mode (`--fix` only)

No `--fix` → stop at Step 3 + suggest `/sync --fix`

Interactive, one item at a time, ordered 🔴 → 🟡:

```
## Drift {N} of {Total}: {Category}

{detail}

### Suggested actions
A) {option 1}
B) {option 2}
C) Skip

Choose [A/B/C]:
```

### Fix Options per Category

**Orphan Code**
```
A) Generate spec retroactively — analyze current code → create new spec
   Status: ✅ (retroactive), Changelog: ADDED retroactively via /sync
B) Add to existing spec — pick task-id → add path to Implementation Status > Files
C) Mark as untracked — add to `.ai/context/untracked.md` (shared util / infra)
```

When editing an existing context file (e.g. untracked.md), write in that file's existing language.

**Stale Files**
```
A) Remove from Files list (+ Changelog "REMOVED {file}")
B) File was renamed — ask for new path → update + Changelog "REFACTORED — renamed {old} → {new}"
C) Feature was reverted — `/change {task-id} --cancel "code reverted"`
```

**Module Orphan**
```
A) Create spec retroactively for this module
B) Mark untracked
C) Module deprecated — confirm + dev deletes it manually
```

**Status Lie**
```
# ✅ + Files empty
A) Fill Implementation Status — scan code → propose Files list

# 📋 + code exists
A) Flip Status → ✅ (acknowledge it was built outside the flow)
B) `/build --resume` — proper flow + tests (recommended)
```

**Post-BUILT Activity**
```
A) Add CHANGED entry (+ reason, update Business Rules if needed)
B) Add FIXED entry (bug fix, not a requirement change)
C) Add REFACTORED entry (internal only)
D) Skip (typo / comment only)
```

---

## Step 5: Chain /reindex + Summary

```
## 🔄 Running /reindex to refresh features.md...
✅ features.md regenerated

## ✅ Sync Complete

Fixed: {X} | Skipped: {Y} | Reindex: ✅

### Changes Made
- Spec files modified: {list}
- New spec files: {list}

### Still Drift (skipped)
{list}

### Next Steps
- `git diff .ai/` review
- Commit: `docs: sync drift fixes`
```

---

## Rules

### Must Do
- **Detect everything before fixing** — don't fix-as-you-go
- **Confirm every fix** — never auto-fix, even if it looks safe
- **Preserve history** — editing a spec must always append to Changelog
- **Order by severity** — 🔴 before 🟡
- **Explain "why flagged"** — commit info, timestamp
- **Chain `/reindex` at the end** of `--fix` mode

### Must Not
- ❌ **Check features.md drift** — that is `/reindex`'s job
- ❌ **Delete files without confirm** even if orphan
- ❌ **Overwrite spec file** — regenerate must merge or backup
- ❌ **Auto-generate spec from heuristic** — dev must review
- ❌ **Mark ✅ Done from sync** — status change needs test backing (suggest `/build --resume`)
- ❌ **Crash if not a git repo** — must gracefully fall back

---

## Edge Cases

**New project (specs/ empty)**
```
Project has no features yet — no drift to check
💡 Start with `/spec <requirement>`
```

**Massive drift (> 20 items)**
```
⚠️ Large amount of drift found ({X} items)
Possible causes: docs added after code (legacy) / long-running branch merge / /sync skipped for a long time

Recommended: fix 🔴 first, then 🟡 group by group
```

**Non-git project**
```
⚠️ Git unavailable — can still detect file-based
but will miss: last commit, recent activity, who/when
```

**Uncommitted changes**
```
⚠️ Uncommitted changes present ({X} files) — detection may be inaccurate
A) Continue  B) `git stash` first  C) Cancel and commit first
```

**Orphan in shared/common directory**
```
⚠️ Likely shared infrastructure — suggest adding to untracked.md instead of creating a spec
```

---

## Output Language

Respond in **Thai** / technical terms, paths, git output → **English**

---

## Examples

```
dev: /sync
AI: ## ✅ Spec ↔ Code in Sync — Scanned 15 specs, 5 modules, 42 files

dev: /sync
AI: ### 🔴 Critical Drift (1)
    **Orphan Code** — `{path}` created 2d ago, not referenced by any spec
    Run `/sync --fix` to fix

dev: /sync --fix
AI: [scan → report → fix one by one → chain /reindex]
    ✅ Sync Complete — Fixed: 1, Skipped: 0, Reindex: ✅
```
