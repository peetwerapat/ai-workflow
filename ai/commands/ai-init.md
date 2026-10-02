---
description: Scaffold .ai/ context + project memory file ให้ repo ที่ยังไม่มี — วิเคราะห์ codebase จริงก่อนเขียน
argument-hint: [--force]
---

# /ai-init — Bootstrap Project Context

เตรียม repo ให้พร้อมใช้ workflow `/spec → /build → /change` โดยสร้าง:
- **project memory file** ที่ root (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md` ตาม assistant ที่ใช้)
- `.ai/context/` พร้อม `ARCHITECTURE.md`, `features.md`, `untracked.md`, `specs/`
- context ทั้งหมดเป็น **local-only ของเครื่องนี้** — exclude ออกจาก git อัตโนมัติ ไม่ commit ขึ้น repo

**ห้ามเดา** — ทุกอย่างที่เขียนลงไฟล์ต้องมาจากการอ่าน code จริงในรอบนี้

## Input

**$ARGUMENTS**

- `--force` — เขียนทับของเดิมที่มีอยู่ (default: merge ไม่ทับ)

---

## Step 1: Detect Existing Setup

ตรวจว่ามีอะไรอยู่แล้วบ้าง:

- `.ai/context/` มีหรือยัง
- project memory file ที่ root (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) — มีตัวไหนบ้าง
- **Legacy context**: `.claude/context/`, `.codex/context/`, `.gemini/context/`, `.agents/context/` (ของเก่าที่แยกต่อ tool)
- **Legacy commands/agents/skills**: `.claude/commands/`, `.claude/agents/`, `.codex/prompts/`, `.codex/agents/`, `.codex/skills/`, `.agents/skills/`, `.agents/workflows/`

> ⚠️ **project-level command ชนะ global เสมอ** — ถ้า repo มี `.claude/commands/spec.md` ค้างอยู่
> `/spec` ใน repo นั้นจะได้ตัวเก่า ไม่ใช่ตัวกลาง และมักชี้ไป path ที่ย้ายไปแล้ว
> **ต้องลบทิ้ง ห้ามแก้ path ให้มันแทน** — ไม่งั้นกลายเป็นชุดที่สองที่ต้องดูแลแยก

**ถ้าเจอ legacy** → เสนอ migrate:
```
พบ setup เดิมแยกตาม tool:

Context (ต้องรวม):
- .claude/context/specs/ ({N} ไฟล์)
- .codex/context/specs/ ({N} ไฟล์)

Commands/agents (ต้องลบ — ชุดกลางที่ ~/.ai/ ทำหน้าที่นี้แล้ว):
- .claude/commands/ ({N} ไฟล์), .claude/agents/ ({N} ไฟล์)
- .codex/agents/ ({N} ไฟล์)

A) Migrate เต็ม — รวม context เป็น .ai/ + ลบ commands/agents เก่า (แนะนำ)
B) Migrate context อย่างเดียว — คง commands เก่าไว้ (จะ override ชุดกลาง)
C) Skip — สร้าง .ai/ เปล่าๆ
```

**Migration steps (option A):**

1. **Context** → `git mv` ไปที่ `.ai/context/` (ห้าม copy+delete — history จะขาด)
   - spec ที่ไม่มี Task ID มาตรฐาน (เช่น `TASK-POS-CRM-SSO.md`) → rename เป็น `TASK-YYYYMMDD-HHMM`
     โดยใช้วันที่ commit แรกของไฟล์นั้น (`git log --diff-filter=A --format=%ad --date=format:%Y%m%d-%H%M -- <file> | tail -1`)
     แล้ว**เขียน migration note** บนหัวไฟล์ว่า migrate มาจากชื่อเดิมอะไร
   - spec ที่ task ID ซ้ำกันข้าม tool → แสดง diff แล้วถาม dev ทีละคู่
2. **Commands/agents เก่า** → `git rm -r` ทิ้ง
   ถ้าไฟล์มี local modification ค้าง → ตรวจ `git diff` ก่อนว่าเป็นแค่ path rewrite จริงไหม แล้วค่อย `git rm -rf`
3. **`.claude/settings.json`** → แก้ permission ที่ตายแล้ว
   - `Edit(.claude/context/**)` → `Edit(.ai/context/**)`
   - ลบ `Edit(.claude/commands/**)`, `Edit(.claude/agents/**)` (ไม่มีโฟลเดอร์นั้นแล้ว)
4. **ลบ directory ที่ว่างเปล่า** ที่เหลือจากการย้าย (เช่น `.codex/`)
5. **เก็บไว้**: `.claude/settings.json` และไฟล์ note อื่นๆ ใน `.claude/*.md` ที่เป็นเอกสารของ project จริง

**ถ้ามี `.ai/context/` ครบแล้ว และไม่มี `--force`** → รายงานว่าพร้อมใช้แล้ว + แนะนำ `/status` แล้วจบ

---

## Step 2: Analyze Codebase

สำรวจของจริง (ห้ามข้าม step นี้):

| หัวข้อ | หาจาก |
|---|---|
| Language / runtime | manifest file (`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, …) |
| Framework | dependency list + entry point |
| Package manager | lockfile (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `uv.lock`, …) |
| Test runner + command | script section ใน manifest + config file |
| Lint / format / typecheck | script section + config file |
| Database / ORM | dependency + config/connection file |
| Migration tool + command | script section + migration folder |
| Module layout | โครงสร้างจริงของ source dir (ห้ามสมมติว่าเป็น `src/modules/`) |
| Layering pattern | อ่าน module ตัวอย่าง 1-2 ตัว |
| Error handling | หา custom exception / error class ที่ใช้อยู่ |
| Auth | หา guard / middleware / decorator |
| Multi-tenant | หา tenant key ที่ repeat ในหลาย query (เช่น `storeCode`, `tenantId`, `orgId`) |
| API shape | response wrapper / envelope ที่ใช้อยู่ |
| Naming convention | ดูจากชื่อไฟล์ + ชื่อ class/function จริง |
| CI | `.github/workflows/`, `.gitlab-ci.yml` |

**Git info**: `git config user.name`, `git log --oneline -20` (ดู commit message convention)

---

## Step 3: Show Findings + Confirm

สรุปสิ่งที่เจอให้ dev ตรวจก่อนเขียนไฟล์:

```
## Codebase Analysis

**Stack**: {language} {version} / {framework} / {db} / {package manager}
**Test**: {runner} — `{command}`
**Lint**: `{command}` | **Typecheck**: `{command}`
**Migration**: `{command}`

**Module layout**: `{path pattern}` ({N} modules: {list})
**Layering**: {ที่เจอจริง เช่น Controller → UseCase → Repository → Entity}
**Error handling**: {ที่เจอจริง}
**Auth**: {ที่เจอจริง}
**Multi-tenant**: {tenant key ที่เจอ | "ไม่พบ — single tenant"}
**Commit convention**: {ที่เห็นจาก git log}

### ❓ ยืนยันหน่อย
1. {จุดที่อ่าน code แล้วยังไม่ชัด — สูงสุด 3 ข้อ}

### ไฟล์ที่จะสร้าง
- `{memory file}` — project memory
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/features.md`
- `.ai/context/untracked.md`
- `.ai/context/specs/.gitkeep`

และแก้ `.git/info/exclude` — context ทั้งชุดจะเป็น **local-only** ไม่ถูก commit ขึ้น repo

พิมพ์ "confirm" เพื่อสร้าง
```

**รอ confirm ก่อนเขียนไฟล์เสมอ**

---

## Step 4: Write Files

ใช้ template จาก `~/.ai/templates/` เป็นโครง แล้วเติมด้วยข้อมูลจริงจาก Step 2

**4.1 Project memory file** (root) — ตั้งชื่อตาม assistant ที่กำลังรันอยู่
ถ้ามีไฟล์อื่นในตระกูลเดียวกันอยู่แล้ว (เช่นมี `CLAUDE.md` แต่กำลังรัน Codex) → **ห้ามสร้างซ้ำ**
สร้าง `AGENTS.md` ที่มีบรรทัดเดียวชี้ไปหาของเดิมแทน:
```markdown
See [CLAUDE.md](CLAUDE.md) — same content, single source of truth.
```

Content = template `project-memory.md` เติมด้วย: domain model, tech stack, layering, critical rules, conventions, directory structure ที่อ่านมาจริง

**4.2 `.ai/context/ARCHITECTURE.md`** — ADR + patterns + anti-patterns ที่ detect ได้
ทุก entry ต้องอ้าง file path จริงเป็นหลักฐาน

**4.3 `.ai/context/features.md`** — ใช้ template เปล่า (จะถูก regen ด้วย `/reindex`)

**4.4 `.ai/context/untracked.md`** — list shared infra ที่ไม่นับเป็น feature (common/, utils/, config/)

**4.5 `.ai/context/specs/.gitkeep`**

**4.6 Local-only context (default)** — ทำให้ context เห็นเฉพาะเครื่องนี้

เพิ่มเข้า `.git/info/exclude` ของ repo งาน (exclude ระดับ clone — ไฟล์นี้ไม่มีทางถูก commit/push ติดไปด้วย):
- memory file ที่สร้างจริง (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`)
- `.ai/`

```
AGENTS.md
.ai/
```

- ไฟล์ context ทั้งชุดยังอยู่ครบและใช้งานได้ปกติ — แค่ git มองไม่เห็น (`git status` ต้องไม่แสดง)
- ❌ อย่าใช้ `.gitignore` ของ repo เพราะไฟล์นั้นต้อง commit — คนอื่นจะรู้ทันทีว่ามี context ซ่อนอยู่
- ไม่ต้องสร้าง `.gitattributes` — `features.md` ไม่ถูก push แล้ว จึงไม่มี merge conflict
- ถ้าวันหน้าจะ share ให้ทีม: ลบบรรทัดพวกนี้ออกจาก `.git/info/exclude` แล้ว `git add` + commit ตามปกติ
  (ถ้าเคยมี `.gitattributes` `merge=ours` ค้างจาก flow เก่า ให้พูดถึงใน final report ว่ายังอยู่แต่ไม่จำเป็นแล้ว)

---

## Step 5: Retroactive Spec (optional)

ถ้า repo มี code อยู่แล้วเยอะ:

```
Repo นี้มี {N} modules อยู่แล้วแต่ยังไม่มี spec

A) ปล่อยไว้ก่อน — feature ใหม่ค่อยใช้ /spec (แนะนำ)
B) รัน /sync ตอนนี้เลย — ดูว่ามี orphan code เท่าไหร่ แล้วทยอยสร้าง spec ย้อนหลัง
```

**ห้าม generate spec ย้อนหลังอัตโนมัติทั้ง repo** — token เยอะและคุณภาพต่ำ

---

## Step 6: Final Report

```
## ✅ Project Initialized

### Files Created
- `{memory file}` ({N} lines)
- `.ai/context/ARCHITECTURE.md` ({N} ADRs)
- `.ai/context/features.md` (empty index)
- `.ai/context/untracked.md` ({N} entries)
- `.ai/context/specs/` (empty)

### ⚠️ ต้อง review เอง
{จุดที่เดาจาก code แล้วอาจไม่ตรงเจตนาจริง}
1. ...

### Migration Summary (ถ้ามี)
- ย้าย: {N} spec files → `.ai/context/specs/` (git mv)
- Rename: {N} spec ที่ไม่มี Task ID มาตรฐาน
- ลบ: {N} legacy commands/agents
- แก้: `.claude/settings.json` permission

### Next Steps
1. Review `{memory file}` + `ARCHITECTURE.md` — แก้ตรงที่ไม่ถูกได้เลย
2. ตรวจว่า `git status` **ไม่แสดง** `.ai/` และ memory file — context เป็น local-only (exclude ไว้ที่ `.git/info/exclude` แล้ว) ไม่ต้อง commit และ ❌ อย่า commit
3. `/spec <requirement>` เพื่อเริ่ม feature แรก
4. `/sync` ถ้าอยากรู้ว่ามี code ที่ยังไม่มี spec เท่าไหร่
```

---

## Rules

### Must Do
- **อ่าน code จริงก่อนเขียนทุกบรรทัด** — ทุก claim ต้องมี file path อ้างอิง
- **Confirm ก่อนเขียนไฟล์**
- **Merge ไม่ทับ** ถ้ามีไฟล์อยู่แล้ว (ยกเว้น `--force`)
- **รวม context เป็น `.ai/` ชุดเดียว** — ไม่แตกตาม tool
- **ลบ commands/agents เก่าของ project ทิ้ง** — ชุดกลางที่ `~/.ai/` ทำหน้าที่แทนแล้ว
- **ใช้ `git mv` / `git rm` เสมอ** เวลาย้ายหรือลบไฟล์ที่ track อยู่ — history ต้องไม่ขาด

### Must Not
- ❌ **เขียน stack/pattern ที่ไม่ได้ verify จาก code** — ถ้าไม่เจอให้เขียนว่า "ไม่พบ" ไม่ใช่เดา
- ❌ **ลบหรือทับไฟล์ที่มีอยู่โดยไม่ถาม**
- ❌ **สร้าง memory file ซ้ำซ้อน** ถ้ามีตัวอื่นในตระกูลเดียวกันแล้ว
- ❌ **แก้ path ใน `.claude/commands/` เก่าแทนการลบ** — project-level ชนะ global จะกลายเป็นชุดที่สอง
- ❌ **Generate spec ย้อนหลังทั้ง repo อัตโนมัติ**
- ❌ **commit / push `.ai/` หรือ memory file** — context เป็น local-only ของเครื่องนี้ (เว้นแต่ dev สั่งเอง)

---

## Output Language

ตอบ dev เป็นภาษาไทย / เนื้อหาไฟล์ตามรูปแบบใน template (ไทย + technical term อังกฤษ)
