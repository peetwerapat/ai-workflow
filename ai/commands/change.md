---
description: แก้ feature เดิม — bug fix / requirement change / refactor พร้อม impact analysis
argument-hint: <task-id> "<description>" [--quick | --dry-run | --cancel <reason> | --deprecate <reason>]
---

# /change — Modify Existing Feature

แก้ feature ที่มีอยู่แล้ว — ครอบคลุม 3 use cases ใน command เดียว:
- **Bug fix** — code เคยทำผิด → แก้ให้ตรง spec
- **Requirement change** — spec เปลี่ยน → code ตาม
- **Refactor** — internal change, behavior เหมือนเดิม

AI แยกประเภทให้อัตโนมัติจาก description

## Context Files

- shared project context (ถ้ามี — ดู `~/.ai/AI.md` › Context Resolution): `PROJECT.md` + ไฟล์ใน context map ที่เกี่ยวกับ task
  - แตะ contract ใน `integrations.md` → flag repo ฝั่ง consumer ใน risk + เสนออัปเดต shared (ห้ามแก้เอง)
- project memory file ที่ root
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/specs/{task-id}.md` (หรือ `CLOSED-TASK-{id}.md`) — **source of truth**

## Runtime Info

```bash
git config user.name
date "+%Y-%m-%d"
```

---

## Input

**$ARGUMENTS**

Format: `<task-id> "<description>" [flags]`

- **task-id** (required, token แรก): `TASK-YYYYMMDD-HHMM` หรือ legacy `{MODULE}-{NNN}`
- **description** (required): ใส่ prefix บังคับ type ได้ — `"refactor: ..."`, `"fix: ..."`, `"change: ..."`
- **Flags**:
  - `--quick` — skip impact analysis (เฉพาะ change เล็กและชัด)
  - `--dry-run` — แสดง impact analysis อย่างเดียว ไม่แก้จริง
  - `--cancel <reason>` — Status → ❌, Changelog `CANCELLED`
  - `--deprecate <reason>` — Status → 📦, Changelog `DEPRECATED`

**args ไม่ครบ** → แจ้ง format ที่ถูกต้อง + หยุด

---

## Step 1: Parse & Validate

```
input: TASK-20260501-1430 "login ค้างเมื่อ Redis down" --quick
→ task-id: TASK-20260501-1430
→ description: login ค้างเมื่อ Redis down
→ flags: [--quick]
```

task-id ไม่ match pattern → หยุด:
```
❌ "{input}" ไม่ใช่ task-id ที่ valid
Format: TASK-YYYYMMDD-HHMM หรือ {MODULE}-{NNN}
ค้นหา: /status <keyword>
```

---

## Step 2: Pre-flight Check

### 2.1 หา spec file

ลองตามลำดับ:
1. `.ai/context/specs/TASK-{id}.md` (active)
2. `.ai/context/specs/CLOSED-TASK-{id}.md` (closed)
3. multi-repo project → `<project>/.ai/context/specs/` (active แล้ว closed) — ดู AI.md › Cross-repo Task

**ไม่พบทั้ง 2**:
```
❌ ไม่พบ spec file สำหรับ {task-id}

