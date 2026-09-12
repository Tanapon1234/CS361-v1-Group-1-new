# [V2] Final Integration / Deploy / Demo Docs #81

## สรุป

รวมงาน V2 ทั้งหมดให้พร้อม demo/deploy โดยตรวจ public repository, admin pilot, database state, AWS foundation, V1 compatibility และเอกสารปิดงาน

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #67 แต่ GitHub issue จริงใช้ #81

## Background

V2 จะถือว่าพร้อมส่งเมื่อทีมพิสูจน์ได้ว่า:

- V1 เดิมยังใช้ได้
- V2 public repository ค้นหา/กรอง/ดู detail ได้
- Admin pilot login และจัดการ work item ได้
- Aurora/Data API/Secrets/IAM foundation ใช้งานได้
- มี demo dataset และ docs ให้คนอื่น run/check ต่อได้

การ์ดนี้เป็น integration gate ไม่ใช่ที่สำหรับเพิ่ม feature ใหม่ก้อนใหญ่

## เป้าหมาย

ทำ final verification และเอกสารส่งมอบ V2:

- run tests/checks หลัก
- deploy หรือเตรียม deployment ตาม environment ที่ทีมเลือก
- เก็บ evidence/screenshots/links
- เขียน demo script
- เขียน issue closing comments template
- ยืนยัน deferred/non-goals ไม่ถูกนับเป็น blocker

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง feature ใหม่ที่ไม่อยู่ในการ์ดก่อนหน้า
- ทำ V3 Secure Faculty Workspace
- ทำ official workload scoring/report
- ทำ production-grade monitoring ครบทุกมิติ
- ทำ data migration จากข้อมูลจริงทั้งหมด

## Scope

### ต้องทำ

- ตรวจ V1 regression
- ตรวจ V2 public repository flow:
  - `/outputs`
  - search/filter/list
  - `/outputs/{id}`
- ตรวจ Admin pilot flow:
  - `/admin/login`
  - `/admin/work-items`
  - create/edit/soft delete/restore ถ้าเปิดใช้
- ตรวจ database state/counts
- ตรวจ AWS foundation:
  - Aurora/Data API
  - Secrets Manager
  - Lambda roles
  - CloudWatch log groups
  - S3 buckets ที่เกี่ยวข้อง
- run automated tests เท่าที่มี
- บันทึก known limitations และ deferred V3/V4 items
- เพิ่ม final demo docs หรือ update `docs/v2/README.md`
- เตรียม closing comment สำหรับ GitHub issues หลัก

### ไม่ต้องทำ

- rewrite architecture
- change schema โดยไม่มี migration card
- add new auth roles/workflows

## Final Demo Checklist

Public:

- [ ] `/faculties` ยังเปิดได้
- [ ] `/faculties/{slug}` ยังเปิดได้
- [ ] `/outputs` เปิดได้
- [ ] search/filter ด้วย demo cases ได้
- [ ] `/outputs/{id}` detail เปิดได้
- [ ] restricted/internal data ไม่โผล่ public

Admin:

- [ ] admin login ได้
- [ ] admin list เปิดได้
- [ ] create work item ได้
- [ ] edit work item ได้
- [ ] soft delete แล้ว public ไม่เห็น
- [ ] restore ได้ถ้า route เปิดใช้

Cloud/Data:

- [ ] Aurora มี tables/schema ถูกต้อง
- [ ] master data seed มีข้อมูล
- [ ] demo fixture data มี counts ตาม expected
- [ ] Data API query ได้
- [ ] secrets ไม่เปิดใน repo/docs
- [ ] CloudWatch logs มี log groups ที่ expected

## Acceptance Criteria

- [ ] full V2 happy path demo ผ่าน
- [ ] V1 compatibility checks ผ่าน
- [ ] public visibility/redaction checks ผ่าน
- [ ] admin auth/CRUD checks ผ่าน
- [ ] database verification ผ่าน
- [ ] docs สำหรับ run/check/demo อัปเดต
- [ ] known limitations ถูกบันทึก
- [ ] มี evidence พร้อมใช้ปิด GitHub issues

## Review Checklist

Tech Lead:

- [ ] ไม่มี feature scope ใหม่แอบเข้ามาใน final integration
- [ ] blockers ที่เหลือถูกจัดเป็น known limitation หรือ follow-up ชัดเจน

QA:

- [ ] test evidence ครบ public/admin/data
- [ ] manual demo script ทำตามได้

Security:

- [ ] secret/ARN sensitive value ไม่ถูกเปิดเกินจำเป็น
- [ ] admin-only data ไม่แสดง public
- [ ] V1 compatibility ไม่เปิดข้อมูลใหม่ผิด boundary

Documentation:

- [ ] README/index ชี้ไฟล์ล่าสุด
- [ ] closing comment template พร้อม
- [ ] deployment/check instructions อ่านแล้วทำตามได้

## Dependencies

Blocked by:

- #75 Integrate Repository UI with Real API
- #79 Integrate Admin UI with Auth & CRUD API
- #80 Execute Migration & Preserve V1 Compatibility

Related:

- #46 Freeze Scope, Architecture & Interface Contracts
- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset

## Suggested Labels

- `v2`
- `integration`
- `deploy`
- `qa`
- `documentation`

## Suggested Owner

Tech Lead / Integration Owner

Reviewers:

- Backend Developer
- Frontend Developer
- Cloud Developer
- QA / Integration
- Security Reviewer

## Estimate

1-2 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มีหลักฐานว่า public repository, admin pilot, database, AWS foundation และ V1 compatibility ทำงานร่วมกันได้ครบตาม scope ที่ freeze ไว้ พร้อมเอกสาร demo/deploy/check สำหรับส่งงานและปิดชุด V2
