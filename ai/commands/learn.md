---
description: Record a specific developer-confirmed project lesson with code evidence, or propose an inferred lesson for review
argument-hint: <lesson or correction>
---

# /learn — Confirmed Project Lessons

Respond in Thai. Input: **$ARGUMENTS**.

1. Read team rules, relevant architecture, existing LESSONS.md, and applicable code. Technical lessons need supporting path and symbol/section, plus commit if available. A workflow preference may cite the developer's specific instruction and the affected workflow section instead. Without supporting evidence, report what is missing and do not persist a rule as fact.
2. Check scope, duplicate lessons, and conflicts. Team rules win. A conflict needs a developer decision; never edit tracked memory or architecture through /learn.
3. An explicit developer instruction to remember a specific rule is confirmation of that rule. For inferred lessons or a materially changed interpretation, show the concrete proposed entry and wait for confirmation. Never record candidates as confirmed.
4. Existing `.ai/context/` → merge the confirmed entry into LESSONS.md using `~/.ai/templates/LESSONS.md`. No context directory → return a proposed entry; /ai-init can create project context, but do not initialize it automatically.
5. Assign the next local L-NNN ID. Include scope, confirmation source/date, path#symbol evidence, source commit, reason, last review date, and invalidation conditions. Preserve history; mark old entries stale or superseded. Match the existing file's language.

On reuse, re-read cited code and check relevant git changes. Unverifiable, stale, and superseded entries must not guide implementation. A lesson never silently becomes an ADR or changes a business rule in a spec. Only /learn writes LESSONS.md after confirmation; other commands may suggest a lesson in their report.

## Feedback from actual work

Apply a developer correction to the current task immediately. Distinguish a project preference, a reproduced failure, and an observation that merely worked once. Phrase a candidate as a scoped action with supporting evidence; propose at most one useful lesson at a natural boundary. Explicit "remember this" confirms the specified rule; praise, frustration, or one successful attempt does not confirm a broader permanent policy. Preferences may cite the developer's exact instruction and the affected workflow section as evidence; technical rules also need code evidence. Never save credentials or raw sensitive logs.