- Task ID ถูกไหม? → `/status {task-id}`
- ถ้าเป็น feature ใหม่ → ใช้ `/spec` ไม่ใช่ `/change`
```

### 2.2 Reopen check (ถ้าเป็น CLOSED file)

rename กลับเป็น active ก่อน: `git mv CLOSED-TASK-{id}.md TASK-{id}.md`
(`/reindex` รอบถัดไปจะ append `REOPENED` Changelog entry ให้)

### 2.3 Check Status

| Status | Action |
|---|---|
| ✅ Done | ✅ proceed |
| ⚠️ Done (untested) | ⚠️ warn + proceed (test อาจมีปัญหาอยู่แล้ว) |
| 🚧 In Progress | ⚠️ ถาม: ยังไม่ build เสร็จ — แก้ spec แล้ว `/build --resume` ดีกว่าไหม? |
| 📋 Planned | ❌ หยุด — ยังไม่ build, แก้ spec file ตรงๆ หรือ cancel + `/spec` ใหม่ |
| 🔴 Blocked | ⚠️ ถาม blocker ก่อน |
| ❌ Cancelled / 📦 Deprecated | ❌ หยุด (ถ้าจะรื้อ → reopen ก่อน) |

---

### 2.4 Cross-repo spec (`**Scope**: cross-repo`)

- impact analysis ครอบคลุม **ทุก repo ใน `**Repos**:`** + repo อื่นที่ `integrations.md` บอกว่า consume contract ที่จะแก้
- change ต้องแตะ repo ที่ยังไม่อยู่ใน `**Repos**:` → แสดงใน Change Plan + ขอ confirm แล้วเพิ่มเข้า Repos / Design / Implementation Status
- Execute (Step 7) ทีละ repo ตาม build order — test ด้วย command ของแต่ละ repo
- Changelog ระบุ repo ที่แตะ: `{TYPE} [{repo}, {repo}]` / update แถวใน Implementation Status + Overall Status
- เปิด session ที่ root ของ project ถ้าต้องเขียนหลาย repo (เหมือน `/build`)
- spec เดิมเป็น repo-level แต่ change ลามไป repo อื่น → เสนอ `/spec` cross-repo ใหม่สำหรับส่วนที่ข้าม repo (อ้าง task เดิม) แทนการยัดลง spec ของ repo เดียว

---

## Step 3: Detect Change Type

**Priority 1 — explicit prefix**
```
"refactor: ..." → REFACTORED
"fix: ..." / "bug: ..." / "bugfix: ..." → FIXED
"change: ..." → CHANGED
```

**Priority 2 — keyword inference**
```
FIXED:      bug, broken, error, ค้าง, พัง, ไม่ทำงาน, ผิด
REFACTORED: refactor, cleanup, extract, rename, move, reorganize, simplify, ปรับโครงสร้าง, แยก
Default:    CHANGED
```

**Priority 3 — confirm** ถ้า confidence ต่ำ:
```
Change type ที่เดา: {TYPE}
A) {TYPE} — ตามที่เดา
B) Override (FIXED / CHANGED / REFACTORED)
```

---

## Step 4: Impact Analysis

**`--quick` → ข้ามไป Step 6**

> ⚠️ `--quick` ใช้เฉพาะ change เล็กและชัด
> **ห้ามใช้กับ**: auth, payment, การคำนวณเงิน, multi-tenant, data migration
> ถ้า dev สั่ง `--quick` กับงานกลุ่มนี้ → warn แล้วทำ analysis เต็มอยู่ดี

### ปกติ → Delegate to impact-analyzer

**Input:**
```
Task ID: {task-id}
Current spec path: .ai/context/specs/{task-id}.md
Current code files: {list จาก Implementation Status}
Change description: {description}
Change type (detected): {FIXED | CHANGED | REFACTORED}
```

**Expect output:**
- **Conflict check** (สำคัญสุด)
- Risk level (🔴 / 🟡 / 🟢) + reasoning
- Affected files (direct + indirect)
- Test impact (existing / new)
- Proposed approach (1-2 options ถ้ามี trade-off)
- Confidence assessment

**ถ้า runtime ไม่รองรับ subagent** → อ่าน `~/.ai/agents/impact-analyzer.md` แล้วทำตาม process นั้นเอง

---

## Step 5: Handle Conflict (ถ้ามี)

เจอ conflict กับ business rule เดิม → **หยุดทันที**:

```
⚠️ Business Rule Conflict Detected

### Task: {task-id}

| | Original (spec) | New (requested) |
|---|---|---|
| Rule | {original rule} | {new behavior} |

### Consequences if Changed
- {what will be removed/modified}
- {side effects}

### ต้องการ confirm จาก BA/PO
1. ต้องการเปลี่ยน business rule นี้จริงไหม?
2. เหตุผล? (จะบันทึกใน Changelog permanent)

พิมพ์ "confirm: <reason>" เพื่อไปต่อ / "cancel" เพื่อหยุด
```

**ไม่มี confirm + reason → ไม่ proceed**

---

## Step 6: Show Analysis + Confirm

```
## Change Plan: {task-id}

