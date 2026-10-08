---
description: Scaffold .ai/ context and project memory only when the dev explicitly invokes /ai-init or asks to initialize project context; a missing .ai/ does not trigger this skill
argument-hint: [--project | --repo] [--lang en|th] [--force]
---

# /ai-init — Bootstrap Project Context

> **Language**: always talk to the dev in **Thai** (technical terms may stay English). This file is written in English only to save tokens — render every message/report below in Thai.

Prepare a repo for the `/spec → /build → /change` workflow — 2 levels:

| Level | Run at | Creates |
|---|---|---|
| **Repo** (default — original behavior) | git repo root | memory file at root (or `.ai/context/MEMORY.md` if the team already tracks a memory file) + `.ai/context/` (`ARCHITECTURE.md`, `features.md`, `untracked.md`, `specs/`) |
| **Project** (multi-repo) | folder containing multiple git repos | `<project>/.ai/context/` (shared + cross-repo specs) + Repo-level for each detected repo |

All context is **local-only to this machine** — auto-excluded from git, never committed to the repo.

**No guessing** — everything written to files must come from reading real code in this run.

## Input

**$ARGUMENTS**

- `--project` — do **project** level (skip detection)
- `--repo` — do **repo** level (skip detection)
- `--force` — overwrite existing files (default: merge, don't overwrite)
- `--lang en|th` — language of the **context files** written (default `en` — fewer tokens on every session). See [Context Language](#context-language)

---

## Step 0: Choose Level (Repo / Project)

`--project` / `--repo` given → use it, no detection.

No flag → detect from cwd:

```bash
git rev-parse --show-toplevel 2>/dev/null          # is cwd inside a repo / where is its root
for d in */; do [ -e "$d.git" ] && echo "$d"; done  # direct children that are git repos (.git may be a dir or file — worktree/submodule)
```

| Situation | Level |
|---|---|
| cwd is in a git repo and has no child repos | **Repo** — use the repo root (if cwd is a subdir, tell the dev it will run at root) → Step 1-6 |
| cwd is not a git repo and (has child repos or has `.ai/context/PROJECT.md`) | **Project** → [Project Mode](#project-mode) |
| cwd is a git repo **and** has child repos (meta-repo / submodule) | ask the dev |
| not a git repo and no child repos | ask the dev whether to create an empty project context now (add repos later) or it's the wrong folder |

Always show the dev the chosen level before starting the next Step — ❌ never guess when ambiguous.

**Repo inside a multi-repo project**: walk up from the repo root looking for `<dir>/.ai/context/PROJECT.md` (see `~/.ai/AI.md` › Context Resolution).
If found → read `PROJECT.md` (+ `conventions.md`) before Step 2, then **never duplicate anything already in shared** into the repo's files — reference the path instead.

---

## Step 1: Detect Existing Setup

Check what already exists:

- does `.ai/context/` exist
- project memory files at root (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) — which ones exist
- **which memory files belong to the team** (tracked in git):
  ```bash
  git ls-files CLAUDE.md AGENTS.md GEMINI.md .claude/CLAUDE.md AGENTS.override.md
  ```
  At least 1 result → **Team memory mode** (see 4.1) — tell the dev right now that those files will not be touched
- does `.ai/context/MEMORY.md` exist (personal memory from a previous Team memory mode run)
- **Legacy context**: `.claude/context/`, `.codex/context/`, `.gemini/context/`, `.agents/context/` (old per-tool setup)
- **Legacy commands/agents/skills**: `.claude/commands/`, `.claude/agents/`, `.codex/prompts/`, `.codex/agents/`, `.codex/skills/`, `.agents/skills/`, `.agents/workflows/`

> ⚠️ **project-level commands always win over global** — if the repo still has `.claude/commands/spec.md`,
> `/spec` in that repo runs the old one, not the central one, and it usually points to paths that have moved.
> **Delete it, do not fix its paths instead** — otherwise it becomes a second set to maintain separately.

**If legacy found** → propose migration:
```
Found old per-tool setup:

Context (must merge):
- .claude/context/specs/ ({N} files)
- .codex/context/specs/ ({N} files)

Commands/agents (must delete — the central set at ~/.ai/ already does this):
- .claude/commands/ ({N} files), .claude/agents/ ({N} files)
- .codex/agents/ ({N} files)

A) Full migrate — merge context into .ai/ + delete old commands/agents (recommended)
B) Migrate context only — keep old commands (they will override the central set)
C) Skip — create an empty .ai/
```

**Migration steps (option A):**

1. **Context** → `git mv` to `.ai/context/` (no copy+delete — history would break)
   - specs without a standard Task ID (e.g. `TASK-POS-CRM-SSO.md`) → rename to `TASK-YYYYMMDD-HHMM`
     using the file's first commit date (`git log --diff-filter=A --format=%ad --date=format:%Y%m%d-%H%M -- <file> | tail -1`)
     then **write a migration note** at the top of the file stating its original name
   - specs whose task ID collides across tools → show the diff and ask the dev pair by pair
2. **Old commands/agents** → `git rm -r` them
   If files have pending local modifications → check `git diff` first that it's really just a path rewrite, then `git rm -rf`
3. **`.claude/settings.json`** → fix dead permissions
   - `Edit(.claude/context/**)` → `Edit(.ai/context/**)`
   - remove `Edit(.claude/commands/**)`, `Edit(.claude/agents/**)` (those folders no longer exist)
4. **Delete empty directories** left after the move (e.g. `.codex/`)
5. **Keep**: `.claude/settings.json` and other note files in `.claude/*.md` that are real project docs

**If `.ai/context/` is already complete and no `--force`** → report it's ready + suggest `/status`, then stop.

---

## Step 2: Analyze Codebase

Survey the real code (never skip this step):

| Topic | Find from |
|---|---|
| Language / runtime | manifest file (`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, …) |
| Framework | dependency list + entry point |
| Package manager | lockfile (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `uv.lock`, …) |
| Test runner + command | script section in manifest + config file |
| Lint / format / typecheck | script section + config file |
| Database / ORM | dependency + config/connection file |
| Migration tool + command | script section + migration folder |
| Module layout | real source dir structure (don't assume `src/modules/`) |
| Layering pattern | read 1-2 sample modules |
| Error handling | find custom exception / error classes in use |
| Auth | find guard / middleware / decorator |
| Multi-tenant | find a tenant key repeated across queries (e.g. `storeCode`, `tenantId`, `orgId`) |
| API shape | response wrapper / envelope in use |
| Naming convention | from real file names + class/function names |
| CI | `.github/workflows/`, `.gitlab-ci.yml` |

**Git info**: `git config user.name`, `git log --oneline -20` (see commit message convention)

**Team memory mode**: read every team memory file first — they are rules the team agreed on (authoritative).
Analyze to find **what the team files don't cover yet** + where the team files **don't match the code** (keep for the Final Report).

---

## Step 3: Show Findings + Confirm

Summarize findings for the dev to check before writing files:

```
## Codebase Analysis

**Stack**: {language} {version} / {framework} / {db} / {package manager}
**Test**: {runner} — `{command}`
**Lint**: `{command}` | **Typecheck**: `{command}`
**Migration**: `{command}`

**Module layout**: `{path pattern}` ({N} modules: {list})
**Layering**: {what was actually found, e.g. Controller → UseCase → Repository → Entity}
**Error handling**: {what was actually found}
**Auth**: {what was actually found}
**Multi-tenant**: {tenant key found | "not found — single tenant"}
**Commit convention**: {what git log shows}

### ❓ Please confirm
1. {points still unclear after reading code — max 3}

**Context language**: {en | th} (change with `--lang`)

### Files to create
- `{memory file}` — project memory
  (Team memory mode: `.ai/context/MEMORY.md` instead — team's `{team memory files}` untouched)
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/features.md`
- `.ai/context/untracked.md`
- `.ai/context/specs/.gitkeep`

and edit `.git/info/exclude` — the whole context set will be **local-only**, never committed to the repo

Type "confirm" to create
```

**Always wait for confirm before writing files.**

---

## Step 4: Write Files

Use templates from `~/.ai/templates/` as the skeleton, filled with real data from Step 2.

**4.1 Project memory file** (root) — named after the assistant currently running.
If another file from the same family already exists (e.g. `CLAUDE.md` exists but Codex is running) → **don't create a duplicate**.
Create an `AGENTS.md` with a single line pointing to the existing one instead:
```markdown
See [CLAUDE.md](CLAUDE.md) — same content, single source of truth.
```

Content = template `project-memory.md` filled with: domain model, tech stack, layering, critical rules, conventions, directory structure as actually read.

**Team memory mode** (Step 1 found a tracked memory file) — replaces all rules above:
- ❌ **never edit / append / overwrite / rename** tracked memory files — even with `--force`
- ❌ **never create a new memory file at root** (including a one-line pointer file) — the day the team adds a file with that name, `git pull` will conflict with the untracked file
- ✅ write personal memory to **`.ai/context/MEMORY.md`** (already excluded with `.ai/`) — same `project-memory.md` template, but:
  - top line: `> Team memory: {team memory files} (tracked — read before this file / on conflict → team wins)`
  - write **only what the team files don't cover yet** — for topics the team already wrote, write only `see {team file} › {topic}` ❌ never copy them over
  - `MEMORY.md` already exists → merge, don't overwrite (unless `--force`)
- an existing memory file that is **not tracked** (the dev's own) → not the team's, use the normal rules above

If the repo is in a multi-repo project (Step 0 found `PROJECT.md` or running from Project Mode) → keep the **Multi-repo project** line in the template (relative path to the shared context),
then write only this repo's specifics — domain / conventions already in shared are referenced instead of copied.
Otherwise → remove that line.

**4.2 `.ai/context/ARCHITECTURE.md`** — ADRs + patterns + anti-patterns detected.
Every entry must cite a real file path as evidence.

**4.3 `.ai/context/features.md`** — empty template (regenerated by `/reindex`)

**4.4 `.ai/context/untracked.md`** — list shared infra not counted as features (common/, utils/, config/)

**4.5 `.ai/context/specs/.gitkeep`**

**4.6 Local-only context (default)** — make context visible on this machine only

Add to the working repo's `.git/info/exclude` (clone-level exclude — this file can never be committed/pushed along):
- the memory file actually created (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`) — none in Team memory mode (nothing created at root)
- `.ai/`

❌ Never add tracked files to exclude — it has no effect on tracked files and misleadingly suggests they're hidden.

```
AGENTS.md
.ai/
```

- The whole context set still exists and works normally — git just can't see it (`git status` must not show it)
- ❌ Don't use the repo's `.gitignore` — that file must be committed, so others would immediately know hidden context exists
- No need to create `.gitattributes` — `features.md` is no longer pushed, so no merge conflicts
- To share with the team later: remove these lines from `.git/info/exclude`, then `git add` + commit normally
  (if a `.gitattributes` `merge=ours` remains from the old flow, mention in the final report that it's still there but no longer needed)

---

## Step 5: Retroactive Spec (optional)

If the repo already has a lot of code:

```
This repo already has {N} modules but no specs

A) Leave it for now — use /spec for new features (recommended)
B) Run /sync now — see how much orphan code there is, then gradually create retroactive specs
```

**Never auto-generate retroactive specs for the whole repo** — token-heavy and low quality.

---

## Step 6: Final Report

```
## ✅ Project Initialized

### Files Created
- `{memory file}` ({N} lines)   ← Team memory mode: `.ai/context/MEMORY.md` ({N} lines) — `{team memory files}` untouched
- `.ai/context/ARCHITECTURE.md` ({N} ADRs)
- `.ai/context/features.md` (empty index)
- `.ai/context/untracked.md` ({N} entries)
- `.ai/context/specs/` (empty)

### ⚠️ Review yourself
{points inferred from code that may not match real intent}
1. ...

### 💬 Suggestions for the team (Team memory mode — if any)
Where the team memory file **doesn't match the code** or misses something important — AI doesn't fix it, the dev decides (e.g. open a PR):
- `{team file}` › {topic}: says {X} but the code actually does {Y} — evidence `{path}`
  ```diff
  {proposed diff}
  ```

### Migration Summary (if any)
- Moved: {N} spec files → `.ai/context/specs/` (git mv)
- Renamed: {N} specs without a standard Task ID
- Deleted: {N} legacy commands/agents
- Fixed: `.claude/settings.json` permissions

### Next Steps
1. Review `{memory file}` + `ARCHITECTURE.md` — fix anything wrong directly
2. Check that `git status` **does not show** `.ai/` or the memory file — context is local-only (excluded in `.git/info/exclude`), no need to commit, and ❌ don't commit
   (Team memory mode: team memory files must have **no diff** — `git diff --stat {team files}` is empty)
3. `/spec <requirement>` to start the first feature
4. `/sync` to see how much code has no spec yet
```

---

## Project Mode

Do 2 parts in order: **shared context** at `<project>/.ai/context/` → **repo-level** for each repo inside.
Number and names of repos are not fixed — use only what is actually detected.

### P1. Detect

- **repo** = direct child of the project with its own `.git`, where `git -C <dir> rev-parse --show-toplevel` = that dir
- **not a repo** → skip with reason: `not a git repository` / `invalid .git` (rev-parse fails)
- hidden dirs (`.ai`, `.idea`, ...) and `node_modules` don't count
- per repo also check: is `.ai/context/` already complete, is there a legacy setup (Step 1)
- shared: does `<project>/.ai/context/` already exist

### P2. Confirm Plan

```
## Project: {project dir}

Shared context: {project}/.ai/context/   {create new | exists — merge, no overwrite | exists — overwrite (--force)}
Context language: {en | th} (shared + every repo below — change with --lang)

Detected repositories:
  ✓ api        → will init
  ✓ web        → will init
  ✓ worker     → skip (.ai/context/ already complete — use --force to redo)
  - docs       (not a git repository)

A) Do shared + every ✓ repo (recommended)
B) Shared only — then cd <repo> && /ai-init one by one later
C) Pick repos: {names}
```

**Always wait for the dev's choice before writing files.**

### P3. Shared Context — Analyze (light — never read code of the whole project)

Per repo read only:
- the repo's memory file + `.ai/context/ARCHITECTURE.md` (if present) — use instead of reading code
- manifest (`package.json`, `go.mod`, ...) → stack
- where repos talk to each other: base URL / API client / OpenAPI / proto / queue topic / env pointing to another repo
- `git log --oneline -10` → is a commit convention shared

### P4. Shared Context — Write

Use templates from `~/.ai/templates/project/` filled with real data from P3 (remove `<!-- TEMPLATE: ... -->` lines).

| File | Contains | ❌ Must not contain |
|---|---|---|
| `PROJECT.md` | repo list, shared domain, context map | stack/layering details of any single repo |
| `ARCHITECTURE.md` | system overview + ADRs affecting ≥ 2 repos | single-repo ADRs |
| `conventions.md` | conventions **actually identical** across repos | things that differ per repo |
| `integrations.md` | contracts between repos with real paths | — |

Also add (for cross-repo tasks — see AI.md › Cross-repo Task):
- `features.md` — empty template from `~/.ai/templates/features.md` (`/reindex` at the project root regenerates it)
- `specs/.gitkeep` — only specs touching ≥ 2 repos / single-repo specs stay in that repo

**Project memory file** at the project root — short, paths only (named after the running assistant — same rules as 4.1).
Project root is a git repo that already tracks a memory file → skip (Team memory mode — `PROJECT.md` serves instead).
Used when the dev opens a session at the project root for cross-repo work:
```markdown
# {Project Name}
Multi-repo project — shared context: [.ai/context/PROJECT.md](.ai/context/PROJECT.md)
Read `PROJECT.md` first, then load `<repo>/.ai/context/` only for repos the task touches
```

**Local-only**: project root is not a git repo → nothing to do / is a git repo → exclude `.ai/` + memory file as in 4.6

### P5. Repo-level — one repo at a time

Run Repo mode Step 1-4 on each repo chosen in P2, where:
- the shared context from P4 already exists → **never duplicate it** into the repo's memory file / `.ai/` — reference the path instead
- **save context**: if the runtime supports subagents → delegate each repo's Step 2 (analyze) to a separate subagent (parallel OK) and take back only the summary
  if not → finish one repo completely before moving to the next; don't read code of multiple repos at once
- Step 3 (confirm) is merged into one round: show the analysis of all repos, then confirm once
- a repo errors (can't read/write, legacy migrate fails) → record the reason and **continue with the next repo** — never stop everything
- legacy setup in a repo → ask per Step 1 rules for that repo
- ❌ never touch repos the dev didn't choose, or repos whose `.ai/` is already complete (unless `--force`)

### P6. Final Report

```
## ✅ Project Initialized: {project}

### Detected repositories
  ✓ api
  ✓ web
  ✓ worker
  - docs (not a git repository)

### Installed
  ✓ {project}/.ai   (PROJECT.md, ARCHITECTURE.md {N} P-ADR, conventions.md, integrations.md {N} contracts, features.md, specs/)
  ✓ {project}/{memory file}
  ✓ api/.ai + api/{memory file}
  ✓ web/.ai + web/{memory file}

### Skipped
  - worker: .ai/context/ already exists (use --force to redo)
  - docs: not a git repository

### Failed
  ✗ {repo}: {reason}

### Summary
  installed {N} · skipped {N} · failed {N}

### ⚠️ Review yourself
1. {contracts / conventions inferred from code that may be wrong}

### Next Steps
1. Review `{project}/.ai/context/PROJECT.md` + `integrations.md`
2. skipped/failed repos → `cd <repo> && /ai-init`
3. repos added later → `cd <repo> && /ai-init` (finds shared automatically) then add a row in `PROJECT.md`
4. tasks touching multiple repos → `cd {project} && /spec <requirement>` (cross-repo spec)
```

---

## Rules

### Must Do
- **Read real code before writing any line** — every claim needs a file path reference
- **Confirm before writing files**
- **Merge, don't overwrite** existing files (unless `--force`)
- **Consolidate context into a single `.ai/`** — not split per tool
- **Multi-repo: shared lives only in `<project>/.ai/`** — repos reference the path, don't copy
- **Delete the project's old commands/agents** — the central set at `~/.ai/` replaces them
- **Always use `git mv` / `git rm`** when moving or deleting tracked files — history must not break

### Must Not
- ❌ **Write stack/patterns not verified from code** — if not found, write "not found", don't guess
- ❌ **Delete or overwrite existing files without asking**
- ❌ **Create a duplicate memory file** if another from the same family exists
- ❌ **Touch team-tracked memory files** (even with `--force`) — personal memory goes to `.ai/context/MEMORY.md`
- ❌ **Fix paths in old `.claude/commands/` instead of deleting** — project-level wins over global, it becomes a second set
- ❌ **Auto-generate retroactive specs for the whole repo**
- ❌ **Copy shared context into a repo** — repos reference `<project>/.ai/context/`
- ❌ **Hardcode repo names** (e.g. web/api) — use only what is detected
- ❌ **Commit / push `.ai/` or the memory file** — context is local-only to this machine (unless the dev says so)

---

## Context Language

Templates in `~/.ai/templates/` are English. `--lang` picks the language of the **prose** written into context files
(memory file / `MEMORY.md`, `ARCHITECTURE.md`, `untracked.md`, and in Project Mode `PROJECT.md`, `conventions.md`, `integrations.md`):

| `--lang` | Prose | Always English |
|---|---|---|
| `en` (default) | English — fewer tokens, these files load on every session | headings, table headers, technical terms, paths, code, commands |
| `th` | Thai | same |

- Same structure either way — only prose changes; never maintain a second template set
- Merging into an existing file (no `--force`) → keep **that file's existing language**, ignore `--lang`
- Project Mode: one `--lang` for shared + every repo in the run
- Spec files are not affected — spec content is always Thai (see `~/.ai/AI.md` › Output Language)

---

## Output Language

- Reply to the dev in Thai (technical terms may stay English)
- Context files → language per [Context Language](#context-language)
