# ai-agent — ชุด AI กลางสำหรับทุก project

ชุด workflow `/spec → /build → /change` สำหรับงานที่ต้องการ spec และ audit trail ใช้ร่วมกันได้กับ **Claude Code**, **Codex CLI**, **Antigravity CLI (`agy`)** และ **ZCode** ในทุก repo คำขอแก้โค้ดด้วยภาษาปกติให้ลงมือทำได้ทันที

```
ai/                      ← source of truth ชุดเดียว
├── AI.md                  rule กลาง (workflow, status vocabulary, critical rules)
├── commands/              /ai-init /spec /build /change /status /reindex /sync
├── agents/                spec-analyzer, impact-analyzer, code-reviewer, debugger, codebase-explorer
├── workflows/             helper routing, practical validation, completeness, feedback
├── tools/                 Python tools: index, validation, context, doctor/rollback, evaluation
├── evals/                 behavioral rubrics (10 scenarios)
└── templates/             โครงไฟล์ระดับ repo สำหรับ /ai-init
    └── project/           โครงไฟล์ shared context ของ multi-repo project
```

## ติดตั้ง

```bash
git clone <repo> && cd ai-workflow
./install.sh              # เลือกจากเมนูว่าจะติดตั้งตัวไหน
./install.sh all          # ทุกตัว ไม่ถามเมนู
./install.sh claude       # เฉพาะตัวใดตัวหนึ่ง (claude | codex | antigravity | zcode | shell)
./install.sh --status     # ดูว่าติดตั้งอะไรไว้
./install.sh --doctor     # ตรวจ config, symlink และไฟล์ generate ที่ล้าสมัย
./install.sh --rollback   # คืนค่าก่อนติดตั้งครั้งล่าสุด ถ้าไฟล์ยังไม่ถูกแก้ภายหลัง
./install.sh --update     # ดึงเวอร์ชันใหม่จากต้นทางแล้วติดตั้งทับ
./install.sh --uninstall  # ถอนเฉพาะสิ่งที่ script สร้าง (รวม ~/.ai-agent + shell wrapper)
```

### ลบ folder ที่ clone มาได้เลย

`install.sh` จะ **copy ตัวเอง + `ai/` ไปไว้ที่ `~/.ai-agent` ก่อน** แล้ว re-exec ติดตั้งจากที่นั่น
symlink ทุกเส้นและ shell wrapper จึงชี้ไป `~/.ai-agent` ไม่ใช่ folder ที่ clone มา

```
~/.ai-agent/          ← ที่เก็บถาวร (ห้ามลบ)
├── ai/                 copy ของ ai/ ใน repo
├── install.sh          copy — ใช้ --update / --uninstall จากที่นี่ได้
├── .source             git remote + commit ที่ติดตั้งมา (ให้ --update รู้ว่าดึงจากไหน)
└── .install-prefs      ตัวเลือกที่ติ๊กไว้ — ไม่หายตอน update
```

ติดตั้งเสร็จ script จะบอกเองว่าลบ clone ได้ อัปเดตรอบหลังไม่ต้อง clone ใหม่:

```bash
~/.ai-agent/install.sh --update     # clone ต้นทางลง temp → copy ทับ → ติดตั้งซ้ำด้วยค่าที่จำไว้
```

รันเปล่าๆ จะขึ้นเมนูให้ติ๊ก — ค่า default ติ๊กเฉพาะตัวที่มี binary จริงในเครื่อง

```
  เลือก assistant ที่จะติดตั้ง

  ❯ ◉ Claude Code        พบ claude
    ◉ Codex CLI          พบ codex
    ◯ Antigravity CLI    ไม่พบ agy ในเครื่อง
    ◉ ZCode              พบ ~/.zcode
    ◉ Shell wrapper      auto-sync ตอนเปิด codex/agy

  ↑/↓ เลื่อน · space ติ๊ก · a ทั้งหมด · n ล้าง · enter ยืนยัน · q ออก
```

| ปุ่ม | ผล |
|---|---|
| `↑` `↓` หรือ `k` `j` | เลื่อน (วนรอบ) |
| `space` | ติ๊ก/เอาติ๊กออกบรรทัดที่อยู่ |
| `1`–`5` | กระโดดไปบรรทัดนั้นแล้วติ๊กเลย |
| `a` / `n` | เลือกหมด / ล้างหมด |
| `enter` | ยืนยัน |
| `q` หรือ `Esc` | ออกโดยไม่ติดตั้ง |

