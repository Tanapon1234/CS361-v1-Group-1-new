# Data Schema — ระบบบันทึกภาระงานอาจารย์

PostgreSQL 15+ | Auth: AWS Cognito | Files: S3 | 14 ตาราง

ตัวอย่างข้อมูลทั้งเอกสารใช้ชุดเดียวกัน: ผศ.ประภาพร รัตนธำรง สาขาวิทยาการคอมพิวเตอร์ รอบ 1 ม.ค. – 30 มิ.ย. 2568

## สูตรคำนวณคะแนน (ใช้ร่วมกันทุกข้อ)

```
score = (quantity / unit_divisor) × weight × base_points(200) × participation_pct
```

| รายการ | ข้อ | การคำนวณ | ได้ |
|---|---|---|---|
| CS222 3 หน่วยกิต | 1.1 | (3÷3) × 1.0 × 200 × 100% | 200 |
| สหกิจ 3 เรื่อง | 1.5 | (3÷1) × 0.2 × 200 × 100% | 120 |
| วิทยานิพนธ์ 6 หน่วยกิต | 1.9 | (6÷1) × 0.1 × 200 × 100% | 120 |
| บทความ มีส่วนร่วม 20% | 2.3.1 | (1÷1) × 1.25 × 200 × 20% | 50 |
| กรรมการ 1 คำสั่ง | 4.2.1 | (1÷1) × 0.05 × 200 × 100% | 10 |

---

## กลุ่ม A — ผู้ใช้และตำแหน่ง

### department

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | smallint PK | |
| code | varchar(10) UNIQUE | |
| name_th | varchar(150) | |
| is_active | boolean | ยุบสาขาแล้วตั้ง false ห้ามลบแถว |

**ข้อมูล**

| id | code | name_th | is_active |
|---|---|---|---|
| 1 | CS | วิทยาการคอมพิวเตอร์ | true |
| 2 | MATH | คณิตศาสตร์ | true |
| 3 | STAT | สถิติ | true |

### faculty_member

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | uuid PK | |
| cognito_sub | varchar(64) UNIQUE | จุดเชื่อมกับ JWT |
| employee_code | varchar(20) UNIQUE | กระทบยอดกับ HR |
| full_name_th | varchar(200) | |
| email | varchar(255) UNIQUE | |
| department_id | FK department | |
| rank | enum academic_rank | lecturer, asst_prof, assoc_prof, prof |
| is_active | boolean | เกษียณแล้วตั้ง false |
| created_at / updated_at | timestamptz | |

**ข้อมูล**

| id | cognito_sub | employee_code | full_name_th | department_id | rank | is_active |
|---|---|---|---|---|---|---|
| a3f8 | 7c9e-4b2a | 650012 | ประภาพร รัตนธำรง | 1 | asst_prof | true |
| b7d1 | 2f1a-9c8e | 590045 | สมชาย ใจดี | 1 | assoc_prof | true |
| c2e9 | 8d3b-1e7f | 551023 | วิไล สุขใจ | 2 | prof | true |
| f1c2 | 4a6c-2d9b | 670301 | ธุรการคณะ | 1 | lecturer | true |

ไม่เก็บ password, MFA, role — ให้ Cognito ถือทั้งหมด

### member_position

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | uuid PK | |
| member_id | FK faculty_member | |
| position | enum position_code | dean, vice_dean, asst_dean, exec_committee, dept_chair, dept_deputy, dept_secretary, dept_committee |
| department_id | FK department NULL | NULL = ตำแหน่งระดับคณะ |
| start_date | date | ช่อง "วันที่ดำรงตำแหน่ง" |
| end_date | date NULL | NULL = ยังอยู่ในวาระ |

**ข้อมูล**

| member_id | ชื่อ | position | department_id | start_date | end_date |
|---|---|---|---|---|---|
| b7d1 | สมชาย | dept_chair | 1 | 2024-10-01 | NULL |
| c2e9 | วิไล | dean | NULL | 2023-10-01 | NULL |
| c2e9 | วิไล | exec_committee | NULL | 2023-10-01 | NULL |
| a3f8 | ประภาพร | dept_committee | 1 | 2024-10-01 | NULL |

