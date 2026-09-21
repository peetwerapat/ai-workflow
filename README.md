# ai-agent — ชุด AI กลางสำหรับทุก project

Workflow `/spec → /build → /change` ชุดเดียว เขียนครั้งเดียว ใช้ได้กับ **Claude Code**, **Codex CLI** และ **Antigravity CLI (`agy`)** ในทุก repo

```
ai/                      ← source of truth ชุดเดียว
├── AI.md                  rule กลาง (workflow, status vocabulary, critical rules)
├── commands/              /ai-init /spec /build /change /status /reindex /sync
├── agents/                spec-analyzer, impact-analyzer
└── templates/             โครงไฟล์สำหรับ /ai-init ไป scaffold ใน repo ใหม่
```

## ติดตั้ง

```bash
git clone <repo> && cd ai-workflow
./install.sh              # เลือกจากเมนูว่าจะติดตั้งตัวไหน
./install.sh all          # ทุกตัว ไม่ถามเมนู
./install.sh claude       # เฉพาะตัวใดตัวหนึ่ง (claude | codex | antigravity | shell)
./install.sh --status     # ดูว่าติดตั้งอะไรไว้
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
    ◉ Shell wrapper      auto-sync ตอนเปิด codex/agy

  ↑/↓ เลื่อน · space ติ๊ก · a ทั้งหมด · n ล้าง · enter ยืนยัน · q ออก
```

| ปุ่ม | ผล |
|---|---|
| `↑` `↓` หรือ `k` `j` | เลื่อน (วนรอบ) |
| `space` | ติ๊ก/เอาติ๊กออกบรรทัดที่อยู่ |
| `1`–`4` | กระโดดไปบรรทัดนั้นแล้วติ๊กเลย |
| `a` / `n` | เลือกหมด / ล้างหมด |
| `enter` | ยืนยัน |
| `q` หรือ `Esc` | ออกโดยไม่ติดตั้ง |

ที่เลือกไว้ถูกจำใน `.install-prefs` (อยู่ที่ `~/.ai-agent/` หลังติดตั้ง — gitignore แล้ว) รอบหน้าไม่ต้องติ๊กใหม่ ลบไฟล์นี้เพื่อกลับไป auto-detect
รันแบบ non-interactive (CI / script) จะข้ามเมนูแล้วใช้ค่าที่จำไว้ หรือ `AI_AGENT_YES=1` เพื่อบังคับข้าม

`install.sh` จะเพิ่ม `codex()` + `agy()` wrapper ใน shell rc ให้ด้วย — sync skill ให้ก่อนเปิดทุกครั้ง
และตั้ง `git config --global merge.ours.driver true` เพื่อให้ `.gitattributes` ของ repo งานทำงานได้

ไม่อยากให้แตะ shell rc → `AI_AGENT_NO_SHELL=1 ./install.sh` (แต่ต้องรัน `./install.sh codex` / `antigravity` เองทุกครั้งที่แก้ command)

ไฟล์เดิมที่ทับจะถูกสำรองเป็น `*.bak-YYYYMMDD-HHMMSS` ก่อนเสมอ
(ยกเว้น symlink ของ script นี้เอง และ symlink ที่เสียค้างเพราะ clone เดิมถูกลบ — เขียนทับเลยไม่สำรอง)

### ติดตั้งไปที่ไหนบ้าง

| | Claude Code | Codex CLI | Antigravity CLI |
|---|---|---|---|
| Memory | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | — (ไม่มี global rules — skill อ่าน `~/.ai/AI.md` เอง) |
| Commands | `~/.claude/commands/*.md` (symlink) | `~/.codex/skills/<n>/SKILL.md` (generate) | `~/.gemini/config/skills/<n>/SKILL.md` (generate) |
| Agents | `~/.claude/agents/*.md` | — (อ่าน `~/.ai/agents/` เอง) | — (อ่าน `~/.ai/agents/` เอง) |
| เรียกด้วย | `/spec` | **`$spec`** | เรียกชื่อ skill (`spec`) |

