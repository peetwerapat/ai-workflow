# ประเมินพฤติกรรม workflow

ใช้ `ai/evals/cases.json` เป็นโจทย์เดียวกันเมื่อต้องเปรียบเทียบ prompt หรือ assistant ต่างกัน ชุดนี้ตรวจพฤติกรรม workflow; การสร้างไฟล์ config ผ่าน tests ไม่ได้แปลว่า model ทำงานตามกฎได้จริง

1. เปิด sandbox repo ที่มีไฟล์ตาม `context` ของแต่ละ case แล้วส่ง `prompt` พร้อม context ให้ assistant ที่ต้องการวัด
2. เก็บ transcript และ tool results ต้นฉบับ บันทึก provider, model, effort, source commit และคำสั่งที่ใช้ โดยไม่เก็บ secrets
3. ผู้ตรวจแปลงการกระทำที่เกิดจริงเป็น `events` ตาม rubric ห้ามนำ `required` มาสร้างผลการทดลอง ใส่ `transcript` เป็น path สำหรับย้อนตรวจ
4. รัน scorer แล้วตรวจรายงานเทียบ transcript โดยเฉพาะการอ้างหลักฐานและคำถามที่ไม่จำเป็น

```bash
python3 ai/tools/evaluate.py --responses /tmp/responses.json --output /tmp/report.json
```

รูปแบบ response (หนึ่งรายการต่อ case; ส่งได้บาง case แต่ case ที่ขาดจะไม่ผ่าน):

```json
[
  {
    "id": "direct-change",
    "transcript": "/tmp/direct-change.txt",
    "provider": "record-the-provider",
    "model": "record-the-model",
    "source_commit": "record-the-commit",
    "events": [
      {"type": "inspect", "path": "app.py"},
      {"type": "edit_code", "path": "app.py"},
      {"type": "test_run", "command": "python3 -m unittest", "result": "passed"},
      {"type": "claim_done"}
    ],
    "metrics": {"duration_seconds": 12, "input_tokens": 500, "output_tokens": 200, "unnecessary_questions": 0}
  }
]
```

ตัวเลขในตัวอย่างเป็นข้อมูลสาธิต กรอก metrics เฉพาะค่าที่วัดได้จริง; ค่าที่ไม่ทราบให้ละไว้ scorer จะแสดงจำนวน samples และค่าเฉลี่ย ไม่แทนค่าที่ขาดด้วยศูนย์

คำจำกัดความของ event อยู่ในแต่ละ case: `required` ต้องมีครบ, `forbidden` ต้องไม่มี, `order` ต้องเกิดตามลำดับ ก่อน `claim_done` ต้องมี test command ที่ผ่าน และไม่มีการแก้ code หลังผลนั้น หลักฐานต้องมี path และ symbol/section

ผล scorer อาศัย trace ที่ผู้ตรวจให้มา จึงไม่ยืนยันว่า tool ถูกเรียกจริงโดยตัวมันเอง ต้องเก็บ transcript และตรวจประกอบเสมอ ยังไม่มีการเรียก provider แบบอัตโนมัติหรือคิดค่าใช้จ่าย API จากเครื่องมือนี้
