# [V2] Provision Aurora, Data API, Secrets & IAM Foundation

## Implementation Artifacts

Repo-side preparation สำหรับการ์ดนี้ถูกเพิ่มแล้ว:

- `infra/v2/aws-foundation.yaml` — CloudFormation baseline สำหรับ Aurora PostgreSQL Serverless v2, RDS Data API, Secrets Manager, IAM roles, S3 data bucket และ CloudWatch log groups
- `infra/v2/parameters.dev.example.json` — parameter example สำหรับ dev/demo deployment
- `infra/v2/README.md` — ขั้นตอน deploy และ verify
- `scripts/setup-v2-aws-foundation.sh` — wizard สำหรับ operator ที่จะ login AWS เอง โดยไม่ต้องส่ง secret ใน chat
- `scripts/check-v2-aws-foundation.sh` — script ตรวจ `SELECT 1` ผ่าน RDS Data API
- `docs/v2/aws-foundation.md` — deployment/resource record
- `docs/v2/deployment-env.md` — environment variables สำหรับ backend/import/projection
- `docs/v2/security.md` — security boundary สำหรับ secret/IAM/Data API/evidence
- `docs/v2/aws-foundation-evidence.md` — evidence checklist สำหรับปิดการ์ด

สถานะ: deploy AWS dev/demo สำเร็จแล้ว และได้หลักฐาน `SELECT 1` ผ่าน RDS Data API

Implementation note:

- AWS account นี้ถูก RDS บังคับให้สร้าง Aurora ด้วย Express Configuration
- CloudFormation `AWS::RDS::DBCluster` schema ใน region นี้ยังไม่รองรับ `WithExpressConfiguration`
- จึงใช้ AWS CLI สร้าง Aurora Express cluster แล้ว deploy CloudFormation ด้วย `AuroraProvisioningMode=external-express` เพื่อสร้าง IAM roles, S3 bucket และ CloudWatch log groups
- Network posture ของ Express cluster เป็น dev/demo exception: `VPCNetworkingEnabled=false`, `InternetAccessGatewayEnabled=true`

Repo preparation checklist:

- [x] เตรียม CloudFormation template สำหรับ AWS foundation
- [x] เตรียม parameter example สำหรับ dev/demo
- [x] เตรียม operator wizard สำหรับ AWS setup โดยไม่รับ secret ผ่าน chat
- [x] เตรียม Data API verification script
- [x] เตรียม deployment env documentation
- [x] เตรียม security boundary documentation
- [x] เตรียม evidence checklist สำหรับปิดการ์ด
- [x] link artifact จาก `docs/v2/README.md`

## สรุป

จัดเตรียม AWS foundation สำหรับ V2 Repository ให้พร้อมใช้งาน โดยสร้าง Aurora PostgreSQL Serverless v2, เปิดใช้ RDS Data API, จัดเก็บ database secret ใน AWS Secrets Manager, แยก IAM runtime roles ตามหน้าที่ และบันทึก resource names / environment variables สำหรับทีม backend, import, projection และ admin ใช้ต่อ

การ์ดนี้เป็นฐาน cloud infrastructure ของ V2 ถ้ายังไม่เสร็จ backend และ migration จะยังไม่สามารถทดสอบกับ repository จริงได้

## Background

V2 เปลี่ยนจาก V1 ที่อ่าน S3 JSON แบบ read-only ไปเป็น managed repository บน Aurora PostgreSQL Serverless v2

Architecture หลักที่ freeze จาก :

```text
Next.js / Vercel
        ↓
Amazon API Gateway HTTP API
        ↓
AWS Lambda
        ↓
Amazon RDS Data API
        ↓
Aurora PostgreSQL Serverless v2
```

การ์ด #47 จะออกแบบ schema และ SQL migration baseline ส่วนการ์ดนี้รับผิดชอบการเตรียม AWS resources และสิทธิ์ที่จำเป็นให้พร้อมสำหรับการรัน migration, seed, query API, admin API, import และ public projection ในการ์ดถัดไป

## เป้าหมาย

สร้าง cloud foundation สำหรับ V2 ที่ปลอดภัย ประหยัด และตรวจสอบได้