```sql
EXCLUDE USING gist (member_id WITH =, position WITH =,
  daterange(start_date, COALESCE(end_date,'infinity')) WITH &&)
```

---

## กลุ่ม B — เกณฑ์ภาระงาน (versioned)

### rubric_version

**โครงสร้าง**

| คอลัมน์ | ชนิด |
|---|---|
| id | smallint PK |
| code | varchar(30) UNIQUE |
| approved_meeting | varchar(50) |
| approved_on | date |
| base_points | numeric(6,2) |
| overall_cap | numeric(8,2) |
| min_required | numeric(8,2) |
| min_teaching_credits | numeric(5,2) |
| is_active | boolean |

**ข้อมูล**

| id | code | approved_meeting | approved_on | base_points | overall_cap | min_required | min_teaching_credits | is_active |
|---|---|---|---|---|---|---|---|---|
| 1 | 2567-r1 | 6/2567 | 2024-05-27 | 200 | 2000 | 650 | 6 | true |

### rubric_category

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | smallint PK | |
| version_id | FK rubric_version | UNIQUE(version_id, code) |
| code | varchar(5) | |
| name_th | varchar(100) | |
| cap | numeric(8,2) | เพดานหมวด |
| sort_order | smallint | เว้นช่วง 10, 20, 30 |

**ข้อมูล**

| id | version_id | code | name_th | cap | sort_order |
|---|---|---|---|---|---|
| 1 | 1 | 1 | งานสอน | 900 | 10 |
| 2 | 1 | 2 | งานวิชาการ | 900 | 20 |
| 3 | 1 | 3 | งานบริหาร | 400 | 30 |
| 4 | 1 | 4 | งานบริการวิชาการและอื่น ๆ | 300 | 40 |
| 5 | 1 | 5 | คะแนนพิเศษ | 100 | 50 |

### rubric_section

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | smallint PK | |
| category_id | FK rubric_category | UNIQUE(category_id, code) |
| parent_id | FK self NULL | รองรับ 2.3 → 2.3.1–2.3.5 และกลุ่ม ป.ตรี / ป.โท-เอก |
| code | varchar(10) | |
| name_th | varchar(255) | |
| cap | numeric(8,2) NULL | เพดานย่อย |
| max_entries | smallint NULL | จำกัดจำนวนแถว |
| sort_order | smallint | |

**ข้อมูล**

| id | category_id | parent_id | code | name_th | cap | max_entries | sort_order |
|---|---|---|---|---|---|---|---|
| 1 | 1 | NULL | A | ระดับปริญญาตรี | NULL | NULL | 10 |
| 2 | 1 | 1 | 1.1 | วิชาบรรยาย | NULL | NULL | 20 |
| 3 | 1 | 1 | 1.2 | วิชาปฏิบัติการ | NULL | NULL | 30 |
| 4 | 1 | 1 | 1.3 | สัมมนา | 120 | NULL | 40 |
| 5 | 1 | 1 | 1.4 | ซีเนียร์โปรเจกหรือปัญหาพิเศษ | 200 | NULL | 50 |
| 6 | 1 | 1 | 1.5 | สหกิจศึกษา | 200 | NULL | 60 |
| 7 | 1 | NULL | B | ระดับปริญญาโทและเอก | NULL | NULL | 70 |
| 8 | 1 | 7 | 1.9 | วิทยานิพนธ์ ใน คณะ/มธ. | NULL | NULL | 110 |
| 9 | 2 | NULL | 2.3 | บทความและผลงานตีพิมพ์ | NULL | NULL | 30 |
| 10 | 2 | 9 | 2.3.1 | วารสารระดับนานาชาติ | NULL | NULL | 31 |
| 11 | 2 | 9 | 2.3.2 | Short Communication | NULL | NULL | 32 |
| 12 | 2 | NULL | 2.4.1 | นำเสนอผลงานระดับนานาชาติ | NULL | NULL | 41 |
| 13 | 3 | NULL | 3.1 | งานบริหารในตำแหน่ง | 400 | NULL | 10 |
| 14 | 3 | NULL | 3.2 | งานบริหารระดับสาขาวิชา | NULL | NULL | 20 |
| 15 | 3 | NULL | 3.3 | ผู้ประสานงานประจำวิชา | 75 | NULL | 30 |
| 16 | 3 | NULL | 3.5 | งานอาจารย์ที่ปรึกษา | NULL | NULL | 50 |
| 17 | 4 | NULL | 4.1.1 | คณะทำงานหรือกรรมการมีวาระ | NULL | 20 | 10 |
| 18 | 4 | NULL | 4.2.1 | กรรมการนอกคณะ | NULL | 10 | 20 |
| 19 | 4 | NULL | 4.3 | บริการวิชาการแก่สังคม | NULL | NULL | 30 |
| 20 | 4 | NULL | 4.4 | ผู้ประเมินผลงานทางวิชาการ | 100 | NULL | 40 |

