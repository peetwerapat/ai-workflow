# ai-agent — shared AI workflow for every project

The `/spec → /build → /change` workflow is available when you want a specification and an audit trail. It works with **Claude Code**, **Codex CLI**, **Antigravity CLI (`agy`)**, and **ZCode** in any repository. For ordinary code changes, an assistant can inspect the available context and work directly without creating a spec.

```
ai/                      ← single source of truth
├── AI.md                  shared rules (workflow, status vocabulary, critical rules)
├── commands/              /ai-init /spec /build /change /status /reindex /sync
├── agents/                spec-analyzer, impact-analyzer, code-reviewer, debugger, codebase-explorer
├── workflows/             helper routing, practical validation, completeness, feedback
├── tools/                 Python tools: index, validation, context, installation, doctor/rollback, evaluation
├── evals/                 behavioral rubrics (10 scenarios)
└── templates/             repo-level files for /ai-init
    └── project/           shared context files for multi-repo projects
```

## Install

```bash
git clone <repo> && cd ai-workflow
./install.sh              # choose what to install from the menu
./install.sh all          # install everything without a menu
./install.sh claude       # install one target (claude | codex | antigravity | zcode | shell)
./install.sh --status     # show what is installed
./install.sh --doctor     # check config, symlinks, and generated files for drift
./install.sh --rollback   # restore the previous installation unless managed files changed afterward
./install.sh --update     # fetch the source and reinstall
./install.sh --uninstall  # remove only files created by this script, including ~/.ai-agent and shell wrappers
```

### Remove the cloned folder after installation

Before installing, `install.sh` **copies itself and `ai/` to `~/.ai-agent`**, then reruns from there. All symlinks and shell wrappers point to `~/.ai-agent`, not to the cloned folder.

```
~/.ai-agent/          ← permanent store (do not delete)
├── ai/                 copy of the repo's ai/
├── install.sh          copy; use it for --update / --uninstall
├── .source             git remote and installed commit (used by --update)
└── .install-prefs      selected options, preserved across updates
```

After installation, the script tells you that the clone can be removed. For future updates, you do not need to clone again:

```bash
~/.ai-agent/install.sh --update     # clone the source to a temp folder, copy it over, and reinstall with saved options
```

Running `./install.sh` without arguments opens a menu. By default, it selects only targets whose binaries are available:

```
  Select assistants to install

  ❯ ◉ Claude Code        found claude
    ◉ Codex CLI          found codex
    ◯ Antigravity CLI    agy not found
    ◉ ZCode              found ~/.zcode
    ◉ Shell wrapper      auto-sync when codex/agy starts

  ↑/↓ move · space toggle · a select all · n clear all · enter confirm · q quit
```

| Key | Action |
|---|---|
| `↑` `↓` or `k` `j` | Move through the list, wrapping at either end |
| `space` | Toggle the selected item |
| `1`–`5` | Jump to an item and toggle it |
| `a` / `n` | Select all / clear all |
| `enter` | Confirm |
| `q` or `Esc` | Quit without installing |

Selections are saved in `.install-prefs` (under `~/.ai-agent/` after installation; it is gitignored), so you do not have to select them again. Delete this file to return to auto-detection. Non-interactive runs (CI / scripts) reuse saved options, or set `AI_AGENT_YES=1` to skip the menu.

`install.sh` can also add `codex()` and `agy()` wrappers to your shell rc file. They sync skills before each launch.

Before launching, a wrapper runs doctor for that provider. If generated files match their source, generation is skipped. If syncing fails, it prints an error and stops before launching the assistant.

To leave your shell rc file untouched, run `AI_AGENT_NO_SHELL=1 ./install.sh` (you will need to run `./install.sh codex` or `./install.sh antigravity` yourself after changing a command).

Existing files are backed up as `*.bak-YYYYMMDD-HHMMSS` before being overwritten, except this script's own symlink and broken symlinks left behind by deleting an old clone.

### Installation locations

| | Claude Code | Codex CLI | Antigravity CLI | ZCode |
|---|---|---|---|---|
| Memory | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | — (no global rules file; skills read `~/.ai/AI.md`) | `~/.zcode/AGENTS.md` |
| Commands | `~/.claude/commands/*.md` (symlink) | `~/.codex/skills/<n>/SKILL.md` (generated) | `~/.gemini/config/skills/<n>/SKILL.md` (generated) | `~/.zcode/commands/*.md` (symlink) |
| Agents | `~/.claude/agents/*.md` (generated) | `~/.codex/agents/*.toml` (generated) | `~/.gemini/config/agents/*.md` (generated) | `~/.zcode/agents/*.md` (generated) |
| Invoke with | `/spec` | **`$spec`** | Skill name (for example, `spec`) | `/spec` |

