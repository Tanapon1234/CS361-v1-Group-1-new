# V2 ERD Table & Attribute Guide

เอกสารนี้ใช้อ่านคู่กับ `docs/v2/erd.md` และ `docs/v2/v2-repository.dbml`

Source of truth ของชนิดข้อมูลและ constraint คือ `database/migrations/001_base.sql`

เป้าหมายของไฟล์นี้คืออธิบายแบบอ่านง่ายว่าแต่ละตารางคืออะไร แต่ละ attribute เก็บอะไร เป็น type อะไร และตัวอย่างค่าควรหน้าตาแบบไหน

---

## Type Quick Reference

| Type | ความหมายแบบง่าย |
|---|---|
| `text` | ข้อความ เช่น id, ชื่อ, code, URL |
| `integer` | จำนวนเต็ม เช่น ปี, จำนวน section, จำนวนคน |
| `numeric(12,2)` | ตัวเลขทศนิยม เก็บได้ละเอียด 2 ตำแหน่ง เช่น 3.00, 45.50 |
| `numeric(12,4)` | ตัวเลขทศนิยมละเอียด 4 ตำแหน่ง เช่น weight 0.2500 |
| `numeric(14,2)` | จำนวนเงิน/งบประมาณที่อาจมีค่ามาก |
| `numeric(5,2)` | เปอร์เซ็นต์ เช่น 50.00, 100.00 |
| `boolean` | จริง/เท็จ เช่น `true`, `false` |
| `date` | วันที่อย่างเดียว เช่น `2025-01-15` |
| `timestamptz` | วันเวลาแบบมี timezone เช่น `2026-09-12T10:30:00+07:00` |
| `jsonb` | ข้อมูล JSON เช่น raw source record หรือ before/after audit |
| `inet` | IP address เช่น `203.0.113.10` |

---

## Table Overview

| Table | ใช้เก็บอะไร |
|---|---|
| `faculty` | ข้อมูลหลักของอาจารย์ |
| `faculty_education` | ประวัติการศึกษาของอาจารย์ |
| `faculty_interest` | ความเชี่ยวชาญ/หัวข้อวิจัย/keyword ของอาจารย์ |
| `app_user` | user ฝั่ง application ที่ map กับ Cognito |
| `app_role` | role ขั้นต่ำของระบบ เช่น `ADMIN`, `SYSTEM` |
| `app_user_role` | ความสัมพันธ์ระหว่าง user กับ role |
| `auth_login_event` | audit การ login ฝั่ง admin |
| `academic_period` | ปีการศึกษาและภาคเรียน |
| `evaluation_period` | รอบประเมินหรือช่วงรวบรวมภาระงาน |
| `work_category` | หมวดงานหลัก เช่น งานสอน งานวิจัย |
| `work_type` | ประเภทงานย่อยภายใต้หมวดงาน |
| `import_batch` | รอบการ import ข้อมูลจาก source |
| `source_record` | record/row ต้นทางที่ import เข้ามา |
| `work_item` | แกนกลางของผลงานหรือภาระงานทุกประเภท |
| `faculty_work_item` | ตารางเชื่อมอาจารย์กับผลงาน/ภาระงาน |
| `teaching_detail` | รายละเอียดงานสอน |
| `publication_detail` | รายละเอียดผลงานตีพิมพ์ |
| `research_project_detail` | รายละเอียดโครงการวิจัย/ทุนวิจัย |
| `supervision_detail` | รายละเอียดการดูแลนักศึกษา |
| `service_detail` | รายละเอียดงานบริการวิชาการ |
| `administration_detail` | รายละเอียดงานบริหาร |
| `evidence_reference` | metadata ของหลักฐานประกอบ |
| `audit_event` | ประวัติการเปลี่ยนแปลงข้อมูล |

---

## 1. `faculty`

เก็บข้อมูลหลักของอาจารย์ ใช้เป็นฐานสำหรับ public profile และใช้เชื่อมกับผลงาน/ภาระงาน

