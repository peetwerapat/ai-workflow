---
description: ตรวจ drift ระหว่าง spec files ↔ code จริง (ไม่ตรวจ features.md — งาน /reindex)
argument-hint: [--fix]
---

# /sync — Detect & Fix Spec ↔ Code Drift

ตรวจว่า spec ใน `.ai/context/specs/` ยังตรงกับ code จริงไหม
— report อย่างเดียว (default) หรือ interactive fix (`--fix`)

**ขอบเขต**: ไม่ตรวจ `features.md` drift — นั่นเป็น derived view แก้ด้วย `/reindex`
**End of run**: `--fix` mode จะ chain `/reindex` อัตโนมัติ (เพราะ spec ถูกแก้)

## Context Files

- project memory file ที่ root
- `.ai/context/features.md` (overview เท่านั้น — ไม่ใช่แหล่ง detect)
- `.ai/context/untracked.md` (whitelist)

## Runtime Info

```bash
git log --oneline -10
git status --short
```

## Input

**$ARGUMENTS**

- **Empty** → Detection mode (report only)
- **`--fix`** → Interactive fix (detect → propose → confirm ทีละรายการ)

---

## Step 1: Scan Sources

### Source A — spec files (source of truth)

อ่านทุกไฟล์ใน `.ai/context/specs/` (ทั้ง `TASK-*.md` และ `CLOSED-TASK-*.md`)

Parse: Task ID, Module, Status, และ **Implementation Status > Files**

Multi-repo project → อ่าน `<project>/.ai/context/specs/` ด้วย เฉพาะ spec ที่ `**Repos**:` มี repo นี้ — ใช้แค่แถวของ repo นี้ใน Implementation Status
(ไฟล์ที่อยู่ในนั้น = tracked ไม่ใช่ orphan) / `--fix` แก้ได้เฉพาะแถวของ repo นี้

### Source B — source code

หา source root จริงของ project (ห้ามสมมติว่าเป็น `src/`) แล้ว list:
- module/package directories ที่มีจริง
- source file ทั้งหมด (ยกเว้น generated / vendor / build output)
- migration files

---

## Step 2: Detect Drift Categories

### 🔴 Category 1: Orphan Code
**ไฟล์ code มีอยู่ แต่ไม่ปรากฏใน Files list ของ spec ใด** (เขียนโดยไม่ผ่าน `/spec`)

Skip: ไฟล์ที่ระบุไว้ใน `untracked.md`, test file ที่คู่กับ source ที่ track แล้ว, config/generated files

```
🔴 {path}
   Created: {commit} "{msg}" ({relative time} by {author})
   ไม่มี spec ใดอ้างถึง
```

### 🔴 Category 2: Stale Files
**spec บอกว่ามีไฟล์ X แต่ filesystem ไม่มี**

```
🔴 CLOSED-TASK-{id}.md ({Module})
   ระบุว่ามี: {path}
   File หาย (อาจถูก rename ใน {commit}, {relative time})
```

### 🟡 Category 3: Module Orphan
**มี module directory แต่ไม่มี spec ที่ `Module` = ชื่อนั้น**

### 🟡 Category 4: Status Lie
- ✅ แต่ Files list ว่าง
- ✅ แต่ไฟล์ใน Files list หายหมด
- 📋 แต่ code มีจริงแล้ว (build แล้วลืม flip status)

### 🟡 Category 5: Post-BUILT Activity (heuristic)
**ไฟล์ใน spec ถูกแก้หลัง Changelog entry ล่าสุด**

- หา date ของ Changelog entry ล่าสุด (BUILT / CHANGED / FIXED / REFACTORED — เอา max)
- `git log --since="{date}" -- {files}`
- มี commit หลังจากนั้นที่ไม่ตรงกับ Changelog → flag

> ⚠️ **Heuristic เท่านั้น** — commit อาจเป็น typo / comment update, dev ต้อง judge เอง

---

## Step 3: Report

```
## Doc Drift Report (Spec ↔ Code)

Scanned: {X} spec files | {Y} modules | {Z} source files

---

### 🔴 Critical Drift ({count})

**Orphan Code ({count})**
- `{path}` — created {commit} "{msg}" ({time} by {author}), ไม่มี spec อ้างถึง

**Stale Files ({count})**
- {task-id}: `{path}` not found — last commit {commit} ({time})

---

### 🟡 Warning Drift ({count})

**Module Orphan ({count})**
- `{module path}` — ไม่มี spec ที่ Module = {name}

**Status Lie ({count})**
- {task-id}: status ✅ แต่ Files list ว่าง
- {task-id}: status 📋 แต่ code มีแล้ว

**Post-BUILT Activity ({count})**
- {task-id} ✅ (last entry {date}) — `{file}` แก้เมื่อ {date}
  Check ว่าเป็น bug fix, refactor, หรือ requirement change

---

### ✅ In Sync
{X} specs ไม่พบ drift
```

**ไม่พบ drift เลย:**
```
## ✅ Spec ↔ Code in Sync
Scanned {X} specs, {Y} modules, {Z} files — no drift detected
(features.md sync เป็นงานของ /reindex)
```

---

## Step 4: Fix Mode (เฉพาะ `--fix`)

