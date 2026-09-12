# V2 Documentation Index

เอกสารชุดนี้เป็น baseline สำหรับ **V2 - Faculty Output Repository** ของโปรเจกต์ CS361

V2 มีเป้าหมายเพื่อยกระบบจาก V1 public read-only faculty information service ไปเป็น repository กลางที่จัดเก็บผลงานและภาระงานอาจารย์แบบมีโครงสร้าง รองรับหลายปีการศึกษา และรองรับการค้นหา/กรอง/เรียกดูรายละเอียดตามเงื่อนไข

---

## Current V2 Baseline

| Artifact | Purpose |
|---|---|
| [V2_Central_Design.md](./V2_Central_Design.md) | เอกสาร freeze หลักของ Issue #46: scope, architecture, contracts, routes, entities, V1 compatibility |
| [erd.md](./erd.md) | ERD และ relationship baseline ของ V2 repository สำหรับ Issue #47 |
| [erd-table-attribute-guide.md](./erd-table-attribute-guide.md) | คำอธิบายทุก table และทุก attribute ใน ERD พร้อม type และตัวอย่างค่า |
| [data-contract.md](./data-contract.md) | data dictionary และ query/data contract ขั้นต้นของ schema |
| [schema-decisions.md](./schema-decisions.md) | design decisions สำคัญของ relational schema |
| [v2-repository.dbml](./v2-repository.dbml) | DBML script สำหรับ paste เข้า dbdiagram.io |
| [v1-to-v2-mapping.md](./v1-to-v2-mapping.md) | mapping จาก V1 public faculty dataset เข้า V2 relational repository สำหรับ Issue #49 |
| [demo-dataset.md](./demo-dataset.md) | summary และ validation matrix ของ V2 multi-year demo dataset สำหรับ Issue #50 |
| [master-data-api.md](./master-data-api.md) | contract และ verification notes ของ V2 Master Data API สำหรับ Issue #64 |
| [aws-foundation.md](./aws-foundation.md) | AWS foundation deployment record สำหรับ Issue #48 |
| [aws-foundation-service-check-guide.md](./aws-foundation-service-check-guide.md) | วิธีเช็ค AWS services หลัง deploy สำหรับคนในทีมที่มาทำต่อ |
| [deployment-env.md](./deployment-env.md) | environment variables ที่ backend/import/projection ต้องใช้หลัง deploy |
| [security.md](./security.md) | V2 security boundary สำหรับ secrets, IAM, Data API และ evidence |
| [aws-foundation-evidence.md](./aws-foundation-evidence.md) | evidence checklist สำหรับปิด Issue #48 |
| [v2-aws-service-architecture.png](./v2-aws-service-architecture.png) | Architecture diagram แบบ AWS service-icon style |
| [v2-full-architecture-clean.png](./v2-full-architecture-clean.png) | Architecture diagram เวอร์ชัน clean/readable |

---

## Frozen Decisions From Issue #46

- V2 คือ **Managed Multi-year Faculty Output Repository**
- Aurora PostgreSQL Serverless v2 เป็น managed repository หลัก
- Lambda access ฐานข้อมูลผ่าน RDS Data API
- S3 ใช้สำหรับ source landing, archive, evidence metadata/reference, exports และ public-serving projection
- Cognito ใช้เฉพาะ Admin pilot authentication
- Public data ต้อง enforce ที่ backend/API ไม่ใช่แค่ซ่อนที่ frontend
- Visibility baseline คือ `PUBLIC`, `INTERNAL`, `RESTRICTED`
- `work_item` เป็นแกนกลางของผลงาน/ภาระงาน
- `faculty_work_item` ใช้รองรับผลงานที่มีอาจารย์หลายคนและ contribution ต่างกัน
- `academic_period` และ `evaluation_period` เป็นคนละ concept
- V1 routes และ `/api/v1` contract ต้องไม่พัง
- CloudFront, OpenSearch, RDS Proxy, ECS/EKS เป็น deferred/non-core สำหรับ V2

---

## Issue Cards

หมายเหตุ: เอกสาร freeze เดิมใน Issue #46 อ้างอิง implementation cards เป็น #51-#67 แต่เลข GitHub issue ปัจจุบันเริ่มงาน implementation ที่ #64 และการ์ดถัดจาก #64 เริ่มที่ #66 ดังนั้นตารางนี้ใช้เลขจริงชุดใหม่ #64 และ #66-#81 โดยยังรักษาลำดับงานเดิมไว้

