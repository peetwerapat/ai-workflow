---
description: Review a specified diff for actionable bugs, integration gaps, and missing requested behavior without editing code
argument-hint: [base-revision | paths | review-scope]
---

# /review — Review Current Changes

Respond in Thai. Input: **$ARGUMENTS**. Follow `~/.ai/workflows/implementation.md` › Select assistance and Check completeness.

Use code-reviewer with the developer goal, specified scope, real diff, applicable rules, and validation evidence. Empty input → inspect current staged and unstaged changes and relevant untracked source files; never invent a base revision. If no changes exist, report that and request a concrete scope only when needed.

Treat untracked files carefully: exclude secrets, generated output, and unrelated artifacts. A base revision supplied by the developer is read-only input; do not switch branches or reset the worktree.

Report supported findings with path/symbol, severity, concrete trigger, and impact. No actionable findings → state scope and limits. This command authorizes review only: do not edit code, specs, statuses, memory, or the index, or run mutating reproduction. Follow-up authorization to fix findings is handled as direct coding.