**Claude** and **ZCode** use command symlinks pointing to `~/.ai-agent/ai/commands/`. Codex and Antigravity generate their command files. Update all of them with `~/.ai-agent/install.sh --update`.

### Configure analyzer models and effort

Edit `ai/agents/models.json` for each agent and provider, then rerun `./install.sh <provider>`, for example `claude`, `codex`, `antigravity`, or `zcode`:

```json
{
  "spec-analyzer": {
    "claude": {"model": "sonnet", "effort": "medium"},
    "codex": {"model": "gpt-6-luna", "effort": "xhigh"},
    "antigravity": {"model": "pro"},
    "zcode": {"model": "inherit"}
  }
}
```

Claude uses `effort`, Codex uses `model_reasoning_effort`, and ZCode uses `thoughtLevel` when a specific model is configured (for example, `{"model": "glm-5.3", "effort": "high"}`). Antigravity CLI accepts the `inherit` / `flash` / `pro` model tiers in agent files, but its published schema does not support agent-level effort, so the installer rejects `effort` for that provider.

All five agents are read-only. Generated Codex agents also set `sandbox_mode = "read-only"`. If the runtime has no subagent tool, commands analyze in the main context, and per-agent model and effort settings have no effect.

**Codex** (0.155+) no longer uses `~/.codex/prompts/`; custom commands must be **skills** (`~/.codex/skills/<name>/SKILL.md`) and are invoked with **`$`**, not `/`. Skill frontmatter accepts only `name`, `description`, `license`, `allowed-tools`, and `metadata`.

**Antigravity** (`agy`) also uses skills. Its global customization root is `~/.gemini/config/` (Google is migrating away from legacy `*.md` workflows, so use skills directly).

Antigravity has no global rules file; rules are directory-based (`AGENTS.md` / `GEMINI.md`, discovered from the working directory upward). Its generated `SKILL.md` therefore instructs the assistant to read `~/.ai/AI.md` at startup.

**ZCode** (Z.ai desktop app, agent `glm`) reads config similarly to Claude. Its `description` / `argument-hint` frontmatter and `$ARGUMENTS` work directly. ZCode skips symlinks in `~/.zcode/agents/`, so agents are generated as regular files with a `generated by ai-agent` marker. After editing `ai/agents/*.md` or `ai/agents/models.json`, rerun `./install.sh zcode`. There is no shell wrapper because ZCode is launched from the app; it is detected from `~/.zcode`, not from a PATH binary.

Codex and Antigravity have `codex()` / `agy()` shell wrappers added by `install.sh`; they sync before launch automatically.

`~/.ai` is a symlink to `~/.ai-agent/ai/`, so every assistant can use the same paths (for example, `~/.ai/agents/spec-analyzer.md`).

## Usage

For a normal request such as “Add usage below the model name,” the assistant reads available context, inspects the code, makes the change, validates it, and reports the result. It does not create a spec or run `/ai-init` automatically, even if the repo has no `.ai/`. Use the commands below when you want a workflow with a recorded spec and change history.

```
New repo:       /ai-init                       scaffold .ai/ + project memory from the actual code
Multi-repo:     /ai-init --project             (from the project root) shared context + .ai/ in each repo
Context language: /ai-init --lang th           write context files in Thai (default: en)
New feature:    /spec <requirement> → /build   → /reindex
Change existing: /change <task-id> "<desc>"    → /reindex
Overview:       /status | /status mine | /status <task-id>
Check drift:    /sync [--fix]
Handoff:        /handoff [task-id]
Record a lesson: /learn <confirmed rule, scope, and evidence>
Review code:    /review [scope]
Debug an issue: /debug <symptom and reproduction steps>
Find code/flow: /explore <question or module>
```

> **Codex uses `$` instead of `/`** — `$spec`, `$build`, `$ai-init`
> **Antigravity** invokes the skill by name (use `/skills` to list them).
> **ZCode** uses `/` like Claude — `/spec`, `/build`.

## File languages

| File | Language |
|---|---|
| `ai/` (AI.md, commands, agents, templates) | English, to reduce tokens for AI (AI.md is loaded every session) |
| Context files in work repos (memory, `MEMORY.md`, `ARCHITECTURE.md`, `PROJECT.md`, etc.) | Choose with `/ai-init --lang en\|th` (default: `en`); later edits follow each file's existing language |
| Specs (`specs/TASK-*.md`) | Thai for business rules and edge cases, with English technical terms |
| Assistant replies | Thai |

