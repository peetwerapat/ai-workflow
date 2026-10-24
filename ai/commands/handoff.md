---
description: Record work and validation evidence for another session when explicitly requested; do not implement new work
argument-hint: [task-id]
---

# /handoff — Work Checkpoint

Respond in Thai. Input: **$ARGUMENTS**. Read current developer instructions and relevant context before recording a checkpoint.

1. Inspect git HEAD, branch, status, and relevant diff. If git is unavailable, state that explicitly. Do not read secrets or include output containing credentials.
2. Record observed completed work, remaining actions in dependency order, confirmed decisions, assumptions, and unresolved blockers. Cite path and symbol/section for material claims.
3. Record exact test commands actually run, result, and code state covered. If no command ran, write `not run`. Changes after a pass invalidate that pass for changed code.
4. Existing `.ai/context/` → merge the current task checkpoint into HANDOFF.md using `~/.ai/templates/HANDOFF.md`. Preserve unrelated task notes; do not overwrite a different task without explicit direction. No context directory → return the checkpoint in the response; do not run /ai-init.
5. Include the next concrete action and instructions to compare HEAD/diff before resuming. Never claim the handoff is equivalent to successful implementation.

This command does not alter code, specs, statuses, team memory, architecture, or the index. Follow the existing context file's language. Context remains local-only.