ที่เลือกไว้ถูกจำใน `.install-prefs` (อยู่ที่ `~/.ai-agent/` หลังติดตั้ง — gitignore แล้ว) รอบหน้าไม่ต้องติ๊กใหม่ ลบไฟล์นี้เพื่อกลับไป auto-detect
รันแบบ non-interactive (CI / script) จะข้ามเมนูแล้วใช้ค่าที่จำไว้ หรือ `AI_AGENT_YES=1` เพื่อบังคับข้าม

`install.sh` จะเพิ่ม `codex()` + `agy()` wrapper ใน shell rc ให้ด้วย — sync skill ให้ก่อนเปิดทุกครั้ง

wrapper ตรวจ doctor เฉพาะ provider ก่อนเปิด ถ้าไฟล์ยังตรงกับ source จะข้ามการ generate; ถ้า sync ล้มเหลวจะแสดง error และหยุดเปิด assistant เพื่อให้แก้ก่อน

ไม่อยากให้แตะ shell rc → `AI_AGENT_NO_SHELL=1 ./install.sh` (แต่ต้องรัน `./install.sh codex` / `antigravity` เองทุกครั้งที่แก้ command)

ไฟล์เดิมที่ทับจะถูกสำรองเป็น `*.bak-YYYYMMDD-HHMMSS` ก่อนเสมอ
(ยกเว้น symlink ของ script นี้เอง และ symlink ที่เสียค้างเพราะ clone เดิมถูกลบ — เขียนทับเลยไม่สำรอง)

### ติดตั้งไปที่ไหนบ้าง

| | Claude Code | Codex CLI | Antigravity CLI | ZCode |
|---|---|---|---|---|
| Memory | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | — (ไม่มี global rules — skill อ่าน `~/.ai/AI.md` เอง) | `~/.zcode/AGENTS.md` |
| Commands | `~/.claude/commands/*.md` (symlink) | `~/.codex/skills/<n>/SKILL.md` (generate) | `~/.gemini/config/skills/<n>/SKILL.md` (generate) | `~/.zcode/commands/*.md` (symlink) |
| Agents | `~/.claude/agents/*.md` (generate) | `~/.codex/agents/*.toml` (generate) | `~/.gemini/config/agents/*.md` (generate) | `~/.zcode/agents/*.md` (generate) |
| เรียกด้วย | `/spec` | **`$spec`** | เรียกชื่อ skill (`spec`) | `/spec` |

**Claude** และ **ZCode** ใช้ commands เป็น symlink (ชี้ไป `~/.ai-agent/ai/commands/`) — Codex/Antigravity ต้อง generate ใหม่
ทั้งสองแบบอัปเดตด้วย `~/.ai-agent/install.sh --update` เหมือนกัน

### กำหนด model และ effort ของ analyzer

แก้ `ai/agents/models.json` แยกตาม agent และ provider แล้วรัน `./install.sh <provider>` ใหม่ เช่น `claude`, `codex`, `antigravity`, `zcode`:

```json
{
  "spec-analyzer": {
    "claude": {"model": "sonnet", "effort": "medium"},
    "codex": {"model": "gpt-6-luna", "effort": "xhigh"},
    "antigravity": {"model": "pro"},
    "zcode": {"model": "inherit"}
  }
}
```

Claude ใช้ `effort`, Codex ใช้ `model_reasoning_effort`, ZCode ใช้ `thoughtLevel` เมื่อระบุ model เฉพาะ (เช่น `{"model": "glm-5.3", "effort": "high"}`) ส่วน Antigravity CLI รองรับ model tier `inherit`/`flash`/`pro` ใน agent file แต่ยังไม่มี effort ระดับ agent ใน schema ที่เผยแพร่ จึงไม่รับ `effort` สำหรับ provider นี้ ตัวติดตั้งจะหยุดพร้อม error หากระบุค่า unsupported

agent ทั้ง 5 ตัวเป็น read-only; Codex agent ที่ generate จะตั้ง `sandbox_mode = "read-only"` ด้วย หาก runtime ไม่มี subagent tool คำสั่งจะวิเคราะห์ใน main context และ model/effort เฉพาะ agent จะไม่มีผล

