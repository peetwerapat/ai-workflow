<!-- TEMPLATE: .ai/context/HANDOFF.md; replace placeholders with observed facts -->
# Work Handoff

**Task**: {task-id or direct request}
**Goal**: {developer's intended result}
**Recorded**: {date and timezone}
**Repository**: {root and branch}
**HEAD**: {commit or unavailable}
**Working changes**: {git status summary; include pre-existing changes}

## Completed

- {behavior implemented; evidence path#symbol}

## Remaining

- {next concrete action in dependency order}

## Validation

**Mode**: flow | tests
**Flow**: {trigger/steps, environment, expected result, observed result; or not run with reason}

| Command | Result | Code state covered | Evidence |
|---|---|---|---|
| {actual command or not run} | {passed/failed/not run} | {HEAD + working changes at run time} | {summary, no secrets} |

## Assistance and Review

- {helper and bounded question; findings accepted/rejected with evidence; or no helper needed}
- {acceptance items complete/missing; entry point/wiring/callers checked; remaining review limits}

## Decisions and Constraints

- {confirmed instruction, source, and approval scope}

## Assumptions and Missing Evidence

- {uncertainty; how to resolve it}

## Resume

Compare HEAD and current diff with this checkpoint. Read relevant rules and referenced files again. Treat validation as stale if covered code changed. Never discard another developer's work.