ไม่มี `--fix` → จบที่ Step 3 + แนะนำ `/sync --fix`

Interactive ทีละรายการ เรียง 🔴 → 🟡:

```
## Drift {N} of {Total}: {Category}

{detail}

### Suggested actions
A) {option 1}
B) {option 2}
C) Skip

เลือก [A/B/C]:
```

### Fix Options ต่อ Category

**Orphan Code**
```
A) Generate spec retroactively — analyze code ปัจจุบัน → สร้าง spec ใหม่
   Status: ✅ (retroactive), Changelog: ADDED retroactively via /sync
B) Add to existing spec — เลือก task-id → เพิ่ม path ใน Implementation Status > Files
C) Mark as untracked — เพิ่มใน `.ai/context/untracked.md` (shared util / infra)
```

**Stale Files**
```
A) Remove from Files list (+ Changelog "REMOVED {file}")
B) File ถูก rename — ถาม path ใหม่ → update + Changelog "REFACTORED — renamed {old} → {new}"
C) Feature ถูก revert — `/change {task-id} --cancel "code reverted"`
```

**Module Orphan**
```
A) Create spec retroactively สำหรับ module นี้
B) Mark untracked
C) Module deprecated — confirm + dev ลบเอง
```

**Status Lie**
```
# ✅ + Files ว่าง
A) Fill Implementation Status — scan code → propose Files list

# 📋 + code มีจริง
A) Flip Status → ✅ (acknowledge ว่า build นอก flow)
B) `/build --resume` — proper flow + tests (แนะนำ)
```

**Post-BUILT Activity**
```
A) Add CHANGED entry (+ reason, update Business Rules ถ้าจำเป็น)
B) Add FIXED entry (bug fix ไม่ใช่ requirement change)
C) Add REFACTORED entry (internal only)
D) Skip (typo / comment เท่านั้น)
```

---

## Step 5: Chain /reindex + Summary

```
## 🔄 Running /reindex to refresh features.md...
✅ features.md regenerated

## ✅ Sync Complete

Fixed: {X} | Skipped: {Y} | Reindex: ✅

### Changes Made
- Spec files modified: {list}
- New spec files: {list}

### Still Drift (skipped)
{list}

### Next Steps
- `git diff .ai/` review
- Commit: `docs: sync drift fixes`
```

---

## Rules

### Must Do
- **Detect ทั้งหมดก่อน fix** — อย่า fix-as-you-go
- **Confirm ทุก fix** — ห้าม auto-fix แม้ดูปลอดภัย
- **Preserve history** — แก้ spec ต้อง append Changelog เสมอ
- **เรียงตาม severity** — 🔴 ก่อน 🟡
- **อธิบาย "ทำไม flag"** — commit info, timestamp
- **Chain `/reindex` ตอนจบ** ของ `--fix` mode

### Must Not
- ❌ **ตรวจ features.md drift** — งานของ `/reindex`
- ❌ **ลบไฟล์โดยไม่ confirm** แม้เป็น orphan
- ❌ **Overwrite spec file** — regenerate ต้อง merge หรือ backup
- ❌ **Auto-generate spec จาก heuristic** — ต้องให้ dev review
- ❌ **Mark ✅ Done จาก sync** — status change ต้องมี test รองรับ (แนะนำ `/build --resume`)
- ❌ **พังถ้าไม่ใช่ git repo** — ต้อง graceful fallback

---

## Edge Cases

**Project ใหม่ (specs/ ว่าง)**
```
Project ยังไม่มี features — ไม่มี drift ให้ตรวจ
💡 เริ่มด้วย `/spec <requirement>`
```

**Massive drift (> 20 items)**
```
⚠️ พบ drift จำนวนมาก ({X} items)
อาจเกิดจาก: เพิ่ม doc หลัง code (legacy) / long-running branch merge / ข้าม /sync มานาน

แนะนำ: แก้จาก 🔴 ก่อน แล้ว 🟡 ทีละกลุ่ม
```

**Non-git project**
```
⚠️ Git ไม่พร้อมใช้งาน — ยัง detect ได้แบบ file-based
แต่จะ miss: last commit, recent activity, who/when
```

**Uncommitted changes**
```
⚠️ มี uncommitted changes ({X} files) — detect อาจไม่แม่น
A) Continue  B) `git stash` ก่อน  C) Cancel แล้วค่อย commit
```

**Orphan ใน shared/common directory**
```
⚠️ น่าจะเป็น shared infrastructure — แนะนำเพิ่มใน untracked.md แทนสร้าง spec
```

---

## Output Language

ตอบเป็น**ภาษาไทย** / technical terms, path, git output → **อังกฤษ**

---

## Examples

```
dev: /sync
AI: ## ✅ Spec ↔ Code in Sync — Scanned 15 specs, 5 modules, 42 files

dev: /sync
AI: ### 🔴 Critical Drift (1)
    **Orphan Code** — `{path}` created 2d ago, ไม่มี spec อ้างถึง
    รัน `/sync --fix` เพื่อแก้

dev: /sync --fix
AI: [scan → report → fix ทีละอัน → chain /reindex]
    ✅ Sync Complete — Fixed: 1, Skipped: 0, Reindex: ✅
```