ตัวอย่าง record: อาจารย์หนึ่งคนที่มี public slug เดิมจาก V1 และมีสถานะ `ACTIVE`

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ภายในของอาจารย์ ใช้อ้างอิงในระบบ | `fac_prapaporn` |
| `public_slug` | `text` | slug สำหรับ URL public profile ต้องไม่ซ้ำ | `prapaporn-p` |
| `name_th` | `text` | ชื่อภาษาไทย | `ผศ.ดร.ประภาภรณ์ พรหมดี` |
| `name_en` | `text` | ชื่อภาษาอังกฤษ | `Asst. Prof. Dr. Prapaporn Promdee` |
| `academic_position` | `text` | ตำแหน่งทางวิชาการ | `ผู้ช่วยศาสตราจารย์` |
| `department` | `text` | สาขา/หน่วยงาน | `Computer Science` |
| `office_public` | `text` | ห้องทำงานที่เปิดเผยได้ | `SC2-401` |
| `phone_public` | `text` | เบอร์โทรที่เปิดเผยได้ | `02-123-4567` |
| `email_public` | `text` | email ที่เปิดเผยได้ | `prapaporn@example.ac.th` |
| `profile_image_url` | `text` | URL รูปโปรไฟล์ | `https://example.ac.th/faculty/prapaporn.jpg` |
| `profile_image_alt` | `text` | alt text ของรูปโปรไฟล์ | `รูปอาจารย์ประภาภรณ์` |
| `visibility` | `text` | ระดับการเปิดเผย profile | `PUBLIC` |
| `status` | `text` | สถานะ record | `ACTIVE` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |
| `deleted_at` | `timestamptz` | เวลาที่ soft delete ถ้ามี | `null` |

---

## 2. `faculty_education`

เก็บประวัติการศึกษาของอาจารย์ หนึ่งอาจารย์มีหลายวุฒิได้

ตัวอย่าง record: วุฒิปริญญาเอกของอาจารย์หนึ่งคน

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของรายการประวัติการศึกษา | `edu_prapaporn_phd` |
| `faculty_id` | `text` | อ้างอิงไปที่ `faculty.id` | `fac_prapaporn` |
| `degree` | `text` | ชื่อวุฒิ | `Ph.D.` |
| `field_of_study` | `text` | สาขาที่จบ | `Computer Science` |
| `institution` | `text` | สถาบัน | `Chulalongkorn University` |
| `country` | `text` | ประเทศ | `Thailand` |
| `graduation_year` | `integer` | ปีที่จบ | `2018` |
| `display_order` | `integer` | ลำดับการแสดงผล | `1` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 3. `faculty_interest`

เก็บความเชี่ยวชาญ research interest หรือ keyword ของอาจารย์

ตัวอย่าง record: อาจารย์มีความสนใจด้าน cloud computing

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของ interest record | `int_prapaporn_cloud` |
| `faculty_id` | `text` | อ้างอิงไปที่ `faculty.id` | `fac_prapaporn` |
| `interest_type` | `text` | ประเภท interest | `RESEARCH_INTEREST` |
| `value` | `text` | ข้อความ interest/keyword | `Cloud Computing` |
| `visibility` | `text` | ระดับการเปิดเผย | `PUBLIC` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 4. `app_user`

เก็บ user ภายใน application ที่ map กับ Cognito user สำหรับ Admin pilot และ audit ไม่ได้เก็บ password