**Codex** (0.155+) เลิกใช้ `~/.codex/prompts/` แล้ว — custom command ต้องเป็น **skill** (`~/.codex/skills/<name>/SKILL.md`)
และเรียกด้วย **`$`** ไม่ใช่ `/` — frontmatter รับแค่ `name`, `description`, `license`, `allowed-tools`, `metadata`

**Antigravity** (`agy`) ใช้ skill เหมือนกัน แต่ customization root ระดับ global คือ `~/.gemini/config/`
(workflows `*.md` เป็นของเก่าที่ Google กำลัง migrate ไป skill — ใช้ skill ตรงๆ เลย)

Antigravity ไม่มี global rules file — rules เป็น directory-based (`AGENTS.md`/`GEMINI.md` ไล่ขึ้นจาก cwd)
เลย generate SKILL.md ให้มีบรรทัดสั่งอ่าน `~/.ai/AI.md` เองตอนเริ่ม

**ZCode** (desktop app ของ Z.ai, agent `glm`) อ่าน config แบบเดียวกับ Claude — frontmatter `description`/`argument-hint` และ `$ARGUMENTS` ใช้ได้ตรงๆ
ZCode ข้าม symlink ใน `~/.zcode/agents/` → agents ถูก generate เป็นไฟล์จริง (มี marker `generated by ai-agent`)
แก้ `ai/agents/*.md` หรือ `ai/agents/models.json` แล้วต้องรัน `./install.sh zcode` ซ้ำ (ไม่มี shell wrapper ให้ เพราะเปิดจาก app) — ตรวจเจอจาก `~/.zcode` ไม่ใช่ binary ใน PATH

Codex/Antigravity มี shell wrapper (`codex()` / `agy()`) ที่ `install.sh` ใส่ให้ — sync ก่อนเปิดทุกครั้งอัตโนมัติ ไม่ต้องจำ

`~/.ai` เป็น symlink ไปที่ `~/.ai-agent/ai/` ทำให้ทุก assistant อ้าง path เดียวกันได้ (`~/.ai/agents/spec-analyzer.md`)

## ใช้งาน

พิมพ์คำขอปกติ เช่น “เพิ่ม usage ใต้ชื่อ model” → assistant อ่าน context ที่มีอยู่ ตรวจโค้ด แก้ ทดสอบ และรายงาน โดยไม่สร้าง spec หรือรัน `/ai-init` เอง แม้ repo ยังไม่มี `.ai/` ก็ตาม ใช้คำสั่งด้านล่างเมื่ออยากได้ workflow ที่บันทึก spec และประวัติการเปลี่ยนแปลง

```
repo ใหม่:     /ai-init                       scaffold .ai/ + project memory จากการอ่าน code จริง
หลาย repo:     /ai-init --project             (ที่ root ของ project) shared context + .ai/ ของทุก repo ข้างใน
ภาษา context:  /ai-init --lang th              ไฟล์ context เป็นไทย (default en — ประหยัด token)
feature ใหม่:  /spec <requirement> → /build   → /reindex
แก้ของเดิม:    /change <task-id> "<desc>"     → /reindex
ดูภาพรวม:      /status | /status mine | /status <task-id>
ตรวจ drift:    /sync [--fix]
ส่งต่องาน:     /handoff [task-id]
จำบทเรียน:     /learn <กฎที่ยืนยันแล้ว พร้อมขอบเขตและหลักฐาน>
ตรวจโค้ด:      /review [scope]
หาสาเหตุ bug:  /debug <อาการและวิธีทำให้เกิด>
หาโค้ด/flow:   /explore <คำถามหรือ module>
```

> **Codex ใช้ `$` แทน `/`** — `$spec`, `$build`, `$ai-init`
> **Antigravity** เรียกชื่อ skill ตรงๆ (`/skills` ดูรายการ)
> **ZCode** ใช้ `/` เหมือน Claude — `/spec`, `/build`

## ภาษาของไฟล์

| ไฟล์ | ภาษา |
|---|---|
| `ai/` (AI.md, commands, agents, templates) | อังกฤษ — AI อ่าน ประหยัด token (`AI.md` โหลดทุก session) |
| ไฟล์ context ใน repo งาน (memory, `MEMORY.md`, `ARCHITECTURE.md`, `PROJECT.md`, ...) | เลือกตอน `/ai-init --lang en\|th` (default `en`) — แก้ไฟล์เดิมทีหลังจะใช้ภาษาเดิมของไฟล์นั้น |
| spec (`specs/TASK-*.md`) | ไทย (business rule / edge case) + technical term อังกฤษ |
| ที่ agent ตอบคุณ | ไทยเสมอ |