### rubric_item

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | smallint PK | |
| section_id | FK rubric_section | |
| label_th | varchar(255) | ข้อความใน dropdown |
| weight_mode | enum | fixed / ranged |
| weight | numeric(6,4) NULL | ใช้เมื่อ fixed |
| weight_min / weight_max | numeric(8,4) NULL | ใช้เมื่อ ranged |
| range_basis | enum NULL | weight = คูณ 200 ต่อ / points = คะแนนตรง |
| assessor_position | enum NULL | ใครมีสิทธิ์ประเมิน |
| assessment_agg | enum | none / single / average |
| unit | enum quantity_unit | credit, topic, course, hour, person, term |
| unit_divisor | numeric(6,2) | ปกติ 1 |
| uses_participation | boolean | |
| counts_teaching_credit | boolean | |
| once_per_round | boolean | |
| tier_min / tier_max | integer NULL | ช่วงจำนวน นศ. |
| field_schema | jsonb NULL | ฟิลด์เสริมของข้อนั้น |
| is_active | boolean | |

**ข้อมูล — กลุ่มน้ำหนักตายตัว**

| id | section | label_th | mode | weight | unit | divisor | part. | credit | tier_min | tier_max |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.1 | นักศึกษา < 100 คน | fixed | 1.0 | credit | 3 | false | true | 0 | 99 |
| 2 | 1.1 | นักศึกษา 100-250 คน | fixed | 1.1 | credit | 3 | false | true | 100 | 250 |
| 3 | 1.1 | นักศึกษา 251-500 คน | fixed | 1.2 | credit | 3 | false | true | 251 | 500 |
| 4 | 1.1 | นักศึกษา > 500 คน | fixed | 1.3 | credit | 3 | false | true | 501 | NULL |
| 10 | 1.4 | เป็นอาจารย์ที่ปรึกษา | fixed | 0.2 | topic | 1 | false | false | NULL | NULL |
| 11 | 1.4 | เป็นอาจารย์ที่ปรึกษาร่วม | fixed | 0.1 | topic | 1 | false | false | NULL | NULL |
| 12 | 1.4 | เป็นกรรมการสอบ | fixed | 0.05 | topic | 1 | false | false | NULL | NULL |
| 13 | 1.5 | เป็นอาจารย์ที่ปรึกษา | fixed | 0.2 | topic | 1 | false | false | NULL | NULL |
| 14 | 1.9 | ที่ปรึกษาหลัก | fixed | 0.1 | credit | 1 | false | false | NULL | NULL |
| 15 | 1.9 | ที่ปรึกษาร่วม | fixed | 0.05 | credit | 1 | false | false | NULL | NULL |

**ข้อมูล — กลุ่มหารตามสัดส่วนผู้ร่วมงาน (หมวด 2 เท่านั้น)**