## Two context layers

| Layer | Location | Contents |
|---|---|---|
| **Global** | `~/.ai/AI.md` | Workflow, status vocabulary, and critical rules for every project |
| **Project shared** (optional) | `<project>/.ai/context/` | System overview, shared domain and conventions, contracts between repos |
| **Repository** | `.ai/context/` + the root memory file | Domain, stack, architecture, and specs |

```
<repo>/
├── CLAUDE.md | AGENTS.md | GEMINI.md
└── .ai/context/
    ├── ARCHITECTURE.md
    ├── features.md          ← derived view; regenerate only with /reindex
    ├── untracked.md
    ├── context-map.json     ← source path prefix → relevant context files
    ├── HANDOFF.md           ← completed and remaining work, plus actual validation
    ├── LESSONS.md           ← developer-confirmed lessons with evidence and review conditions
    └── specs/
        ├── TASK-YYYYMMDD-HHMM.md
        └── CLOSED-TASK-YYYYMMDD-HHMM.md
```

All assistants share the same `.ai/`; they do not keep separate copies in `.claude/context/`, `.codex/context/`, and similar locations. `/ai-init` offers to migrate repos that still use the old layout.

### Multi-repo projects

A project with any number of Git repositories can share project-level context without copying it into each repo.

```
project/                      does not need to be a Git repository
├── CLAUDE.md                 short pointer to .ai/context/PROJECT.md for sessions at the project root
├── .ai/context/              shared: PROJECT.md, ARCHITECTURE.md, conventions.md, integrations.md
│                             + specs/ and features.md for cross-repo tasks
├── web/.ai/context/          web only: ARCHITECTURE.md, features.md, untracked.md, specs/
├── api/.ai/context/          api only
└── docs/                     not a Git repository; skipped
```

```
cd ~/dev/project && /ai-init            auto-detect the project level (or use /ai-init --project)
cd ~/dev/project/api && /ai-init        repo level; reference shared context above instead of copying it (or use --repo)
```

- **Project level**: detect direct child directories that contain their own `.git`, let you choose repos, write shared context, then initialize each repo. Existing `.ai/` directories are skipped unless `--force` is used. A final summary lists Installed / Skipped / Failed.
- **How agents load context** (`ai/AI.md` › Context Resolution): walk upward from the repo root to find `.ai/context/PROJECT.md`, then read shared context and the `.ai/` files for **only the repo involved in the task**. A task in `api/` does not need the context for `web/` or `worker/`.
- A standalone repo outside a multi-repo project works as before.

#### Tasks that touch multiple repos

```
cd ~/dev/project
/spec Allow users to attach files in comments   → identify api, worker, web → one cross-repo spec
/build TASK-20261003-1400                      → build each repo in order (api → worker → web)
/build TASK-20261003-1400 --repo web           → or build one repo from a separate session
/reindex                                       → project features.md + "Cross-repo" sections in relevant repos
```

```markdown
# TASK-20261003-1400 — Comment attachments
**Scope**: cross-repo
**Repos**: api, worker, web          ← build order: provider before consumer
**Status**: 🚧 In Progress           ← calculated from all repos

## Business Rules                    ← written once, not duplicated per repo
## Contract Changes                  ← api → worker, web
## Proposed Design                   ← ### api / ### worker / ### web
## Implementation Status
| Repo   | Status | Files | Tests |
| api    | ✅ | api/src/... | 14/14 |
| worker | 🚧 | ... | |
| web    | 📋 | — | — |
```

- Specs live in `project/.ai/context/specs/`. Commands such as `/build`, `/change`, and `/status` can find them by task ID from a repo.
- Open the session at `project/` when building across repos (Codex sandbox can write only inside the opened directory).
- If a provider repo's tests fail, do not build repos that depend on its contract.
- Commit each Git repo separately, using the same `Task: TASK-...` line for traceability.

## Share with your team

The repo is not tied to a particular path or machine. `install.sh` resolves paths from its own location, so anyone can clone it anywhere.

**Repo owner — push once**

```bash
cd ~/Documents/dev/ai-agent
git add -A
git commit -m "feat: central AI config for claude/codex/antigravity"
git remote add origin <repo-url>
git push -u origin main
```

**Teammates — clone and install once**

```bash
git clone <repo-url> ~/dev/ai-agent   # clone anywhere
cd ~/dev/ai-agent
./install.sh
```