## Context 2 ชั้น

| ชั้น | ที่อยู่ | เนื้อหา |
|---|---|---|
| **Global** | `~/.ai/AI.md` | workflow, status vocabulary, critical rules ที่ใช้ได้ทุก project |
| **Project shared** (optional) | `<project>/.ai/context/` | ภาพรวมระบบ, domain ร่วม, convention ร่วม, contract ระหว่าง repo |
| **Project** | `.ai/context/` + memory file ที่ root ของ repo | domain, stack, architecture, specs |

```
<repo>/
├── CLAUDE.md | AGENTS.md | GEMINI.md
└── .ai/context/
    ├── ARCHITECTURE.md
    ├── features.md          ← derived view, regen ด้วย /reindex เท่านั้น
    ├── untracked.md
    ├── context-map.json     ← source prefix → context files ที่เกี่ยวข้อง
    ├── HANDOFF.md           ← งานที่ทำแล้ว/เหลือ และ validation ที่เกิดขึ้นจริง
    ├── LESSONS.md           ← บทเรียนที่ dev ยืนยัน พร้อมหลักฐานและเงื่อนไขทบทวน
    └── specs/
        ├── TASK-YYYYMMDD-HHMM.md
        └── CLOSED-TASK-YYYYMMDD-HHMM.md
```

**`.ai/` ใช้ร่วมกันทุก assistant** — ไม่แตกเป็น `.claude/context/`, `.codex/context/` แยกกัน spec จึงไม่มีวัน drift ระหว่าง tool
repo ที่ยังใช้ layout เก่าอยู่ → `/ai-init` จะเสนอ migrate ให้

### Multi-repo project

project ที่มีหลาย git repo (กี่ตัวก็ได้ ชื่ออะไรก็ได้) แชร์ context ระดับ project ร่วมกันได้ — ไม่ copy ซ้ำลงทุก repo

```
project/                      ไม่ต้องเป็น git repo
├── CLAUDE.md                 สั้นๆ ชี้ไป .ai/context/PROJECT.md (ใช้ตอนเปิด session ที่ root ทำงานข้าม repo)
├── .ai/context/              shared: PROJECT.md, ARCHITECTURE.md, conventions.md, integrations.md
│                             + specs/ features.md ของ cross-repo task
├── web/.ai/context/          เฉพาะ web: ARCHITECTURE.md, features.md, untracked.md, specs/
├── api/.ai/context/          เฉพาะ api
└── docs/                     ไม่ใช่ git repo → ข้าม
```

```
cd ~/dev/project && /ai-init            detect เองว่าเป็นระดับ project (หรือ /ai-init --project)
cd ~/dev/project/api && /ai-init        ระดับ repo — เจอ shared ด้านบนแล้วอ้างถึง ไม่ copy (หรือ /ai-init --repo)
```

- **ระดับ project**: detect repo จากลูกตรงที่มี `.git` ของตัวเอง → ให้เลือก repo → เขียน shared → init ทีละ repo
  repo ที่มี `.ai/` แล้วจะข้าม (ยกเว้น `--force`) และสรุป Installed / Skipped / Failed ตอนจบ
- **Agent โหลด context ยังไง** (`ai/AI.md` › Context Resolution): ไล่ขึ้นจาก root ของ repo หา `.ai/context/PROJECT.md`
  → อ่าน shared + `.ai/` ของ **repo ที่ task แตะเท่านั้น** — ทำงานใน `api/` ไม่ต้องโหลด context ของ web/worker
- repo เดี่ยวที่ไม่อยู่ใน project ใดๆ → ทำงานเหมือนเดิมทุกอย่าง

#### Task ที่แตะหลาย repo (2, 3, ... N)

```
cd ~/dev/project
/spec ให้ user แนบไฟล์ใน comment ได้        → ตรวจว่าแตะ api, worker, web → cross-repo spec ไฟล์เดียว
/build TASK-20261003-1400                   → build ทีละ repo ตาม build order (api → worker → web)
/build TASK-20261003-1400 --repo web        → หรือทำทีละ repo จาก session แยก
/reindex                                    → features.md ของ project + section "Cross-repo" ใน repo ที่เกี่ยว
```