เมื่อการ์ดนี้เสร็จ ทีมควรมี:

- Aurora PostgreSQL Serverless v2 cluster สำหรับ V2
- Database name สำหรับ V2 repository
- RDS Data API enabled
- Database secret ใน Secrets Manager
- IAM roles แยกตาม runtime responsibility
- CloudWatch log baseline
- resource names / ARNs / env vars ที่ต้องใช้ต่อ
- หลักฐานว่า Data API สามารถเชื่อมต่อ database ได้ด้วย `SELECT 1`

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- ออกแบบ schema เองแทน 
- เขียน application backend
- เขียน Lambda handler จริง
- สร้าง `/api/v2` routes
- สร้าง Cognito admin auth
- เขียน import pipeline
- migrate ข้อมูล V1
- deploy frontend
- ทำ full Infrastructure as Code ถ้ายังไม่ถึง scope V5
- เปิด CloudFront
- เปิด OpenSearch
- ใช้ RDS Proxy
- ใช้ ECS/EKS

## Scope

### ต้องทำ

- สร้าง Aurora PostgreSQL Serverless v2 สำหรับ V2 repository
- เลือก region ตาม V2 design: `ap-southeast-1`
- ตั้ง low-cost serverless capacity สำหรับ dev/demo
- เปิด RDS Data API
- สร้าง database secret ใน Secrets Manager
- สร้างหรือระบุ database name
- สร้าง IAM roles สำหรับ Lambda responsibilities
- จำกัดสิทธิ์แบบ least privilege
- ตั้ง CloudWatch log group baseline หรือ naming convention
- ทดสอบ connectivity ขั้นต่ำผ่าน Data API
- บันทึก resource names / ARNs / env vars
- บันทึก cost/risk notes ที่ทีมต้องรู้

### ไม่ต้องทำ

- เขียน production query code
- seed master data
- run full migration
- สร้าง admin user pool
- สร้าง API Gateway routes

## AWS Resources ที่ต้องเตรียม

### Aurora PostgreSQL Serverless v2

ต้องเตรียม:

- Aurora PostgreSQL-compatible cluster
- Serverless v2 capacity
- Database name สำหรับ V2
- Data API enabled
- Backup setting ตาม default หรือค่าที่ทีมตกลง
- No direct public DB exposure

Recommended configuration สำหรับ dev/demo:

```text
Region: ap-southeast-1
Engine: Aurora PostgreSQL-compatible
Mode: Serverless v2
MinCapacity: 0 ACU ถ้า engine version รองรับ
MaxCapacity: 1-2 ACU
Auto-pause: 5-30 minutes ถ้ารองรับ
Public access: disabled
```

หมายเหตุ:

- ต้องตรวจ feature availability ของ engine version ในวันที่ deploy จริง
- ถ้า `MinCapacity = 0` ยังไม่รองรับใน engine version ที่เลือก ให้ใช้ค่าต่ำสุดที่รองรับและบันทึกเหตุผล
- ก่อน demo อาจตั้ง MinCapacity สูงขึ้นชั่วคราวเพื่อลด cold resume latency ได้ แต่ต้องบันทึกไว้

### RDS Data API

ต้องเปิดให้ Lambda ใช้ query Aurora ผ่าน AWS SDK โดยไม่ต้องจัดการ persistent DB connection

ต้อง verify:

- Data API enabled
- Query role สามารถ `ExecuteStatement` ได้เฉพาะ cluster นี้
- Admin/import roles มี transaction permissions ตามจำเป็น

### AWS Secrets Manager

ต้องสร้าง secret สำหรับ database credential

ห้าม:

- commit database password ลง repo
- ใส่ DB password ใน frontend env
- ใส่ secret จริงใน `.env.example`

ต้องบันทึก:

- secret name
- secret ARN
- rotation decision ถ้ายังไม่เปิด rotation ให้บันทึกเหตุผล

### IAM Roles

แนะนำแยก role ตาม responsibility:

- `CS361V2QueryLambdaRole`
- `CS361V2AdminLambdaRole`
- `CS361V2ImportLambdaRole`
- `CS361V2ProjectionLambdaRole`

#### Query Lambda Role

