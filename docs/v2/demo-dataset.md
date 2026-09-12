# V2 Multi-Year Demo Dataset

เอกสารนี้สรุปชุดข้อมูลตัวอย่างสำหรับ Issue #50 - Prepare Multi-Year Demo Dataset

Dataset หลักอยู่ที่:

- `data/v2/fixtures/`
- `data/v2/fixtures/dataset-summary.json`

Dataset นี้เป็น fixture สำหรับพัฒนาและ demo V2 repository เท่านั้น ยังไม่ถูก insert เข้า Aurora และยังไม่ใช่ official workload report

---

## Dataset Scope

ครอบคลุม:

- faculty จาก V1 จริง 3 คน พร้อม `public_slug` เดิม
- academic years 2566, 2567, 2568
- academic periods 5 period
- teaching, research, publication, supervision, academic service, administration
- evidence reference 8 รายการ
- visibility ครบ `PUBLIC`, `INTERNAL`, `RESTRICTED`
- many-faculty work item และ contribution percent
- source/provenance metadata สำหรับ migration/import ต่อ

ไม่ครอบคลุม:

- automated extraction จาก PDF workload form
- official workload scoring
- official annual report
- production data completeness
- Aurora insert/migration execution

---

## Files

| File | Purpose |
|---|---|
| `faculties.json` | faculty ที่ reuse จาก V1 public serving files |
| `academic-periods.json` | academic periods หลายปี |
| `evaluation-periods.json` | evaluation windows สำหรับ demo |
| `work-categories.json` | category master data subset |
| `work-types.json` | type master data subset |
| `work-items.json` | repository work item หลัก |
| `faculty-work-items.json` | relation ระหว่าง faculty กับ work item |
| `teaching-details.json` | teaching subtype detail |
| `publication-details.json` | publication subtype detail |
| `research-project-details.json` | research project/grant subtype detail |
| `supervision-details.json` | supervision subtype detail |
| `service-details.json` | academic service subtype detail |
| `administration-details.json` | administration subtype detail |
| `evidence-references.json` | evidence/reference examples |
| `dataset-summary.json` | expected count, visibility, and search/filter matrix |

---

## Validation Summary

| Entity | Count |
|---|---:|
| Faculty | 3 |
| Academic years | 3 |
| Academic periods | 5 |
| Evaluation periods | 3 |
| Work categories | 5 |
| Work types | 14 |
| Work items | 18 |
| Faculty work item links | 20 |
| Teaching details | 4 |
| Research project details | 3 |
| Publication details | 3 |
| Supervision details | 3 |
| Service details | 3 |
| Administration details | 2 |
| Evidence references | 8 |

Work item coverage:

| Category | Count |
|---|---:|
| `TEACHING` | 4 |
| `RESEARCH` | 6 |
| `SUPERVISION` | 3 |
| `ACADEMIC_SERVICE` | 3 |
| `ADMINISTRATION` | 2 |

Visibility coverage:

| Visibility | Work items | Evidence |
|---|---:|---:|
| `PUBLIC` | 4 | 3 |
| `INTERNAL` | 12 | 3 |
| `RESTRICTED` | 2 | 2 |

---

## Important Demo Cases

The dataset includes:

- public publication: `wi-pub-2019-multi-container`
- internal teaching record: `wi-teach-2567-2-cs333`
- restricted supervision record: `wi-supervision-2567-phd-thesis`
- many-faculty publication: `wi-pub-2024-privacy-edge`
- many-faculty research project: `wi-research-2567-privacy-platform`
- contribution percent examples: 60/40 and 50/50
- external evidence URL examples: DOI and synthetic public event URLs
- S3 placeholder evidence examples with no real credential
- source section code examples from workload-form-style sections such as `1.1`, `2.3.1`, `4.3`

---

## Search / Filter Matrix

| Query | Expected result |
|---|---|
| Faculty = `prapaporn-rattanatamrong`, Academic Year = `2567` | teaching, publication, research, supervision, service, administration rows |
| Academic Year = `2567`, Category = `TEACHING` | `wi-teach-2567-2-cs333`, `wi-teach-2567-2-cs333-lab` |
| Faculty = `prapaporn-rattanatamrong`, Category = `RESEARCH`, Type = `PUBLICATION` | `wi-pub-2019-multi-container`, `wi-pub-2024-privacy-edge` |
| Academic Year `2566-2568`, Keyword = `privacy` | publication, research project, restricted supervision, public service examples |
| Category = `SUPERVISION`, Degree Level = `PhD` | `wi-supervision-2567-phd-thesis` |
| Faculty = `prapaporn-rattanatamrong`, Year = `2567`, Semester = `2`, Category = `TEACHING` | CS333 lecture and lab rows |

---

## Data Safety

- No secret values are included.
- No real private S3 object is referenced.
- S3 keys are placeholders under `s3://cs361-v2-demo-placeholder/...`.
- No real student identifiers are included.
- Student-related supervision examples use `REDACTED` or `NOT_STORED`.
- Restricted records must not appear in public projection/API responses.

---

## Known Limitations

- Fixture files contain `metadata` for migration planning; a direct SQL seed loader may need to strip those fields or convert them to `import_batch` / `source_record`.
- Publication authors and citation text are not normalized because the #47 schema has no publication-author table and no dedicated `citation_text` column.
- The dataset is intentionally small but covers V2 core query and detail cases.
- This card does not load data into Aurora.