Then open a work repo and run `/ai-init` if it has no `.ai/` yet. The generated context is **local-only to that machine**; `/ai-init` adds it to `.git/info/exclude` so it is not committed to the repo.

```
Once per person per work repo: run /ai-init; context stays on that machine
After that:                    use /spec /build /change as needed
```

**Antigravity**: `install.sh` installs its skills but not the CLI. Install `agy` separately; the installer warns if it is not on PATH.

**Update the shared package later**

```bash
cd ~/dev/ai-agent && git pull && ./install.sh
```

After self-installation, run the installer or `~/.ai-agent/install.sh --update` to copy new source files into the permanent store. Every provider uses that store. Codex and Antigravity wrappers check for generation drift before launch; rerun the installer for ZCode after changing agents.

### What is shared and what is not

| | Location | How to share |
|---|---|---|
| Shared rules, commands, agents | This repo | `git pull` + `./install.sh` |
| Specs / architecture for each work repo | `.ai/` in that repo | Not shared by default; local-only and excluded in `.git/info/exclude` |

By default, `.ai/` and the memory file belong to the machine. `/ai-init` adds them to `.git/info/exclude`; they remain available locally but Git does not see them. Do not commit or push them, and do not add them to the repo's `.gitignore`: that file is tracked, so teammates would see the exclusions.

To share them with the team later, remove the entries from `.git/info/exclude` and commit the files normally.

### Repos with the old layout

If a repo still has `.claude/commands/` or `.codex/agents/`, those files must be removed because project-level configuration takes precedence over global configuration. `/ai-init` detects them and offers the full migration option.

### Teams using different assistants

All assistants on the same machine read the same `.ai/context/`. Context is local-only, though, so teams using multiple machines must share it manually if they want the same specs everywhere.

The team only needs to agree on one primary root memory file (for example, `CLAUDE.md`); the other two can be one-line pointers to it. `/ai-init` creates those pointers automatically.

### Repos where the team tracks `CLAUDE.md` / `AGENTS.md`

`/ai-init` checks with `git ls-files`. A tracked memory file is treated as **team-owned**:

- ❌ Do not edit, append to, or create a root pointer file, even with `--force`; nothing is added to `git diff`.
- ✅ Store personal memory in `.ai/context/MEMORY.md` (excluded along with `.ai/`); add only information that is missing from the team file.
- Every command reads team memory before `MEMORY.md`; team guidance wins in case of conflict.
- If team memory conflicts with the code, include a proposed diff under "For the team" in the final report; the developer decides whether to open a PR.

---

## Edit the shared package

Edit files in `ai/`; each source exists in one place.

- Edit a command or agent → `ai/commands/*.md`, `ai/agents/*.md`
- Edit shared rules → `ai/AI.md`
- Add a command → place a `.md` file in `ai/commands/`, then run `./install.sh`

Commands use the `description` and `argument-hint` frontmatter fields. Claude and ZCode read both. Codex and Antigravity use `name` and `description` (generated from the source); `$ARGUMENTS` is replaced by the text the user adds after the command.

## Helpers for different tasks

Choose helpers according to `ai/workflows/implementation.md`, which applies to direct code changes, `/build`, and `/change`.

| Agent | Use when | What it returns |
|---|---|---|
| `codebase-explorer` | The entry point, pattern, or consumers in a large repo are unclear | A short flow and the paths/symbols to inspect or change |
| `debugger` | The cause is unclear, or the first fix did not resolve the symptom | Confirmed causes or hypotheses, evidence, and the smallest fix |
| `code-reviewer` | A change affects behavior, multiple files, a public contract, or a critical area | Reproducible bugs, missed wiring/callers, and uncovered requirements |

For clear, small tasks, the main assistant does the work directly. Helpers are read-only and must not call other agents. The main assistant owns edits. Normally, each role is used once and its findings are reused; another pass needs new evidence or a specific correction to verify.

You can invoke these roles with `/review`, `/debug`, and `/explore` (Codex uses `$review`, `$debug`, and `$explore`). These commands are read-only; `/debug` edits only when you explicitly request a fix. Selecting a helper is an instruction to the assistant, not a separate background orchestrator. If the runtime lacks native roles, the assistant uses the same prompt through a generic helper or performs a focused pass itself, and reports if no independent review occurred.

Before finishing, the assistant checks the request against the actual code, including entry points, wiring, config, exports, callers, and contracts. Review findings must cite a file and a scenario that triggers the issue. Missing automated tests alone are not a bug.