ตัวอย่าง record: admin หนึ่งคนที่ login ผ่าน Cognito

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ภายในของ user | `usr_admin_suphanat` |
| `cognito_sub` | `text` | Cognito subject identifier | `b7a1c5d0-1111-2222-3333-abcdef000001` |
| `email` | `text` | email จาก identity provider | `suphanat@example.com` |
| `display_name` | `text` | ชื่อที่แสดงใน admin/audit | `Suphanat Chanlek` |
| `identity_provider` | `text` | แหล่ง identity | `COGNITO` |
| `status` | `text` | สถานะ user | `ACTIVE` |
| `last_login_at` | `timestamptz` | เวลา login สำเร็จล่าสุด | `2026-09-12T18:30:00+07:00` |
| `created_at` | `timestamptz` | เวลาที่สร้าง user mapping | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T18:30:00+07:00` |
| `deleted_at` | `timestamptz` | เวลาที่ soft delete ถ้ามี | `null` |

---

## 5. `app_role`

เก็บ role ขั้นต่ำของระบบ V2 เช่น admin ที่เป็น human login และ system actor สำหรับงานอัตโนมัติ

ตัวอย่าง record: role `ADMIN`

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `code` | `text` | role code | `ADMIN` |
| `label` | `text` | ชื่อ role สำหรับแสดงผล | `Admin` |
| `description` | `text` | คำอธิบาย role | `V2 admin pilot user` |
| `is_active` | `boolean` | role นี้ยังใช้งานอยู่หรือไม่ | `true` |
| `created_at` | `timestamptz` | เวลาที่สร้าง role | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 6. `app_user_role`

เก็บความสัมพันธ์ว่า user คนไหนมี role อะไร และถ้า revoke แล้วก็ยังเก็บประวัติไว้

ตัวอย่าง record: user หนึ่งคนได้รับ role `ADMIN`

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของการ assign role | `ur_admin_suphanat` |
| `user_id` | `text` | อ้างอิงไปที่ `app_user.id` | `usr_admin_suphanat` |
| `role_code` | `text` | อ้างอิงไปที่ `app_role.code` | `ADMIN` |
| `assigned_by_user_id` | `text` | admin ที่ assign role นี้ | `usr_admin_owner` |
| `assigned_at` | `timestamptz` | เวลา assign role | `2026-09-12T10:00:00+07:00` |
| `revoked_at` | `timestamptz` | เวลา revoke ถ้ามี | `null` |
| `revoke_reason` | `text` | เหตุผลการ revoke | `null` |

---

## 7. `auth_login_event`

เก็บเหตุการณ์ login ฝั่ง admin เพื่อ audit ว่าใคร login สำเร็จหรือล้มเหลวเมื่อไหร่

ตัวอย่าง record: admin login สำเร็จจาก browser

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของ login event | `login_20260912_001` |
| `user_id` | `text` | อ้างอิง `app_user.id` ถ้า resolve ได้ | `usr_admin_suphanat` |
| `cognito_sub` | `text` | Cognito subject จาก token/event | `b7a1c5d0-1111-2222-3333-abcdef000001` |
| `email` | `text` | email จาก token/event | `suphanat@example.com` |
| `login_status` | `text` | ผล login | `SUCCESS` |
| `failure_reason` | `text` | เหตุผลถ้า login failed | `null` |
| `ip_address` | `inet` | IP address ของ client | `203.0.113.10` |
| `user_agent` | `text` | browser/client info | `Mozilla/5.0` |
| `request_id` | `text` | request correlation id | `req_01k5abcxyz` |
| `occurred_at` | `timestamptz` | เวลาที่ event เกิดขึ้น | `2026-09-12T18:30:00+07:00` |

---

## 8. `academic_period`

เก็บปีการศึกษาและภาคเรียน ใช้กับการจัดกลุ่มภาระงานหลายปี

ตัวอย่าง record: ภาคเรียนที่ 2 ปีการศึกษา 2567

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของปี/ภาคเรียน | `ap_2567_2` |
| `academic_year` | `integer` | ปีการศึกษา | `2567` |
| `semester` | `text` | ภาคเรียน | `2` |
| `label` | `text` | label สำหรับแสดงผล | `2/2567` |
| `start_date` | `date` | วันที่เริ่มโดยประมาณ | `2024-11-01` |
| `end_date` | `date` | วันที่สิ้นสุดโดยประมาณ | `2025-03-31` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 9. `evaluation_period`

เก็บรอบประเมินหรือช่วงรวบรวมข้อมูล ซึ่งอาจไม่ตรงกับ academic period ตรง ๆ

ตัวอย่าง record: รอบประเมินครึ่งหลังของปีการศึกษา 2567

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของรอบประเมิน | `eval_2567_h2` |
| `code` | `text` | code ของรอบประเมิน | `2567-H2` |
| `label` | `text` | label ที่คนอ่านเข้าใจ | `รอบประเมิน 2/2567` |
| `start_date` | `date` | วันเริ่มรอบ | `2024-11-01` |
| `end_date` | `date` | วันจบรอบ | `2025-03-31` |
| `academic_period_id` | `text` | อ้างอิง academic period ถ้าเกี่ยวข้อง | `ap_2567_2` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 10. `work_category`

เก็บหมวดงานหลักของ repository เช่น งานสอน งานวิจัย งานบริการ

ตัวอย่าง record: หมวดงานวิจัย

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `code` | `text` | code ของหมวดงาน | `RESEARCH` |
| `label_th` | `text` | ชื่อภาษาไทย | `งานวิชาการ/วิจัย` |
| `label_en` | `text` | ชื่อภาษาอังกฤษ | `Research and Academic Output` |
| `description` | `text` | คำอธิบายหมวด | `Research projects, publications, grants` |
| `display_order` | `integer` | ลำดับการแสดงผล | `20` |
| `is_active` | `boolean` | ยังใช้งานในระบบหรือไม่ | `true` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 11. `work_type`

เก็บประเภทงานย่อยภายใต้ `work_category` เช่น lecture, publication, committee

ตัวอย่าง record: ประเภทผลงานตีพิมพ์ภายใต้หมวดวิจัย

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `code` | `text` | code ของประเภทงาน | `PUBLICATION` |
| `category_code` | `text` | อ้างอิง `work_category.code` | `RESEARCH` |
| `label_th` | `text` | ชื่อภาษาไทย | `ผลงานตีพิมพ์` |
| `label_en` | `text` | ชื่อภาษาอังกฤษ | `Publication` |
| `description` | `text` | คำอธิบายประเภทงาน | `Journal, proceedings, or article` |
| `default_visibility` | `text` | visibility เริ่มต้นของงานประเภทนี้ | `PUBLIC` |
| `display_order` | `integer` | ลำดับการแสดงผล | `210` |
| `is_active` | `boolean` | ยังใช้งานในระบบหรือไม่ | `true` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 12. `import_batch`

เก็บ metadata ของรอบ import ข้อมูลจากไฟล์/source เพื่อ trace ได้ว่าข้อมูลชุดไหนเข้าระบบเมื่อไหร่

ตัวอย่าง record: import จากแบบฟอร์มภาระงาน 2/2567

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของรอบ import | `imp_2567_2_workload_v1` |
| `source_system` | `text` | ระบบ/แหล่งที่มาของข้อมูล | `WORKLOAD_FORM` |
| `source_name` | `text` | ชื่อ source หรือไฟล์ | `01 แบบฟอร์มกรอกภาระงาน 2-2567` |
| `source_version` | `text` | version ของ source ถ้ามี | `v2026-09-12` |
| `source_type` | `text` | ประเภท source | `PDF` |
| `source_s3_key` | `text` | path ใน S3 สำหรับ source/archive | `source/workload/2567-2/form.pdf` |
| `source_hash` | `text` | hash ของ source เพื่อกัน import ซ้ำ | `sha256:abc123` |
| `status` | `text` | สถานะการ import | `SUCCEEDED` |
| `record_count` | `integer` | จำนวน record ทั้งหมด | `120` |
| `valid_count` | `integer` | จำนวน record ที่ valid | `118` |
| `warning_count` | `integer` | จำนวน warning | `2` |
| `error_count` | `integer` | จำนวน error | `0` |
| `started_at` | `timestamptz` | เวลาเริ่ม import | `2026-09-12T10:00:00+07:00` |
| `completed_at` | `timestamptz` | เวลา import เสร็จ | `2026-09-12T10:05:00+07:00` |
| `created_by` | `text` | actor ที่สร้าง import | `SYSTEM` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |

---

## 13. `source_record`

เก็บ row/record ต้นทางแต่ละรายการจาก import เพื่อย้อนกลับไปดู raw data และ idempotency ได้

ตัวอย่าง record: row หนึ่งรายการจากแบบฟอร์มที่ถูก map เป็น `work_item`

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของ source record | `src_2567_2_row_001` |
| `import_batch_id` | `text` | อ้างอิง `import_batch.id` | `imp_2567_2_workload_v1` |
| `source_system` | `text` | แหล่งที่มาของข้อมูล | `WORKLOAD_FORM` |
| `source_record_key` | `text` | key จาก source | `faculty=fac_prapaporn;section=2.1;row=1` |
| `source_section_code` | `text` | section ใน source/form | `2.1` |
| `source_hash` | `text` | hash เฉพาะ record | `sha256:def456` |
| `row_number` | `integer` | เลข row/page/sequence จาก source | `1` |
| `raw_record` | `jsonb` | raw data จาก source | `{"course_code":"CS361","credits":3}` |
| `target_entity_type` | `text` | entity ที่สร้างจาก record นี้ | `work_item` |
| `target_entity_id` | `text` | id ของ entity ที่สร้าง | `wi_2567_2_cs361` |
| `status` | `text` | สถานะ record ตอน import | `IMPORTED` |
| `error_message` | `text` | error ถ้า import ไม่สำเร็จ | `null` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |

---

## 14. `work_item`

เป็นตารางแกนกลางของผลงาน/ภาระงานทุกประเภท ไม่ว่าจะเป็นงานสอน งานวิจัย งานบริการ หรือดูแลนักศึกษา

ตัวอย่าง record: ผลงานตีพิมพ์หนึ่งรายการ

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของ work item | `wi_2567_pub_001` |
| `category_code` | `text` | หมวดงานหลัก | `RESEARCH` |
| `work_type_code` | `text` | ประเภทงานย่อย | `PUBLICATION` |
| `title` | `text` | ชื่อผลงาน/ภาระงาน | `A Cloud-Based Faculty Workload Repository` |
| `description` | `text` | รายละเอียดทั่วไป | `Journal article about workload repository design` |
| `start_date` | `date` | วันที่เริ่มงาน | `2025-01-10` |
| `end_date` | `date` | วันที่สิ้นสุด/เผยแพร่ | `2025-03-15` |
| `visibility` | `text` | ระดับการเปิดเผย | `PUBLIC` |
| `status` | `text` | สถานะ record | `ACTIVE` |
| `source_score` | `numeric(12,2)` | คะแนนจาก source/form ถ้ามี | `3.50` |
| `source_weight` | `numeric(12,4)` | น้ำหนักจาก source/form ถ้ามี | `1.0000` |
| `source_section_code` | `text` | section จาก source/form | `3.1` |
| `import_batch_id` | `text` | อ้างอิงรอบ import | `imp_2567_2_workload_v1` |
| `source_record_id` | `text` | อ้างอิง source record | `src_2567_2_row_001` |
| `created_by` | `text` | actor/user ที่สร้าง | `SYSTEM` |
| `updated_by` | `text` | actor/user ที่แก้ล่าสุด | `usr_admin_suphanat` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |
| `deleted_at` | `timestamptz` | เวลาที่ soft delete ถ้ามี | `null` |

---

## 15. `faculty_work_item`

ตารางเชื่อมอาจารย์กับ work item รองรับผลงานหนึ่งชิ้นมีอาจารย์หลายคน และอาจารย์แต่ละคนมี role/contribution ต่างกัน

ตัวอย่าง record: อาจารย์หนึ่งคนเป็น author ของ publication หนึ่งรายการ

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของความสัมพันธ์ | `fwi_prapaporn_pub_001` |
| `faculty_id` | `text` | อ้างอิง `faculty.id` | `fac_prapaporn` |
| `work_item_id` | `text` | อ้างอิง `work_item.id` | `wi_2567_pub_001` |
| `academic_period_id` | `text` | ปี/ภาคเรียนที่เกี่ยวข้อง | `ap_2567_2` |
| `evaluation_period_id` | `text` | รอบประเมินที่เกี่ยวข้อง | `eval_2567_h2` |
| `role` | `text` | บทบาทของอาจารย์ในงานนั้น | `author` |
| `contribution_order` | `integer` | ลำดับผู้ร่วมงาน/contribution | `1` |
| `contribution_percent` | `numeric(5,2)` | สัดส่วน contribution | `60.00` |
| `contribution_note` | `text` | หมายเหตุ contribution | `corresponding author` |
| `quantity` | `numeric(12,2)` | จำนวนรายการ/จำนวนชิ้นงาน | `1.00` |
| `credits` | `numeric(12,2)` | จำนวนหน่วยกิต ถ้าเกี่ยวกับงานสอน | `3.00` |
| `hours` | `numeric(12,2)` | จำนวนชั่วโมงภาระงาน | `45.00` |
| `source_section_code` | `text` | section จาก source/form | `3.1` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |
| `updated_at` | `timestamptz` | เวลาที่แก้ไขล่าสุด | `2026-09-12T10:20:00+07:00` |

---

## 16. `teaching_detail`

เก็บรายละเอียดเฉพาะของ work item ประเภทงานสอน

ตัวอย่าง record: รายวิชา CS361 ที่สอนในภาคเรียน 2/2567

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `work_item_id` | `text` | id ของ work item และเป็น primary key | `wi_2567_2_cs361` |
| `course_code` | `text` | รหัสวิชา | `CS361` |
| `course_title` | `text` | ชื่อวิชา | `Cloud Computing` |
| `degree_level` | `text` | ระดับการศึกษา | `UNDERGRADUATE` |
| `teaching_mode` | `text` | รูปแบบการสอน | `LECTURE` |
| `section_count` | `integer` | จำนวน section | `2` |
| `student_count` | `integer` | จำนวนนักศึกษา | `85` |
| `credits` | `numeric(12,2)` | หน่วยกิต | `3.00` |
| `lecture_hours` | `numeric(12,2)` | ชั่วโมงบรรยาย | `45.00` |
| `lab_hours` | `numeric(12,2)` | ชั่วโมงปฏิบัติการ | `30.00` |
| `workload_hours` | `numeric(12,2)` | ชั่วโมงภาระงานรวม | `75.00` |
| `reference_label` | `text` | reference/label จากเอกสารต้นทาง | `ตารางสอน 2/2567` |

---

## 17. `publication_detail`

เก็บรายละเอียดเฉพาะของ work item ประเภทผลงานตีพิมพ์

ตัวอย่าง record: journal article หนึ่งรายการ

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `work_item_id` | `text` | id ของ work item และเป็น primary key | `wi_2567_pub_001` |
| `publication_title` | `text` | ชื่อ publication | `A Cloud-Based Faculty Workload Repository` |
| `venue` | `text` | วารสาร/งานประชุม | `Journal of Cloud Education Systems` |
| `publisher` | `text` | สำนักพิมพ์ | `Example Press` |
| `publication_year` | `integer` | ปีที่ตีพิมพ์ | `2025` |
| `publication_date` | `date` | วันที่ตีพิมพ์ | `2025-03-15` |
| `doi` | `text` | DOI | `10.1234/example.2025.001` |
| `isbn` | `text` | ISBN ถ้าเป็นหนังสือ/proceedings | `978-1-23456-789-0` |
| `issn` | `text` | ISSN ถ้าเป็นวารสาร | `1234-5678` |
| `quartile` | `text` | quartile/tier | `Q2` |
| `indexing_database` | `text` | ฐานข้อมูลที่ index | `Scopus` |
| `publication_kind` | `text` | ประเภท publication | `journal_article` |
| `external_url` | `text` | URL ไปยัง publication | `https://doi.org/10.1234/example.2025.001` |