สำหรับ read/query API

Allow ขั้นต่ำ:

- `rds-data:ExecuteStatement`
- `secretsmanager:GetSecretValue`

เฉพาะ V2 cluster และ V2 secret

#### Admin Lambda Role

สำหรับ admin create/edit/soft delete

Allow เพิ่มตามจำเป็น:

- `rds-data:ExecuteStatement`
- `rds-data:BeginTransaction`
- `rds-data:CommitTransaction`
- `rds-data:RollbackTransaction`
- `secretsmanager:GetSecretValue`

เฉพาะ V2 cluster และ V2 secret

#### Import Lambda Role

สำหรับ controlled import

Allow ขั้นต่ำ:

- read S3 `landing/*`
- write S3 `archive/*`
- write S3 `metadata/*`
- Data API execute/transaction permissions
- `secretsmanager:GetSecretValue`

#### Projection Lambda Role

สำหรับสร้าง public projection ให้ V1/V2 public surface ใช้

Allow ขั้นต่ำ:

- DB read ผ่าน Data API
- write S3 เฉพาะ `public-serving/*`
- `secretsmanager:GetSecretValue`

### ห้ามใช้ Broad Permission

Runtime roles ห้ามมี:

- `AdministratorAccess`
- `rds:*`
- `s3:*`
- `secretsmanager:*`

ถ้าจำเป็นต้องใช้สิทธิ์กว้างชั่วคราว ต้องบันทึกเหตุผลและมี follow-up เพื่อลดสิทธิ์ก่อนปิด V2

## Environment Variables ที่ต้องบันทึก

สำหรับ Lambda:

```text
DB_CLUSTER_ARN=
DB_SECRET_ARN=
DB_NAME=
DATA_BUCKET_NAME=
LOG_LEVEL=
ENVIRONMENT=
```

สำหรับ frontend ในอนาคต:

```text
NEXT_PUBLIC_API_BASE_URL=
NEXT_PUBLIC_COGNITO_USER_POOL_ID=
NEXT_PUBLIC_COGNITO_CLIENT_ID=
```

การ์ดนี้ยังไม่ต้องตั้งค่า frontend env จริง ยกเว้นถ้าจำเป็นสำหรับเอกสาร deploy

## Connectivity Verification

ต้องมีหลักฐานว่าเชื่อมต่อผ่าน Data API ได้

ขั้นต่ำ:

```sql
SELECT 1;
```

ถ้า  migration พร้อมแล้ว สามารถทดสอบเพิ่มเติมด้วย:

```sql
SELECT current_database();
SELECT current_user;
```

แต่ห้ามถือว่าการ์ดนี้ต้อง run full migration หรือ seed data ถ้ายังไม่ใช่ scope ที่ทีมตกลง

## Expected Documentation

ต้องบันทึกผลไว้ในเอกสาร เช่น:

```text
docs/v2/aws-foundation.md
docs/v2/deployment-env.md
docs/v2/security.md
```

หรือชื่ออื่นที่ทีมตกลง แต่ต้อง link จาก `docs/v2/README.md`

เอกสารควรมี:

- region
- cluster name
- database name
- cluster ARN
- secret name / secret ARN
- Data API status
- IAM role names
- allowed actions summary
- S3 bucket/prefix ที่เกี่ยวข้อง
- env vars ที่ backend ต้องใช้
- verification result
- known limitations / cost notes

## Evidence ที่ต้องแนบตอนปิดการ์ด

ควรมีอย่างน้อย:

- screenshot หรือ command output ที่แสดง Aurora cluster พร้อมใช้งาน
- screenshot หรือ command output ที่แสดง Data API enabled
- screenshot หรือ command output ของ secret ใน Secrets Manager โดยไม่เปิดเผย secret value
- IAM policy summary ของแต่ละ runtime role
- ผล `SELECT 1` ผ่าน Data API
- เอกสาร resource names/env vars ที่ทีมใช้ต่อได้

ห้ามแนบ:

- database password
- access key
- secret value
- full JWT/token
- screenshot ที่มี credential

## Acceptance Criteria

