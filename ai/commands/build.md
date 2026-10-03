---
description: Implement feature ตาม spec พร้อมเขียน test — รองรับ incremental mode และ resume
argument-hint: [task-id] [--repo <name>] [--incremental | --no-test | --resume]
---

# /build — Implement Feature

Implement ตาม spec file และเขียน test คู่กันไป
Default: code + test + รัน test รวดเดียวจบ

## Context Files

อ่านก่อนเริ่มเสมอ:
- shared project context (ถ้ามี — ดู `~/.ai/AI.md` › Context Resolution): `PROJECT.md` + ไฟล์ใน context map ที่เกี่ยวกับ task
- project memory file ที่ root
- `.ai/context/ARCHITECTURE.md`
- `.ai/context/specs/{task-id}.md` — **source of truth ของ build นี้**
- module rule file ของ module ที่จะแก้ (ถ้ามี)

`features.md` อ่านเป็น overview เท่านั้น — รายละเอียดอยู่ใน spec file

## Input

**$ARGUMENTS**

- **task-id** (optional): `TASK-YYYYMMDD-HHMM` หรือ legacy `{MODULE}-{NNN}`
  - ไม่ระบุ → ใช้ feature ที่ status 📋 หรือ 🚧 ล่าสุด
- **Flags**:
  - `--incremental` — หยุดให้ dev review ทุก layer
  - `--no-test` — skip test (prototype เท่านั้น)
  - `--resume` — ทำต่อจาก state เดิม
  - `--repo <name>` — cross-repo spec: build เฉพาะ repo นี้ (default: ทุก repo ที่ยังไม่ ✅ ตาม build order)

---

## Step 1: Pre-flight Check

**1.1 หา spec file**

- มี task-id → อ่าน `.ai/context/specs/{task-id}.md` (หรือ `CLOSED-TASK-{id}.md`)
  ไม่เจอ + อยู่ใน multi-repo project → หาต่อที่ `<project>/.ai/context/specs/` (ดู AI.md › Cross-repo Task)
- ไม่มี task-id → scan `specs/TASK-*.md` หาไฟล์ที่ `**Status**:` = 📋 หรือ 🚧 (ล่าสุดก่อน)
  (รวม cross-repo spec ที่ `**Repos**:` มี repo ปัจจุบัน)
- **หาไม่เจอ**:
  ```
  ❌ ไม่พบ spec file

  Feature นี้ยังไม่ผ่าน /spec — กรุณารัน:
    /spec <requirement>
  ```
  → **หยุดทันที**

**1.2 Check status**

| Status | Action |
|---|---|
| 📋 Planned | ✅ proceed |
| 🚧 In Progress (ไม่มี `--resume`) | ถาม: เริ่มใหม่ หรือ resume? |
| ✅ Done (ไม่มี `--resume`) | warn + ถาม: จะ re-build จริงไหม (ต้อง reopen ก่อน) |
| ⚠️ Done (untested) | proceed — focus ที่การเขียน test |
| 🔴 Blocked | ถาม blocker ก่อน |
| ❌ / 📦 | หยุด — feature ถูกปิดแล้ว ต้อง reopen ก่อน |

**1.3 Load module context** — จาก spec หา module → อ่าน rule file ของ module นั้นถ้ามี

**1.4 Scan existing code** — สำรวจพื้นที่ที่ spec จะไปแตะ:
- โครงสร้างไฟล์ที่มีอยู่
- pattern ที่ใช้ (follow ให้เหมือน)
- conflict กับ code ที่จะเขียน

