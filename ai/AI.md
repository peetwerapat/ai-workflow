# AI Working Agreement (Global)

ไฟล์นี้เป็น **rule กลาง** ที่ใช้กับทุก project และทุก assistant (Claude Code / Codex CLI / Antigravity CLI / ZCode)
Project แต่ละตัวมี context ของตัวเองใน `.ai/` — อ่านทั้งสองชั้นเสมอ

---

## Two-Layer Context

| Layer | ที่อยู่ | ใครดูแล | เนื้อหา |
|---|---|---|---|
| **Global** (ไฟล์นี้) | `~/.ai/AI.md` | shared ทุก project | workflow, commands, rule ที่ใช้ได้ทุกที่ |
| **Project** | `.ai/` ใน repo + memory file ที่ root | per project | domain, tech stack, architecture, specs |

**Project memory file** = ไฟล์ที่ assistant โหลดเองอัตโนมัติจาก root ของ repo
- Claude Code → `CLAUDE.md`
- Codex CLI → `AGENTS.md`
- Antigravity CLI (`agy`) → `AGENTS.md` หรือ `GEMINI.md` (อ่านทั้งสองแบบ ไล่ขึ้นจาก cwd ถึง repo root)
- ZCode → `AGENTS.md` (หรือ `.zcode/AGENTS.md` / `.agents/AGENTS.md`)

> ถ้า repo มีไฟล์ใดไฟล์หนึ่งใน 3 ตัวนี้ ให้ถือว่าเป็น project memory เดียวกัน — อ่านตัวที่มี
> ถ้า repo ยังไม่มี `.ai/` เลย → เสนอให้ dev รัน `/ai-init`

---

## Project Layout (convention กลาง)

```
<repo>/
├── CLAUDE.md | AGENTS.md | GEMINI.md   # project memory (root, assistant โหลดเอง)
└── .ai/
    └── context/
        ├── ARCHITECTURE.md   # ADR, patterns, anti-patterns
        ├── features.md       # derived index — regen ด้วย /reindex เท่านั้น
        ├── untracked.md      # shared infra ที่ไม่นับเป็น feature
        └── specs/
            ├── TASK-YYYYMMDD-HHMM.md          # active
            └── CLOSED-TASK-YYYYMMDD-HHMM.md   # terminal status
```

**`.ai/` ใช้ร่วมกันทุก assistant** — ห้ามแตกเป็น `.claude/context/`, `.codex/context/` แยกกัน
spec ชุดเดียว ไม่มี drift

**`.ai/` + memory file เป็น local-only ของเครื่องนี้ (default)** — `/ai-init` จะเพิ่ม memory file + `.ai/` เข้า `.git/info/exclude` ของ repo งานให้ → ไม่ต้อง commit และ ❌ ห้าม commit/push ขึ้น repo (ไฟล์ยังอยู่ครบ แค่ git มองไม่เห็น)
ถ้า dev ต้องการ share ให้ทีม: ลบบรรทัดเหล่านั้นออกจาก `.git/info/exclude` แล้ว dev commit เอง

---

## Development Workflow

ใช้ slash commands เหล่านี้ — อย่าข้ามขั้น

| Command | ใช้เมื่อ |
|---|---|
| `/ai-init` | repo ใหม่ยังไม่มี `.ai/` → scaffold context + project memory |
| `/spec <requirement>` | รับ requirement ใหม่ → วิเคราะห์ + บันทึก spec |
| `/build [task-id]` | Implement ตาม spec + เขียน test |
| `/change <task-id> "<desc>"` | แก้ feature เดิม (bug / req change / refactor) |
| `/status [filter]` | ดูภาพรวม features |
| `/reindex [--force]` | regen `features.md` จาก `specs/` + auto-close terminal tasks |
| `/sync [--fix]` | ตรวจ drift ระหว่าง spec ↔ code จริง |

### Standard Flows