- [x] Aurora PostgreSQL Serverless v2 cluster ถูกสร้างหรือระบุ resource ที่ใช้สำหรับ V2 แล้ว
- [x] cluster อยู่ใน region ที่ทีมตกลง
- [x] database name สำหรับ V2 ถูกกำหนดแล้ว
- [x] Serverless capacity ถูกตั้งค่าแบบ low-cost dev/demo แล้ว
- [x] Data API enabled แล้ว
- [x] database secret ถูกเก็บใน Secrets Manager แล้ว
- [x] ไม่มี secret value ถูก commit หรือเผยแพร่ในเอกสาร
- [x] Query Lambda role ถูกสร้างหรือกำหนดแล้ว
- [x] Admin Lambda role ถูกสร้างหรือกำหนดแล้ว
- [x] Import Lambda role ถูกสร้างหรือกำหนดแล้ว
- [x] Projection Lambda role ถูกสร้างหรือกำหนดแล้ว
- [x] runtime roles ไม่มี `AdministratorAccess`
- [x] runtime roles ไม่มี wildcard กว้างเกินจำเป็น เช่น `rds:*`, `s3:*`, `secretsmanager:*`
- [x] Query role จำกัดสิทธิ์เฉพาะ read/query ที่จำเป็น
- [x] Admin role มี transaction permissions เท่าที่จำเป็น
- [x] Import role จำกัด S3 prefixes ตามหน้าที่
- [x] Projection role จำกัด write เฉพาะ public projection prefix
- [x] CloudWatch log baseline หรือ naming convention ถูกบันทึกแล้ว
- [x] `SELECT 1` ผ่าน RDS Data API สำเร็จ
- [x] resource names, ARNs และ env vars ถูกบันทึกในเอกสารแล้ว
- [x] cost/risk notes เช่น auto-pause, min/max ACU, cold resume latency ถูกบันทึกแล้ว
- [x] เอกสารพร้อมให้ backend, data, import, projection และ integration ใช้อ้างอิง

## Review Checklist

Cloud / AWS:

- [x] Aurora configuration เหมาะกับ dev/demo V2
- [x] Data API เปิดใช้งานได้จริง
- [x] Secrets Manager ใช้ถูกต้อง
- [x] IAM roles แยกตาม responsibility
- [x] ไม่มี broad runtime permissions

Backend:

- [x] env vars เพียงพอสำหรับ Data API client
- [x] Query/admin/import/projection roles ตรงกับ backend responsibilities
- [x] verification result เพียงพอให้เริ่ม API work

Data / Database:

- [x] database พร้อมรองรับ migration จาก #47
- [x] database name และ connection metadata ชัดเจน

Security / QA:

- [x] ไม่มี secret leak
- [x] least privilege ตรวจสอบได้
- [x] evidence ไม่มี credential

Tech Lead:

- [x] resource naming สอดคล้องกับ V2 naming convention
- [x] cost notes และ deferred services ชัดเจน
- [x] งานไม่ล้ำ scope ไป Cognito/API/import implementation

## Dependencies

Blocked by:

- #46 Freeze V2 Scope, Architecture & Interface Contracts
- #47 Design Relational Schema & SQL Migration

Blocks:

- #50 Prepare Multi-Year Demo Dataset
- #51 Build Master Data API
- #52 Build Work Item List/Search/Filter API
- #53 Build Faculty Work Items API
- #54 Build Work Item Detail API
- #56 Build Admin Create Work Item API
- #57 Build Admin Update / Soft Delete API
- #66 Execute Migration & Preserve V1 Compatibility
- #67 Final Integration / Deploy / Demo Docs

Related:

- #55 Configure Admin Authentication

## Suggested Labels

- `v2`
- `cloud`
- `aws`
- `database`
- `security`
- `blocking`
- `ready-for-review`

## Suggested Owner

Cloud Developer

Reviewers:

- Tech Lead
- Backend Developer
- Data / Database Developer
- QA / Security

## Estimate

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มี Aurora/Data API/Secrets/IAM foundation ที่เชื่อมต่อได้จริงผ่าน Data API, มี runtime roles แบบ least privilege, ไม่มี secret leak และมีเอกสาร resource/env ที่ทีม backend, data, import, projection และ integration ใช้ต่อได้