เฉพาะ **Claude** ที่ commands เป็น symlink (ชี้ไป `~/.ai-agent/ai/commands/`) — Codex/Antigravity ต้อง generate ใหม่
ทั้งสองแบบอัปเดตด้วย `~/.ai-agent/install.sh --update` เหมือนกัน

**Codex** (0.155+) เลิกใช้ `~/.codex/prompts/` แล้ว — custom command ต้องเป็น **skill** (`~/.codex/skills/<name>/SKILL.md`)
และเรียกด้วย **`$`** ไม่ใช่ `/` — frontmatter รับแค่ `name`, `description`, `license`, `allowed-tools`, `metadata`

**Antigravity** (`agy`) ใช้ skill เหมือนกัน แต่ customization root ระดับ global คือ `~/.gemini/config/`
(workflows `*.md` เป็นของเก่าที่ Google กำลัง migrate ไป skill — ใช้ skill ตรงๆ เลย)

Antigravity ไม่มี global rules file — rules เป็น directory-based (`AGENTS.md`/`GEMINI.md` ไล่ขึ้นจาก cwd)
เลย generate SKILL.md ให้มีบรรทัดสั่งอ่าน `~/.ai/AI.md` เองตอนเริ่ม

ทั้งสองตัวมี shell wrapper (`codex()` / `agy()`) ที่ `install.sh` ใส่ให้ — sync ก่อนเปิดทุกครั้งอัตโนมัติ ไม่ต้องจำ

`~/.ai` เป็น symlink ไปที่ `~/.ai-agent/ai/` ทำให้ทุก assistant อ้าง path เดียวกันได้ (`~/.ai/agents/spec-analyzer.md`)

## ใช้งาน

```
repo ใหม่:     /ai-init                       scaffold .ai/ + project memory จากการอ่าน code จริง
feature ใหม่:  /spec <requirement> → /build   → /reindex
แก้ของเดิม:    /change <task-id> "<desc>"     → /reindex
ดูภาพรวม:      /status | /status mine | /status <task-id>
ตรวจ drift:    /sync [--fix]
```

> **Codex ใช้ `$` แทน `/`** — `$spec`, `$build`, `$ai-init`
> **Antigravity** เรียกชื่อ skill ตรงๆ (`/skills` ดูรายการ)

## Context 2 ชั้น

| ชั้น | ที่อยู่ | เนื้อหา |
|---|---|---|
| **Global** | `~/.ai/AI.md` | workflow, status vocabulary, critical rules ที่ใช้ได้ทุก project |
| **Project** | `.ai/context/` + memory file ที่ root ของ repo | domain, stack, architecture, specs |

```
<repo>/
├── CLAUDE.md | AGENTS.md | GEMINI.md
└── .ai/context/
    ├── ARCHITECTURE.md
    ├── features.md          ← derived view, regen ด้วย /reindex เท่านั้น
    ├── untracked.md
    └── specs/
        ├── TASK-YYYYMMDD-HHMM.md
        └── CLOSED-TASK-YYYYMMDD-HHMM.md
```

**`.ai/` ใช้ร่วมกันทุก assistant** — ไม่แตกเป็น `.claude/context/`, `.codex/context/` แยกกัน spec จึงไม่มีวัน drift ระหว่าง tool
repo ที่ยังใช้ layout เก่าอยู่ → `/ai-init` จะเสนอ migrate ให้

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

จากนั้นเปิด repo งานแล้ว `/ai-init` (ถ้า repo นั้นยังไม่มี `.ai/`) — ถ้ามีคนทำไว้แล้วและ commit ขึ้น git แล้ว ก็ใช้ได้เลยไม่ต้องทำอะไร

```
ครั้งเดียวต่อคน        git clone <ai-agent> && ./install.sh
ครั้งเดียวต่อ repo งาน   คนใดคนหนึ่ง /ai-init → commit → push
หลังจากนั้น            ทุกคน git pull แล้ว /spec /build /change ได้เลย
```

**Antigravity**: `install.sh` วาง skill ให้ แต่ไม่ได้ลงตัว CLI — ใครจะใช้ต้องติดตั้ง `agy` เอง (ไม่พบใน PATH จะมี warning)