```
Repo ใหม่:      /ai-init → /spec
Feature ใหม่:   /spec → confirm → /build → /reindex → review
แก้ของเดิม:     /change → confirm → auto-apply → /reindex
Bug urgent:    /change <task-id> "bug: <desc>"
Daily start:   /status mine
Weekly check:  /sync → /reindex
```

### Flags

- `--quick` (spec / change) — skip analysis, trust dev
- `--incremental` (build) — หยุด review ทุก layer
- `--no-test` (build) — skip test (prototype เท่านั้น)
- `--resume` (build) — ทำต่อจากที่ค้าง
- `--dry-run` (change) — ดู impact ไม่แก้จริง
- `--fix` (sync) — แก้ drift ที่เจอ
- `--force` (reindex) — re-read closed specs

> ⚠️ **ห้ามใช้ `--quick` กับ**: auth, payment, การคำนวณเงิน/point/tier, multi-tenant isolation, data migration
> งานกลุ่มนี้ต้องทำ analysis เต็มเสมอ แม้ dev จะสั่ง `--quick` มา — ให้ warn แล้วทำเต็ม

---

## Status Vocabulary

ใช้ชุดเดียวกันทุก project ทั้งใน spec file และ `features.md`

| Icon | Status | ความหมาย | Terminal? |
|---|---|---|---|
| 📋 | Planned | มี spec แล้ว ยังไม่ build | — |
| 🚧 | In Progress | กำลัง build / ค้างอยู่ | — |
| ⚠️ | Done (untested) | build แล้วแต่ไม่มี test | — |
| ✅ | Done | build + test ผ่าน | ✔ |
| 🔴 | Blocked | ติด blocker | — |
| ❌ | Cancelled | ยกเลิก | ✔ |
| 📦 | Deprecated | เลิกใช้ | ✔ |

**Terminal** = `/reindex` จะ rename ไฟล์เป็น `CLOSED-TASK-*.md` อัตโนมัติ

**Task ID**: `TASK-YYYYMMDD-HHMM` (สร้างตอน finalize spec เท่านั้น)
**Revision ID**: `{task-id}-R{NN}` (เพิ่มทุกครั้งที่ `/change` สำเร็จ)

---

## Ownership Rules (ใครแก้ไฟล์ไหนได้)

| ไฟล์ | เขียนได้โดย | ห้ามแตะโดย |
|---|---|---|
| `specs/TASK-*.md` (เนื้อ spec) | `/spec`, `/change` | `/build`, `/status`, `/reindex` |
| `specs/TASK-*.md` (Status / Implementation Status / Changelog / Gotchas) | `/build`, `/change`, `/sync --fix` | `/status` |
| `features.md` | `/reindex` เท่านั้น | ทุก command อื่น |
| `ARCHITECTURE.md` | dev (AI เสนอได้ ต้อง confirm) | — |
| source code | `/build`, `/change` | `/spec`, `/status`, `/reindex`, `/sync` (ยกเว้น `--fix` ที่แก้ doc) |

> `features.md` เป็น **derived view** ไม่ใช่ source of truth — source of truth คือ `specs/`

---

## Critical Rules (ทุก project)

### 1. ไม่มี spec = ไม่ implement

- Feature ใหม่ต้องผ่าน `/spec` ก่อนเสมอ
- dev พิมพ์ขอแก้ business rule ตรงๆ → แนะนำให้ใช้ `/change` เพื่อให้มี audit trail
- งานจิ๊บจ๊อย (typo, log message, format) → ทำได้เลย ไม่ต้อง spec

### 2. อ่าน context ก่อนเขียน code เสมอ

ลำดับ: project memory (root) → `.ai/context/ARCHITECTURE.md` → spec file → module rule (ถ้ามี) → code จริง

### 3. Follow existing pattern

- ดู code รอบข้างก่อน — ตั้งชื่อ, layering, error handling, test style ให้เหมือนของเดิม
- เจอ pattern ใหม่ที่ไม่อยู่ใน `ARCHITECTURE.md` → แจ้ง dev ว่าควรเพิ่ม ADR (ห้ามเพิ่มเอง)
- ❌ ห้ามสร้าง style ใหม่เพราะคิดว่าดีกว่า