| id | section | label_th | mode | weight | unit | part. | field_schema |
|---|---|---|---|---|---|---|---|
| 20 | 2.3.1 | บทความวิจัย Tier 1 | fixed | 2.50 | topic | **true** | quartile |
| 21 | 2.3.1 | บทความวิจัย Q1 | fixed | 2.25 | topic | true | quartile |
| 22 | 2.3.1 | บทความวิจัย Q2 | fixed | 2.00 | topic | true | quartile |
| 23 | 2.3.1 | บทความวิจัย Q3 | fixed | 1.75 | topic | true | quartile |
| 24 | 2.3.1 | บทความวิจัย Q4 | fixed | 1.50 | topic | true | quartile |
| 25 | 2.3.1 | บทความวิจัยที่ไม่มี Q | fixed | 1.25 | topic | true | quartile |
| 26 | 2.4.1 | นำเสนอแบบบรรยาย | fixed | 0.75 | topic | true | NULL |
| 27 | 2.4.1 | นำเสนอแบบโปสเตอร์ | fixed | 0.375 | topic | true | NULL |

**ข้อมูล — กลุ่มงานบริหารและบริการวิชาการ**

| id | section | label_th | mode | weight | unit |
|---|---|---|---|---|---|
| 30 | 3.3 | ผู้ประสานงานวิชาที่มีผู้สอน 1 คน | fixed | 0.05 | course |
| 31 | 3.3 | ผู้ประสานงานวิชาที่มีผู้สอน 2-4 คน | fixed | 0.10 | course |
| 32 | 3.5 | อาจารย์ที่ปรึกษาทั่วไป | fixed | 0.125 | person |
| 40 | 4.1.1 | ประธานหรือเลขานุการ | fixed | 0.075 | topic |
| 41 | 4.1.1 | คณะทำงาน | fixed | 0.05 | topic |
| 42 | 4.2.1 | ประธานหรือเลขานุการ | fixed | 0.075 | topic |
| 43 | 4.2.1 | กรรมการ | fixed | 0.05 | topic |
| 44 | 4.3 | วิทยากรหรือผู้ทรงคุณวุฒิ | fixed | 0.075 | topic |
| 45 | 4.4 | ผู้ประเมินระดับนานาชาติ | fixed | 0.075 | topic |

**ข้อมูล — กลุ่มที่ผู้บริหารเป็นคนให้คะแนน**

| id | section | label_th | mode | min | max | range_basis | assessor_position | agg | unit |
|---|---|---|---|---|---|---|---|---|---|
| 50 | 3.1 | คณบดี | ranged | 1.5 | 2.5 | weight | exec_committee | average | term |
| 51 | 3.1 | หัวหน้าสาขาวิชา | ranged | 1.0 | 2.0 | weight | exec_committee | average | term |
| 52 | 3.2 | ผู้ช่วยหรือรองหัวหน้าสาขา | ranged | 50 | 100 | **points** | dept_chair | single | term |
| 53 | 3.2 | กรรมการประจำสาขาวิชา | ranged | 0 | 25 | **points** | dept_chair | single | term |

ข้อ 3.1 ช่วงเป็นน้ำหนัก ต้องคูณ 200 ต่อ ส่วนข้อ 3.2 ช่วงเป็นคะแนนตรง ไม่ต้องคูณ

```sql
CHECK (weight_mode='fixed'  AND weight IS NOT NULL)
   OR (weight_mode='ranged' AND weight_min IS NOT NULL AND weight_min <= weight_max)
```

**ตัวอย่าง field_schema**

| section | field_schema |
|---|---|
| 1.1 | `{"hours":{"type":"int","required":true},"student_count":{"type":"int","required":true}}` |
| 2.3.1 | `{"quartile":{"type":"enum","values":["Tier1","Q1","Q2","Q3","Q4","none"]}}` |
| 2.8.1 | `{"budget":{"type":"money","required":true}}` |

---

## กลุ่ม C — ข้อมูลที่กรอก

### evaluation_round

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | smallint PK | |
| rubric_version_id | FK rubric_version | ล็อกเกณฑ์ของรอบ |
| name_th | varchar(100) | |
| period_start / period_end | date | ช่วงผลงาน |
| salary_effective_on | date | คนละวันกับ period_end |
| academic_year | smallint | |
| semester | smallint NULL | |
| submit_due_at | timestamptz NULL | |
| is_open | boolean | สวิตช์เปิด/ปิดการกรอก |

**ข้อมูล**

| id | rubric_version_id | name_th | period_start | period_end | salary_effective_on | academic_year | semester | is_open |
|---|---|---|---|---|---|---|---|---|
| 3 | 1 | รอบ 1/2568 | 2025-01-01 | 2025-06-30 | 2025-10-01 | 2567 | 2 | true |