---

## 18. `research_project_detail`

เก็บรายละเอียดเฉพาะของโครงการวิจัยหรือทุนวิจัย

ตัวอย่าง record: โครงการวิจัยที่ได้รับทุนภายนอก

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `work_item_id` | `text` | id ของ work item และเป็น primary key | `wi_2567_research_001` |
| `project_title` | `text` | ชื่อโครงการวิจัย | `Faculty Workload Data Platform` |
| `funding_source` | `text` | แหล่งทุน | `NRCT` |
| `funding_type` | `text` | ประเภททุน | `external_grant` |
| `budget_amount` | `numeric(14,2)` | งบประมาณ | `250000.00` |
| `currency` | `text` | สกุลเงิน | `THB` |
| `project_status` | `text` | สถานะโครงการ | `ONGOING` |
| `contract_number` | `text` | เลขสัญญา/เลขอ้างอิง | `NRCT-2567-001` |
| `principal_investigator` | `text` | หัวหน้าโครงการ | `ผศ.ดร.ประภาภรณ์ พรหมดี` |
| `project_start_date` | `date` | วันที่เริ่มโครงการ | `2025-01-01` |
| `project_end_date` | `date` | วันที่สิ้นสุดโครงการ | `2025-12-31` |

---

## 19. `supervision_detail`

