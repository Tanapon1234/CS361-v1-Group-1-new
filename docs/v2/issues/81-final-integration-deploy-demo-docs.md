# [V2] Final Integration / Deploy / Demo Docs #81

## สรุป

รวมงาน V2 ทั้งหมดให้พร้อมส่งงานจริงบน deployed AWS-connected environment โดยตรวจ public repository, admin pilot, database state, AWS foundation, S3, V1 compatibility และเอกสารปิดงาน

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #67 แต่ GitHub issue จริงใช้ #81

## Production AWS Requirement

การ์ดนี้เป็น final production integration gate ของ V2 ต้องตรวจระบบที่ deploy แล้วจริง:

```text
Deployed frontend
→ Amazon API Gateway public/admin routes
→ AWS Lambda read/admin handlers
→ Amazon RDS Data API
→ Aurora PostgreSQL Serverless v2

Admin flow:
Deployed frontend
→ Amazon Cognito
→ protected API Gateway admin routes
→ Admin Lambda
→ Aurora

Supporting services:
Amazon S3 private buckets
CloudWatch log groups/metrics
IAM roles/policies
Secrets Manager
```

ห้ามปิดการ์ดด้วย local run, mock API, fixture response, หรือ screenshot จากเครื่องอย่างเดียว ต้องมี URL/resource/evidence จาก AWS environment จริงที่ทีมใช้ส่งงาน

## Background

V2 จะถือว่าพร้อมส่งเมื่อทีมพิสูจน์ได้ว่า:

- V1 เดิมยังใช้ได้
- V2 public repository ค้นหา/กรอง/ดู detail ได้
- Admin pilot login และจัดการ work item ได้
- Aurora/Data API/Secrets/IAM/S3 foundation ใช้งานได้
- API Gateway/Lambda/Cognito เชื่อมกันครบตาม production path
- มี demo dataset ใน Aurora และ docs ให้คนอื่น run/check ต่อได้

การ์ดนี้เป็น integration gate ไม่ใช่ที่สำหรับเพิ่ม feature ใหม่ก้อนใหญ่

## เป้าหมาย

ทำ final verification และเอกสารส่งมอบ V2:

- run tests/checks หลัก
- deploy และตรวจ deployed frontend/API/backend ตาม environment ที่ทีมใช้ส่งงาน
- เก็บ evidence/screenshots/links/resource names
- เขียน demo script
- เขียน issue closing comments template
- ยืนยัน deferred/non-goals ไม่ถูกนับเป็น blocker

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง feature ใหม่ที่ไม่อยู่ในการ์ดก่อนหน้า
- ทำ V3 Secure Faculty Workspace
- ทำ official workload scoring/report
- ทำ enterprise-grade monitoring ครบทุกมิติ เช่น alarm ทุก metric, synthetic monitoring, on-call workflow
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
  - API Gateway stages/routes
  - Lambda functions และ execution roles
  - Aurora/Data API
  - Secrets Manager
  - Cognito User Pool/App Client
  - Lambda roles
  - CloudWatch log groups
  - S3 buckets/private object paths ที่เกี่ยวข้อง
  - IAM roles/policies ที่ใช้จริง
- run automated tests เท่าที่มี
- run AWS smoke tests สำหรับ public/admin API paths
- บันทึก deployed frontend URL, API Gateway base URL, Cognito resource ids, Lambda names, CloudWatch log group names, Aurora cluster/database name และ S3 bucket names โดยไม่ใส่ secret value
- บันทึก known limitations และ deferred V3/V4 items
- เพิ่ม final demo docs หรือ update `docs/v2/README.md`
- เตรียม closing comment สำหรับ GitHub issues หลัก

### ไม่ต้องทำ

- rewrite architecture
- change schema โดยไม่มี migration card
- add new auth roles/workflows

## Final Demo Checklist

Public:

- [ ] deployed `/faculties` ยังเปิดได้
- [ ] deployed `/faculties/{slug}` ยังเปิดได้
- [ ] deployed `/outputs` เปิดได้
- [ ] search/filter ด้วย demo cases ผ่าน API Gateway/Lambda/Aurora ได้
- [ ] deployed `/outputs/{id}` detail เปิดได้
- [ ] restricted/internal data ไม่โผล่ public

Admin:

- [ ] admin login ผ่าน Cognito จริงได้
- [ ] admin list เปิดได้โดยส่ง token ไป protected AWS API
- [ ] create work item เขียน Aurora จริงได้
- [ ] edit work item แก้ Aurora จริงได้
- [ ] soft delete แล้ว public ไม่เห็น
- [ ] restore ได้ถ้า route เปิดใช้

Cloud/Data:

- [ ] Aurora มี tables/schema ถูกต้อง
- [ ] master data seed มีข้อมูล
- [ ] demo fixture data มี counts ตาม expected
- [ ] Data API query ได้
- [ ] API Gateway routes ผูก Lambda ถูกต้อง
- [ ] Lambda handlers ใช้ role และ secret ที่ถูกต้อง
- [ ] Cognito auth ใช้กับ admin route จริง
- [ ] S3 private buckets/object paths ที่เกี่ยวข้องตรวจได้และไม่เปิด public access โดยไม่ตั้งใจ
- [ ] secrets ไม่เปิดใน repo/docs
- [ ] CloudWatch logs มี log groups ที่ expected

## Acceptance Criteria

- [ ] full V2 happy path demo ผ่านบน deployed frontend + AWS APIs จริง
- [ ] V1 compatibility checks ผ่านบน deployed routes จริง
- [ ] public visibility/redaction checks ผ่าน
- [ ] admin auth/CRUD checks ผ่านด้วย Cognito + protected API Gateway + Lambda + Aurora
- [ ] database verification ผ่านจาก Aurora target environment
- [ ] S3/Secrets/IAM/CloudWatch resource verification ผ่าน
- [ ] docs สำหรับ run/check/demo อัปเดตพร้อม resource names/placeholders
- [ ] known limitations ถูกบันทึก
- [ ] มี evidence พร้อมใช้ปิด GitHub issues

## Review Checklist

Tech Lead:

- [ ] ไม่มี feature scope ใหม่แอบเข้ามาใน final integration
- [ ] blockers ที่เหลือถูกจัดเป็น known limitation หรือ follow-up ชัดเจน

QA:

- [ ] test evidence ครบ public/admin/data/AWS services
- [ ] manual demo script ทำตามได้

Security:

- [ ] secret/ARN sensitive value ไม่ถูกเปิดเกินจำเป็น
- [ ] admin-only data ไม่แสดง public
- [ ] V1 compatibility ไม่เปิดข้อมูลใหม่ผิด boundary
- [ ] S3 private access และ IAM least-privilege ถูกตรวจสำหรับ services ที่ใช้จริง

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

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มีหลักฐานจาก deployed environment จริงว่า frontend, API Gateway, Lambda, Cognito, Aurora/Data API, Secrets Manager, S3, CloudWatch/IAM และ V1 compatibility ทำงานร่วมกันได้ครบตาม scope ที่ freeze ไว้ พร้อมเอกสาร demo/deploy/check สำหรับส่งงานและปิดชุด V2
