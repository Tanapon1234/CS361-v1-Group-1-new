# [V2] Define V1 to V2 Data Mapping

## สรุป

กำหนด mapping จากข้อมูล V1 เดิมเข้าสู่ V2 relational repository ให้ชัดเจนก่อนทำ migration/import จริง

การ์ดนี้เป็นสะพานระหว่าง V1 public faculty dataset กับ V2 repository schema โดยต้องตอบให้ได้ว่า field จาก V1 เช่น faculty profile, education, research interests, expertise, selected publications และ publication profiles จะถูก map ไป table/field ใดใน V2 และต้องรักษา `public_slug` เดิมอย่างไรเพื่อไม่ให้ V1 public URL พัง

## Implementation Status

Status: Ready for review / ready to close

Implemented artifacts:

- `docs/v2/v1-to-v2-mapping.md`
- `data/v2/mappings/v1-to-v2-field-mapping.csv`
- `docs/v2/README.md` links both the human-readable mapping document and the field-level CSV

Important scope note:

- This card maps V1 public faculty data only.
- It intentionally does not execute database migration and does not insert records into Aurora.
- It intentionally does not map the workload form PDF; workload-form import belongs to later demo dataset / migration cards.

## Background

V1 ปัจจุบันมีข้อมูล public-safe อยู่ใน:

```text
data/v1/source/faculty_profiles.json
build/v1/serving/faculties.json
build/v1/serving/faculties/{id}.json
fixtures/v1/
```

V1 contract หลัก:

- faculty list
- faculty detail
- public slug เป็น `id`
- public profile fields
- education
- research interests
- expertise
- selected publications
- external academic profiles

V2 จะย้ายข้อมูลเหล่านี้เข้า relational repository โดยต้องไม่ทำให้ V1 public experience เดิมพัง

การ์ดนี้ไม่ใช่ migration runner แต่เป็นการ freeze mapping rule เพื่อให้  demo dataset,  migration และ public projection ทำงานบนกติกาเดียวกัน

## เป้าหมาย

จัดทำ V1 to V2 mapping ที่ทีมใช้ implement migration และ compatibility checks ได้

ผลลัพธ์ของการ์ดนี้ต้องตอบได้ว่า:

- V1 field แต่ละ field ไปลง V2 table/column ไหน
- field ไหน required / optional
- missing/null/empty value จัดการอย่างไร
- V1 faculty `id` จะถูก preserve เป็น `faculty.public_slug` อย่างไร
- V1 selected publications จะกลายเป็น `work_item` + `publication_detail` + `faculty_work_item` อย่างไร
- V1 research interests/expertise จะ map ไป `faculty_interest` อย่างไร
- V1 education จะ map ไป `faculty_education` อย่างไร
- public visibility จะกำหนดอย่างไร
- ข้อมูลใดไม่ควร migrate หรือควรเก็บเป็น evidence/reference/provenance
- ต้องใช้ test case อะไรเพื่อยืนยันว่า V1 compatibility ไม่พัง

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- เขียน migration runner จริง
- เขียน import pipeline จริง
- insert ข้อมูลเข้า Aurora จริง
- สร้าง public projection จริง
- แก้ frontend V1
- แก้ Lambda V1
- แก้ schema จาก #47 ยกเว้นพบ gap แล้วเสนอ feedback
- map workload form PDF ทั้งหมดเข้าสู่ V2 demo dataset
- สร้าง multi-year synthetic dataset

งานเหล่านี้อยู่ในการ์ด #50 และ #66

## Scope

### ต้องทำ

- inventory V1 source/serving fields
- เขียน V1 to V2 mapping table
- ระบุ required/optional/missing rules
- ระบุ visibility mapping
- ระบุ publication mapping
- ระบุ education mapping
- ระบุ research interest / expertise mapping
- ระบุ external profile mapping
- ระบุ provenance/source metadata mapping
- ระบุ V1 compatibility test cases
- ระบุ open questions หรือ field gaps ที่ต้องตัดสินใจก่อน #66
### ไม่ต้องทำ

