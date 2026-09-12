# [V2] Build Work Item Detail API #68

## สรุป

สร้าง `GET /api/v2/work-items/{id}` สำหรับเรียกดูรายละเอียด work item รายการเดียว รวมข้อมูล faculty, subtype detail และ evidence metadata แบบ public-safe

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #54 แต่ GitHub issue จริงใช้ #68

## Production AWS Requirement

การ์ดนี้ต้อง deploy เป็น production read API จริง:

```text
Amazon API Gateway
→ AWS Lambda query handler
→ Amazon RDS Data API
→ Aurora PostgreSQL Serverless v2
```

fixture/mock ใช้ได้เฉพาะ tests เท่านั้น Detail API ต้องอ่าน core/detail/evidence rows จาก Aurora จริง

## Background

List API แสดงข้อมูลสรุปเท่านั้น แต่ V2 repository ต้องมี detail page ที่อธิบายงานแต่ละรายการ เช่น งานสอน, publication, research project, supervision, service หรือ administration

เนื่องจากรายละเอียดแต่ละ category ไม่เหมือนกัน schema จึงแยก subtype tables:

- `teaching_detail`
- `publication_detail`
- `research_project_detail`
- `supervision_detail`
- `service_detail`
- `administration_detail`

## เป้าหมาย

สร้าง Detail API ที่:

- ดึงข้อมูลกลางจาก `work_item`
- แนบ faculty contributors จาก `faculty_work_item`
- แนบ subtype detail ตาม category/type
- แนบ evidence metadata ที่ public-safe เท่านั้น
- redact/omit field ที่ไม่ควรเปิด public
- ใช้ error/status code ตาม V2 baseline

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- เปิด evidence file download
- ทำ signed URL
- ทำ admin detail response ที่เห็น restricted fields
- ทำ UI detail page
- ทำ official report rendering

## Scope

### ต้องทำ

- implement `GET /api/v2/work-items/{id}`
- join ข้อมูลจาก:
  - `work_item`
  - `work_category`
  - `work_type`
  - `academic_period`
  - `evaluation_period`
  - `faculty_work_item`
  - `faculty`
  - subtype detail table ที่ตรงกับ record
  - `evidence_reference`
- return `detail.kind` ตาม subtype ที่พบ
- evidence response ต้องเป็น metadata/reference เท่านั้น
- เพิ่ม Lambda route/handler สำหรับ `GET /api/v2/work-items/{id}`
- เพิ่ม Data API query layer สำหรับ core row, faculty contributors, subtype detail และ evidence metadata
- configure API Gateway path parameter และ error handling
- เพิ่ม CloudWatch logs สำหรับ work item id, visibility decision และ errors
- add tests สำหรับทุก category ใน demo dataset
- add tests สำหรับ restricted/internal redaction
- เพิ่ม AWS smoke test สำหรับ public detail, not found และ restricted/internal case

### ไม่ต้องทำ

- create/edit/delete
- admin-only detail expansion
- evidence upload/download
- frontend route `/outputs/{id}`

## API Contract

```http
GET /api/v2/work-items/{id}
```

Response:

```json
{
  "id": "wi-pub-2024-privacy-edge",
  "title": "Privacy-preserving edge analytics publication",
  "description": "Publication detail summary",
  "category": "RESEARCH",
  "type": "PUBLICATION",
  "visibility": "PUBLIC",
  "academic_period": {
    "id": "ap_2567_2",
    "label": "2/2567"
  },
  "faculty": [
    {
      "id": "fac_prapaporn",
      "display_name": "ผศ. ดร. ประภาภรณ์ รัตนธรรมรงค์",
      "slug": "prapaporn-rattanatamrong",
      "role": "AUTHOR",
      "contribution_order": 1,
      "contribution_percent": 50
    }
  ],
  "detail": {
    "kind": "publication",
    "publication_title": "Privacy-preserving edge analytics publication",
    "venue": "Example Journal",
    "publication_year": 2567
  },
  "evidence": [
    {
      "id": "ev-pub-2024-doi",
      "label": "DOI",
      "reference_type": "URL",
      "visibility": "PUBLIC"
    }
  ],
  "updated_at": "2026-09-12T00:00:00Z"
}
```

## Visibility Rules

- public route return ได้เฉพาะ `work_item.visibility = PUBLIC` และ `status = ACTIVE`
- `INTERNAL` หรือ `RESTRICTED` records ควร return `404` ใน public route
- evidence ที่ไม่ `PUBLIC` ต้องถูก omit หรือ redact ตาม contract
- source/provenance/audit fields ไม่อยู่ใน public response

## Acceptance Criteria

- [ ] detail endpoint return work item detail ได้
- [ ] subtype detail ถูกเลือกตาม category/type
- [ ] faculty contributors เรียงตาม `contribution_order`
- [ ] public evidence metadata แสดงได้
- [ ] internal/restricted evidence ไม่ leak
- [ ] internal/restricted work item return public-safe error
- [ ] `404` สำหรับ id ที่ไม่มีอยู่
- [ ] มี tests ครอบคลุม subtype หลักทั้งหมดใน V2 demo dataset
- [ ] API Gateway route deploy แล้ว
- [ ] Lambda อ่าน Aurora subtype/evidence tables ผ่าน RDS Data API จริง
- [ ] smoke test ผ่าน AWS endpoint อย่างน้อย public detail, not found และ restricted case

## Review Checklist

Backend:

- [ ] mapper แยก subtype ชัดเจนและเพิ่ม category ใหม่ได้ภายหลัง
- [ ] response ไม่ผูกกับ raw fixture shape
- [ ] query/error path มี request id หรือ log ที่ debug ได้
- [ ] production path ไม่อ่าน fixture file

QA:

- [ ] ตรวจ detail demo cases จาก `docs/v2/demo-dataset.md`
- [ ] ตรวจ restricted supervision record ไม่โผล่ใน public detail

Security:

- [ ] evidence ไม่เปิด storage key/private path ที่ไม่ควร public
- [ ] source/import/audit fields ไม่ออก public response

## Dependencies

Blocked by:

- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API

Blocks:

- #74 Build Work Item Detail UI
- #75 Integrate Repository UI with Real API

Related:

- #50 Prepare Multi-Year Demo Dataset
- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `backend`
- `api`
- `detail`
- `ready-for-agent`

## Suggested Owner

Backend Developer

Reviewers:

- Tech Lead
- Data Developer
- Frontend Developer
- QA / Integration

## Estimate

1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มี Detail API ที่ deploy บน AWS จริงและแสดง work item รายการเดียวจาก Aurora ได้ครบตาม subtype พร้อม faculty, evidence metadata, public-safe redaction, CloudWatch logs และ AWS smoke evidence ที่ทดสอบได้
