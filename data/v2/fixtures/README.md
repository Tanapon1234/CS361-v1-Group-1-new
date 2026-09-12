# V2 Multi-Year Demo Dataset

ชุดข้อมูลนี้เป็น fixture สำหรับ Issue #50 - Prepare Multi-Year Demo Dataset

เป้าหมายคือให้ทีม backend/frontend/QA มีข้อมูลกลางสำหรับทดสอบ V2 repository โดยไม่ต้องรอข้อมูลจริงครบทุกส่วน

## Scope

ชุดข้อมูลนี้ครอบคลุม:

- faculty จาก V1 จริง 3 คน โดย preserve `public_slug`
- academic years 2566, 2567, 2568
- academic periods 5 period
- teaching, research, publication, supervision, academic service, administration
- evidence reference ทั้ง `PUBLIC`, `INTERNAL`, `RESTRICTED`
- many-faculty work item และ contribution percent
- source/provenance metadata สำหรับ migration/import ต่อ

ชุดข้อมูลนี้ยังไม่ใช่:

- official production data
- official workload scoring result
- data ที่ถูก insert เข้า Aurora แล้ว
- automated extraction จาก PDF workload form

## Synthetic Data

ข้อมูล faculty profile มาจาก V1 public serving files จริง

ข้อมูล work item ส่วนใหญ่เป็น synthetic demo data และมี metadata:

```json
"synthetic": true,
"source_system": "SYNTHETIC_TEST_DATA"
```

Publication บางรายการอ้างอิงจาก V1 selected publications และมี metadata:

```json
"source_system": "V1_PUBLIC_FACULTY"
```

## Files

| File | Purpose |
|---|---|
| `faculties.json` | faculty ที่ reuse จาก V1 |
| `academic-periods.json` | academic periods หลายปี |
| `evaluation-periods.json` | evaluation periods สำหรับ filter/report demo |
| `work-categories.json` | work categories ที่ใช้ใน fixture |
| `work-types.json` | work types ที่ใช้ใน fixture |
| `work-items.json` | work item แกนกลางของ repository |
| `faculty-work-items.json` | link faculty กับ work item รวม contribution |
| `teaching-details.json` | subtype detail สำหรับ teaching |
| `publication-details.json` | subtype detail สำหรับ publication |
| `research-project-details.json` | subtype detail สำหรับ research project/grant |
| `supervision-details.json` | subtype detail สำหรับ supervision |
| `service-details.json` | subtype detail สำหรับ academic service |
| `administration-details.json` | subtype detail สำหรับ administration |
| `evidence-references.json` | evidence/reference ตัวอย่าง |
| `dataset-summary.json` | machine-readable validation summary |

## Safety Rules

- ไม่มี secret หรือ credential
- ไม่มี private S3 URL จริง
- S3 keys เป็น placeholder เท่านั้น
- ไม่มีข้อมูลระบุตัวนักศึกษาจริง
- supervision ที่เกี่ยวกับ student-related data ใช้ synthetic code และ visibility `RESTRICTED`

## Usage

สำหรับ implementation ในการ์ดต่อไป:

1. โหลด master files ก่อน: faculty, periods, categories, types
2. โหลด `work-items.json`
3. โหลด detail files ตาม `work_type_code`
4. โหลด `faculty-work-items.json`
5. โหลด `evidence-references.json`
6. ใช้ `dataset-summary.json` เป็น expected count และ smoke-test baseline
