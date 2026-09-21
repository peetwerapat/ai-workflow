<!-- TEMPLATE: .ai/context/ARCHITECTURE.md -->
<!-- ทุก entry ต้องอ้าง file path จริงเป็นหลักฐาน — ไม่มีหลักฐาน = ไม่ใส่ -->

# Architecture

> ADR + patterns ของ project นี้ — `/spec`, `/build`, `/change` อ่านไฟล์นี้ก่อนเสนอ design
> เพิ่ม ADR ใหม่ได้เฉพาะเมื่อ dev confirm

---

## Decisions (ADR)

### ADR-001: {Decision title}

**Status**: Accepted | Superseded by ADR-XXX
**Date**: {YYYY-MM-DD}

**Context**: {ปัญหาหรือข้อจำกัดที่ทำให้ต้องตัดสินใจ}
**Decision**: {ตัดสินใจอะไร}
**Consequences**: {ผลที่ตามมา ทั้งดีและแย่}
**Evidence**: `{path}` — {บรรทัด/ส่วนที่เป็นตัวอย่างจริง}

---

## Patterns (ต้องทำตาม)

### {Pattern name}

{คำอธิบาย}

```
{ตัวอย่าง code จริงจาก repo}
```

**ใช้ที่**: `{path}`, `{path}`

---

## Anti-patterns (ห้ามทำ)

| Anti-pattern | ทำไมห้าม | ใช้อะไรแทน |
|---|---|---|
| {} | {} | {} |

---

## Security Rules

- {rule} — evidence: `{path}`

---

## Performance Notes

- {known bottleneck / index ที่ต้องมี / query ที่ต้องระวัง}