```markdown
# TASK-20261003-1400 — Comment attachments
**Scope**: cross-repo
**Repos**: api, worker, web          ← build order: provider ก่อน consumer
**Status**: 🚧 In Progress           ← overall คำนวณจากทุก repo

## Business Rules                    ← เขียนครั้งเดียว ไม่ซ้ำในแต่ละ repo
## Contract Changes                  ← api → worker, web
## Proposed Design                   ← ### api / ### worker / ### web
## Implementation Status
| Repo   | Status | Files | Tests |
| api    | ✅ | api/src/... | 14/14 |
| worker | 🚧 | ... | |
| web    | 📋 | — | — |
```

- spec อยู่ที่ `project/.ai/context/specs/` — `/build`, `/change`, `/status` ใน repo หาเจอเองจาก task-id
- เปิด session ที่ `project/` ตอน build หลาย repo (Codex sandbox เขียนได้เฉพาะ directory ที่เปิด)
- repo ก่อนหน้า test fail → ไม่ build repo ที่พึ่ง contract ของมัน
- commit แยกต่อ repo (คนละ git repo) ใส่ `Task: TASK-...` เดียวกันเพื่อ trace

## ให้คนอื่นในทีมใช้ด้วย

ชุดนี้ไม่ผูกกับ path หรือเครื่องไหน — `install.sh` อ้าง path จากที่ตัวเองอยู่ ใคร clone ไปวางที่ไหนก็ได้

**เจ้าของ repo — push ขึ้น remote ครั้งเดียว**
```bash
cd ~/Documents/dev/ai-agent
git add -A
git commit -m "feat: central AI config for claude/codex/antigravity"
git remote add origin <repo-url>
git push -u origin main
```

**เพื่อนร่วมทีม — clone แล้วรัน install ครั้งเดียว**
```bash
git clone <repo-url> ~/dev/ai-agent   # วางที่ไหนก็ได้
cd ~/dev/ai-agent
./install.sh
```

จากนั้นเปิด repo งานแล้ว `/ai-init` (ถ้า repo นั้นยังไม่มี `.ai/`) — context ที่ได้เป็น **local-only ของเครื่องนั้น** (`/ai-init` จะ exclude ที่ `.git/info/exclude` ให้ ไม่ commit ขึ้น repo)

```
ครั้งเดียวต่อคนต่อ repo งาน   รัน /ai-init — context อยู่กับเครื่องนั้น
หลังจากนั้น                  /spec /build /change ได้เลย
```

**Antigravity**: `install.sh` วาง skill ให้ แต่ไม่ได้ลงตัว CLI — ใครจะใช้ต้องติดตั้ง `agy` เอง (ไม่พบใน PATH จะมี warning)

**อัปเดตชุดกลางทีหลัง**
```bash
cd ~/dev/ai-agent && git pull && ./install.sh
```
หลัง self-install ให้รันตัวติดตั้งหรือ `~/.ai-agent/install.sh --update` เพื่อคัดลอก source ใหม่เข้า permanent store ทุก provider ใช้ชุดใน store นั้น
Codex/Antigravity มี wrapper ตรวจ generation drift ก่อนเปิด ส่วน ZCode ให้ติดตั้งซ้ำเมื่อแก้ agents

### สิ่งที่แชร์ vs ไม่แชร์

| | อยู่ที่ไหน | แชร์ยังไง |
|---|---|---|
| Rule กลาง, commands, agents | repo นี้ | `git pull` + `./install.sh` |
| Spec / architecture ของแต่ละงาน | `.ai/` ใน repo งานนั้น | ไม่แชร์ — local-only ของเครื่อง (exclude ที่ `.git/info/exclude`) |

`.ai/` + memory file เป็นของเครื่องนั้นโดย default — `/ai-init` จะเพิ่มเข้า `.git/info/exclude` ให้
ไฟล์ยังอยู่ครบและใช้งานได้ปกติ แค่ git มองไม่เห็น — อย่า commit/push ขึ้น repo และ ❌ อย่าใส่ `.gitignore` ของ repo เพราะไฟล์นั้นต้อง commit คนอื่นจะรู้ทันทีว่ามี context ซ่อนอยู่

