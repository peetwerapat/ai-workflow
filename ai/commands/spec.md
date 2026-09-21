---
description: แปลง requirement เป็น spec + วิเคราะห์ risk + บันทึกเป็น feature ใหม่
argument-hint: <requirement> [--quick]
---

# /spec — Create Feature Specification

รับ requirement ดิบจาก BA/PO หรือ dev → วิเคราะห์ business rules + risks + edge cases →
ถาม ambiguity ที่สำคัญ → บันทึกเป็น spec file

## Context Files

อ่านก่อนเริ่มเสมอ:
- project memory file ที่ root (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md` ตัวที่มี)
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/features.md` (overview เท่านั้น)

**ถ้าไม่มี `.ai/context/`** → แจ้ง dev ให้รัน `/ai-init` ก่อน แล้ว **หยุด**

## Input

**$ARGUMENTS**

Parse rules:
- **requirement text** (required): ข้อความ requirement — ประโยค, bullet, paragraph, user story ก็ได้
- **Flags**: `--quick` — ข้าม ambiguity questions (trust dev)

**ถ้า argument ว่าง** → ถาม dev:
```
กรุณาระบุ requirement ที่ต้องการ spec
ตัวอย่าง: /spec ลูกค้าต้องการ login ด้วย email + password
```
แล้ว **หยุด** รอ input ใหม่

---

## Runtime Info

รัน:
```bash
git config user.name
git config user.email
date "+%Y-%m-%d %H:%M"
```

ใช้เป็น `**Created**:` field และ Task ID generation

---

## Step 1: Identify Module

จาก requirement เดาว่า feature นี้อยู่ใน module/area ใด:

1. อ่าน `features.md` → ดู module sections ที่มีอยู่ (หรือ scan `specs/` หา distinct Module fields)
2. Match keyword ใน requirement กับชื่อ module + โครงสร้าง source dir จริง
3. Match หลายตัว → ถาม dev ให้ชัด
4. ไม่ match (module ใหม่) → propose module name + ถาม dev confirm

ตัวอย่าง:
- "login ด้วย email" → Auth
- "แสดงราคาสินค้า" → Product (ถ้ามี) หรือ propose ใหม่
- "comment ใน blog post" → มี Blog/Post → ใช้; ไม่มี → propose "Comment"

**อ่าน module context**: ถ้า module นั้นมีไฟล์ rule ของตัวเอง (เช่น `<module>/CLAUDE.md` หรือ `<module>/AGENTS.md`) → อ่านก่อน analyze

---

## Step 2: Delegate to spec-analyzer

ส่งให้ agent `spec-analyzer` วิเคราะห์

**Input:**
- Requirement text (ดิบ ตามที่ dev พิมพ์)
- Target module
- Context files ที่ relevant (`ARCHITECTURE.md`, module rule file ถ้ามี)
- Mode: `normal` | `quick`

**Expect output:**
- Business rules (เขียนเป็น "ระบบต้องทำ X เมื่อ Y")
- Risks (security, data integrity, performance, breaking change, multi-tenant)
- Edge cases (validation, state, query, error, empty state)
- Dependencies (module อื่น, external lib/service)
- Proposed design (files, API shape, data model)
- Ambiguity questions (ไม่เกิน 3 ข้อ ที่สำคัญจริง)
- Confidence assessment

**ถ้า runtime ไม่รองรับ subagent** → อ่าน `~/.ai/agents/spec-analyzer.md` แล้วทำตาม process นั้นเอง
ผลลัพธ์ต้องอยู่ใน format เดียวกัน

> delegate = analyze ใน context แยก → ประหยัด main context

---

## Step 3: Ask Ambiguity (ถ้าไม่มี --quick)

แสดงคำถามจาก analyzer (สูงสุด 3 ข้อ) พร้อม options:

```
## Spec Draft: {Feature Name}

### ✅ Business Rules ที่เข้าใจแล้ว
1. ...

### 🔴 Risks ที่พบ
- {risk}: mitigation?

### ❓ Questions (ตอบก่อน confirm)
1. {คำถาม}
   - A) ...
   - B) ...
   - C) ...

กรุณาตอบทุกข้อก่อน แล้วจะ proceed ต่อ
```

**รอ dev ตอบ** — parse คำตอบ map เข้ากับ options ถ้าตอบไม่ชัด ถามใหม่

**ถ้ามี `--quick`**: skip step นี้ ใช้ sensible default ทุกข้อ แต่ต้อง list ใน `## Assumed Defaults` ของ spec file

---

## Step 4: Show Full Draft + Confirm

```
## Spec Draft (Full)

### Feature: {name}
### Module: {module}

### Business Rules
1. ...

### Edge Cases
- {case}: {handling}

### Risks + Mitigation
- 🔴 {risk}: {how to handle}

### Dependencies
- {module / lib}  ⚠️ NEW ถ้าต้องติดตั้งเพิ่ม

### Proposed Design
**Files to create/modify:**
- {path} — {purpose}

**API / Interface:**
- {method} {path} — {purpose}

**Data model:**
{schema draft}

### Ambiguity Resolutions
1. Q: {question} → A: {answer}

---
พิมพ์ "confirm" เพื่อบันทึก spec
หรือพิมพ์สิ่งที่อยากแก้ เช่น "เปลี่ยน rate limit เป็น 10/min"
```

**Loop จนกว่า dev จะ confirm:**
- dev แก้ไข → update draft → show ใหม่
- dev "confirm" → Step 5
- dev "cancel" → ยกเลิก **ไม่สร้างไฟล์**

---

## Step 5: Generate Task ID

```bash
date "+TASK-%Y%m%d-%H%M"
```

Format: `TASK-YYYYMMDD-HHMM` เช่น `TASK-20260501-1430`
**Generate ตอนนี้เท่านั้น** — ไม่ใช่ตอนเริ่ม command

ถ้าไฟล์ชื่อนี้มีอยู่แล้ว (collision) → เติม suffix `-B`, `-C` ห้าม overwrite

---

## Step 6: Create Spec File

สร้าง `.ai/context/specs/{task-id}.md`:

```markdown
# {Task ID} — {Feature Name}

**Module**: {module}
**Status**: 📋 Planned
**Created**: {YYYY-MM-DD HH:MM} by {git user.name} \<{git user.email}\>
**Last Updated**: {YYYY-MM-DD HH:MM} by {git user.name} \<{git user.email}\>

---

## Requirement (Original)

{raw requirement ที่ dev พิมพ์มา — preserve ไว้ trace ย้อนกลับ}

---

## Business Rules

1. ...

---

## Risks

| Level | Category | Risk | Mitigation |
|---|---|---|---|
| 🔴 | Security | {risk} | {how} |

---

## Edge Cases

- **{case}**: {expected behavior}

---

## Dependencies

### Internal
- Module {X}: {reason}

### External
- {library / service}: {reason}

---

## Proposed Design

### Files

**Create:**
- `{path}` — {purpose}

**Modify:**
- `{path}` — {what changes}

### API / Interface

| Method | Path | Purpose | Auth |
|---|---|---|---|

### Data Model

{schema}

### Flow

{sequence / state — ใส่เมื่อ complex เท่านั้น}

---

## Ambiguity Resolutions

1. **Q**: {question}
   **A**: {answer}
   **Rationale**: {why}

---

## Assumed Defaults (--quick mode)

_ใส่เฉพาะเมื่อรันด้วย `--quick`_

- {assumption}

---

## Implementation Status

_(TBD — pending /build)_

---

## Changelog

- **{YYYY-MM-DD}** ADDED — Initial spec

---

## Known Gotchas

_(None yet — will be populated during /build)_
```

---

## Step 7: Final Report

```
## ✅ Spec Created: {Task ID}

**Feature**: {name} | **Module**: {module} | **Status**: 📋 Planned

### File Created
- `.ai/context/specs/{task-id}.md`

### Business Rules (สรุป)
1. ...

### 🔴 Key Risks to Watch
- {risk}

### Next Steps
1. Review spec file — แก้เพิ่มได้ถ้ายังไม่ชัด
2. `/build {task-id}` เพื่อเริ่ม implement
3. `/reindex` เมื่ออยาก update features.md

### Pro tips
- requirement เปลี่ยนก่อน build → แก้ spec file ตรงๆ ได้
- build ไปแล้วค่อยมาแก้ → ใช้ `/change {task-id} "..."`
```

---

## Rules

### Must Do
- **อ่าน ARCHITECTURE.md + module rule** ก่อน analyze เพื่อไม่เสนอ pattern ที่ขัด
- **Delegate ให้ spec-analyzer** — ไม่ analyze เองใน main context (ยกเว้น runtime ไม่รองรับ)
- **ถามเฉพาะ ambiguity ที่สำคัญจริง** (สูงสุด 3)
- **Preserve original requirement** ใน spec file
- **รอ dev confirm** ก่อนเขียนไฟล์ทุกครั้ง (แม้มี `--quick`)

### Must Not
- ❌ **เขียน code ใน command นี้** — นี่คือ spec phase
- ❌ **แตะ `features.md`** — เป็นงานของ `/reindex`
- ❌ **Generate Task ID ก่อน Step 5**
- ❌ **ถาม ambiguity เกิน 3 ข้อ**
- ❌ **Overwrite spec file ที่มีอยู่**

### Edge Cases

- **Requirement คลุมหลาย module**: ถามว่าควรแยกเป็น 2 spec หรือไม่
- **Requirement ซ้ำกับ feature เดิม**: flag + ถาม — อาจต้องใช้ `/change` ไม่ใช่ `/spec`
- **Requirement เป็นแค่ idea**: ขอ clarify ก่อน ถ้ายัง vague เกิน → แนะนำให้ refine ก่อน

---

## Output Language

- ตอบ dev เป็น**ภาษาไทย**
- Spec file: business rules / edge cases → ไทย; technical term, path, code → อังกฤษ
- Original requirement → preserve ภาษาที่ dev พิมพ์

---

## Examples

**Normal flow**
```
dev: /spec ลูกค้าต้องการระบบ comment ใน blog post โดยไม่ต้อง login
AI: [identify module → delegate → ถาม 3 ข้อ → draft → confirm → save]
    ✅ Spec Created: TASK-20260501-1430
```

**Quick mode**
```
dev: /spec --quick เพิ่ม GET /health endpoint คืน {status: "ok"}
AI: [skip ambiguity → draft → confirm → save]
    ⚠️ Assumed defaults: ไม่มี auth, ไม่มี rate limit
```

**Vague requirement**
```
dev: /spec อยากได้ระบบ notification
AI: "Requirement กว้างไป — channel ไหน? trigger จากอะไร? ..."
```

**Conflict กับของเดิม**
```
dev: /spec ให้ user login ด้วย OTP ผ่าน SMS
AI: "⚠️ พบ TASK-20260424-1153 (Login + JWT) ที่อาจซ้อน
     A) /spec — feature ใหม่แยก
     B) /change TASK-20260424-1153 — เปลี่ยน auth flow เดิม"
```
