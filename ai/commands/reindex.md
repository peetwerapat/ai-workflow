---
description: Regenerate features.md deterministically from validated specs using the shared Python tool
argument-hint: [--force | --dry-run]
---

# /reindex — Regenerate Feature Index

Respond in **Thai**. Input: **$ARGUMENTS**.

Use the installed tool; do not implement the algorithm in the conversation:

```bash
python3 ~/.ai/tools/workflow.py reindex --root .
```

Forward `--dry-run` to preview the output path, task count, terminal renames, and warnings without writing. `--force` is accepted for compatibility; the tool always reads current spec metadata, including CLOSED files. It does not trust cached index entries. Python 3.9+ is required.

## Behavior

- Discover the nearest repo/project root and shared context, including from a subdirectory.
- Read local specs and shared cross-repo specs relevant to this repo.
- Validate Task ID against filename and heading, status, cross-repo rows, and duplicate IDs before writing.
- Compute overall status from per-repo rows; preserve task-level Cancelled/Deprecated.
- Group by module, use per-repo status for Cross-repo entries, include counts and revision badges.
- Link shared specs relative to the actual index directory, including CLOSED files.
- Rename local terminal specs to CLOSED, without changing their content or staging git changes.
- Never rename a shared spec when invoked from a child repo.
- Write the complete index atomically. Repeated runs with unchanged specs produce identical bytes.
- Do not add a current timestamp: it would break idempotence. Entries show source Last Updated instead.

## Ownership

`features.md` is derived. Only `/reindex` writes it. `/reindex` may rename local terminal specs but must not change spec content, status, or Changelog. `/change` records reopen and status transitions. A mismatching cross-repo header produces a warning; report the discrepancy for `/change` rather than silently changing it.

## Errors and reporting

Invalid or duplicate specs → report errors and stop; do not overwrite the index or guess a status. Suggest reviewing the named spec. An empty specs directory produces an empty registry. A missing directory is allowed for indexing but reported by `validate`.

Summarize tasks indexed, terminal renames, warnings, and output path. If Python is unavailable, report the prerequisite; never claim the tool ran.
