<!-- TEMPLATE: project memory file — placed at the repo root as CLAUDE.md / AGENTS.md / GEMINI.md (or .ai/context/MEMORY.md in Team memory mode) -->
<!-- Fill every section from reading real code — if not found write "not found", never guess -->

# {Project Name}

{1-2 lines: what this system is and who uses it}
{if multi-tenant: the isolation unit and its key name}

> Global working agreement lives at `~/.ai/AI.md` — this file holds only what is specific to this project
> **Multi-repo project** (delete this line for a standalone repo): this repo is part of `{project}` — shared context at [`{../}.ai/context/PROJECT.md`]({../}.ai/context/PROJECT.md); read it first and never copy its content into this file

---

## Domain Model

```
{ASCII diagram of the main entities and their relations}
```

| Entity | Role | Tenant key |
|---|---|---|
| {Entity} | {responsibility} | {key or —} |

## Personas

| Persona | Scope |
|---|---|
| {persona} | {what they can access / auth type} |

---

## Tech Stack

- **Language / Runtime**: {}
- **Framework**: {}
- **Database**: {} ({ORM/driver})
- **Cache / Queue**: {}
- **Auth**: {}
- **Package manager**: {}
- **Test**: {runner} — `{command}`
- **Lint / Format / Typecheck**: `{commands}`
- **Migration**: `{command}`
- **Docs**: {swagger/openapi path if any}

Architecture decisions → [.ai/context/ARCHITECTURE.md](.ai/context/ARCHITECTURE.md)

---

## Critical Rules

### 1. {Tenant isolation / the most non-negotiable rule of this project}

{rule + real code pattern from the repo}

### 2. Layering

```
{Layer → Layer → Layer actually used}
```

- ❌ Never {anti-pattern found or forbidden by the project}
- ✅ {required pattern} — example: `{path}`

### 3. Error Handling

{exception/error classes used + mapping to status codes + example}

### 4. API / Response Shape

{envelope used + example + route path convention}

### 5. Database Migration

{command to generate + naming + prohibitions}

### 6. Security

{secret management, password hashing, token storage, PII handling}

---

## Conventions

### Naming

| Context | Convention | Example |
|---|---|---|
| variables / methods | {} | {} |
| classes / interfaces | {} | {} |
| files | {} | {} |
| DB tables / columns | {} | {} |
| env vars | {} | {} |

> Use full words, no abbreviations — `customerRepository`, not `custRepo`
> Except standard abbreviations (`id`, `url`, `db`, `dto`, `i18n`) and short loop indexes in narrow scope

### File / Folder Layout (per module)

```
{real structure of one module}
```

### Testing

{existing tests + current coverage + mocking pattern used}

---

## Directory Structure (real)

```
{tree of the real source dir — not what it is assumed to be}
```

---

## Module Dependency

```
{dependency order between modules}
```

Before changing a module → read that module's rule file first (if any)

---

## Known Gaps

- {unfinished work / technical debt the AI should know}
