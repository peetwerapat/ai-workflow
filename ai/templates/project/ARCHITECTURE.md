<!-- TEMPLATE: <project>/.ai/context/ARCHITECTURE.md — ภาพรวมระบบ + ADR ที่มีผลกับหลาย repo -->
<!-- ทุก entry ต้องอ้าง repo + file path จริงเป็นหลักฐาน — ADR ที่กระทบ repo เดียวให้ไปอยู่ใน <repo>/.ai/context/ARCHITECTURE.md -->

# System Architecture

> อ่านก่อนเสนอ design ที่แตะมากกว่า 1 repo — เพิ่ม ADR ใหม่ได้เฉพาะเมื่อ dev confirm

---

## Overview

```
{ASCII diagram: repo/service ไหนคุยกับใคร ผ่านอะไร (HTTP / queue / DB / file)}
```

## Decisions (Cross-repo ADR)

### P-ADR-001: {Decision title}

**Status**: Accepted | Superseded by P-ADR-XXX
**Date**: {YYYY-MM-DD}
**Affects**: `{repo}`, `{repo}`

**Context**: {ปัญหาหรือข้อจำกัด}
**Decision**: {ตัดสินใจอะไร}
**Consequences**: {ผลที่ตามมาในแต่ละ repo}
**Evidence**: `{repo}/{path}` — {ส่วนที่เป็นตัวอย่างจริง}

---

## Cross-repo Anti-patterns

| Anti-pattern | ทำไมห้าม | ใช้อะไรแทน |
|---|---|---|
| {เช่น repo หนึ่งอ่าน DB ของอีก repo ตรงๆ} | {} | {} |
