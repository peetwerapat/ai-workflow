<!-- TEMPLATE: <project>/.ai/context/integrations.md — contract ระหว่าง repo -->
<!-- ทุกแถวต้องอ้าง path ของ contract จริง (OpenAPI, proto, DTO, event schema) -->

# Integrations

> แก้ contract ในตารางนี้ = breaking change ข้าม repo — `/spec` / `/change` ต้อง flag ทุก repo ฝั่ง consumer

| Provider | Consumer | ช่องทาง | Contract | หมายเหตุ |
|---|---|---|---|---|
| `{repo}` | `{repo}` | {REST / gRPC / queue / DB / file} | `{repo}/{path}` | {auth, versioning} |

## Breaking-change Rules

- {เช่น เพิ่ม field ได้ ห้ามลบ/เปลี่ยน type โดยไม่ version}