เก็บรายละเอียดการดูแลนักศึกษา โดย V2 ตั้งใจไม่เก็บ student identity แบบเปิดเผย

ตัวอย่าง record: ดูแล senior project 3 คน

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `work_item_id` | `text` | id ของ work item และเป็น primary key | `wi_2567_supervision_001` |
| `supervision_type` | `text` | ประเภทการดูแล | `SENIOR_PROJECT` |
| `supervision_role` | `text` | บทบาทในการดูแล | `advisor` |
| `degree_level` | `text` | ระดับการศึกษา | `UNDERGRADUATE` |
| `program_name` | `text` | หลักสูตร/สาขา | `Computer Science` |
| `course_code` | `text` | รหัสวิชาที่เกี่ยวข้องถ้ามี | `CS499` |
| `student_count` | `integer` | จำนวนนักศึกษา | `3` |
| `credits` | `numeric(12,2)` | หน่วยกิตที่เกี่ยวข้อง | `3.00` |
| `student_identifier_policy` | `text` | policy การเก็บ/ซ่อน identity นักศึกษา | `REDACTED` |

---

## 20. `service_detail`

เก็บรายละเอียดงานบริการวิชาการ เช่น กรรมการ วิทยากร reviewer editor หรืองานบริการภายนอก

ตัวอย่าง record: เป็น reviewer ให้ conference

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `work_item_id` | `text` | id ของ work item และเป็น primary key | `wi_2567_service_001` |
| `service_scope` | `text` | ขอบเขตงานบริการ | `external_academic_service` |
| `organization_name` | `text` | หน่วยงาน/องค์กร | `Thai Computing Society` |
| `service_role` | `text` | บทบาท | `reviewer` |
| `committee_name` | `text` | ชื่อคณะกรรมการ/งานประชุม | `TCC 2025 Program Committee` |
| `order_reference` | `text` | เลขคำสั่ง/หนังสือเชิญ | `ORD-2567-045` |
| `service_date` | `date` | วันที่เริ่ม/วันที่ให้บริการ | `2025-02-01` |
| `service_end_date` | `date` | วันที่สิ้นสุด | `2025-02-15` |