- execute migration
- create actual DB records
- provision database
- build API
- build UI

## Input Sources

ใช้แหล่งข้อมูลต่อไปนี้เป็นฐาน:

```text
data/v1/source/faculty_profiles.json
data/v1/source/source-metadata.json
build/v1/serving/faculties.json
build/v1/serving/faculties/*.json
build/v1/metadata/manifest.json
build/v1/metadata/preparation-summary.json
docs/v1/V1_Final_Documentation_Architecture_Decisions_Demo_Evidence.md
```

ถ้าใช้ไฟล์อื่นเพิ่มเติม ต้องระบุไว้ในเอกสาร mapping

## Required Mapping Output

ต้องสร้างเอกสาร mapping อย่างน้อย:

```text
docs/v2/v1-to-v2-mapping.md
data/v2/mappings/v1-to-v2-field-mapping.csv
```

ถ้าทีมเลือกชื่อไฟล์อื่น ต้อง link จาก `docs/v2/README.md`

## Mapping Overview

Baseline mapping:

```text
V1 Faculty
→ faculty

V1 Education
→ faculty_education

V1 Research Interests
→ faculty_interest(type = RESEARCH_INTEREST)

V1 Expertise
→ faculty_interest(type = EXPERTISE)

V1 Selected Publications
→ work_item
 + publication_detail
 + faculty_work_item

V1 Publication Profiles
→ evidence_reference หรือ external profile model ตาม schema ที่ freeze

V1 Dataset Metadata
→ import_batch / source_record / repository metadata
```

## Mapping Rules

### Faculty Identity

V1 `id` ต้อง preserve เป็น:

```text
faculty.public_slug
```

ตัวอย่าง:

```text
V1 id: prapaporn-rattanatamrong
V2 faculty.public_slug: prapaporn-rattanatamrong
```

Rule สำคัญ:

- ห้าม generate slug ใหม่แทน V1 id เดิม
- ถ้า V1 id ซ้ำ ต้อง fail/hold migration ไม่ใช่แก้เงียบ ๆ
- ถ้า V1 id ผิด format ต้องบันทึกเป็น mapping error

### Faculty Profile

V1 fields:

- `id`
- `name.th`
- `name.en`
- `academic_position`
- `contact.office`
- `contact.phone`
- `contact.extension`
- `contact.email`
- `profile_image.url`
- `profile_image.alt`
- `badges`
- `cv`

ควร map ไป:

- `faculty.public_slug`
- `faculty.name_th`
- `faculty.name_en`
- `faculty.academic_position`
- `faculty.office_public`
- `faculty.phone_public`
- `faculty.email_public`
- `faculty.profile_image_url`
- evidence/reference table สำหรับ `cv` หรือ `badges` ถ้า schema รองรับ

Missing rule:

- ต้องมีอย่างน้อยชื่อไทยหรือชื่ออังกฤษ
- optional public contact ถ้าว่างให้เป็น null
- invalid email/url ต้องไม่ migrate แบบเงียบ ให้บันทึก warning/error ตาม severity ที่ตกลง

### Faculty Education

V1 `education[]` map ไป:

```text
faculty_education
```

field ที่ควรพิจารณา:

- degree
- field
- institution
- country
- graduation_year
- additional_information
- sort_order
- visibility

Rule:

- preserve order จาก V1
- missing optional field เป็น null
- default visibility เป็น `PUBLIC` ถ้ามาจาก V1 public serving data

### Research Interests / Expertise

V1 `research_interests[]` map ไป:

```text
faculty_interest.interest_type = RESEARCH_INTEREST
```

V1 `expertise[]` map ไป:

```text
faculty_interest.interest_type = EXPERTISE
```

Rule:

- preserve text ไม่ rewrite ความหมาย
- trim whitespace
- dedupe exact/casefold duplicate
- preserve order ด้วย `sort_order`
- default visibility เป็น `PUBLIC`

