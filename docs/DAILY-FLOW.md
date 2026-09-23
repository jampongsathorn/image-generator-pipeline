# Daily flow / ขั้นตอนใช้งานประจำวัน

Bilingual quickstart. English first, Thai summary at the end. 🇹🇭

---

## For data entry (คนกรอกข้อมูล)

**What you do:** fill one row per image in a request sheet, drop the reference photos next to it,
and tell the agent to run the batch.

1. Copy the sheet template:

   ```bash
   mkdir -p inbox/2026-09-24-catalogue
   cp templates/requests.csv inbox/2026-09-24-catalogue/requests.csv
   ```

2. Fill **one row per image**. Required columns: `id`, `item_name`, `use_case`, `description`.

   | column | what to write | example |
   | --- | --- | --- |
   | `id` | unique SKU / item code | `SKU-1001` |
   | `item_name` | product name | `Classic Leather Tote` |
   | `use_case` | what kind of image (see `skills/arena-imagegen/references/use-cases.md`) | `food-hero`, `packaging-shot`, `flat-lay` |
   | `description` | short factual description: product, colour, finish, what is happening | `matte black full-grain leather tote with gold clasp` |
   | `ref_images` | reference file(s) in `refs/`, separated by `;` | `refs/SKU-1001-front.jpg` |
   | `aspect` | `1:1`, `4:5`, `16:9`, ... | `1:1` |
   | `delivery_px` | long edge in pixels for the final file | `2048` |
   | `format` | `jpeg`, `png` (png for cutouts/logos/text) | `jpeg` |
   | `text_verbatim` | exact text that must appear in the image, if any | `ACME` |
   | `must_keep` | what must not change (used for edits) | `shape, proportions, gold clasp` |
   | `must_avoid` | what must not appear | `text, logos, extra straps` |
   | `asset_type` | where the image will be used | `marketplace hero image` |
   | `priority` | `high` / `medium` / `low` | `high` |
   | `notes` | anything the agent should know | `hero for the new listing` |

3. Put the photos in `inbox/<batch>/` using the exact filenames from `ref_images`.

4. Tell the agent:

   > Run the intake for `inbox/2026-09-24-catalogue` as round `2026-09-24-r01`, show me the prompt
   > plan, then generate.

**Rules of thumb for a good row**

- Write **facts, not feelings**: "matte black leather, gold clasp" beats "premium look".
- One image per row. Want 3 angles? Write 3 rows.
- A `description` that is too vague is the #1 reason an image comes back wrong.
- Reference photo quality sets the ceiling for identity accuracy - front, well lit, whole product.

**Food & drink specifics**

- Say whether it is served **hot or cold** - that decides steam vs condensation/ice.
- Name the garnish, the container and the portion if they matter: "tall glass, orange peel, no straw".
- For anything with a label: put the exact wording in `text_verbatim`; never let the model invent
  badges, nutrition marks or health claims.
- Props are welcome for food shots (that is what makes them appetizing) - list the ones you want in
  the `description` instead of leaving it to the generator.

---

## For the agent (Arena AI)

1. **Intake + plan** (free, no generation spent)

   ```bash
   python3 tools/igp.py intake --name 2026-09-24-catalogue --round-id 2026-09-24-r01
   ```

   Read `rounds/<id>/plan.md`. Fix any `QA` notes, and list open questions for the user with a
   default you will use if they do not answer.

2. **Generate the round** - at most **10** images, in one message, straight into `rounds/<id>/raw/`
   using the exact `raw_file` paths from `plan.json`. Never use the OpenAI API; use Arena's
   built-in image tool.

3. **Finish the round**

   ```bash
   python3 tools/igp.py optimize --round rounds/<id> --delete-source --upscale-to-spec
   python3 tools/igp.py sheet    --round rounds/<id>
   python3 tools/igp.py verify   --round rounds/<id>
   python3 tools/igp.py deliver  --round rounds/<id>
   python3 tools/igp.py budget
   ```

4. **Report**: accepted / retried / deferred, the contact-sheet path, the delivery zip, open
   questions, budget. Then start the next round if rows remain.

5. **Review standard** before accepting anything: subject matches the row, no invented text or
   props, framing as planned, identity preserved vs the reference, no anatomy/geometry defects,
   detail good at delivery size. See `skills/arena-imagegen/references/quality-control.md`.

---

## What the team gets back