---

## 21. `administration_detail`

เก็บรายละเอียดงานบริหาร เช่น ตำแหน่งบริหาร งานบริหารหลักสูตร หรือ appointment

ตัวอย่าง record: เป็นกรรมการบริหารหลักสูตร

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `work_item_id` | `text` | id ของ work item และเป็น primary key | `wi_2567_admin_001` |
| `position_title` | `text` | ชื่อตำแหน่ง/หน้าที่บริหาร | `กรรมการบริหารหลักสูตร` |
| `organization_unit` | `text` | หน่วยงานที่เกี่ยวข้อง | `Computer Science Program` |
| `appointment_type` | `text` | ประเภทการแต่งตั้ง | `committee_assignment` |
| `appointed_from` | `date` | วันที่เริ่มแต่งตั้ง | `2024-06-01` |
| `appointed_to` | `date` | วันที่สิ้นสุดแต่งตั้ง | `2025-05-31` |
| `appointment_reference` | `text` | เลขคำสั่ง/หนังสือแต่งตั้ง | `CMD-2567-012` |

---

## 22. `evidence_reference`

เก็บ metadata ของหลักฐานประกอบ work item เช่น URL, S3 object, document id หรือ note

ตัวอย่าง record: หลักฐานเป็นไฟล์ PDF ใน private S3

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของหลักฐาน | `ev_pub_001_pdf` |
| `work_item_id` | `text` | อ้างอิง `work_item.id` | `wi_2567_pub_001` |
| `reference_type` | `text` | ประเภทหลักฐาน | `S3_OBJECT` |
| `label` | `text` | ชื่อหลักฐานสำหรับแสดงผล | `Published article PDF` |
| `external_url` | `text` | URL ภายนอกถ้ามี | `https://doi.org/10.1234/example.2025.001` |
| `s3_key` | `text` | private S3 key | `evidence/2567/pub-001/article.pdf` |
| `mime_type` | `text` | MIME type | `application/pdf` |
| `checksum_sha256` | `text` | checksum ของไฟล์ | `sha256:789abc` |
| `visibility` | `text` | ระดับการเปิดเผยหลักฐาน | `INTERNAL` |
| `created_at` | `timestamptz` | เวลาที่สร้าง record | `2026-09-12T10:00:00+07:00` |