### submission

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | uuid PK | |
| round_id | FK evaluation_round | **UNIQUE(round_id, member_id)** |
| member_id | FK faculty_member | |
| status | enum submission_status | draft, submitted, assessing, dept_review, returned, dept_approved, sent_to_faculty |
| rank_snapshot | enum academic_rank | สำเนาตอนส่ง |
| department_snapshot | FK department | สำเนาตอนส่ง |
| teaching_credits | numeric(6,2) | ต้อง ≥ 6 |
| raw_total | numeric(8,2) | |
| capped_total | numeric(8,2) | |
| submitted_at | timestamptz NULL | |
| created_at / updated_at | timestamptz | |

**ข้อมูล**

| id | round_id | member_id | status | rank_snapshot | dept_snapshot | teaching_credits | raw_total | capped_total | submitted_at |
|---|---|---|---|---|---|---|---|---|---|
| 8c1f | 3 | a3f8 | dept_approved | asst_prof | 1 | 9.00 | 1590.0 | 1430.0 | 2025-07-10 09:15 |
| 9d2a | 3 | b7d1 | dept_review | assoc_prof | 1 | 6.00 | 1120.0 | 1120.0 | 2025-07-11 16:40 |

### submission_entry

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | uuid PK | |
| submission_id | FK submission | ON DELETE CASCADE |
| item_id | FK rubric_item | รู้ section/category ต่อได้ ไม่เก็บซ้ำ |
| title | varchar(500) NULL | ชื่อเรื่อง/โครงการ/นักศึกษา |
| course_code | varchar(15) NULL | text เฉย ๆ ไม่มีตาราง course |
| section_no | varchar(10) NULL | |
| student_count | integer NULL | ตัวกำหนดน้ำหนัก ยกเป็นคอลัมน์จริง |
| data_source | enum | manual / registrar / registrar_edited |
| synced_at | timestamptz NULL | |
| quantity | numeric(8,2) | |
| participation_pct | numeric(5,2) | default 100 |
| weight_applied | numeric(8,4) NULL | NULL ระหว่างรอผู้ประเมิน |
| credits | numeric(5,2) NULL | |
| score | numeric(8,2) | |
| details | jsonb NULL | |
| note | text NULL | |
| sort_order | smallint | |
| created_at / updated_at | timestamptz | |

**ข้อมูล** — ฟอร์มของประภาพร 24 แถว