| Issue | File |
|---|---|
| #46 Freeze Scope, Architecture & Interface Contracts | [issues/46-freeze-v2-scope-architecture-interface-contracts.md](./issues/46-freeze-v2-scope-architecture-interface-contracts.md) |
| #47 Design Relational Schema & SQL Migration | [issues/47-design-relational-schema-and-sql-migration.md](./issues/47-design-relational-schema-and-sql-migration.md) |
| #48 Provision Aurora / Data API / Secret / IAM | [issues/48-provision-aurora-data-api-secret-iam.md](./issues/48-provision-aurora-data-api-secret-iam.md) |
| #49 Define V1 to V2 Data Mapping | [issues/49-define-v1-to-v2-data-mapping.md](./issues/49-define-v1-to-v2-data-mapping.md) |
| #50 Prepare Multi-Year Demo Dataset | [issues/50-prepare-multi-year-demo-dataset.md](./issues/50-prepare-multi-year-demo-dataset.md) |
| #64 Build Master Data API | [issues/64-build-master-data-api.md](./issues/64-build-master-data-api.md) |
| #66 Build Work Item List/Search/Filter API | [issues/66-build-work-item-list-search-filter-api.md](./issues/66-build-work-item-list-search-filter-api.md) |
| #67 Build Faculty Work Items API | [issues/67-build-faculty-work-items-api.md](./issues/67-build-faculty-work-items-api.md) |
| #68 Build Work Item Detail API | [issues/68-build-work-item-detail-api.md](./issues/68-build-work-item-detail-api.md) |
| #69 Configure Admin Authentication | [issues/69-configure-admin-authentication.md](./issues/69-configure-admin-authentication.md) |
| #70 Build Admin Create Work Item API | [issues/70-build-admin-create-work-item-api.md](./issues/70-build-admin-create-work-item-api.md) |
| #71 Build Admin Update / Soft Delete API | [issues/71-build-admin-update-soft-delete-api.md](./issues/71-build-admin-update-soft-delete-api.md) |
| #72 Build Repository Page Shell & Filter UI | [issues/72-build-repository-page-shell-filter-ui.md](./issues/72-build-repository-page-shell-filter-ui.md) |
| #73 Build Repository Result List & Pagination UI | [issues/73-build-repository-result-list-pagination-ui.md](./issues/73-build-repository-result-list-pagination-ui.md) |
| #74 Build Work Item Detail UI | [issues/74-build-work-item-detail-ui.md](./issues/74-build-work-item-detail-ui.md) |
| #75 Integrate Repository UI with Real API | [issues/75-integrate-repository-ui-with-real-api.md](./issues/75-integrate-repository-ui-with-real-api.md) |
| #76 Build Admin Login UI | [issues/76-build-admin-login-ui.md](./issues/76-build-admin-login-ui.md) |
| #77 Build Admin Work Item List UI | [issues/77-build-admin-work-item-list-ui.md](./issues/77-build-admin-work-item-list-ui.md) |
| #78 Build Admin Create/Edit Form UI | [issues/78-build-admin-create-edit-form-ui.md](./issues/78-build-admin-create-edit-form-ui.md) |
| #79 Integrate Admin UI with Auth & CRUD API | [issues/79-integrate-admin-ui-with-auth-crud-api.md](./issues/79-integrate-admin-ui-with-auth-crud-api.md) |
| #80 Execute Migration & Preserve V1 Compatibility | [issues/80-execute-migration-preserve-v1-compatibility.md](./issues/80-execute-migration-preserve-v1-compatibility.md) |
| #81 Final Integration / Deploy / Demo Docs | [issues/81-final-integration-deploy-demo-docs.md](./issues/81-final-integration-deploy-demo-docs.md) |

---

## How To Use This Folder

สำหรับเริ่มงาน V2 ให้ใช้ลำดับนี้:

1. อ่าน [V2_Central_Design.md](./V2_Central_Design.md) เพื่อเข้าใจ scope และ contracts ที่ freeze แล้ว
2. อ่าน [erd.md](./erd.md), [data-contract.md](./data-contract.md), และ [schema-decisions.md](./schema-decisions.md) ก่อนเริ่มงาน database/API
3. ใช้ [v2-aws-service-architecture.png](./v2-aws-service-architecture.png) ในรายงานหรือ slide เพื่ออธิบาย architecture
4. เริ่ม implementation planning จาก issue #48 เป็นต้นไปหลัง schema baseline ผ่าน review
5. ถ้างานถัดไปต้องเปลี่ยนชื่อ entity, route, visibility rule หรือ V1 compatibility rule ให้เปิด decision/update แยกก่อนแก้

---

## Database Baseline

| Artifact | Purpose |
|---|---|
| [../../database/README.md](../../database/README.md) | วิธี review และลำดับการรัน SQL baseline |
| [../../database/migrations/001_base.sql](../../database/migrations/001_base.sql) | SQL migration baseline สำหรับ Aurora PostgreSQL |
| [../../database/seeds/001_master_data.sql](../../database/seeds/001_master_data.sql) | seed master data สำหรับ `work_category` และ `work_type` |
| [../../data/v2/mappings/v1-to-v2-field-mapping.csv](../../data/v2/mappings/v1-to-v2-field-mapping.csv) | field-level mapping จาก V1 public faculty dataset เข้า V2 tables สำหรับ Issue #49 |
| [../../data/v2/fixtures/README.md](../../data/v2/fixtures/README.md) | V2 multi-year demo fixture dataset สำหรับ search/filter/detail/API demo |

---

## AWS Foundation Baseline

| Artifact | Purpose |
|---|---|
| [../../infra/v2/aws-foundation.yaml](../../infra/v2/aws-foundation.yaml) | CloudFormation baseline สำหรับ Aurora/Data API/Secrets/IAM/S3/CloudWatch |
| [../../infra/v2/parameters.dev.example.json](../../infra/v2/parameters.dev.example.json) | ตัวอย่าง parameter file สำหรับ dev/demo deploy |
| [../../scripts/setup-v2-aws-foundation.sh](../../scripts/setup-v2-aws-foundation.sh) | interactive setup wizard สำหรับ operator ที่จะ login AWS เอง |
| [../../scripts/check-v2-aws-foundation.sh](../../scripts/check-v2-aws-foundation.sh) | verification script สำหรับ `SELECT 1` ผ่าน RDS Data API |

---

## V2 Boundary Reminder

V2 ทำ repository foundation และ Admin pilot

V2 ยังไม่ทำ:

- faculty self-service
- reviewer workflow
- approval process
- official workload scoring
- official annual report generation
- full multi-role workspace

รายการเหล่านี้เป็นทิศทางของ V3/V4/V7 ไม่ใช่ blocker ของ V2