**1.4b Cross-repo spec** (`**Scope**: cross-repo`) → ทำตาม [Cross-repo Build](#cross-repo-build) แทน Step 2-6 ต่อ repo

**1.5 Detect project commands** — อ่าน manifest/script ของ project หา test / lint / typecheck / migration command จริง
**ห้าม hardcode `npm test`** ถ้า project ใช้อย่างอื่น

---

## Step 2: Announce Plan

```
## Build Plan: {Task ID} — {Feature Name}

**Mode**: default | incremental | resume
**Skip tests**: yes | no

### Files to create
- `{path}` — {purpose}

### Files to modify
- `{path}` — {what changes}

### Test coverage plan
- Unit: {count} tests
- Integration: {count} (ถ้า critical flow)
- Focus: happy path, rule violations, tenant isolation

### Dependencies
- Existing: {ที่จะ import มาใช้}
- New: {package} — ⚠️ ต้อง confirm ก่อนติดตั้ง

### Approach
{1-2 ประโยคสรุป strategy}
```

**`--incremental`** → รอ confirm ก่อน proceed
**ไม่ใช่** → proceed ทันที

---

## Step 3: Update Status to In Progress

แก้ spec file:
- `**Status**:` → `🚧 In Progress`
- `**Last Updated**:` → `{now}` by `{git user}`

(`--resume` → status เป็น 🚧 อยู่แล้ว แค่ update Last Updated)

> ไม่แตะ `features.md` — `/reindex` จัดการเอง

---

## Step 4: Implement

### Default Mode

Implement ตาม dependency order (ปรับตามสถาปัตยกรรมจริงของ project):

1. **Data model / Entity / Schema**
2. **Migration** (ถ้ามี schema change)
   - ❌ **ห้ามสร้างไฟล์ migration เอง / ตั้ง timestamp เอง** — generate ผ่าน CLI ของ project เสมอ
   - แล้วค่อยเขียนเนื้อ `up()` / `down()` ลงในไฟล์ที่ CLI gen ออกมา
   - หลาย migration ใน task เดียว → generate ทีละไฟล์ตามลำดับที่ต้อง run จริง
3. **Data access layer** (repository / DAO / query module)
4. **Business logic layer** (service / usecase / handler)
5. **Input/Output contract** (DTO / schema / validator)
6. **Transport layer** (controller / route / resolver / CLI)
7. **Wiring** (module registration / DI container / route table)

### Incremental Mode (`--incremental`)

หลังแต่ละ layer → **หยุด**:
```
✅ Completed: {layer}
Files:
- `{path}` (+45 lines)

Preview:
{key signatures}

review ก่อนไหม? (ตอบอะไรก็ได้เพื่อ proceed)
```

### Resume Mode (`--resume`)

1. อ่าน code ที่มีอยู่ในพื้นที่ของ feature
2. Diff กับ spec → หา gap
3. Implement เฉพาะ gap (ไม่เขียนทับของเดิม)
4. เจอ code ที่ขัดกับ spec → flag ให้ dev confirm ก่อนแก้

### Implementation Rules

- ✅ Follow convention ใน `ARCHITECTURE.md` + module rule
- ✅ ใช้ pattern เดียวกับ code ที่มีอยู่
- ✅ แยก layer ตามที่ project กำหนด — ห้าม bypass (เช่น query DB ตรงจาก transport layer)
- ✅ Error handling ตามที่ project ใช้อยู่ — ห้าม throw error ดิบถ้า project มี custom exception
- ✅ Multi-tenant → filter tenant key ทุก query จาก authenticated context
- ❌ ห้าม hardcode secret — อ่านจาก config/env
- ❌ ห้าม `setTimeout` / `setInterval` สำหรับ background work — ใช้ queue/scheduler ของ project

---

## Step 5: Test (ถ้าไม่มี `--no-test`)

### 5.1 Generate Tests

ครอบคลุม 4 ประเภทต่อทุก business method:
1. **Happy path** — input ถูก, output ตรง
2. **Business rule violation** — throw/return error ที่ควร
3. **Edge cases** — null, empty, boundary
4. **Tenant isolation** (ถ้า multi-tenant) — query ไม่ leak ข้าม tenant

### 5.2 Run Tests

ใช้ command จริงของ project (จาก Step 1.5) — scope ให้แคบที่สุดที่ครอบคลุม เช่น filter ตาม module/path

### 5.3 Handle Failures

- **Attempt 1**: วิเคราะห์ error → แก้ code หรือ test → รันใหม่
- **Attempt 2**: วิเคราะห์ลึก (อาจเป็น assumption ผิดใน spec) → แก้ → รันใหม่
- **Attempt 3**: **หยุด**
  ```
  ⚠️ Tests ยัง fail หลังพยายาม 3 รอบ

  Error ล่าสุด: {error}
  การวิเคราะห์: {what I think is wrong}

  Status ยังเป็น 🚧 (ไม่ mark ว่า done)
  ```

### 5.4 Lint / Typecheck

หลัง test ผ่าน → รัน lint + typecheck ของ project ให้ผ่านด้วย ก่อนถือว่า build เสร็จ

---

## Step 6: Update Spec File

### 6.1 Status
- test ผ่าน → `✅ Done`
- `--no-test` → `⚠️ Done (untested)`
- test ไม่ผ่าน → คง `🚧 In Progress`

### 6.2 Implementation Status

แทน `_(TBD — pending /build)_`:
```markdown
## Implementation Status

**Files**:
- `{path}`
- ... (ทุกไฟล์ที่ create / modify ใน build รอบนี้)

**Tests**: {N passing} / {N failing}
**Coverage**: {ถ้าวัดได้}
```

### 6.3 Changelog
```markdown
- **{YYYY-MM-DD}** BUILT — Implemented {brief summary} + {N} tests
```
(`--no-test` → ระบุชัดว่า "no tests written — --no-test flag used")

### 6.4 Last Updated
```markdown
**Last Updated**: {now} by {git user.name} \<{git user.email}\>
```

### 6.5 Known Gotchas (ถ้ามี)
เจอ pitfall ที่ maintainer ต่อไปควรรู้ → เพิ่มใน `## Known Gotchas`

---

## Cross-repo Build

spec เดียว หลาย repo — ทำ Step 1.3-6 **ทีละ repo ตาม `**Repos**:` (build order)**

**Pre-flight**
- repo ที่จะ build = ทุก repo ใน Implementation Status ที่ยังไม่ ✅ (หรือเฉพาะ `--repo <name>`)
- เช็คว่าเขียนไฟล์ได้ทุก repo ที่จะ build — ไม่ได้ (เช่น session เปิดใน repo อื่น / sandbox) → หยุด แนะนำ:
  `cd <project>` แล้วเปิด session ใหม่ หรือ `/build {task-id} --repo <name>` จาก session ใน repo นั้น
- repo ใดยังไม่มี `.ai/` → warn (ไม่มี ARCHITECTURE ให้ follow) แนะนำ `/ai-init` ก่อน

**Plan** (Step 2) แสดงรวมทุก repo ครั้งเดียว: build order, files ต่อ repo, test command ต่อ repo, contract ที่ repo ถัดไปจะพึ่ง

**ต่อ repo** (ตามลำดับ):
1. อ่าน memory file + `ARCHITECTURE.md` + module rule **ของ repo นั้น** — ไม่โหลด context ของ repo ที่ยังไม่ถึงคิว
2. Implement เฉพาะ section `### {repo}` ใน Proposed Design — path อ้างจาก root ของ project
3. Test ด้วย command ของ repo นั้น (Step 1.5 ต่อ repo) — repo ต่างกันใช้ runner ต่างกันได้
4. Update แถวของ repo นั้นใน Implementation Status (Status / Files / Tests) + Changelog `BUILT [{repo}]`
5. คำนวณ **Overall Status** ใหม่ (AI.md › Cross-repo Task) แล้ว update `**Status**:` + Last Updated
6. ส่ง contract ที่ implement จริง (path, shape) ต่อให้ repo ถัดไป

**ประหยัด context**: runtime รองรับ subagent → delegate step 1-4 ของแต่ละ repo ให้ subagent ทีละตัว (ตามลำดับ ห้ามขนาน — repo หลังพึ่ง contract ของ repo ก่อน)
ส่ง input: spec path + ชื่อ repo + contract summary จาก repo ก่อนหน้า / รับกลับ: files, tests, contract จริง, gotchas

**Failure**: test ของ repo ใด fail ครบ 3 รอบ → หยุดที่ repo นั้น (แถวเป็น 🚧) **ไม่ build repo ถัดไป**
ที่ depend กับมัน — repo ที่ไม่ depend (ไม่มีใน Contract Changes ร่วมกัน) ถาม dev ว่าจะทำต่อไหม

**Contract drift**: implement จริงต่างจาก Contract Changes ใน spec → หยุด ให้ dev เลือก: แก้ code ให้ตรง spec หรือ `/change`

**Final Report** (Step 7) เพิ่ม:
- ตาราง Implementation Status ต่อ repo + Overall Status
- diff ที่เสนอสำหรับ `<project>/.ai/context/integrations.md` (ถ้า contract เปลี่ยน — รอ dev confirm ก่อนเขียน)
- suggested commit **แยกต่อ repo**:
  ```
  cd {repo} && git commit -m "feat({scope}): {description}

  Task: {task-id}"
  ```

---

## Step 7: Final Report

```
## ✅ Build Complete: {Task ID}

### Summary
{1-2 ประโยค}

### Files Changed
Created:
- `{path}` (+X lines)
Modified:
- `{path}` (+X / -Y lines)

### Tests
- Unit: X added ({all passing | Y passing, Z failing})
- Lint / Typecheck: ✅ | ⚠️
{หรือ "⚠️ Tests skipped — ใช้ --no-test"}

### ⚠️ Assumptions
{ทุก assumption ที่ใช้เมื่อ spec ไม่ชัด}
1. ...

### 🔍 จุดที่ควร Review
{จุดที่ต้องการ human judgment}
1. ...

### ⚠️ Anti-patterns Detected (ถ้ามี)
{pattern ที่ขัดกับ ARCHITECTURE.md แต่ implement ไปเพราะ spec บังคับ}

### 📘 API / Interface ที่เพิ่มหรือแก้
สำหรับทุก endpoint/public interface ที่ build รอบนี้ — ให้ consumer ใช้ได้ทันทีโดยไม่ต้องอ่าน code:

**`{METHOD} {path}`** — {short purpose}
- **Auth**: {scheme}
- **Path params** / **Query params**: ตาราง `name | type | default | desc`
- **Request body**: shape + field สำคัญ + validation
- **Response 2xx**: ตัวอย่าง JSON + key fields (เน้นชื่อ field จริง เช่น `pageSize` ไม่ใช่ `limit`)
- **Error cases**: ตาราง `status | error key | when`
- **Edge cases / behaviors สำคัญ**
- **ตัวอย่างการเรียก**: 1-3 ตัวอย่าง (default / with filter / edge)

> ไม่มี public interface ใหม่ (แก้แต่ internal) → ข้าม section นี้

### Next Steps
1. Review code + tests
2. `git diff` ดูการเปลี่ยนแปลงทั้งหมด
3. `/reindex` เพื่อ update features.md (terminal status จะถูก auto-close)
4. Commit + push
```

---

## Rules

### Must Do
- **อ่าน spec + ARCHITECTURE.md + module rule** ก่อนเขียน code ทุกครั้ง
- **Follow existing pattern** — ไม่สร้าง style ใหม่
- **เขียน test คู่กับ code** (ยกเว้น `--no-test`)
- **รัน test + lint + typecheck ให้ผ่าน** ก่อน mark ✅
- **Update spec file** (Status / Implementation Status / Changelog / Last Updated) ทุกครั้ง
- **Report assumptions + review points** เสมอ
- **อธิบาย public interface ทุกตัวที่ build** ใน Final Report

### Must Not
- ❌ **Build โดยไม่มี spec file**
- ❌ **แก้เนื้อ spec (Business Rules / Design)** — ถ้า spec ไม่ชัด → หยุด ขอให้ dev รัน `/change`
  (แก้ Status / Implementation Status / Changelog / Last Updated / Known Gotchas ได้ — เป็น state ของ build)
- ❌ **แตะ `features.md`**
- ❌ **Bypass architecture rules**
- ❌ **Mark ✅ ถ้า test ยัง fail** — ปล่อย 🚧 ดีกว่า
- ❌ **ติดตั้ง dependency โดยไม่ confirm**
- ❌ **Commit / push อัตโนมัติ**
- ❌ **Cross-repo: build repo ถัดไปทั้งที่ repo ก่อนหน้า (ที่มันพึ่ง) test ยัง fail**
- ❌ **Cross-repo: mark Overall ✅ ถ้ามี repo ใดยังไม่ ✅**

### Flag-specific Rules

- **`--no-test`**: ใช้ได้เฉพาะ prototype/exploration — ถ้าเป็นงาน production → warn dev ก่อน
- **`--incremental`**: ใช้เมื่อ feature complex หรือ dev อยาก tune ระหว่างทาง
- **`--resume`**: ห้าม overwrite code เดิมโดยไม่ confirm

---

## Output Language

- ตอบ dev เป็น**ภาษาไทย**
- Code / code comment / commit message → **อังกฤษ**
- Commit message format: `feat({module}): {description}`

---

## Examples

```
dev: /build TASK-20260501-1430
AI: [pre-flight → plan → implement → test → update spec → report]

dev: /build --resume
AI: [หา feature 🚧 ล่าสุด → diff กับ spec → ทำต่อเฉพาะ gap]

dev: /build TASK-20260501-1430 --incremental
AI: [implement layer → หยุด → confirm → layer ต่อไป → ...]

dev: /build --no-test
AI: [implement อย่างเดียว → status ⚠️ → warn ว่าควร test ก่อน production]
```
