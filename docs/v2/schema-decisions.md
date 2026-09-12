# V2 Schema Decisions

เอกสารนี้บันทึก design decisions ของ relational schema สำหรับ Issue #47

---

## Decision 1: `work_item` เป็น central entity

ใช้ `work_item` เป็น table กลางสำหรับผลงานและภาระงานทุกประเภท

เหตุผล:

- API list/search/filter ใช้ model เดียว
- รองรับ category/type หลายแบบโดยไม่สร้าง list endpoint แยกทุกประเภท
- frontend `/outputs` ทำ pagination และ filter ได้จาก shape เดียว
- import/migration trace กลับ source ได้ในจุดเดียว

ผลกระทบ:

- subtype detail ต้องแยกเป็น table เฉพาะประเภท
- API detail ต้อง join subtype ตาม `work_type_code` หรือ category

---

## Decision 2: subtype detail table ใช้ `work_item_id` เป็น primary key

Subtype detail tables ได้แก่:

- `teaching_detail`
- `publication_detail`
- `research_project_detail`
- `supervision_detail`
- `service_detail`
- `administration_detail`

แต่ละ table ใช้ `work_item_id` เป็นทั้ง primary key และ foreign key

เหตุผล:

- detail หนึ่งชุดเป็น extension ของ work item หนึ่งรายการ
- ทำให้ delete/update ตาม work item ง่าย
- ลด duplicate detail record ต่อ work item

---

## Decision 3: `faculty_work_item` รองรับ many-to-many และ contribution

ไม่ใส่ `faculty_id` ตรงใน `work_item`

เหตุผล:

- publication หรือ research project หนึ่งรายการอาจมีอาจารย์หลายคน
- อาจารย์แต่ละคนอาจมี role/contribution ต่างกัน
- workload form มีสัดส่วนความรับผิดชอบและ role หลายแบบ

ผลกระทบ:

- query faculty work item ต้อง join ผ่าน `faculty_work_item`
- contribution percent ไม่ enforce ให้รวมกันเท่ากับ 100 เพราะ source อาจไม่ระบุ contributor ครบทุกคน

---

## Decision 4: แยก `academic_period` กับ `evaluation_period`

ไม่ derive academic year จาก calendar year

เหตุผล:

- ตัวอย่างฟอร์มมีภาคเรียน `2/2567` แต่ช่วงประเมินอยู่ในปีปฏิทิน 2568
- academic period ใช้กับการเรียนการสอน
- evaluation period ใช้กับรอบประเมิน/รายงาน

ผลกระทบ:

- `faculty_work_item` มีได้ทั้ง `academic_period_id` และ `evaluation_period_id`
- API filter ต้องรองรับทั้งสอง concept

---

## Decision 5: เก็บคะแนน/น้ำหนักจาก source เป็น source-reported เท่านั้น

ใช้ field:

- `work_item.source_score`
- `work_item.source_weight`
- `faculty_work_item.quantity`
- `faculty_work_item.credits`
- `faculty_work_item.hours`

เหตุผล:

- V2 ยังไม่ใช่ official workload scoring engine
- ฟอร์มภาระงานมีสูตรและเพดานคะแนนเฉพาะกิจจำนวนมาก
- การสร้าง scoring engine เป็น scope หลังจาก repository foundation

ผลกระทบ:

- ห้ามใช้ field เหล่านี้เป็นคะแนนรับรองโดยระบบ
- UI/API ต้องสื่อสารว่าเป็นค่าจาก source ถ้านำไปแสดง

---

## Decision 6: Evidence เป็น metadata/reference ก่อน

V2 เก็บ `evidence_reference` ไม่ใช่ full evidence workflow

เหตุผล:

- ไฟล์หลักฐานอาจมีข้อมูล internal/restricted
- V2 ยังไม่มี role workflow เต็มแบบ V3
- public API ต้องไม่เปิด private S3 key

ผลกระทบ:

- `s3_key` เป็น internal field
- public projection ต้อง redact restricted evidence

---

## Decision 7: Import idempotency อยู่ที่ `source_record`

ใช้ unique key:

```text
source_system + source_record_key + source_hash
```

เหตุผล:

- import ซ้ำ source เดิมไม่ควรสร้าง duplicate
- source row เดียวกันที่ content เปลี่ยนควรตรวจจับได้จาก hash ใหม่
- import batch ใช้เป็น context แต่ idempotency ของ record อยู่ที่ source record

---

## Decision 8: ใช้ text ID แทน database-generated UUID ใน baseline

V2 baseline ใช้ `text` primary key

เหตุผล:

- import pipeline สามารถสร้าง deterministic ID ได้
- demo dataset อ่านง่าย
- ไม่ผูก migration กับ PostgreSQL extension เช่น `uuid-ossp` หรือ `pgcrypto`
- RDS Data API ใช้งานง่ายกับ app-generated IDs

ผลกระทบ:

- application/import layer ต้องรับผิดชอบการสร้าง ID
- production อาจเปลี่ยนเป็น UUID ได้ในอนาคตผ่าน migration ที่ควบคุมแล้ว

---

## Decision 9: Auth tables เป็น identity mapping ไม่ใช่ full RBAC

เพิ่มตาราง:

- `app_user`
- `app_role`
- `app_user_role`
- `auth_login_event`

เหตุผล:

- V2 Admin pilot ต้องตรวจสอบได้ว่า admin คนใด login และทำ mutation อะไร
- Cognito เป็น source ของ authentication แต่ repository ยังต้องมี user identity สำหรับ audit และ role mapping
- ไม่ควรเก็บ password/session token ใน database

ขอบเขต:

- รองรับ role ขั้นต่ำ `ADMIN` และ `SYSTEM`
- ยังไม่ทำ dynamic permission matrix
- ยังไม่ทำ faculty self-service, reviewer workflow หรือ approval workflow

ผลกระทบ:

- `audit_event.actor_user_id` สามารถอ้างถึง `app_user`
- `auth_login_event` ช่วยตรวจสอบ login success/failure
- #55 Configure Admin Authentication สามารถต่อยอดได้โดยไม่ต้องเปลี่ยน schema หลัก

---

## Decision 10: Publication duplicate strategy ใช้ DOI ก่อน แล้ว fallback ไป title/year

V2 baseline ใช้ duplicate strategy สองชั้นสำหรับ publication:

1. ถ้ามี DOI ให้ใช้ `publication_detail.doi` เป็น hard database guard ผ่าน partial unique index แบบ case-insensitive
2. ถ้าไม่มี DOI ให้ใช้ normalized publication title + publication year เป็น import/review fallback ที่ application หรือ import layer ตรวจจับและส่งเข้า warning/manual review

เหตุผล:

- DOI เป็น identifier ที่เหมาะกับ database-level uniqueness เมื่อมีค่า
- publication หลายรายการอาจชื่อเหมือนหรือใกล้เคียงกันได้ จึงไม่ควรทำ unique constraint ตรง ๆ บน title อย่างเดียว
- `idx_publication_title` และ `idx_publication_year` ช่วย lookup สำหรับ fallback duplicate review ได้

ผลกระทบ:

- database ป้องกัน duplicate DOI ได้ทันที
- import pipeline ต้องรับผิดชอบ normalized title/year matching สำหรับ record ที่ไม่มี DOI
- งาน #49/#50 สามารถระบุ mapping/demo case สำหรับ title/year fallback เพิ่มได้