**Type**: {FIXED | CHANGED | REFACTORED}
**Description**: {description}
**Risk Level**: 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW — {why}

### 📁 Direct Impact
- `{path}` — {what changes}

### 🔗 Indirect Impact
{cross-module impact หรือ "Isolated — ไม่กระทบ module อื่น"}

### 🧪 Affected Tests
- `{test file}` — test "{name}" (อาจต้องแก้)

### 💡 Approach
{approach เดียว ถ้าชัด}

{หรือถ้ามี trade-off:}
Option A: {name} — Pros / Cons
Option B: {name} — Pros / Cons
เลือก A หรือ B?

### ⚠️ Pre-execution Checklist
- [ ] เข้าใจ risk level แล้ว
- [ ] มี test coverage ในไฟล์ที่จะแก้
- [ ] Breaking change มี migration path (ถ้ามี)

พิมพ์ "confirm" เพื่อ execute / "cancel" เพื่อหยุด
```

### `--dry-run` → หยุดที่นี่
```
✅ Dry-run complete — ไม่มีการเปลี่ยนแปลงไฟล์
ต้องการ execute จริง → รัน command เดิม **ไม่มี** --dry-run
```

---

## Step 7: Execute

### 7.1 Generate Revision ID

หา revision ล่าสุดจาก Changelog ใน spec file:
```
{task-id}-R02 (ล่าสุด) → ต่อไป R03
ไม่มี R → R01
```
Format: `{task-id}-R{NN}` (2 หลัก zero-padded)

### 7.2 Edit Files One-by-One

**ห้ามแก้หลายไฟล์พร้อมกัน**

```
สำหรับแต่ละไฟล์:
  1. อ่าน content ปัจจุบัน
  2. Apply change
  3. รัน test ที่เกี่ยวข้อง
  4. fail → วิเคราะห์ + แก้ (สูงสุด 3 รอบ)
  5. ยัง fail → rollback ไฟล์นี้ + report dev
  6. ไฟล์ถัดไป
```

### 7.3 Test Strategy per Type

**FIXED**
- เขียน regression test **ก่อน** fix (TDD-ish) — ต้อง fail ก่อน, pass หลัง
- หา test เดิมไม่เจอ → เขียนใหม่

**CHANGED**
- Update test เดิมให้ตรง spec ใหม่
- เพิ่ม test cases ที่เกิดจาก rule ใหม่

**REFACTORED**
- test เดิมต้อง **pass เหมือนเดิม** — ไม่แก้ test
- test พัง = ไม่ใช่ refactor แต่เป็น change → หยุด + confirm
- ไม่เพิ่ม test ใหม่

### 7.4 Handle Test Failures

**FIXED / CHANGED**: attempt 1 → 2 → 3 แล้วหยุด (ปล่อยไฟล์ที่แก้ไว้, mark 🚧)

**REFACTORED**:
```
⚠️ Test เดิม fail หลัง refactor
นี่อาจไม่ใช่ refactor แท้ — behavior เปลี่ยนไป

A) Rollback (ไม่ refactor ตรงนี้)
B) เปลี่ยน type เป็น CHANGED (แก้ test ตาม behavior ใหม่)
```

---

## Step 8: Update Spec File

### 8.1 Append Changelog

```markdown
- **{date}** {TYPE} — {description}
  - **Reason**: {reason — required สำหรับ CHANGED / FIXED / CANCELLED / DEPRECATED}
  - **Files**: {affected files}
  - **Revision**: {revision-id}
```
`{TYPE}` ∈ `CHANGED` / `FIXED` / `REFACTORED` / `CANCELLED` / `DEPRECATED`

### 8.2 Update sections อื่น (ตาม type)

**CHANGED + business rule เปลี่ยน** → update `## Business Rules`, `## Ambiguity Resolutions`
**`--cancel` / `--deprecate`** → update `**Status**:` เป็น ❌ / 📦

### 8.3 Last Updated
```markdown
**Last Updated**: {now} by {git user.name} \<{git user.email}\>
```

