---
description: Create a recorded feature spec and risk analysis when the dev explicitly invokes /spec or asks for a spec; ordinary coding requests proceed directly
argument-hint: <requirement> [--quick]
---

# /spec — Create Feature Specification

> **Language**: always talk to the dev in **Thai** (technical terms may stay English). This file is written in English only to save tokens — render every message/report below in Thai.

Take a raw requirement from BA/PO or dev → analyze business rules + risks + edge cases →
ask the important ambiguities → save as a spec file

## Context Files

Always read before starting:
- shared project context (if any — see `~/.ai/AI.md` › Context Resolution): `PROJECT.md` + files in the context map relevant to the task
  - touches a contract in `integrations.md` → flag the consumer-side repos in risks + propose a shared update (never edit it yourself)
- project memory file at root (whichever of `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` exists) + `.ai/context/MEMORY.md` (if any — the team's file wins on conflict)
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/features.md` (overview only)

**If `.ai/context/` does not exist** → tell the dev to run `/ai-init` first, then **stop**

**Running at the project root** (multi-repo, cwd is not a git repo): read the shared context instead of a repo memory file,
then read the memory file + `ARCHITECTURE.md` of **only the repos the requirement touches** (after Step 0)

## Input

**$ARGUMENTS**

Parse rules:
- **requirement text** (required): the requirement — sentence, bullets, paragraph, or user story
- **Flags**: `--quick` — skip ambiguity questions (trust dev)

**If the argument is empty** → ask the dev:
```
Please provide the requirement to spec
Example: /spec ลูกค้าต้องการ login ด้วย email + password
```
then **stop** and wait for new input

---

## Runtime Info

Run:
```bash
git config user.name
git config user.email
date "+%Y-%m-%d %H:%M"
```

Use for the `**Created**:` field and Task ID generation

---

## Step 0: Identify Scope (only inside a multi-repo project)

No shared context (single repo) → skip to Step 1 (original behavior)

From the requirement + `PROJECT.md` (repo list) + `integrations.md` (contracts) → determine which repos it touches:

| Touches | Scope | Spec lives at |
|---|---|---|
| 1 repo | **repo** | `<repo>/.ai/context/specs/` (if run at the project root → tell the dev which repo it will be written to) |
| ≥ 2 repos (any number) | **cross-repo** | `<project>/.ai/context/specs/` |

cross-repo → propose the repo list + **build order** (provider before consumer, per `integrations.md`) for the dev to confirm:
```
This requirement touches {N} repos:
  1. api     — provider: add endpoint
  2. worker  — consumes event from api
  3. web     — calls the new endpoint
A) single cross-repo spec file, in this build order (recommended)
B) edit list / order: ...
```
❌ Never guess a repo with no evidence it is involved — if unsure, ask

---

## Step 1: Identify Module

From the requirement, guess which module/area this feature belongs to:

1. Read `features.md` → see existing module sections (or scan `specs/` for distinct Module fields)
2. Match requirement keywords against module names + the actual source dir structure
3. Multiple matches → ask the dev to clarify
4. No match (new module) → propose a module name + ask the dev to confirm

Examples:
- "login ด้วย email" → Auth
- "แสดงราคาสินค้า" → Product (if it exists) or propose a new one
- "comment ใน blog post" → Blog/Post exists → use it; otherwise → propose "Comment"

**Read module context**: if the module has its own rule file (e.g. `<module>/CLAUDE.md` or `<module>/AGENTS.md`) → read it before analyzing

---

## Step 2: Delegate to spec-analyzer

Send to the installed `spec-analyzer` agent for analysis. Use its provider-specific model and effort from `~/.ai/agents/models.json`; do not override them at invocation unless the dev asks.

**Input:**
- Requirement text (raw, as the dev typed it)
- Target module
- Relevant context files (`ARCHITECTURE.md`, module rule file if any)
- Mode: `normal` | `quick`
- Scope: `repo` | `cross-repo` + Repos (build order) + path of the shared context

**Expect output:**
- Business rules (written as "the system must do X when Y")
- Risks (security, data integrity, performance, breaking change, multi-tenant)
- Edge cases (validation, state, query, error, empty state)
- Dependencies (other modules, external lib/service)
- Proposed design (files, API shape, data model) — cross-repo: **split per repo** + contract changes between repos
- Ambiguity questions (max 3, only truly important ones)
- Confidence assessment

**If the runtime does not support subagents** → read `~/.ai/agents/spec-analyzer.md` and follow that process yourself. Report that the configured subagent model and effort were not used.
Output must be in the same format

> delegate = analyze in a separate context → saves main context

---

## Step 3: Ask Ambiguity (unless --quick)

Show the analyzer's questions (max 3) with options:

```
## Spec Draft: {Feature Name}