| id | item | ข้อ | title | course | นศ. | qty | part% | weight | credits | score | details |
|---|---|---|---|---|---|---|---|---|---|---|---|
| e001 | 1 | 1.1 | NULL | CS222 | 60 | 3 | 100 | 1.0 | 3.0 | 200 | hours 45 |
| e002 | 1 | 1.1 | NULL | CS232 | 45 | 3 | 100 | 1.0 | 3.0 | 200 | hours 45 |
| e003 | 1 | 1.1 | NULL | CS333 | 38 | 3 | 100 | 1.0 | 3.0 | 200 | hours 45 |
| e004 | 10 | 1.4 | NULL | CS403 | NULL | 1 | 100 | 0.2 | NULL | 40 | NULL |
| e005 | 11 | 1.4 | NULL | CS403 | NULL | 1 | 100 | 0.05 | NULL | 10 | NULL |
| e006 | 10 | 1.4 | NULL | CS303 | NULL | 1 | 100 | 0.2 | NULL | 40 | NULL |
| e007 | 13 | 1.5 | NULL | CS304 | NULL | 3 | 100 | 0.2 | NULL | 120 | NULL |
| e008 | 14 | 1.9 | จรัลชัย ศรีสวัสดิ์ | CS800 | NULL | 2 | 100 | 0.1 | NULL | 40 | NULL |
| e009 | 14 | 1.9 | ปรีชา เสาแบน | CS800 | NULL | 3 | 100 | 0.1 | NULL | 60 | NULL |
| e010 | 14 | 1.9 | กฤษณพล ไพเราะห์ | CS800 | NULL | 6 | 100 | 0.1 | NULL | 120 | NULL |
| e011 | 25 | 2.3.1 | Preserving Privacy | NULL | NULL | 1 | **20** | 1.25 | NULL | 50 | quartile none |
| e012 | 26 | 2.4.1 | Preserving Privacy | NULL | NULL | 1 | **20** | 0.75 | NULL | 30 | NULL |
| e013 | 26 | 2.4.1 | Identifying Key Fac | NULL | NULL | 1 | **20** | 0.75 | NULL | 30 | NULL |
| e014 | 26 | 2.4.1 | A Robustness Study | NULL | NULL | 1 | **20** | 0.75 | NULL | 30 | NULL |
| e015 | 30 | 3.3 | NULL | CS222 | NULL | 1 | 100 | 0.05 | NULL | 10 | NULL |
| e016 | 31 | 3.3 | NULL | CS232 | NULL | 1 | 100 | 0.10 | NULL | 20 | NULL |
| e017 | 30 | 3.3 | NULL | CS333 | NULL | 1 | 100 | 0.05 | NULL | 10 | NULL |
| e018 | 32 | 3.5 | NULL | NULL | NULL | 1 | 100 | 0.125 | NULL | 25 | NULL |
| e019 | 32 | 3.5 | NULL | NULL | NULL | 1 | 100 | 0.125 | NULL | 25 | NULL |
| e020 | 41 | 4.1.1 | ปรับปรุงหลักสูตร 2570 | NULL | NULL | 1 | 100 | 0.05 | NULL | 10 | NULL |
| e021 | 40 | 4.1.1 | บริหารสหกิจ 2567 | NULL | NULL | 1 | 100 | 0.075 | NULL | 15 | NULL |
| e022 | 43 | 4.2.1 | InCIT2025 Program Com | NULL | NULL | 1 | 100 | 0.05 | NULL | 10 | NULL |
| e023 | 44 | 4.3 | SEAIP Invited Talk | NULL | NULL | 1 | 100 | 0.075 | NULL | 15 | NULL |
| e024 | 45 | 4.4 | CENTRA8 Project 5 | NULL | NULL | 1 | 100 | 0.075 | NULL | 15 | NULL |

ทุกแถว `data_source = manual` และ `synced_at = NULL` เพราะยังไม่ต่อ API ทะเบียน

ไม่ใช้ soft delete — ลบได้เฉพาะตอน `status = draft`

```sql
CHECK participation_pct > 0 AND participation_pct <= 100
CHECK quantity > 0 AND score >= 0
```

### entry_assessment

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | uuid PK | |
| entry_id | FK submission_entry | ON DELETE CASCADE |
| assessor_id | FK faculty_member | **UNIQUE(entry_id, assessor_id)** |
| position_used | enum position_code | snapshot สิทธิ์ที่ใช้ |
| value_given | numeric(8,4) | ต้องอยู่ในช่วงของ item |
| comment | text NULL | |
| assessed_at | timestamptz | |

**ข้อมูล — แบบ single (ข้อ 3.2 หัวหน้าสาขาให้คนเดียว ช่วง 50-100 เป็นคะแนนตรง)**

| entry_id | assessor_id | ชื่อ | position_used | value_given | comment | assessed_at |
|---|---|---|---|---|---|---|
| e030 | b7d1 | สมชาย | dept_chair | 85 | ช่วยงานหลักสูตรดีมาก | 2025-07-15 10:00 |

ผลลัพธ์: `weight_applied = NULL`, `score = 85` เพราะ range_basis เป็น points

**ข้อมูล — แบบ average (ข้อ 3.1 กรรมการบริหารหลายคน ช่วง 1.0-2.0 เป็นน้ำหนัก)**

| entry_id | assessor_id | ชื่อ | position_used | value_given | assessed_at |
|---|---|---|---|---|---|
| e031 | c2e9 | วิไล | exec_committee | 1.8 | 2025-07-15 10:05 |
| e031 | d4a7 | สมหญิง | exec_committee | 1.5 | 2025-07-15 11:20 |
| e031 | e8b3 | ประเสริฐ | exec_committee | 1.6 | 2025-07-16 09:40 |

