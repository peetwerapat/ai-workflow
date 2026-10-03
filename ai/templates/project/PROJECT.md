<!-- TEMPLATE: <project>/.ai/context/PROJECT.md — marker ของ multi-repo project (agent ไล่ขึ้นจาก repo มาเจอไฟล์นี้) -->
<!-- เติมจากการอ่าน repo จริงด้วย /ai-init ที่ root ของ project — ไม่พบให้เขียนว่า "ไม่พบ" ห้ามเดา -->

# {Project Name}

{1-2 บรรทัด: ระบบนี้คืออะไร ใช้กับใคร}

> **Shared context** ของทุก repo ใน project นี้ — source of truth ของเรื่องที่ข้าม repo
> เรื่องเฉพาะ repo อยู่ที่ `<repo>/.ai/context/` — ❌ ห้าม copy เนื้อหาในโฟลเดอร์นี้ไปไว้ใน repo

---

## Repositories

| Repo | หน้าที่ | Stack | Context |
|---|---|---|---|
| `{dir}` | {} | {} | `{dir}/.ai/context/` |

## Domain

{entity / คำศัพท์ที่ใช้ร่วมกันหลาย repo — อะไรเป็นเจ้าของ data ไหน}

| Term | ความหมาย | Owner repo |
|---|---|---|
| {} | {} | `{dir}` |

---

## Context Map (โหลดเท่าที่จำเป็น)

| ไฟล์ | อ่านเมื่อ |
|---|---|
| `PROJECT.md` (ไฟล์นี้) | ทุก task ใน project นี้ |
| `ARCHITECTURE.md` | เสนอ design / task ที่แตะ boundary ระหว่าง repo |
| `conventions.md` | เขียน code ใน repo ใดก็ได้ |
| `integrations.md` | task ที่แตะ API / event / data ที่ repo อื่นใช้ |
| `specs/` + `features.md` | cross-repo task (แตะ ≥ 2 repo) — spec ของ repo เดียวอยู่ใน repo นั้น |
| `<repo>/.ai/context/*` | เฉพาะ repo ที่ task แตะจริง — ไม่ต้องโหลด repo อื่น |