ถ้าวันหน้าอยาก share ให้ทีม: ลบบรรทัดที่ exclude ไว้ออกจาก `.git/info/exclude` แล้ว commit ตามปกติ

### repo ที่เคยใช้ layout เก่า

repo ที่มี `.claude/commands/`, `.codex/agents/` ค้างอยู่ — **ต้องลบทิ้ง** เพราะ project-level ชนะ global
`/ai-init` จะตรวจเจอและเสนอลบให้ (option A: Migrate เต็ม)

### ทีมใช้ assistant คนละตัว

ไม่มีปัญหา — ทุก assistant อ่าน `.ai/context/` ชุดเดียวกันในเครื่องเดียวกัน
แต่ context เป็น local-only — ถ้าใช้หลายเครื่อง หรืออยากให้เพื่อนร่วมทีมเห็น spec เดียวกัน ต้อง share กันเอง (ลบ exclude ออกแล้ว commit หรือ sync ไฟล์เอง)

ข้อเดียวที่ต้องตกลงกัน: **memory file ที่ root ให้มีตัวเดียวเป็นหลัก** (เช่น `CLAUDE.md`) แล้วอีก 2 ตัวเป็นไฟล์บรรทัดเดียวชี้มาหา — `/ai-init` ทำให้อัตโนมัติอยู่แล้ว

### repo ที่ทีม commit `CLAUDE.md` / `AGENTS.md` ไว้แล้ว

`/ai-init` ตรวจด้วย `git ls-files` — memory file ที่ track อยู่ถือเป็น**ของทีม**:

- ❌ ไม่แก้ ไม่เขียนเพิ่ม ไม่สร้างไฟล์ pointer ที่ root (แม้มี `--force`) — จึงไม่มีอะไรหลุดไปใน `git diff`
- ✅ memory ส่วนตัวไปอยู่ที่ `.ai/context/MEMORY.md` (exclude ไปกับ `.ai/`) — เขียนเฉพาะส่วนที่ไฟล์ของทีมยังไม่มี ไม่ copy ซ้ำ
- ทุก command อ่าน memory ของทีม → `MEMORY.md` — ขัดกันให้ของทีมชนะ
- จุดที่ไฟล์ของทีมไม่ตรงกับ code → อยู่ใน Final Report หัวข้อ "เสนอทีม" พร้อม diff — dev ตัดสินใจเองว่าจะเปิด PR ไหม

---

## แก้ชุดกลาง

แก้ไฟล์ใน `ai/` ได้เลย — มีที่เดียว

- แก้ command / agent → `ai/commands/*.md`, `ai/agents/*.md`
- แก้ rule กลาง → `ai/AI.md`
- เพิ่ม command ใหม่ → วาง `.md` ใน `ai/commands/` แล้วรัน `./install.sh`

Frontmatter ที่ command ใช้: `description`, `argument-hint`
Claude + ZCode อ่านครบ / Codex + Antigravity ใช้ `name` + `description` (generator แปลงให้) และแทน `$ARGUMENTS` ด้วยข้อความที่ user พิมพ์ต่อท้าย

## Agent ช่วยทำงานตามสถานการณ์

เลือก helper ตามกฎใน `ai/workflows/implementation.md` ซึ่งใช้ร่วมกันทั้ง direct coding, `/build` และ `/change`:

| Agent | ใช้เมื่อ | สิ่งที่ส่งกลับ |
|---|---|---|
| `codebase-explorer` | ไม่รู้ entry point, pattern หรือ consumer ใน repo ใหญ่ | flow สั้น ๆ กับ path/symbol ที่ควรอ่านและแก้ |
| `debugger` | สาเหตุไม่ชัด หรือแก้ครั้งแรกแล้วอาการยังอยู่ | สาเหตุที่ยืนยันได้/สมมติฐาน หลักฐาน และแนวแก้ที่เล็กที่สุด |
| `code-reviewer` | แก้ behavior, หลายไฟล์, public contract หรือจุดสำคัญ | bug ที่มี trigger จริง จุด wiring/caller ตกหล่น และ requirement ที่ยังไม่ครบ |

งานเล็กที่ชัดเจนให้ตัวหลักทำจบ helper ทุกตัวอ่านอย่างเดียวและห้ามเรียก agent ต่อ ตัวหลักเป็นผู้แก้โค้ด โดยปกติเรียกแต่ละบทบาทหนึ่งรอบและใช้ findings เดิมต่อ รอบเพิ่มต้องมีข้อมูลใหม่หรือมีจุดแก้ที่ต้องตรวจยืนยัน