### Selected Publications

V1 `selected_publications[]` ต้อง map เป็น repository work item

ขั้นต่ำ:

```text
work_item
  category_code = RESEARCH
  work_type = PUBLICATION
  visibility = PUBLIC

publication_detail
  publication_title
  authors
  publication_year
  venue
  volume
  issue
  pages
  doi
  url
  citation_text

faculty_work_item
  faculty_id
  work_item_id
  role/contribution if known
```

Rule:

- DOI ถ้ามี ใช้เป็น duplicate key ลำดับแรก
- ถ้าไม่มี DOI ใช้ normalized title + year
- ถ้า publication year ไม่มี ให้บันทึก warning แต่ไม่เดาปี
- ถ้า authors เป็น string/list ต้องกำหนด normalization rule
- source citation text ควร preserve เพื่อ traceability
- default visibility เป็น `PUBLIC` เพราะมาจาก V1 public serving data

### External Academic Profiles

V1 `publication_profiles[]` เช่น Google Scholar / ResearchGate

ต้องตัดสินใจใน mapping ว่าจะเก็บเป็น:

- `evidence_reference`
- หรือ table/field external profile เฉพาะ ถ้า schema มี

ถ้าใช้ `evidence_reference`:

- `reference_type = EXTERNAL_PROFILE`
- `reference_label = provider`
- `external_url = url`
- `visibility = PUBLIC`

Rule:

- provider required
- URL ต้อง validate
- invalid URL ให้ warning/error ตาม severity ที่ตกลง

### Badges / CV / Profile Assets

ต้องระบุ mapping สำหรับ:

- `profile_image`
- `badges`
- `cv`

Baseline:

- `profile_image.url` เข้า `faculty.profile_image_url`
- `cv.url` เข้า `evidence_reference` หรือ external reference
- `badges[]` เข้า `evidence_reference` หรือ deferred ถ้า schema ยังไม่รองรับ

ถ้า field ใด deferred ต้องบันทึกชัดเจนว่าไม่หาย แต่ยังไม่ migrate ใน V2 baseline

### Source Metadata / Provenance

V1 dataset metadata ควร map ไป:

```text
import_batch
source_record
```

Rule:

- record ต้อง trace ได้ว่ามาจาก V1 source snapshot หรือ V1 serving JSON
- ต้องมี source name/version/date ถ้ามี
- ต้องมี source hash ถ้า migration/import ต้องการ idempotency

## Required Mapping Table Columns

CSV mapping ควรมี columns อย่างน้อย:

```text
v1_source_file
v1_json_path
v1_example
v2_table
v2_column
required_level
visibility
transform_rule
missing_rule
validation_rule
notes
```

ตัวอย่าง:

```text
build/v1/serving/faculties/{id}.json,id,prapaporn-rattanatamrong,faculty,public_slug,required,PUBLIC,preserve as-is,fail if missing,slug format,Must not regenerate
```

## Compatibility Test Cases

ต้องนิยาม test cases อย่างน้อย:

- V1 faculty count เท่ากับจำนวน faculty ที่ migrate
- V1 `id` ทุกตัวมีอยู่ใน `faculty.public_slug`
- slug เดิมยังใช้ lookup ได้
- faculty name จาก V1 list/detail ตรงกับ V2 projection
- education count ต่อ faculty ไม่หาย
- research interests ไม่หาย
- expertise ไม่หาย
- selected publications ไม่หาย
- DOI ไม่ duplicate
- public-only data ไม่กลายเป็น internal โดยไม่ตั้งใจ
- internal/restricted fields ไม่ถูกสร้างจาก V1 public data แบบผิดประเภท

## Expected Deliverables

ต้องมี:

```text
docs/v2/v1-to-v2-mapping.md
data/v2/mappings/v1-to-v2-field-mapping.csv
```

เอกสารควรครอบคลุม:

- mapping overview
- field-by-field mapping
- transform rules
- missing value rules
- validation rules
- visibility rules
- duplicate handling
- compatibility test cases
- open questions

## Acceptance Criteria

- [x] inventory V1 source/serving fields ครบ
- [x] mapping จาก V1 faculty ไป `faculty` ชัดเจน
- [x] mapping จาก V1 education ไป `faculty_education` ชัดเจน
- [x] mapping จาก V1 research interests ไป `faculty_interest` ชัดเจน
- [x] mapping จาก V1 expertise ไป `faculty_interest` ชัดเจน
- [x] mapping จาก V1 selected publications ไป `work_item` ชัดเจน
- [x] mapping จาก V1 selected publications ไป `publication_detail` ชัดเจน
- [x] mapping จาก V1 selected publications ไป `faculty_work_item` ชัดเจน
- [x] mapping สำหรับ publication profiles ชัดเจน
- [x] mapping สำหรับ CV/profile image/badges ชัดเจน หรือระบุ deferred ชัดเจน
- [x] mapping สำหรับ source metadata/provenance ชัดเจน
- [x] ระบุ required/optional ของ field สำคัญแล้ว
- [x] ระบุ missing/null/empty rules แล้ว
- [x] ระบุ validation rules แล้ว
- [x] ระบุ visibility mapping แล้ว
- [x] ระบุ duplicate publication rule แล้ว
- [x] ระบุว่า V1 `id` ต้อง preserve เป็น `faculty.public_slug`
- [x] ระบุ compatibility test cases แล้ว
- [x] open questions ถูกบันทึกพร้อม owner/decision needed
- [x] เอกสารพร้อมให้ #66 ใช้ทำ migration

## Review Checklist

Data / Database:

- [x] mapping สอดคล้องกับ schema จาก #47
- [x] field required/optional เหมาะสม
- [x] transform rules ไม่ทำให้ข้อมูลเสียความหมาย
- [x] duplicate rules ใช้ได้จริง

Backend:

- [x] mapping รองรับ API list/detail/search ในอนาคต
- [x] `public_slug` ใช้ lookup ได้
- [x] publication mapping รองรับ detail API ได้

Frontend:

- [x] V1 public fields ที่ frontend ใช้อยู่ยัง projection กลับมาได้
- [x] slug เดิมยังใช้ route เดิมได้
- [x] public display fields ไม่หาย

QA / Integration:

- [x] compatibility tests ตรวจได้
- [x] missing/invalid cases มี expected outcome
- [x] public/internal/restricted rules test ได้

Tech Lead:

- [x] mapping ไม่ขยาย scope ไป V3/V4/V7
- [x] mapping ไม่ผูก schema กับ V1 JSON มากเกินไป
- [x] open questions ถูกบันทึกเป็น field gaps พร้อม owner/decision needed ก่อน #66

## Dependencies

Blocked by:

- #46 Freeze V2 Scope, Architecture & Interface Contracts
- #47 Design Relational Schema & SQL Migration

Blocks:

- #50 Prepare Multi-Year Demo Dataset
- #66 Execute Migration & Preserve V1 Compatibility
- #67 Final Integration / Deploy / Demo Docs

Related:

- #51 Build Master Data API
- #52 Build Work Item List/Search/Filter API
- #53 Build Faculty Work Items API
- #54 Build Work Item Detail API

## Suggested Labels

- `v2`
- `data`
- `mapping`
- `migration`
- `compatibility`
- `blocking`
- `ready-for-review`

## Suggested Owner

Data Developer

Reviewers:

- Tech Lead
- Backend Developer
- Frontend Developer
- QA / Integration

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อทีมมี V1 to V2 mapping ที่ละเอียดพอให้ #66 เขียน migration/seed ได้โดยไม่ต้องเดา field เอง และมี compatibility test cases ที่ชัดเจนพอจะยืนยันว่า V1 public experience ไม่พัง
