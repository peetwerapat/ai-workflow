---
description: ดูภาพรวม features หรือ filter ตาม task-id / module / keyword / developer
argument-hint: [mine | done | <task-id> | <module> | <keyword>]
---

# /status — Feature Status Overview

Read-only command สำหรับดูภาพรวม features และหาข้อมูลเร็วๆ
**ไม่แก้ไฟล์อะไรทั้งสิ้น** — ปลอดภัยรันบ่อยๆ

## Context Files

- `.ai/context/features.md`

**ถ้าไม่มี `.ai/context/`** → แจ้งให้รัน `/ai-init` แล้วหยุด

## Runtime Info

```bash
git config user.name
```
ใช้สำหรับ `mine` filter

---

## Input

**$ARGUMENTS** — dispatch ตาม priority:

1. **Empty** → Overview mode
2. **`mine`** → filter ตาม current git user
3. **`done`** → list ✅ ทั้งหมด (ที่ overview ซ่อนไว้)
4. **Match task-id** (`TASK-\d{8}-\d{4}` หรือ `[A-Z]+-\d+`) → Detail view
5. **Match module name** (H1 ใน features.md) → Module filter
6. **อื่นๆ** → Keyword search

---

## Step 1: Load features.md

parse:
- `At a Glance` counts + `Last reindex` timestamp
- Module sections (`# {Module Name}`)
- Feature entries (1 บรรทัด: `- {icon} [TASK-id](link) — {Title} ({Dev}) — updated {date}`)
- `# Archived` section

> `features.md` เป็น index — รายละเอียดอยู่ใน spec file
> Detail mode เท่านั้นที่ follow link เข้าไปอ่าน spec

---

## Step 2: Dispatch by Mode

### 🔹 Overview (no args)

แสดง active items — **ไม่รวม ✅ Done** (ปกติเยอะเกิน)

เรียง: 🔴 Blocked > 🚧 In Progress > 📋 Planned

```
## Project Status

**Total**: {X} | ✅ {X} | ⚠️ {X} | 🚧 {X} | 📋 {X} | 🔴 {X}

### 🔴 Blocked ({count})
- {task-id} ({module}): {name} — {blocker reason}

### 🚧 In Progress ({count})
- {task-id} ({module}): {name} — {developer}

### 📋 Planned ({count})
- {task-id} ({module}): {name} — created {relative time}

> {X} completed features hidden — `/status done` เพื่อดูทั้งหมด
```

### 🔹 Mine

features ที่ `**Created**:` / `**Last Updated**:` match current git user
หรือมี recent commit โดย user นี้ในไฟล์ของ feature

```
## Your Tasks ({git user.name})

### 🚧 In Progress ({count})
- {task-id}: {name}
  - Last commit: {abbrev} "{message}" ({relative time})
  - Next: {hint จาก Known Gotchas / Implementation Status}
  - Spec: `.ai/context/specs/{task-id}.md`

### ✅ Recently Done (7 วันล่าสุด)
- {task-id}: {name} — done {relative time}

### 📋 Planned
- {task-id}: {name}

> ไม่มี task ของคุณตอนนี้ — `/spec` เพื่อเริ่ม feature ใหม่
```

git: `git log --author="{user.name}" --since="7 days ago" --oneline | head -20`

### 🔹 Task Detail

อ่าน spec file: `.ai/context/specs/TASK-{id}.md` (หรือ `CLOSED-TASK-{id}.md`)

```
## {task-id} — {feature name} {status-icon}

**Module**: {module}
**Created**: {date} by {dev}
**Status**: {icon + label}
**Last Updated**: {date} by {dev}
**Spec**: `.ai/context/specs/{path}.md`

---

### Files (จาก Implementation Status)
- {list}

### Business Rules
{top 3-5 — ที่เหลือบอก "ดูใน spec file"}

### Recent Activity
**Changelog**: {entries ล่าสุด 3-5 อัน}
**Git**: `git log -5 --format='- %h %s (%cr by %an)' -- <files>`

### Known Gotchas
{แสดงทั้งหมด — สำคัญ}

### Pending Questions
{Ambiguity ที่ยังไม่ resolve — ถ้า resolve หมดแล้ว skip section นี้}

### Next Actions
- 📋 Planned → `/build {task-id}`
- 🚧 In Progress → `/build --resume`
- ⚠️ Untested → เขียน test เพิ่ม แล้ว `/build --resume`
- ✅ Done → ถ้าต้องแก้ → `/change {task-id} "..."`
- 🔴 Blocked → แก้ blocker ก่อน
- ❌ / 📦 → ปิดแล้ว ถ้าจะรื้อ → reopen (rename CLOSED-)
```

### 🔹 Module Filter

```
## {Module Name} ({total} features)

### 🚧 In Progress ({count})
### 📋 Planned ({count})
### ✅ Done ({count})
### 🔴 Blocked ({count})
```

### 🔹 Keyword Search

grep ผ่าน `features.md` (ชื่อ feature) + `specs/*.md` (Business Rules / Changelog / Gotchas)

```
## Search: "{keyword}"

### Matches ({count})

**In Feature Names:**
- {task-id} ({module}): {name} {status-icon}

**In Spec Content:**
- {task-id} ({module}): {name} {status-icon}
  > "{matching context}..."

{ถ้าไม่เจอ → suggestions: /status, /status mine, ลอง keyword สั้นลง}
```

---

## Step 3: Enrich with Git (เฉพาะ Detail + Mine)

Overview / keyword mode → **skip git** เพื่อความเร็ว

---

## Rules

### Must Do
- **Read-only strict** — ห้าม write/edit (git query อ่านอย่างเดียวได้)
- **Concise** — fit หน้าจอเดียว
- **Sort by urgency** — 🔴 > 🚧 > 📋 > ⚠️ > ✅
- **Actionable next step** ใน Detail mode
- **เร็ว** — overview ไม่ต้องรัน git

### Must Not
- ❌ **แก้ไฟล์ใดๆ** — เจอ drift → แนะนำ `/reindex` (index drift) หรือ `/sync` (code drift)
- ❌ **Output ยาวจนต้อง scroll**
- ❌ **แสดง ✅ ทั้งหมดใน overview**
- ❌ **อ่าน spec file ใน overview / mine / module mode** (ใช้ features.md พอ)

---

## Edge Cases

**ยังไม่มี features**
```
## Project Status
ยังไม่มี features ในโปรเจคนี้ — เริ่มด้วย `/spec <requirement>`
```

**features.md stale**
```
⚠️ features.md อาจไม่ตรง — Last reindex: {date} ({N} วันที่แล้ว)
แนะนำ: /reindex
```

**Task ID ผิด format**
```
❌ "{input}" ไม่ใช่ task-id ที่ valid
Format: TASK-YYYYMMDD-HHMM หรือ {MODULE}-{NNN}
ค้นหาแทน: /status {keyword}
```

**Git user ไม่ตั้งค่า (mine mode)**
```
⚠️ Git user ยังไม่ตั้งค่า
  git config --global user.name "Your Name"
ระหว่างนี้แสดง overview แทน
```

---

## Output Language

ตอบเป็น**ภาษาไทย** / technical terms, task-id, path, git output → **อังกฤษ**

---

## Examples

```
dev: /status          → ภาพรวม active tasks
dev: /status mine     → งานของตัวเอง + git activity
dev: /status TASK-20260501-1430  → detail + next action
dev: /status payment  → keyword search
dev: /status Auth     → module filter
```