ผลลัพธ์: เฉลี่ย 1.6333 → `weight_applied = 1.6333`, `score = 1 × 1.6333 × 200 = 326.67`

แยกตารางเพราะ: ผู้ประเมินมีได้หลายคน, อาจารย์เจ้าของฟอร์มต้องแก้ไม่ได้, ต้องมี audit trail

### entry_evidence

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | uuid PK | |
| entry_id | FK submission_entry | ON DELETE CASCADE |
| ref_code | varchar(50) NULL | รหัสจากระบบ wolf |
| label | varchar(255) NULL | |
| s3_key | varchar(512) UNIQUE | ไม่เก็บ bucket/region — เป็น config |
| file_name | varchar(255) | ชื่อเดิมของผู้ใช้ |
| mime_type | varchar(100) | |
| size_bytes | bigint | |
| checksum | char(64) NULL | SHA-256 |
| status | enum | pending / uploaded |
| uploaded_by | FK faculty_member | |
| created_at | timestamptz | |

**ข้อมูล** — บทความ Preserving Privacy ต้องแนบ 3 ใบ

| entry_id | ref_code | label | s3_key | file_name | mime_type | size_bytes | status |
|---|---|---|---|---|---|---|---|
| e011 | RG301-2025-000076 | หน้าแรกบทความ | subm/8c1f/e011/a7f3.pdf | preserving-privacy.pdf | application/pdf | 842113 | uploaded |
| e011 | NULL | Quartile จาก Scimago | subm/8c1f/e011/b2c8.pdf | scimago-q.pdf | application/pdf | 115004 | uploaded |
| e011 | NULL | ใบรับรองสัดส่วน 20% | subm/8c1f/e011/c9d1.pdf | share-cert.pdf | application/pdf | 230551 | uploaded |
| e021 | คำสั่งที่ 112/2567 | คำสั่งแต่งตั้ง | subm/8c1f/e021/d5e2.pdf | order-112.pdf | application/pdf | 98220 | uploaded |
| e023 | NULL | หนังสือเชิญ | subm/8c1f/e023/f8a9.pdf | seaip-invite.pdf | application/pdf | 0 | **pending** |

แถวสุดท้ายคือกรณีที่ออก presigned URL แล้วแต่ยังอัปโหลดไม่เสร็จ ต้องมี job กวาดแถว pending ค้างเกิน 24 ชม.

---

## กลุ่ม D — ผลสรุปและลายเซ็น

### submission_category_total

**โครงสร้าง**

| คอลัมน์ | ชนิด |
|---|---|
| submission_id | FK submission, PK ร่วม |
| category_id | FK rubric_category, PK ร่วม |
| raw_score | numeric(8,2) |
| capped_score | numeric(8,2) |

**ข้อมูล**

| submission_id | category_id | หมวด | raw_score | capped_score | หายไป |
|---|---|---|---|---|---|
| 8c1f | 1 | งานสอน | 1030.0 | 900.0 | **130** |
| 8c1f | 2 | งานวิชาการ | 140.0 | 140.0 | 0 |
| 8c1f | 3 | งานบริหาร | 90.0 | 90.0 | 0 |
| 8c1f | 4 | บริการวิชาการ | 330.0 | 300.0 | **30** |
| 8c1f | 5 | คะแนนพิเศษ | 0.0 | 0.0 | 0 |
| | | **รวม** | **1590.0** | **1430.0** | 160 |

เขียนครั้งเดียวตอน submit แล้วห้ามแตะ ผ่านเกณฑ์ขั้นต่ำ 650

### submission_approval

**โครงสร้าง**

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| id | uuid PK | |
| submission_id | FK submission | |
| signer_id | FK faculty_member | |
| role | enum signer_role | performer, receiver, dept_chair, dept_committee |
| decision | enum | approved / returned |
| comment | text NULL | |
| signed_at | timestamptz | |

**ข้อมูล** — append-only ไม่มี UPDATE ไม่มี DELETE