```
rounds/<id>/review/
  contact-sheet.jpg          one image showing the whole round
  verify-report.md           what was delivered, at what size, and what was flagged
  <id>-manifest.csv          every image + the exact prompt that produced it
  <id>-delivery.zip          finals + manifest + plan  <- this is the handover file
```

---

## สรุปภาษาไทย (Thai summary)

**หลักการ:** ข้อมูลเข้าเป็น "ตารางคำขอ" 1 แถว = 1 รูป แล้ว AI จะสร้างเป็นรอบ รอบละไม่เกิน 10 รูป
(ระบบให้ 10 รูปต่อรอบ ไม่ใช่ต่อ session) เก็บเป็นไฟล์ในเวิร์กสเปซได้จำกัด 128MB / 10,000 ไฟล์
ดังนั้นทุกรอบต้องบีบอัดรูป + ลบไฟล์ต้นฉบับทิ้ง + ทำ contact sheet 1 ใบไว้ให้ทีมดู และอย่าให้ไฟล์เกิน limit

**ขั้นตอน**

1. **คนกรอกข้อมูล:** คัดลอก `templates/requests.csv` ไปไว้ใน `inbox/<ชื่อชุดงาน>/` กรอก 1 บรรทัดต่อ 1 รูป
   ใส่คอลัมน์บังคับ `id`, `item_name`, `use_case`, `description` และวางไฟล์รูปอ้างอิงไว้ในโฟลเดอร์เดียวกัน
   (ชื่อไฟล์ต้องตรงกับคอลัมน์ `ref_images`)
2. **สั่ง AI:** พิมพ์ว่า "ทำ intake โฟลเดอร์ `inbox/<ชื่อชุด>` เป็นรอบ `<วันที่>` แล้วโชว์ plan ให้ดูก่อนสร้างรูป"
3. **AI จะ:** ตรวจตาราง → สร้าง prompt ทีละรูป (ดูได้ใน `plan.md`) → สร้างรูปรอบละไม่เกิน 10 รูป →
   บีบอัด + ขยายขนาดถ้าจำเป็น (`--upscale-to-spec`) → ลบไฟล์ต้นฉบับ → ทำ contact sheet + รายงาน
   → รวมไฟล์ส่งมอบเป็น zip เดียว
4. **ได้อะไรกลับ:** โฟลเดอร์ `rounds/<รหัสรอบ>/review/` มี `contact-sheet.jpg` (ดูทุกรูปในไฟล์เดียว),
   `verify-report.md` (รายงานตรวจ), `<รหัสรอบ>-manifest.csv` (รายการรูป + prompt ที่ใช้),
   `<รหัสรอบ>-delivery.zip` (ชุดส่งมอบ)
5. **ถ้ามีรูปเยอะกว่า 10 รูป:** AI จะแบ่งเป็นหลายรอบ ทำรอบให้จบก่อนแล้วค่อยเริ่มรอบใหม่
   ถ้าไม่จบใน session เดียว ให้เริ่ม session ใหม่แล้วทำต่อจาก `rounds/<รหัสรอบ>/plan.json` ได้เลย

**ข้อควรระวัง**

- ระบบไม่ใช้ OpenAI API (ไม่ต้องใส่คีย์) ใช้เครื่องมือสร้างรูปของ Arena เท่านั้น
- คำบรรยาย (description) ยิ่งชัด รูปยิ่งตรง - เขียนเป็นข้อเท็จจริง เช่น สี วัสดุ ทรง
- ต้องแก้ไขรูปเดิม ให้ใส่ `must_keep` ว่ารายละเอียดไหนห้ามเปลี่ยน
- ถ้ารูปมีข้อความ ให้ใส่ `text_verbatim` เป็นข้อความตรงเป๊ะ
- รูปอาหาร/เครื่องดื่ม: ระบุว่าร้อนหรือเย็น (ร้อนให้มีไอน้ำ เย็นให้มีหยดน้ำ/น้ำแข็ง) และระบุเครื่องตกแต่ง
- ถ้าเป็นสินค้าบรรจุภัณฑ์ ให้ใส่ข้อความบนฉลากใน `text_verbatim` ห้ามให้ AI คิดข้อความ สัญลักษณ์ หรือคำกล่าวอ้างสุขภาพขึ้นมาเอง
- สินค้าอาหารใส่พร็อพได้ (เพื่อให้ดูน่ากิน) โดยระบุพร็อพที่ต้องการในช่อง description
