<!-- TEMPLATE: <project>/.ai/context/ARCHITECTURE.md — system overview + ADRs affecting several repos -->
<!-- Every entry must cite repo + real file path as evidence — ADRs affecting one repo belong in <repo>/.ai/context/ARCHITECTURE.md -->

# System Architecture

> Read before proposing a design that touches more than 1 repo — new ADRs only after the dev confirms

---

## Overview

```
{ASCII diagram: which repo/service talks to which, via what (HTTP / queue / DB / file)}
```

## Decisions (Cross-repo ADR)

### P-ADR-001: {Decision title}

**Status**: Accepted | Superseded by P-ADR-XXX
**Date**: {YYYY-MM-DD}
**Affects**: `{repo}`, `{repo}`

**Context**: {problem or constraint}
**Decision**: {what was decided}
**Consequences**: {effects on each repo}
**Evidence**: `{repo}/{path}` — {section that is a real example}

---

## Cross-repo Anti-patterns

| Anti-pattern | Why forbidden | Use instead |
|---|---|---|
| {e.g. one repo reading another repo's DB directly} | {} | {} |
