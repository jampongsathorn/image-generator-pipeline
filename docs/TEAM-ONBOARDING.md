# คู่มือ onboard ทีม / Team onboarding

วิธีตั้งค่าให้สมาชิกทีมเปิด Arena session แล้ว **ใช้ skill นี้ได้ทันที** — ทีละขั้น
(English version: see the second half of this file.)

---

## 0. ก่อนแชร์ — เช็กลิสต์สำหรับเจ้าของ repo

| # | ต้องทำ | สถานะ |
| --- | --- | --- |
| 1 | merge PR ที่มีงานทั้งหมดเข้า `main` | ☐ **จำเป็น** — ตอนนี้ `main` ยังเป็นไฟล์ว่าง มีแค่ README 1 บรรทัด งานทั้งหมดอยู่บน branch `arena/01a0cccf-image-generator-pipeline` (PR #1) |
| 2 | ให้สิทธิ์ทีมเข้าถึง repo ( collaborator หรือ org team ) | ☐ |
| 3 | แก้ชื่อแบรนด์ใน `templates/brand.json` (`brand_name`, `campaign`) | ☐ |
| 4 | บอกทีมว่า "ห้ามใช้ OpenAI API" และโควตาคือ 10 รูป/รอบ | ☐ |

> ข้อ 1 คือด่านเดียวที่บล็อกทุกอย่างอยู่ ถ้าไม่ merge สมาชิกทีมที่เปิด repo นี้จะเห็นแค่ README เปล่า

---

## 1. สิ่งที่ทีมต้องมี

- บัญชี Arena (ใช้ตัวเดียวกับที่แชร์ session ได้)
- สิทธิ์อ่าน repo `jampongsathorn/image-generator-pipeline` บน GitHub
- ไม่ต้องติดตั้งอะไรในเครื่องเลย — ทุกอย่างรันใน Arena session

---

## 2. เปิด session ใหม่ให้ "อ่าน skill" (ทำครั้งเดียวต่อ session)

1. เปิด Arena → **New session**
2. เลือก **repository**: `jampongsathorn/image-generator-pipeline` → branch: **`main`** (หลัง merge ข้อ 0.1)
3. ส่งข้อความแรกนี้ให้ agent (คัดลอกได้เลย):

```text
อ่าน AGENTS.md และ skills/arena-imagegen/SKILL.md ให้ครบก่อน
จากนั้นรัน: python3 tools/igp.py doctor  และ  python3 tools/check_templates.py
แล้วสรุปให้ฟังสั้น ๆ ว่า:
1) กติกา 3 ข้อที่ห้ามละเมิดคืออะไร
2) environment นี้พร้อมสร้างรูปไหม (มี image engine อะไร)
3) ขั้นตอนการทำงานเป็นรอบ (round) มีอะไรบ้าง
```

4. ถ้า agent ตอบถูกทั้ง 3 ข้อ = พร้อมใช้งาน
   ถ้า `doctor` บอก **NOT ready** → สั่ง agent ว่า:

```text
ติดตั้ง image engine แล้วรัน doctor อีกครั้ง: pip install --break-system-packages Pillow
```

> **หมายเหตุ:** แต่ละ session อาจไม่ได้รับ auto-context จากไฟล์ในรีโป จึงควรส่งข้อความข้อ 3 นี้ทุกครั้ง
> ที่เปิด session ใหม่ (เก็บไว้เป็น snippet ได้เลย) — เชื่อถือได้กว่าไว้ใจว่า agent อ่านเอง

---

## 3. เริ่มงาน (3 วิธี)

| วิธี | ทำอะไร | เหมาะกับ |
| --- | --- | --- |
| **แนบรูปในแชท** | แนบรูป + พิมพ์สั่งเป็นภาษาไทย/อังกฤษ | งานด่วน 1-10 รูป |
| **วางโฟลเดอร์** | วางรูปใน `inbox/<ชื่องาน>/` แล้วบอก agent ให้ intake | มีรูปเยอะ ไม่อยากกรอกตาราง |
| **กรอก CSV** | คัดลอก `templates/requests.csv` เติม 1 บรรทัด/รูป | งานจริงจัง ต้องคุมทุกอย่าง |

ตัวอย่างข้อความสั่งงาน:

```text
ทำรูปจากรูปที่แนบ ให้เป็นภาพเมนู 1:1 ขนาด 2048px jpeg
สินค้า: กาแฟ Cold Brew แก้วสูง ใส่น้ำแข็ง + เปลือกส้ม
อยากได้: ดูน่ากิน แสงเชาธรรมชาติ และทุกใบสไตล์เดียวกัน
ทำ plan ให้ดูก่อน ยังไม่ต้องสร้างรูป
```

รายละเอียดทั้งหมดดูที่ [`QUICKSTART-TH.md`](QUICKSTART-TH.md)

---

## 4. เรื่อง storage / session (คำถามที่พบบ่อย)

**สรุป: ถูกต้อง — session ใหม่ = workspace ใหม่ 128MB แต่ "ไฟล์ที่ push ขึ้น GitHub แล้วจะอยู่ต่อ"**

| คำถาม | คำตอบ |
| --- | --- |
| workspace เต็ม 128MB ทำไง | เปิด session ใหม่ workspace จะรีเซ็ตเป็น 128MB ใหม่ |
| แล้วงานเก่าหายไหม | **ไม่หาย ถ้า push ขึ้น GitHub แล้ว** — งานที่ไม่ได้ commit/push จะหายไปกับ session |
| ต้องทำอะไรทุกครั้งก่อนจบ session | `git add -A && git commit && git push` (ให้ agent ทำ) |
| รูปที่สร้างเอง (`rounds/*/out/`) ติดไปกับ repo ไหม | ติด ถ้า commit — `raw/` และ `*.zip` ถูกกันไว้ใน `.gitignore` แล้ว |
| ถ้าระหว่างงาน session ใกล้เต็ม | สั่ง agent: `commit + push แล้ว prune --scratch` ก่อน จากนั้นเปิด session ใหม่ |
| ทำงานต่อใน session ใหม่ยังไง | บอก agent: "อ่าน AGENTS.md แล้วทำงานต่อจาก `rounds/<รหัสรอบ>/plan.json`" — prompt ถูกเก็บไว้หมดแล้ว |

**กติกาเก็บไฟล์ที่แนะนำ (กัน repo บวม)**

- commit เฉพาะ **`plan.json`, `plan.md`, `out/` (รูปส่งมอบ), `review/contact-sheet.jpg`, manifest**
- ไม่ต้อง commit `raw/`, zip, ไฟล์ทดลอง (ถูก ignore ไว้แล้ว)
- ถ้า repo โตเกิน: `python3 tools/igp.py prune --archive-older-than 30` (บีบรอบเก่าเป็น zip)

---

## 5. เอารูปกลับเข้าเครื่อง (3 ช่องทาง)

| ช่องทาง | ขั้นตอน | ข้อดี/ข้อจำกัด |
| --- | --- | --- |
| **1. GitHub (ชัวร์สุด)** | ให้ agent push → เปิด repo บน GitHub → เข้า `rounds/<รหัสรอบ>/out/` → กด **Download** ทีละไฟล์ หรือ **Code → Download ZIP** ทั้ง repo | ได้ไฟล์ต้นฉบับครบ ไม่ขึ้นกับ UI ของ Arena |
| **2. Arena file viewer** | สั่ง agent: "เปิด `rounds/<id>/review/contact-sheet.jpg` ให้ดู" → ดาวน์โหลดจากตัวดูไฟล์ในหน้า Arena | เร็ว ดูได้ทันที (ปุ่มดาวน์โหลดอยู่ในตัวดูไฟล์ของ Arena — ถ้าไม่เห็นให้ใช้ช่องทาง 1) |
| **3. Delivery zip** | สั่ง agent: `python3 tools/igp.py deliver --round rounds/<id>` แล้วเปิดไฟล์ zip | ได้รูป + manifest + prompt ในไฟล์เดียว |

> ผมยืนยันปุ่มใน UI ของ Arena ให้ 100% ไม่ได้ (ไม่ใช่ส่วนที่ agent ควบคุม) แต่ช่องทาง GitHub
> ใช้ได้เสมอและเหมาะกับการส่งงานให้ทีมจริง ๆ — แนะนำให้ใช้เป็นหลัก

---

## 6. กติกาการทำงานเป็นทีม

1. **1 session = 1 branch ของ Arena** → สองคนไม่ควรแก้ไฟล์เดียวกันในเวลาเดียวกัน (จะ conflict)
   งานที่แยกกัน (คนละรอบ/คนละสินค้า) ทำงานพร้อมกันได้ปกติ
2. ทุก session ที่ทำงานเสร็จควรเปิด **PR** กลับเข้า `main` แล้วให้เจ้าของ repo review/merge
3. **อย่า commit รูปซ้ำ ๆ หลายเวอร์ชัน** — เก็บเฉพาะที่ส่งมอบจริง
4. **ห้ามใช้ OpenAI API / ใส่ API key** — ใช้เครื่องมือสร้างรูปของ Arena เท่านั้น (อยู่ใน `AGENTS.md` แล้ว)
5. โควตา **10 รูป/รอบ** — ถ้างาน 30 รูป agent จะแบ่งเป็น 3 รอบให้

---

## 7. ตรวจว่ารีโปพร้อมแชร์แล้วหรือยัง

```bash
python3 tools/igp.py doctor            # session นี้พร้อมไหม
python3 tools/check_templates.py       # template/prompt ถูกต้องไหม
bash tools/smoke_test.sh               # ทดสอบครบวงจร 23 ข้อ (ไม่กินโควตาสร้างรูป)
```

ทั้งสามคำสั่งรันบน GitHub Actions อัตโนมัติทุกครั้งที่มี push/PR (`.github/workflows/validate.yml`)

---
---

# Team onboarding (English)

## 0. Before sharing - owner checklist

1. **Merge PR #1 into `main`.** Currently `main` holds only the placeholder README; all work is on
   `arena/01a0cccf-image-generator-pipeline`.
2. Grant the team read access to the repo.
3. Set `brand_name` / `campaign` in `templates/brand.json`.
4. Tell the team: 10 images per round, 128MB per session, no OpenAI API.

## 1. What a teammate needs

An Arena account plus repo access. Nothing to install locally - everything runs in the session.

## 2. Open a session that follows this skill

1. Arena → New session → choose this repository → branch `main`.
2. Send this first message:

```text
Read AGENTS.md and skills/arena-imagegen/SKILL.md in full.
Then run: python3 tools/igp.py doctor   and   python3 tools/check_templates.py
and tell me: (1) the three non-negotiable rules,
(2) whether this environment is ready to generate images, and
(3) the steps of a round.
```

3. If `doctor` reports NOT ready, tell the agent:
   `pip install --break-system-packages Pillow` then re-run `doctor`.

Sessions do not reliably auto-load repo instructions, so sending that first message each time is the
dependable way to make the agent follow the skill.

## 3. Start work

Attach images in chat (fastest), drop a folder in `inbox/<batch>/`, or fill
`templates/requests.csv`. Always ask for the plan first, approve it, then generate.

## 4. Storage and sessions (the short version)

A new session resets the workspace to 128MB - **but only files pushed to GitHub survive**. So the
rule is: finish a round, run `optimize --delete-source`, `deliver`, then **commit and push**. Never
leave work unpushed when a session might end. `raw/` and zips are git-ignored; commit `out/`,
`plan.*`, the contact sheet and the manifest. If a session fills up mid-task, push first, then
continue in a new session from `rounds/<id>/plan.json`.

## 5. Getting images onto your computer

| Channel | How | Notes |
| --- | --- | --- |
| GitHub (most reliable) | agent pushes → open the repo → `rounds/<id>/out/` → Download, or Code → Download ZIP | exact originals, independent of the Arena UI |
| Arena file viewer | ask the agent to open `contact-sheet.jpg` or the zip | fastest for a quick look; download button lives in the viewer |
| Delivery bundle | `python3 tools/igp.py deliver --round rounds/<id>` | finals + manifest + prompts in one zip |

## 6. Team rules

One session = one Arena branch, so avoid two people editing the same round at once; open PRs back to
`main`; keep only delivered finals in git; never use an OpenAI API key; respect 10 images per round.

## 7. Verify the repo is share-ready

`python3 tools/igp.py doctor` · `python3 tools/check_templates.py` · `bash tools/smoke_test.sh`
(all three also run in CI on every push/PR).
