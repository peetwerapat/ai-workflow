# Implementation Assistance

Shared execution protocol for direct coding, /build, /change, /review, /debug, and /explore. Read the relevant sections only. Developer instructions and team rules take precedence. This protocol never creates a spec or initializes context implicitly.

## Select assistance

The main assistant owns implementation, validation, and the final response. Select a helper from concrete task evidence:

| Situation | Helper | Timing |
|---|---|---|
| Small localized change with a clear existing pattern | Main assistant | Complete directly |
| Unknown entry point, unclear consumers, unfamiliar large module | codebase-explorer | Before choosing edit locations |
| Complex bug, unclear cause, or one attempted correction did not fix the symptom | debugger | Before the next speculative edit |
| Behavior change, multi-file change, public contract, or sensitive path | code-reviewer | After a coherent implementation, before final completion |
| Explicit /spec or /change | Existing spec-analyzer or impact-analyzer | Preserve their recorded workflow |

Small, low-risk text/style changes or obvious localized fixes with known callers may stay in the main assistant even though visible output changes. Sensitive paths and public-contract changes still trigger review. Do not invoke every helper for every task. Give a bounded question, root(s), goal, relevant paths/diff, known evidence, and prior attempts. Mention the helper briefly in a progress update. Reuse its answer instead of repeating its full investigation.

Use the installed role by name when available. When a runtime exposes only generic delegation, read `~/.ai/agents/<role>.md` and pass its full instructions and inputs to a read-only helper on the inherited model; disclose that the native role's model/effort settings were not applied. Do not override a model at invocation unless the developer requests it. If delegation is unavailable, read the same role prompt and perform one focused pass in the main context. Never claim an independent review occurred when it did not.

Helpers must not delegate or edit. Keep execution sequential when inputs depend on earlier findings. Default budget: one explorer pass if needed, one debugger pass when triggered, and one reviewer pass. A second pass is allowed only for a changed question, new evidence, or checking a concrete correction; stop speculative loops and report unresolved evidence.

For review findings, verify the trigger in current code. Fix supported issues within scope, including P2 issues that break the requested outcome. Stop completion for unresolved P0/P1 issues and report remaining defects. Reject unsupported findings with evidence. Do not expand into unrelated refactors or run repeated reviews without a new reason.

## Validate with practical flows

Default to a focused real flow using available tools and a safe environment. State the selected mode before acting. `--validation flow` is the default; `--validation tests` opts into relevant automated tests. `--no-test` skips automated tests but still permits a flow check. Latest developer instructions and mandatory team checks override defaults; conflicting flags require clarification, not silent guessing.

1. Identify the user-visible trigger and expected result. Exercise the changed path and an adjacent unaffected case where practical, using existing local UI, CLI, API, or runtime.
2. Record actual input/steps, environment, expected and observed output, result, and code state covered. A command that merely starts a process does not prove the flow works. A reviewer opinion is not runtime evidence.
3. If the runtime/account/data is unavailable, finish the authorized code work, state that the flow was not run, and provide short steps for the developer to try. Ask only for missing business decisions or access that is actually required. Do not invent results or block implementation because a test runner is absent.
4. Run existing automated checks when they directly clarify a risky calculation or recurring bug, when requested, or when team rules require them. Avoid adding test infrastructure or a new suite as a side effect. New dependencies still need approval.
5. A demonstrated failure stays 🚧 until resolved or explicitly reported incomplete. Stop after three failed attempts on the same failure. Do not hide a failure by switching modes.

Keep the established status vocabulary: current relevant automated tests passing supports ✅; implementation without automated test evidence remains ⚠️ Done (untested), even if a manual flow passed. Add `Validation: flow passed / tests passed / failed / not run` separately so ⚠️ does not imply the developer's practical check failed. An unexercised flow remains explicitly unverified. A later code change invalidates evidence for the changed code.

## Check completeness

Before the final response, compare the original goal and later corrections against the actual diff:

- Can a user reach the changed behavior through the real entry point? Check registration, wiring, exports, routes, configuration names, and caller updates that apply.
- Are all requested outcomes implemented, including applicable error/empty/boundary behavior and downstream contracts?
- Did the selected flow produce the expected result? What remains unverified or inaccessible?
- Were unrelated pre-existing changes preserved and any out-of-scope problems reported?
- Were material reviewer findings resolved, and do status and handoff match actual evidence?

Return a concise result, what was exercised, and any remaining limits. For substantial work, keep a checkpoint only when project context already exists. Do not print an exhaustive checklist for a trivial edit.

## Use feedback from real work

When the developer says a result is wrong, questions were excessive, or an approach worked, apply that steering to the current task immediately. Identify the concrete symptom/preference and its intended scope. Use debugger only when its trigger applies; do not treat every correction as a bug investigation.

A current instruction authorizes the current behavior. It becomes a persistent lesson only through /learn with a specific confirmed rule, supporting evidence, and scope. Explicit "remember this" confirms the stated rule. Otherwise propose at most one useful lesson at a natural boundary; wait for confirmation before recording. Never persist every exchange, extrapolate a project preference globally, or save secrets. No existing .ai/ → return the proposal in conversation.