### 8.4 Status
ส่วนใหญ่ไม่เปลี่ยน (ยัง ✅) ยกเว้น:
- test fail 3 รอบ → 🚧
- major change ที่ต้อง re-test เยอะ → อาจลดเป็น ⚠️

---

## Step 9: Final Report

```
## ✅ Change Complete: {revision-id}

**Type**: {TYPE} | **Description**: {description}

### Files Modified
- `{path}` (+X / -Y lines)

### Tests
- Updated: X | Added: X (regression)
- All passing ✅ | Some failing ⚠️

### Doc Updates
- spec file: appended Changelog + updated Last Updated
- features.md: ยังไม่ update — รัน `/reindex`

### ⚠️ Assumptions Made
1. ...

### 🔍 จุดที่ควร Review
1. ...

### Next Steps
- `git diff` review
- `/reindex` เพื่อ update features.md
- Commit (suggested — cross-repo: แยก commit ต่อ repo ใส่ Task เดียวกัน):
  ```
  {type}({module}): {description}

  Task: {task-id} / {revision-id}
  ```
```

---

## Rules

### Must Do
- **Validate task-id ก่อน analyze**
- **Delegate impact analysis** — ไม่ analyze เอง (ยกเว้น runtime ไม่รองรับ)
- **หยุดถ้าเจอ conflict** — รอ dev ยืนยัน + reason
- **Test หลังทุกไฟล์** — detect regression เร็ว
- **บันทึก reason ใน Changelog** สำหรับ FIXED และ CHANGED

### Must Not
- ❌ **แก้หลายไฟล์พร้อมกัน**
- ❌ **Skip impact analysis** สำหรับ auth / payment / เงิน / multi-tenant / migration แม้มี `--quick`
- ❌ **Mark ✅ ถ้า test fail**
- ❌ **แก้ test ใน REFACTORED**
- ❌ **Commit อัตโนมัติ**
- ❌ **แตะ `features.md`**

---

## Edge Cases

**Description vague**
```
dev: /change TASK-XXX "แก้ตรง login"
AI: คำอธิบายไม่ชัด — bug อะไร? / requirement เปลี่ยนตรงไหน? / หรือแค่ refactor?
```

**Feature ยังไม่ build (📋)**
```
⚠️ {task-id} ยังไม่ build — /change ใช้กับ feature ที่ build แล้ว
A) แก้ spec file ตรงๆ → แล้วรัน /build
B) Cancel + /spec ใหม่
```

**หลาย change ใน command เดียว**
```
dev: /change TASK-XXX "fix login + add rate limit + change UI"
AI: ตรวจพบ 3 change — แยก 3 commands ดีกว่า (แต่ละอันมี revision + audit ของตัวเอง)
```

**Rollback**
```
dev: cancel (หลัง test fail 3 รอบ)
AI: 1. `git checkout .` revert working tree
    2. ตรวจไฟล์ใหม่ที่ AI สร้าง
    3. spec file ยังไม่ถูกแก้ (Step 8 ยังไม่ถึง)
    → state กลับเป็นก่อน /change
```

---

## Output Language

- ตอบเป็น**ภาษาไทย**
- Technical terms, code, paths, task-id, revision-id, commit message → **อังกฤษ**

---

## Examples

```
dev: /change TASK-20260424-1430 "login ค้างเมื่อ Redis down"
AI: [FIXED → impact → เสนอ timeout vs circuit breaker → dev เลือก A → implement + regression test]
    ✅ Change Complete: TASK-20260424-1430-R01 (FIXED)

dev: /change TASK-20260424-1445 "comment ต้องมี captcha + rate limit 3/hr"
AI: ⚠️ Conflict: spec เดิมระบุ "ไม่มี rate limit" — ขอ reason?
dev: confirm: โดน spam ยิงจริง
AI: ✅ Change Complete: TASK-20260424-1445-R01 (CHANGED)

dev: /change AUTH-001 "refactor: แยก JWT validation เป็น guard"
AI: [REFACTORED → low risk → implement → test เดิม pass ไม่แก้ test]
    ✅ Change Complete: AUTH-001-R01 (REFACTORED)
```