---

## 23. `audit_event`

เก็บประวัติการเปลี่ยนแปลงข้อมูลจาก admin/import/projection เพื่อให้ตรวจสอบย้อนหลังได้

ตัวอย่าง record: admin แก้ title ของ work item

| Attribute | Type | เก็บอะไร | ตัวอย่างค่า |
|---|---|---|---|
| `id` | `text` | id ของ audit event | `audit_20260912_001` |
| `actor_user_id` | `text` | user ที่ทำ action ถ้าเป็น human/admin | `usr_admin_suphanat` |
| `actor_subject` | `text` | subject/actor string จาก Cognito หรือระบบ | `b7a1c5d0-1111-2222-3333-abcdef000001` |
| `action` | `text` | action ที่เกิดขึ้น | `UPDATE_WORK_ITEM` |
| `entity_type` | `text` | ประเภท entity ที่ถูกแก้ | `work_item` |
| `entity_id` | `text` | id ของ entity ที่ถูกแก้ | `wi_2567_pub_001` |
| `before_json` | `jsonb` | ค่าเดิมก่อนแก้ | `{"title":"Old title"}` |
| `after_json` | `jsonb` | ค่าใหม่หลังแก้ | `{"title":"New title"}` |
| `request_id` | `text` | request correlation id | `req_01k5abcxyz` |
| `occurred_at` | `timestamptz` | เวลาที่ action เกิดขึ้น | `2026-09-12T18:40:00+07:00` |

---

## How To Read Relationships

ความสัมพันธ์หลักใน ERD:

- `faculty` เชื่อมกับ `work_item` ผ่าน `faculty_work_item`
- `work_item` เป็นแกนกลาง แล้ว detail tables เช่น `teaching_detail`, `publication_detail`, `research_project_detail` ใช้ `work_item_id` เป็น key
- `work_category` และ `work_type` ใช้จัดกลุ่มและ filter งาน
- `academic_period` และ `evaluation_period` ใช้รองรับข้อมูลหลายปี/หลายรอบประเมิน
- `import_batch` และ `source_record` ใช้ trace ข้อมูลกลับไปยัง source
- `app_user`, `app_role`, `app_user_role`, `auth_login_event` เป็น auth/audit baseline สำหรับ Admin pilot
- `audit_event` ใช้ตรวจย้อนหลังว่าใครเปลี่ยนข้อมูลอะไร เมื่อไหร่

---

## V2 Boundary Reminder

เอกสารนี้อธิบาย schema baseline ของ V2 เท่านั้น

V2 ยังไม่ทำ:

- password store ใน database
- full dynamic RBAC permission matrix
- faculty self-service workflow
- reviewer/approval workflow
- official workload scoring engine
- official annual report generator
