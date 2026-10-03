---
description: Feature overview, or filter by task-id / module / keyword / developer
argument-hint: [mine | done | <task-id> | <module> | <keyword>]
---

# /status — Feature Status Overview

> **Language**: always talk to the dev in **Thai** (technical terms may stay English). This file is written in English only to save tokens — render every message/report below in Thai.

Read-only command for a feature overview and quick lookups
**Does not modify any file** — safe to run often

## Context Files

- `.ai/context/features.md`

**If `.ai/context/` doesn't exist** → tell the dev to run `/ai-init` and stop

**Multi-repo project**: run in a repo → the repo's `features.md` already has a `# Cross-repo` section (from `/reindex`)
Run at the project root → the project's `features.md` (cross-repo tasks) — for an overview of all repos, also read the At a Glance of each repo's `features.md` (don't read specs)

## Runtime Info

```bash
git config user.name
```
Used for the `mine` filter

---

## Input

**$ARGUMENTS** — dispatch by priority:

1. **Empty** → Overview mode
2. **`mine`** → filter by current git user
3. **`done`** → list all ✅ (hidden in overview)
4. **Match task-id** (`TASK-\d{8}-\d{4}` or `[A-Z]+-\d+`) → Detail view
5. **Match module name** (H1 in features.md) → Module filter
6. **Anything else** → Keyword search

---

## Step 1: Load features.md

parse:
- `At a Glance` counts + `Last reindex` timestamp
- Module sections (`# {Module Name}`)
- Feature entries (1 line: `- {icon} [TASK-id](link) — {Title} ({Dev}) — updated {date}`)
- `# Archived` section

> `features.md` is an index — details live in the spec file
> Only Detail mode follows the link to read the spec

---

## Step 2: Dispatch by Mode

### 🔹 Overview (no args)

Show active items — **exclude ✅ Done** (usually too many)

Order: 🔴 Blocked > 🚧 In Progress > 📋 Planned

```
## Project Status

**Total**: {X} | ✅ {X} | ⚠️ {X} | 🚧 {X} | 📋 {X} | 🔴 {X}

### 🔴 Blocked ({count})
- {task-id} ({module}): {name} — {blocker reason}

### 🚧 In Progress ({count})
- {task-id} ({module}): {name} — {developer}

### 📋 Planned ({count})
- {task-id} ({module}): {name} — created {relative time}

> {X} completed features hidden — `/status done` to see all
```

### 🔹 Mine

Features whose `**Created**:` / `**Last Updated**:` match the current git user
or that have recent commits by this user in the feature's files

```
## Your Tasks ({git user.name})

### 🚧 In Progress ({count})
- {task-id}: {name}
  - Last commit: {abbrev} "{message}" ({relative time})
  - Next: {hint from Known Gotchas / Implementation Status}
  - Spec: `.ai/context/specs/{task-id}.md`

### ✅ Recently Done (last 7 days)
- {task-id}: {name} — done {relative time}

### 📋 Planned
- {task-id}: {name}

> You have no tasks right now — `/spec` to start a new feature
```

git: `git log --author="{user.name}" --since="7 days ago" --oneline | head -20`

### 🔹 Task Detail

Read spec file: `.ai/context/specs/TASK-{id}.md` (or `CLOSED-TASK-{id}.md`) — not found → look in `<project>/.ai/context/specs/` (AI.md › Cross-repo Task)

cross-repo spec → add a `**Repos**:` line + per-repo Implementation Status table, and Next Actions points to the first repo not yet ✅ in build order
(`/build {task-id} --repo {name}`)

```
## {task-id} — {feature name} {status-icon}

**Module**: {module}
**Created**: {date} by {dev}
**Status**: {icon + label}
**Last Updated**: {date} by {dev}
**Spec**: `.ai/context/specs/{path}.md`

---

### Files (from Implementation Status)
- {list}

### Business Rules
{top 3-5 — for the rest say "see spec file"}

### Recent Activity
**Changelog**: {latest 3-5 entries}
**Git**: `git log -5 --format='- %h %s (%cr by %an)' -- <files>`

### Known Gotchas
{show all — important}

### Pending Questions
{unresolved Ambiguities — if all resolved, skip this section}

### Next Actions
- 📋 Planned → `/build {task-id}`
- 🚧 In Progress → `/build --resume`
- ⚠️ Untested → add tests, then `/build --resume`
- ✅ Done → if changes needed → `/change {task-id} "..."`
- 🔴 Blocked → resolve the blocker first
- ❌ / 📦 → closed; to revive → reopen (rename CLOSED-)
```

### 🔹 Module Filter

```
## {Module Name} ({total} features)

### 🚧 In Progress ({count})
### 📋 Planned ({count})
### ✅ Done ({count})
### 🔴 Blocked ({count})
```

### 🔹 Keyword Search

grep through `features.md` (feature names) + `specs/*.md` (Business Rules / Changelog / Gotchas)

```
## Search: "{keyword}"

### Matches ({count})

**In Feature Names:**
- {task-id} ({module}): {name} {status-icon}

**In Spec Content:**
- {task-id} ({module}): {name} {status-icon}
  > "{matching context}..."

{if nothing found → suggestions: /status, /status mine, try a shorter keyword}
```

---

## Step 3: Enrich with Git (Detail + Mine only)

Overview / keyword mode → **skip git** for speed

---

## Rules

### Must Do
- **Read-only strict** — no write/edit (read-only git queries are fine)
- **Concise** — fit on one screen
- **Sort by urgency** — 🔴 > 🚧 > 📋 > ⚠️ > ✅
- **Actionable next step** in Detail mode
- **Fast** — overview doesn't run git

### Must Not
- ❌ **Modify any file** — drift found → suggest `/reindex` (index drift) or `/sync` (code drift)
- ❌ **Output so long it needs scrolling**
- ❌ **Show all ✅ in overview**
- ❌ **Read spec files in overview / mine / module mode** (features.md is enough)

---

## Edge Cases

**No features yet**
```
## Project Status
No features in this project yet — start with `/spec <requirement>`
```

**features.md stale**
```
⚠️ features.md may be out of date — Last reindex: {date} ({N} days ago)
Suggested: /reindex
```

**Invalid task ID format**
```
❌ "{input}" is not a valid task-id
Format: TASK-YYYYMMDD-HHMM or {MODULE}-{NNN}
Search instead: /status {keyword}
```

**Git user not configured (mine mode)**
```
⚠️ Git user not configured
  git config --global user.name "Your Name"
Showing overview instead for now
```

---

## Output Language

Reply in **Thai** / technical terms, task-id, path, git output → **English**

---

## Examples

```
dev: /status          → overview of active tasks
dev: /status mine     → your own tasks + git activity
dev: /status TASK-20260501-1430  → detail + next action
dev: /status payment  → keyword search
dev: /status Auth     → module filter
```