### ✅ Business Rules understood
1. ...

### 🔴 Risks found
- {risk}: mitigation?

### ❓ Questions (answer before confirm)
1. {question}
   - A) ...
   - B) ...
   - C) ...

Please answer all questions first, then I will proceed
```

**Wait for the dev's answers** — parse and map them to the options; if an answer is unclear, ask again

**With `--quick`**: skip this step, use sensible defaults for all, but list them in `## Assumed Defaults` of the spec file

---

## Step 4: Show Full Draft + Confirm

```
## Spec Draft (Full)

### Feature: {name}
### Module: {module}

### Business Rules
1. ...

### Edge Cases
- {case}: {handling}

### Risks + Mitigation
- 🔴 {risk}: {how to handle}

### Dependencies
- {module / lib}  ⚠️ NEW if it must be installed

### Proposed Design
**Files to create/modify:**
- {path} — {purpose}

**API / Interface:**
- {method} {path} — {purpose}

**Data model:**
{schema draft}

### Ambiguity Resolutions
1. Q: {question} → A: {answer}

---
Type "confirm" to save the spec
or type what you want changed, e.g. "change rate limit to 10/min"
```

**Loop until the dev confirms:**
- dev edits → update draft → show again
- dev "confirm" → Step 5
- dev "cancel" → abort, **create no file**

---

## Step 5: Generate Task ID

```bash
date "+TASK-%Y%m%d-%H%M"
```

Format: `TASK-YYYYMMDD-HHMM` e.g. `TASK-20260501-1430`
**Generate only now** — not when the command starts

If a file with this name already exists (collision) → append suffix `-B`, `-C`; never overwrite
In a multi-repo project check collisions in both `<project>/.ai/context/specs/` and every repo's `specs/` (task-id must be unique across the project)

---

## Step 6: Create Spec File

Create `.ai/context/specs/{task-id}.md`:

Spec file content (business rules, edge cases, risks, resolutions) is written in **Thai**; headings, technical terms, paths, code stay English.

```markdown
# {Task ID} — {Feature Name}

**Module**: {module}
**Status**: 📋 Planned
**Created**: {YYYY-MM-DD HH:MM} by {git user.name} \<{git user.email}\>
**Last Updated**: {YYYY-MM-DD HH:MM} by {git user.name} \<{git user.email}\>

---

## Requirement (Original)

{raw requirement as the dev typed it — preserved for traceability}

---

## Business Rules

1. ...

---

## Risks

| Level | Category | Risk | Mitigation |
|---|---|---|---|
| 🔴 | Security | {risk} | {how} |

---

## Edge Cases

- **{case}**: {expected behavior}

---

## Dependencies

### Internal
- Module {X}: {reason}

### External
- {library / service}: {reason}

---

## Proposed Design

### Files

**Create:**
- `{path}` — {purpose}

**Modify:**
- `{path}` — {what changes}

### API / Interface

| Method | Path | Purpose | Auth |
|---|---|---|---|

### Data Model

{schema}

### Flow

{sequence / state — include only when complex}

---

## Ambiguity Resolutions

1. **Q**: {question}
   **A**: {answer}
   **Rationale**: {why}

---

## Assumed Defaults (--quick mode)

_Include only when run with `--quick`_

- {assumption}

---

## Implementation Status

_(TBD — pending /build)_

---

## Changelog

- **{YYYY-MM-DD}** ADDED — Initial spec

---

## Known Gotchas

_(None yet — will be populated during /build)_
```

---

### Cross-repo spec

Create at `<project>/.ai/context/specs/{task-id}.md` — same structure as above, differing only in:

```markdown
# {Task ID} — {Feature Name}

**Scope**: cross-repo
**Repos**: {repo-1}, {repo-2}, ..., {repo-N}   ← build order
**Module**: {feature area}
**Status**: 📋 Planned   ← overall (computed from Implementation Status — see AI.md › Cross-repo Task)
...

## Business Rules          ← written once, shared by all repos

## Contract Changes        ← what one repo provides for another to use

| Provider | Consumer(s) | Channel | Contract | Breaking? |
|---|---|---|---|---|
| `{repo}` | `{repo}`, `{repo}` | {REST / event / ...} | {shape / schema path} | yes / no |

## Proposed Design

### {repo-1}
**Create:** / **Modify:** — paths prefixed with the repo name (`{repo-1}/src/...`)

### {repo-2}
...

## Implementation Status

| Repo | Status | Files | Tests |
|---|---|---|---|
| {repo-1} | 📋 | — | — |
| {repo-2} | 📋 | — | — |

## Changelog

- **{YYYY-MM-DD}** ADDED [{repo-1}, {repo-2}, ...] — Initial spec
```

