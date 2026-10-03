<!-- TEMPLATE: <project>/.ai/context/PROJECT.md — marker of a multi-repo project (agents walk up from a repo and find this file) -->
<!-- Fill from reading the real repos via /ai-init at the project root — if not found write "not found", never guess -->

# {Project Name}

{1-2 lines: what this system is and who uses it}

> **Shared context** for every repo in this project — source of truth for cross-repo matters
> Repo-specific matters live in `<repo>/.ai/context/` — ❌ never copy this folder's content into a repo

---

## Repositories

| Repo | Responsibility | Stack | Context |
|---|---|---|---|
| `{dir}` | {} | {} | `{dir}/.ai/context/` |

## Domain

{entities / terms shared across repos — which repo owns which data}

| Term | Meaning | Owner repo |
|---|---|---|
| {} | {} | `{dir}` |

---

## Context Map (load only what is needed)

| File | Read when |
|---|---|
| `PROJECT.md` (this file) | every task in this project |
| `ARCHITECTURE.md` | proposing a design / task crossing repo boundaries |
| `conventions.md` | writing code in any repo |
| `integrations.md` | task touching an API / event / data used by another repo |
| `specs/` + `features.md` | cross-repo task (touches ≥ 2 repos) — single-repo specs live in that repo |
| `<repo>/.ai/context/*` | only repos the task actually touches — do not load other repos |