เรียกเองได้ด้วย `/review`, `/debug`, `/explore` (Codex ใช้ `$review`, `$debug`, `$explore`) ทั้งสามคำสั่งเป็น read-only; `/debug` จะแก้โค้ดเมื่อคุณระบุให้แก้ด้วยเท่านั้น การเลือก helper เป็นคำสั่งให้ assistant ปฏิบัติตามและขึ้นกับ runtime ไม่ได้มี background orchestrator แยก ถ้าไม่มี native role จะใช้ prompt เดียวกันผ่าน helper ทั่วไปหรือทำ focused pass ในตัวหลัก และต้องบอกหากไม่ได้ review แบบแยก agent

ก่อนจบงานมี completeness check เทียบคำขอเดิมกับ code จริง รวม entry point, wiring, config, exports, caller และ contract ที่เกี่ยวข้อง reviewer ต้องอ้างไฟล์และสถานการณ์ที่ทำให้เกิดปัญหา การไม่มี automated test เพียงอย่างเดียวไม่ถือเป็น bug

ค่าเริ่มต้นการตรวจคือ **ลอง flow จริง** และบอก input/steps, environment, expected/observed result ถ้าลองไม่ได้จะระบุว่า `not run` พร้อมวิธีให้คุณลองต่อ ไม่หยุดงานเพียงเพราะไม่มี test runner เลือก automated tests ได้ด้วย `/build ... --validation tests` หรือ `/change ... --validation tests`; required checks ของทีมยังใช้ตามเดิม

สถานะยังแยกหลักฐานตามเดิม: ✅ มี automated checks ที่เกี่ยวข้องผ่านใน code state ปัจจุบัน; ⚠️ คือ implementation ที่ไม่มีหลักฐาน automated tests โดยบันทึก `flow passed` หรือ `flow not run` แยก; มี failure ที่ยังไม่แก้เป็น 🚧

feedback ระหว่างใช้งานจะปรับงานปัจจุบันทันที หากเป็นบทเรียนที่ควรใช้ต่อ จะเสนอเป็นกฎเฉพาะขอบเขตผ่าน `/learn` ก่อนบันทึก การชมว่าครั้งหนึ่งใช้ได้หรือการแก้คำตอบหนึ่งครั้งไม่ทำให้เกิดกฎถาวรอัตโนมัติ

## เครื่องมือ Python

ใช้ Python standard library เท่านั้น: runtime tools ต้องการ Python 3.9+ ส่วน tests ใช้ Python 3.11+ เพราะอ่าน TOML ด้วย `tomllib` ไม่ต้องติดตั้ง package เพิ่ม

```bash
python3 ai/tools/workflow.py resolve --root /path/to/repo/subdirectory
python3 ai/tools/workflow.py context --root /path/to/repo --path src/customer/handler.py
python3 ai/tools/workflow.py validate --root /path/to/repo
python3 ai/tools/workflow.py reindex --root /path/to/repo --dry-run
python3 ai/tools/workflow.py reindex --root /path/to/repo
```

เมื่อติดตั้งแล้วใช้ path `~/.ai/tools/` แทน `ai/tools/` ได้ ผลลัพธ์เป็น JSON และ exit code ไม่เป็นศูนย์เมื่อพบ error

`/reindex` ใช้เครื่องมือเดียวกันทุก assistant: ตรวจ ID ซ้ำ/สถานะ/แถว cross-repo ก่อนสร้าง index, คำนวณ overall status, สร้างลิงก์จากตำแหน่งจริง และ rename terminal specs เฉพาะ scope ที่รัน โดยไม่แก้เนื้อหา spec หรือ stage git การรันซ้ำให้เนื้อหาเหมือนเดิม จึงไม่ใส่ timestamp ปัจจุบันและไม่ใช้ cache จาก index เก่า `--force` ยังใช้ได้เพื่อรองรับคำสั่งเดิม

