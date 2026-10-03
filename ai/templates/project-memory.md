<!-- TEMPLATE: project memory file — วางที่ root ของ repo ในชื่อ CLAUDE.md / AGENTS.md / GEMINI.md -->
<!-- ทุกหัวข้อต้องเติมจากการอ่าน code จริง — หัวข้อไหนไม่พบให้เขียนว่า "ไม่พบ" ห้ามเดา -->

# {Project Name}

{1-2 บรรทัด: ระบบนี้คืออะไร ใช้กับใคร}
{ถ้า multi-tenant: หน่วย isolation คืออะไร key ชื่ออะไร}

> Global working agreement อยู่ที่ `~/.ai/AI.md` — ไฟล์นี้เก็บเฉพาะเรื่องที่เป็นของ project นี้
> **Multi-repo project** (ลบบรรทัดนี้ถ้าเป็น repo เดี่ยว): repo นี้เป็นส่วนหนึ่งของ `{project}` — shared context อยู่ที่ [`{../}.ai/context/PROJECT.md`]({../}.ai/context/PROJECT.md) อ่านก่อน และห้าม copy เนื้อหาจากที่นั่นมาไว้ในไฟล์นี้

---

## Domain Model

```
{ASCII diagram ของ entity หลักและความสัมพันธ์}
```

| Entity | Role | Tenant key |
|---|---|---|
| {Entity} | {หน้าที่} | {key หรือ —} |

## Personas

| Persona | Scope |
|---|---|
| {persona} | {เข้าถึงอะไรได้ / auth แบบไหน} |

---

## Tech Stack

- **Language / Runtime**: {}
- **Framework**: {}
- **Database**: {} ({ORM/driver})
- **Cache / Queue**: {}
- **Auth**: {}
- **Package manager**: {}
- **Test**: {runner} — `{command}`
- **Lint / Format / Typecheck**: `{commands}`
- **Migration**: `{command}`
- **Docs**: {swagger/openapi path ถ้ามี}

รายละเอียด architecture decisions → [.ai/context/ARCHITECTURE.md](.ai/context/ARCHITECTURE.md)

---

## Critical Rules

### 1. {Tenant isolation / rule ที่ non-negotiable ที่สุดของ project นี้}

{กติกา + ตัวอย่าง code pattern จริงจาก repo}

### 2. Layering

```
{Layer → Layer → Layer ที่ใช้จริง}
```

- ❌ ห้าม {anti-pattern ที่เจอจริงหรือที่ project ห้าม}
- ✅ {pattern ที่ต้องใช้} — ตัวอย่าง: `{path}`

### 3. Error Handling

{exception/error class ที่ใช้ + mapping ไป status code + ตัวอย่าง}

### 4. API / Response Shape

{envelope ที่ใช้ + ตัวอย่าง + convention ของ route path}

### 5. Database Migration

{command ที่ต้องใช้ generate + naming + ข้อห้าม}

### 6. Security

{secret management, password hashing, token storage, PII handling}

---

## Conventions

### Naming

| Context | Convention | Example |
|---|---|---|
| variables / methods | {} | {} |
| classes / interfaces | {} | {} |
| files | {} | {} |
| DB tables / columns | {} | {} |
| env vars | {} | {} |

> ตั้งชื่อเต็มคำ ห้ามย่อ — `customerRepository` ไม่ใช่ `custRepo`
> ยกเว้นตัวย่อมาตรฐาน (`id`, `url`, `db`, `dto`, `i18n`) และ loop index สั้นใน scope แคบ

### File / Folder Layout (per module)

```
{โครงสร้างจริงของ 1 module}
```

### Testing

{test ที่มีอยู่จริง + coverage ปัจจุบัน + pattern ที่ใช้ mock}

---

## Directory Structure (จริง)

```
{tree ของ source dir จริง — ไม่ใช่ที่คิดว่าน่าจะเป็น}
```

---

## Module Dependency

```
{ลำดับ dependency ระหว่าง module}
```

ก่อนแก้ module ใด → อ่าน rule file ของ module นั้นก่อน (ถ้ามี)

---

## Known Gaps

- {สิ่งที่ยังไม่ได้ทำ / หนี้ทางเทคนิคที่ AI ควรรู้}