**อัปเดตชุดกลางทีหลัง**
```bash
cd ~/dev/ai-agent && git pull && ./install.sh
```
Claude เห็นทันทีหลัง `git pull` (symlink) ส่วน Codex/Antigravity มี wrapper sync ให้ตอนเปิด

### สิ่งที่แชร์ vs ไม่แชร์

| | อยู่ที่ไหน | แชร์ยังไง |
|---|---|---|
| Rule กลาง, commands, agents | repo นี้ | `git pull` + `./install.sh` |
| Spec / architecture ของแต่ละงาน | `.ai/` ใน repo งานนั้น | commit ไปกับ repo งานตามปกติ |

`.ai/` ต้อง **commit เข้า repo งาน** ไม่ใช่ใส่ `.gitignore` — spec เป็นของทีม ไม่ใช่ของเครื่องใครเครื่องมัน

### `features.md` กับ merge conflict

`features.md` เป็นไฟล์ที่ `/reindex` generate ใหม่ทั้งไฟล์ → 2 คนรันคนละ branch แล้ว merge เมื่อไหร่ก็ชน

`/ai-init` จะใส่ `.gitattributes` ให้อยู่แล้ว:
```
.ai/context/features.md merge=ours
```
ส่วน merge driver `install.sh` ตั้ง `git config --global merge.ours.driver true` ให้อัตโนมัติ

ถ้ายังชนอยู่ดี — **ห้าม resolve มือ** เอาฝั่งไหนก็ได้ผ่านไปก่อน แล้วรัน `/reindex` ใหม่ มัน regen จาก `specs/` ให้ถูกเอง
(`specs/` เป็นไฟล์ละ task แทบไม่ชนกัน)

### repo ที่เคยใช้ layout เก่า

repo ที่มี `.claude/commands/`, `.codex/agents/` ค้างอยู่ — **ต้องลบทิ้ง** เพราะ project-level ชนะ global
`/ai-init` จะตรวจเจอและเสนอลบให้ (option A: Migrate เต็ม)

### ทีมใช้ assistant คนละตัว

ไม่มีปัญหา — ทุกคนอ่าน `.ai/context/` ชุดเดียวกัน
คนที่ใช้ Claude รัน `/spec` แล้ว commit → คนที่ใช้ Codex `/build` ต่อได้เลย เห็น spec เดียวกัน

ข้อเดียวที่ต้องตกลงกัน: **memory file ที่ root ให้มีตัวเดียวเป็นหลัก** (เช่น `CLAUDE.md`) แล้วอีก 2 ตัวเป็นไฟล์บรรทัดเดียวชี้มาหา — `/ai-init` ทำให้อัตโนมัติอยู่แล้ว

---

## แก้ชุดกลาง

แก้ไฟล์ใน `ai/` ได้เลย — มีที่เดียว

- แก้ command / agent → `ai/commands/*.md`, `ai/agents/*.md`
- แก้ rule กลาง → `ai/AI.md`
- เพิ่ม command ใหม่ → วาง `.md` ใน `ai/commands/` แล้วรัน `./install.sh`

Frontmatter ที่ command ใช้: `description`, `argument-hint`
Claude อ่านครบ / Codex + Antigravity ใช้ `name` + `description` (generator แปลงให้) และแทน `$ARGUMENTS` ด้วยข้อความที่ user พิมพ์ต่อท้าย

---

## skill ชุดเก่าที่ชื่อซ้ำ

ถ้าเครื่องเคยติดตั้ง AI agent template อื่นที่ใช้ชื่อ skill ซ้ำกัน (`spec`, `build`, …)
`install.sh` จะย้ายของเก่าไป backup ให้ ไม่ลบทิ้ง:
- Codex → `~/.codex/skills-disabled-old-template/<name>.bak-<timestamp>/`
- Antigravity → `~/.gemini/config/skills-disabled-old/<name>.bak-<timestamp>/`

กู้คืน:
```bash
mv ~/.codex/skills-disabled-old-template/spec.bak-* ~/.codex/skills/spec
```