`validate` ตรวจโครงสร้าง metadata กับลิงก์ไฟล์ภายใน ไม่ได้พิสูจน์ business behavior หรือยืนยันว่ารันทดสอบจริง สถานะ ✅ ยังต้องมีหลักฐานจากคำสั่งทดสอบปัจจุบัน ส่วน `/sync` รายงานโค้ดที่ไม่มี spec เป็นข้อมูล coverage; จะเป็น critical เมื่อพบหลักฐานว่าขัดกับ rule/contract

ตัวอย่าง `.ai/context/context-map.json` (เติมจากโครงสร้างจริงตอน `/ai-init`):

```json
{
  "version": 1,
  "modules": [
    {"path": "src/customer", "context": [".ai/context/customer-rules.md"]}
  ]
}
```

selector คืน candidate paths ให้ AI ตรวจต่อ ใช้เฉพาะ module ที่เกี่ยวข้อง และไม่แทนที่กฎของทีม การทำงานต่อให้อ่าน `HANDOFF.md` แล้วเทียบ HEAD/diff; บทเรียนใน `LESSONS.md` ต้องผ่านการยืนยัน มี path/symbol อ้างอิง และทบทวนเมื่อ code ที่รองรับเปลี่ยน

## ตรวจสุขภาพและย้อนกลับการติดตั้ง

```bash
./install.sh --doctor
./install.sh --rollback
```

ก่อนติดตั้งจะ validate source และเก็บ snapshot ของ source store กับตำแหน่งไฟล์ที่ installer จัดการ เมื่อติดตั้งล้มเหลวจะคืนค่าเดิม การติดตั้งสำเร็จบันทึก manifest แยกตาม provider เพื่อให้ doctor ตรวจ broken symlink, ไฟล์ถูกแก้/หาย และ source ที่เปลี่ยนหลัง generate ได้ การติดตั้ง provider เดียวไม่ล้างสถานะ stale ของตัวอื่น

snapshot อยู่ที่ `~/.ai-agent-history/` (กรณีเปลี่ยน `AI_AGENT_HOME` จะอยู่ข้าง store ตามชื่อเดียวกัน) และเก็บไว้หลัง uninstall `--rollback` ย้อนการติดตั้งล่าสุดหนึ่งครั้งและหยุดถ้าไฟล์ใน snapshot ถูกแก้ภายหลัง เพื่อรักษางานใหม่ของผู้ใช้ ไฟล์ backup แบบ `.bak-*` เดิมยังคงอยู่ การคืนค่าไม่ครอบคลุมไฟดับหรือ process ที่ถูก kill แบบไม่เปิดโอกาสให้ cleanup; กรณีนั้น snapshot ยังใช้ตรวจสอบกู้คืนได้

doctor ตรวจสถานะไฟล์ในเครื่อง ไม่รับรองว่า provider โหลด schema หรือรองรับ model นั้นจริง หากเปลี่ยน `models.json` ควรทดลองเรียก analyzer ใน provider นั้นด้วย

## Tests และการประเมิน AI

```bash
python3.11 -m unittest discover -s tests -v
bash -n install.sh
python3 ai/tools/installation.py validate-source --root .
python3 ai/tools/evaluate.py --responses /tmp/responses.json --output /tmp/report.json
```

CI รันบน Linux/macOS และครอบคลุม generation, index, context selection, doctor, failure recovery, rollback และ scorer ส่วน behavioral evaluation มี 10 โจทย์ใน `ai/evals/cases.json` พร้อมวิธีเก็บ trace และ metrics ใน [evals/README.md](evals/README.md) ต้องรันกับ assistant จริงแล้วตรวจ transcript เพื่อเปรียบเทียบความสามารถ; unit tests ของ scorer ไม่ใช่ผลประเมิน model

---

## skill ชุดเก่าที่ชื่อซ้ำ

ถ้าเครื่องเคยติดตั้ง AI agent template อื่นที่ใช้ชื่อ skill ซ้ำกัน (`spec`, `build`, …)
`install.sh` จะย้ายของเก่าไป backup ให้ ไม่ลบทิ้ง:
- Codex → `~/.codex/skills-disabled-old-template/<name>.bak-<timestamp>/`
- Antigravity → `~/.gemini/config/skills-disabled-old/<name>.bak-<timestamp>/`
- Claude / ZCode → ไฟล์เดิมถูก rename เป็น `<name>.md.bak-<timestamp>` ข้างกัน

กู้คืน:
```bash
mv ~/.codex/skills-disabled-old-template/spec.bak-* ~/.codex/skills/spec
```