### 4. Multi-tenant isolation (ถ้า project เป็น multi-tenant)

- ทุก query ต้อง filter ด้วย tenant key ที่ derive จาก **authenticated context** เท่านั้น
- ❌ ห้าม trust tenant key จาก query / body / header
- Cross-tenant access → คืน 404 ไม่ใช่ 403 (ซ่อน existence)
- ไม่แน่ใจว่า query ไหนต้อง filter → **ถามก่อน ห้ามเดา**

### 5. Security

- ❌ ห้าม hardcode secret / credential / API key — อ่านจาก config หรือ env เสมอ
- ❌ ห้ามอ่านหรือ print เนื้อหา `.env`, `*.pem`, `*.key`, `secrets/`
- ❌ ห้าม commit / push อัตโนมัติ — dev review แล้ว commit เอง
- ❌ ห้ามรัน destructive command (`rm -rf`, `DROP`, force push, `git reset --hard`) โดยไม่ confirm

### 6. Test

- `/build` และ `/change` ต้องมี test คู่เสมอ ยกเว้น `--no-test`
- test fail 3 รอบ → **หยุด** รายงาน dev ปล่อย status ค้าง 🚧 ดีกว่า mark ✅ หลอก
- REFACTORED → test เดิมต้อง pass เหมือนเดิม ถ้าพัง = ไม่ใช่ refactor แท้

### 7. Migration / schema change

- ห้ามสร้างไฟล์ migration เอง หรือตั้ง timestamp เอง — generate ผ่าน CLI ของ project เสมอ
- ต้อง reversible (มี up/down) และห้ามแก้ migration ที่ merge ไปแล้ว

### 8. Dependency ใหม่

- ต้อง flag + ขอ confirm จาก dev ก่อนติดตั้งทุกครั้ง
- บอกเหตุผลว่าทำไมใช้ของที่มีอยู่ไม่ได้

---

## Subagents

`/spec` และ `/change` ออกแบบให้ delegate งานวิเคราะห์ไปยัง agent แยก เพื่อประหยัด main context

| Agent | ใช้โดย | หน้าที่ |
|---|---|---|
| `spec-analyzer` | `/spec` | requirement → business rules / risks / edge cases / design |
| `impact-analyzer` | `/change` | change request → conflict check / dependency trace / risk / approach |

**ถ้า runtime รองรับ subagent** (เช่น Claude Code: Task tool) → delegate
**ถ้าไม่รองรับ** (เช่น Codex CLI) → อ่าน `~/.ai/agents/{agent}.md` แล้วทำตามนั้นเองใน pass เดียวแบบ focused
ผลลัพธ์ที่ต้องได้เหมือนกันทั้งสองทาง

---

## Output Language

- **ตอบ dev เป็นภาษาไทย** (ผสม technical term อังกฤษได้)
- **Code / code comment / commit message / branch name** → ภาษาอังกฤษเสมอ
- **Spec file**: business rules / edge cases → ภาษาไทย, technical term + path + code → อังกฤษ
- **Original requirement** ใน spec → preserve ภาษาที่ dev พิมพ์มา
- Commit message format: `{type}({scope}): {description}` (conventional commits)

---

## Working Style

1. **ไม่แน่ใจ → ถาม** ดีกว่า assume แล้วมาแก้ทีหลัง
2. **รายงาน assumption ทุกครั้ง** ที่ต้องเดาเพราะ spec ไม่ชัด
3. **บอกจุดที่ควร review** — จุดที่ต้องใช้ human judgment
4. **อย่าขยาย scope เอง** — ทำตามที่ขอ ถ้าเจอปัญหาอื่นให้ flag ไว้ ไม่ใช่แก้เลย
5. **ทำไม่เสร็จ ต้องบอกว่าไม่เสร็จ** — ห้ามรายงานว่า done ถ้า test ยังไม่ผ่าน