The default validation is to exercise a real flow and report the input/steps, environment, expected result, and observed result. If the flow cannot be run, say `not run` and provide concise steps for you to try it. Automated tests can be selected with `/build ... --validation tests` or `/change ... --validation tests`; required team checks still apply.

Evidence stays distinct: ✅ means relevant automated checks passed against the current code; ⚠️ means implemented without automated test evidence, with `flow passed` or `flow not run` recorded separately; an unresolved failure remains 🚧.

Feedback changes the current work immediately. For lessons that should persist, propose a scoped rule with `/learn` before recording it. A single successful interaction or correction does not automatically create a permanent rule.

## Python tools

The tools use only the Python standard library. Runtime tools require Python 3.9+; tests require Python 3.11+ because they use `tomllib`. No additional packages are needed.

```bash
python3 ai/tools/workflow.py resolve --root /path/to/repo/subdirectory
python3 ai/tools/workflow.py context --root /path/to/repo --path src/customer/handler.py
python3 ai/tools/workflow.py validate --root /path/to/repo
python3 ai/tools/workflow.py reindex --root /path/to/repo --dry-run
python3 ai/tools/workflow.py reindex --root /path/to/repo
```

After installation, use `~/.ai/tools/` instead of `ai/tools/`. The tools output JSON and return a non-zero exit code when they find an error.

`/reindex` uses the same tool in every assistant: it checks duplicate IDs, statuses, and cross-repo rows before building the index; calculates overall status; creates links from the actual locations; and renames terminal specs only in the selected scope. It does not edit spec contents or stage Git changes. Repeated runs produce the same content: no current timestamp or cache from an old index is used. `--force` remains supported for compatibility.

`validate` checks metadata structure and internal file links. It does not verify business behavior or prove that tests ran. ✅ still requires evidence from a current test command. `/sync` reports code without a spec as coverage information; it is critical only when there is evidence of a rule or contract conflict.

Example `.ai/context/context-map.json` (populate it from the actual repo structure when running `/ai-init`):

```json
{
  "version": 1,
  "modules": [
    {"path": "src/customer", "context": [".ai/context/customer-rules.md"]}
  ]
}
```

The selector returns candidate paths for the assistant to inspect. It selects only relevant modules and does not override team rules. To continue work, read `HANDOFF.md` and compare the recorded HEAD and diff with the current state. `LESSONS.md` entries must be confirmed, cite a path and symbol, and be reviewed when the supporting code changes.

## Check installation health and roll back

```bash
./install.sh --doctor
./install.sh --rollback
```

Before installing, the script validates the source and snapshots the source store and managed files. If installation fails, it restores the previous state. After a successful install, it records a manifest per provider so doctor can find broken symlinks, changed or missing files, and stale generated files. Installing one provider does not clear stale state for another.

Snapshots live in `~/.ai-agent-history/` (or next to the store when `AI_AGENT_HOME` is changed) and remain after uninstall. `--rollback` reverts the most recent installation and stops if an installer-managed file changed afterward, protecting newer user work. Older `.bak-*` backups are retained. A power loss or killed process may prevent cleanup; in that case, the snapshot remains available for recovery.

Doctor checks local files; it cannot guarantee that a provider accepts a schema or model. After changing `models.json`, try the analyzer in that provider.

## Tests and AI evaluation

```bash
python3.11 -m unittest discover -s tests -v
bash -n install.sh
python3 ai/tools/installation.py validate-source --root .
python3 ai/tools/evaluate.py --responses /tmp/responses.json --output /tmp/report.json
```

CI runs on Linux and macOS and covers agent generation, workflow indexing and context selection, installation health, failure recovery, rollback, and the scorer. Behavioral evaluation has ten scenarios in `ai/evals/cases.json`; see [evals/README.md](evals/README.md) for collecting traces and metrics. Run them against a real assistant and inspect the transcript to compare behavior; scorer unit tests do not evaluate the model.

---

## Existing skills with duplicate names

If another AI agent template installed skills with the same names (`spec`, `build`, etc.), `install.sh` moves the old files to backups instead of deleting them:

- Codex → `~/.codex/skills-disabled-old-template/<name>.bak-<timestamp>/`
- Antigravity → `~/.gemini/config/skills-disabled-old/<name>.bak-<timestamp>/`
- Claude / ZCode → the old file is renamed to `<name>.md.bak-<timestamp>` beside it

Restore a backup:

```bash
mv ~/.codex/skills-disabled-old-template/spec.bak-* ~/.codex/skills/spec
```