Contract Changes that affect `integrations.md` → show the proposed diff in the Final Report (dev confirms before writing — see Ownership in AI.md)

---

## Step 7: Final Report

```
## ✅ Spec Created: {Task ID}

**Feature**: {name} | **Module**: {module} | **Status**: 📋 Planned

### File Created
- `.ai/context/specs/{task-id}.md`

### Business Rules (summary)
1. ...

### 🔴 Key Risks to Watch
- {risk}

### Next Steps
1. Review spec file — add/edit if still unclear
2. `/build {task-id}` to start implementing
3. `/reindex` when you want to update features.md

### Pro tips
- requirement changes before build → edit the spec file directly
- changes after build → use `/change {task-id} "..."`
```

**Cross-repo spec** → replace `### Next Steps` above with ready-to-copy commands, one session per repo, in build order:

```
### Next Steps (cross-repo — one session per repo, in build order)
1. Review spec: `{project}/.ai/context/specs/{task-id}.md`
2. Build each repo in a **fresh session** (only that repo's context + spec loaded, no history from other repos):
   cd {project}/{repo-1} && /build {task-id} --repo {repo-1}
   cd {project}/{repo-2} && /build {task-id} --repo {repo-2}
   ...
   (start {repo-N} only after {repo-N-1} is ✅ — it depends on that contract)
3. `cd {project} && /reindex` after the last repo

Alternative: `cd {project} && /build {task-id}` builds every repo in one session —
fine for small changes (few files per repo); for larger ones history from earlier repos stays in context and costs more tokens.
```

- Use the assistant's real invocation syntax (`$build` for Codex, `/build` for Claude / ZCode)
- Repos with no dependency between them (no shared Contract Changes) → mark them as runnable in parallel sessions
- Recommend the one-session alternative instead only when Proposed Design is small (a few files per repo)

---

## Rules

### Must Do
- **Read ARCHITECTURE.md + module rule** before analyzing, to avoid proposing conflicting patterns
- **Delegate to spec-analyzer** — do not analyze in the main context (unless the runtime doesn't support it)
- **Ask only truly important ambiguities** (max 3)
- **Preserve original requirement** in the spec file
- **Wait for dev confirm** before writing any file, every time (even with `--quick`)

### Must Not
- ❌ **Write code in this command** — this is the spec phase
- ❌ **Touch `features.md`** — that is `/reindex`'s job
- ❌ **Generate Task ID before Step 5**
- ❌ **Ask more than 3 ambiguity questions**
- ❌ **Overwrite an existing spec file**

### Edge Cases

- **Requirement spans multiple modules**: ask whether it should be split into 2 specs
- **Requirement spans multiple repos**: single cross-repo spec file (Step 0) — ❌ never split into duplicate specs per repo
- **Repo has no `.ai/`**: a cross-repo spec can still be created, but recommend `cd <repo> && /ai-init` before `/build`
- **Requirement duplicates an existing feature**: flag + ask — may need `/change` instead of `/spec`
- **Requirement is just an idea**: ask to clarify first; if still too vague → recommend refining it first

---

## Output Language

- Reply to the dev in **Thai**
- Spec file: business rules / edge cases → Thai; technical terms, paths, code → English
- Original requirement → preserve the language the dev typed

---

## Examples

**Normal flow**
```
dev: /spec ลูกค้าต้องการระบบ comment ใน blog post โดยไม่ต้อง login
AI: [identify module → delegate → ask 3 questions → draft → confirm → save]
    ✅ Spec Created: TASK-20260501-1430
```

**Quick mode**
```
dev: /spec --quick เพิ่ม GET /health endpoint คืน {status: "ok"}
AI: [skip ambiguity → draft → confirm → save]
    ⚠️ Assumed defaults: no auth, no rate limit
```

**Vague requirement**
```
dev: /spec อยากได้ระบบ notification
AI: "Requirement too broad — which channel? triggered by what? ..."
```

**Conflict with existing feature**
```
dev: /spec ให้ user login ด้วย OTP ผ่าน SMS
AI: "⚠️ Found TASK-20260424-1153 (Login + JWT) which may overlap
     A) /spec — separate new feature
     B) /change TASK-20260424-1153 — change the existing auth flow"
```