| signer_id | ชื่อ | role | decision | comment | signed_at |
|---|---|---|---|---|---|
| a3f8 | ประภาพร | performer | approved | NULL | 2025-07-10 09:15 |
| f1c2 | ธุรการคณะ | receiver | approved | NULL | 2025-07-10 14:30 |
| b7d1 | สมชาย | dept_chair | **returned** | ข้อ 2.3.1 ขาดเอกสาร Quartile | 2025-07-14 11:00 |
| a3f8 | ประภาพร | performer | approved | แนบเพิ่มแล้ว | 2025-07-16 10:20 |
| b7d1 | สมชาย | dept_chair | approved | NULL | 2025-07-18 09:00 |
| c2e9 | วิไล | dept_committee | approved | NULL | 2025-07-18 09:30 |

---

## Index เพิ่มเติม

```sql
CREATE INDEX CONCURRENTLY idx_entry_details
  ON submission_entry USING GIN (details);

CREATE INDEX CONCURRENTLY idx_position_active
  ON member_position (department_id, position) WHERE end_date IS NULL;

CREATE INDEX CONCURRENTLY idx_submission_draft
  ON submission (member_id) WHERE status = 'draft';
```

## Composite FK กันข้ามฉบับเกณฑ์

โครงสร้างมีสองเส้นทางไปถึง rubric_version ต้องบังคับให้ไปจบที่ฉบับเดียวกัน

```sql
ALTER TABLE rubric_category ADD UNIQUE (id, version_id);

ALTER TABLE rubric_section ADD COLUMN version_id smallint NOT NULL,
  ADD FOREIGN KEY (category_id, version_id) REFERENCES rubric_category(id, version_id);
ALTER TABLE rubric_section ADD UNIQUE (id, version_id);

ALTER TABLE rubric_item ADD COLUMN version_id smallint NOT NULL,
  ADD FOREIGN KEY (section_id, version_id) REFERENCES rubric_section(id, version_id);
ALTER TABLE rubric_item ADD UNIQUE (id, version_id);

ALTER TABLE submission ADD COLUMN rubric_version_id smallint NOT NULL,
  ADD UNIQUE (id, rubric_version_id);

ALTER TABLE submission_entry ADD COLUMN rubric_version_id smallint NOT NULL,
  ADD FOREIGN KEY (submission_id, rubric_version_id)
      REFERENCES submission(id, rubric_version_id),
  ADD FOREIGN KEY (item_id, rubric_version_id)
      REFERENCES rubric_item(id, version_id);
```

## Trigger ที่ต้องมี

- บล็อก INSERT / UPDATE / DELETE บน `submission_entry` และ `entry_evidence` เมื่อ `submission.status <> 'draft'`
- บล็อก UPDATE / DELETE บน `submission_category_total` และ `submission_approval` ทั้งหมด

## Query ตัวอย่าง

```sql
-- รวมคะแนนรายข้อย่อยพร้อมตัดเพดาน
SELECT s.code, s.name_th,
       SUM(e.score) AS raw_score,
       LEAST(SUM(e.score), COALESCE(s.cap, 1e9)) AS capped_score
FROM submission_entry e
JOIN rubric_item    i ON i.id = e.item_id
JOIN rubric_section s ON s.id = i.section_id
WHERE e.submission_id = '8c1f…'
GROUP BY s.id, s.code, s.name_th, s.cap
ORDER BY s.sort_order;

-- เช็คเงื่อนไขหน่วยกิตสอน >= 6
SELECT COALESCE(SUM(e.credits), 0) AS teaching_credits
FROM submission_entry e
JOIN rubric_item i ON i.id = e.item_id
WHERE e.submission_id = '8c1f…' AND i.counts_teaching_credit;

-- หาผู้มีสิทธิ์ประเมินหมวด 3 ของอาจารย์คนนี้ในรอบนี้
SELECT mp.member_id
FROM member_position mp
JOIN rubric_item i ON i.assessor_position = mp.position
WHERE i.id = 52
  AND mp.department_id = 1
  AND mp.start_date <= '2025-06-30'
  AND (mp.end_date IS NULL OR mp.end_date >= '2025-01-01');
```

## ลำดับสร้างและ seed

```
department → faculty_member → member_position
→ rubric_version → rubric_category → rubric_section → rubric_item
→ evaluation_round → เปิด is_open
```
