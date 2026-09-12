# คู่มือการทดสอบ การตรวจสอบ และหลักฐาน

ไฟล์นี้อธิบายวิธีทดสอบและเก็บหลักฐานสำหรับปิดการ์ด V2

เนื้อหาหลักเขียนเป็นภาษาไทยเพื่อให้ทีมใช้เป็น checklist กลางได้ ส่วน command, route, JSON field และ AWS service ยังคงเป็นภาษาอังกฤษตามของจริง

หลักสำคัญ: V2 issue card ต้องปิดด้วยหลักฐานจากระบบจริง ไม่ใช่แค่ “โค้ด compile ได้”

## ระดับการตรวจสอบ

ใช้การตรวจสอบ 4 ชั้น:

1. unit/contract tests ในเครื่อง
2. build/static checks
3. deploy/smoke tests บน AWS
4. evidence docs/GitHub comment

แต่ละการ์ดไม่จำเป็นต้องมีทุกอย่างเท่ากัน แต่ production API/Admin/UI cards ต้องมี smoke/evidence จาก AWS จริง

## ชุดคำสั่งที่ตรวจแล้วว่าใช้ได้ตอนนี้

Backend #64 tests:

```bash
python3 -m unittest backend.v2.query.test_master_data
```

ผลที่ควรได้:

```text
Ran 8 tests - OK
```

Frontend local V2 master data contract test:

```bash
cd frontend
npm run test:v2:master-data
```

ผลที่ควรได้:

```text
9 tests passed
```

Master Data API AWS smoke:

```bash
AWS_REGION=ap-southeast-1 \
API_STACK=cs361-v2-master-data-api-dev \
scripts/smoke-v2-master-data-api.sh
```

ผลที่ควรได้หลังจาก Aurora พร้อมตอบสนอง:

```text
PASS /api/v2/academic-periods count=5
PASS /api/v2/evaluation-periods count=3
PASS /api/v2/work-categories count=6
PASS /api/v2/work-types count=26
PASS /api/v2/faculties count=3
PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY
```

## ต้องทดสอบอะไรตามประเภทการ์ด

### การ์ด Public Read API

ตัวอย่าง: #64, #66, #67, #68

สิ่งที่ต้องทดสอบ:

- unit tests ของ Lambda/service
- query validation
- กรณีผลลัพธ์ว่าง
- invalid query ต้องคืน error shape มาตรฐาน
- บังคับกฎ public visibility
- success response envelope ถูกต้อง
- API Gateway route ถูก deploy แล้ว
- CloudWatch log มีจริง
- อ่านข้อมูล Aurora ผ่าน RDS Data API จริง

หลักฐานที่ควรเก็บ:

- API endpoint
- Lambda name
- route list
- smoke output
- CloudWatch log group
- sample response ที่ redact secret แล้ว
- commit hash

### การ์ด Admin API

ตัวอย่าง: #69, #70, #71

สิ่งที่ต้องทดสอบ:

- request ที่ไม่ login ต้องคืน `401`
- user ที่ login แล้วแต่ไม่ใช่ admin ต้องคืน `403`
- admin success path ต้องทำงานได้
- invalid payload ต้องคืน `400`
- entity ที่ไม่มีอยู่ต้องคืน `404`
- transaction rollback ต้องทำงานได้
- mutation ต้องเขียน Aurora จริง
- ต้อง insert `audit_event`

หลักฐานที่ควรเก็บ:

- Cognito resource id/name
- protected API route
- Lambda name
- ผล query ตรวจสอบใน Aurora
- CloudWatch logs
- ผลตรวจ auth/audit tables

### การ์ด Frontend Public UI

ตัวอย่าง: #72, #73, #74, #75

สิ่งที่ต้องทดสอบ:

- หน้าเปิดได้
- loading state แสดงเหมาะสม
- filter controls โหลดจาก endpoint จริงของ #64
- list results โหลดจาก endpoint จริงของ #66
- detail page โหลดจาก endpoint จริงของ #68
- empty/error/404 states ทำงานได้
- URL query state ทำงานคาดเดาได้
- restricted/internal records ไม่โผล่ใน public UI

หลักฐานที่ควรเก็บ:

- deployed frontend URL
- API Gateway base URL ที่ใช้งาน
- screenshots ถ้ามีประโยชน์
- manual QA matrix
- ผลตรวจ console/network errors

### การ์ด Admin UI

ตัวอย่าง: #76, #77, #78, #79

สิ่งที่ต้องทดสอบ:

- login page เปิดได้
- Cognito login ใช้งานได้ด้วย admin user
- protected pages redirect user ที่ยังไม่ login
- admin list โหลดจาก protected API
- create/edit form submit ไป real API
- validation errors map เข้ากับ field ที่ถูกต้อง
- soft-delete แล้ว record ต้องหายจาก public path
- restore ทำงานได้ถ้ามี implementation

หลักฐานที่ควรเก็บ:

- frontend URL
- Cognito user pool/app client names หรือ redacted ids
- admin API route
- smoke/manual QA screenshots
- CloudWatch logs
- ผลตรวจ row ใน Aurora

### การ์ด Database/Migration

ตัวอย่าง: #80

สิ่งที่ต้องทดสอบ:

- migration รันจาก clean/reset state ได้
- seed รันซ้ำได้ หรือมี reset path ที่ document ไว้
- fixture import ทำงานได้
- table counts ตรงกับ expected
- deployed V2 APIs อ่าน imported data ได้
- V1 routes ยังทำงานได้

หลักฐานที่ควรเก็บ:

- command log
- table counts
- ผลลัพธ์ endpoint สำหรับ V1 compatibility
- smoke matrix
- rollback/reset instructions

## รูปแบบ Error มาตรฐาน

V2 APIs ควรคืน error รูปแบบนี้:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "category must be a known work category code",
    "details": {
      "field": "category"
    }
  }
}
```

error ที่ไม่คาดคิดควรคืนข้อความกว้างๆ:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Unable to load V2 master data"
  }
}
```

ห้ามหลุดข้อมูลเหล่านี้:

- stack trace
- DB secret
- secret ARN ถ้าไม่จำเป็น
- password
- raw SQL ที่มี sensitive values
- private S3 key
- internal raw source JSON

## วิธีเช็ค API Gateway Routes

ดึง API id จาก stack:

```bash
API_ID=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-master-data-api-dev \
  --query "Stacks[0].Outputs[?OutputKey=='MasterDataApiId'].OutputValue | [0]" \
  --output text)
```

ดูรายการ route:

```bash
aws apigatewayv2 get-routes \
  --region ap-southeast-1 \
  --api-id "$API_ID" \
  --query 'Items[].RouteKey' \
  --output table
```

สำหรับ #64 route ที่ควรมีคือ:

```text
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
```

## วิธีเช็ค CloudWatch Logs

ดู log stream ล่าสุด:

```bash
aws logs describe-log-streams \
  --region ap-southeast-1 \
  --log-group-name /aws/lambda/cs361-v2-dev-query \
  --order-by LastEventTime \
  --descending \
  --max-items 3 \
  --query 'logStreams[].{name:logStreamName,last:lastEventTimestamp}' \
  --output table
```

ดู event ล่าสุด:

```bash
LOG_STREAM=$(aws logs describe-log-streams \
  --region ap-southeast-1 \
  --log-group-name /aws/lambda/cs361-v2-dev-query \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --query 'logStreams[0].logStreamName' \
  --output text)

aws logs get-log-events \
  --region ap-southeast-1 \
  --log-group-name /aws/lambda/cs361-v2-dev-query \
  --log-stream-name "$LOG_STREAM" \
  --limit 20
```

## วิธีเช็คจำนวนข้อมูลในฐานข้อมูล

ใช้ Data API:

```bash
DB_CLUSTER_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBClusterArn'].OutputValue | [0]" \
  --output text)

DB_SECRET_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBSecretArn'].OutputValue | [0]" \
  --output text)

DB_NAME=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBName'].OutputValue | [0]" \
  --output text)

aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "select
    (select count(*) from faculty) as faculties,
    (select count(*) from work_item) as work_items,
    (select count(*) from faculty_work_item) as faculty_work_items,
    (select count(*) from evidence_reference) as evidence_references"
```

## พฤติกรรม Auto-Pause ที่ต้องรู้

Aurora สามารถ auto-pause ได้ ถ้าระบบไม่ได้ถูกใช้งานมาสักพัก request แรกอาจล้มเหลวด้วย:

```text
DatabaseResumingException
```

ฝั่ง API อาจเห็นเป็น `500`

วิธีจัดการตอนทดสอบ:

1. บันทึกไว้ว่า DB กำลัง resume ถ้าเกิดเหตุการณ์นี้จริง
2. รอ 15-30 วินาที
3. retry smoke test
4. ใช้ผล retry เป็นหลักฐาน pass/fail

ในอนาคตสามารถเพิ่ม retry/backoff ใน Lambda สำหรับ `DatabaseResumingException` ได้

## รูปแบบโฟลเดอร์ Evidence

เก็บหลักฐานไว้ที่:

```text
evidence/v2/<issue-or-feature>/README.md
```

ตัวอย่าง:

```text
evidence/v2/aws-foundation/README.md
evidence/v2/master-data-api/README.md
```

หลักฐานควรมี:

- วันที่
- issue number
- branch/commit
- AWS region
- stack names
- resource names
- commands ที่รัน
- test output
- known limitations
- ยืนยันว่าไม่มี secret values

## Template Comment สำหรับปิด GitHub Issue

ใช้รูปแบบนี้:

````md
อัปเดต Issue #<number> - <title> เสร็จแล้วครับ

สิ่งที่ทำ:
- ...
- ...

AWS/resources:
- Region: `ap-southeast-1`
- Stack: `<stack-name>`
- API endpoint: `<endpoint>`
- Lambda: `<lambda-name>`
- CloudWatch: `<log-group>`

Verification:
```text
<paste smoke/unit test output>
```

Evidence/docs:
- `<docs path>`
- `<evidence path>`

Commit:
`<commit-hash> <commit-message>`

Known notes:
- ไม่มี secret value ถูกเปิดใน docs/repo
- ถ้า Aurora auto-pause อาจต้อง retry หลัง resume

สรุป: การ์ดนี้พร้อมปิดได้ เพราะ <อธิบายว่าตรง acceptance criteria อย่างไร>
````

## ตัวอย่างหลักฐานของ #64

````md
อัปเดต Issue #64 - Build Master Data API เสร็จแล้วครับ

สิ่งที่ทำ:
- เพิ่ม Production Master Data API ตาม path จริง: `API Gateway -> Lambda -> RDS Data API -> Aurora`
- เพิ่ม Lambda handler สำหรับ read-only master data
- เพิ่ม CloudFormation stack สำหรับ API Gateway + Query Lambda
- เพิ่ม deploy script และ smoke test script
- อัปเดต docs contract และ evidence

AWS resources:
- Region: `ap-southeast-1`
- API stack: `cs361-v2-master-data-api-dev`
- API endpoint: `https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com`
- Lambda: `cs361-v2-dev-query`
- CloudWatch log group: `/aws/lambda/cs361-v2-dev-query`

Smoke test:
```text
PASS /api/v2/academic-periods count=5
PASS /api/v2/evaluation-periods count=3
PASS /api/v2/work-categories count=6
PASS /api/v2/work-types count=26
PASS /api/v2/faculties count=3
PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY
```

Evidence:
- `docs/v2/issues/64-build-master-data-api.md`
- `docs/v2/master-data-api.md`
- `evidence/v2/master-data-api/README.md`

Commit:
`df03830 feat: deploy V2 master data API`

สรุป: พร้อมปิดได้ เพราะ endpoint ทั้ง 5 ตัว deploy แล้วบน AWS, อ่าน Aurora จริงผ่าน RDS Data API, มี CloudWatch/API smoke evidence และไม่มี secret value เปิดใน docs/repo
````

## Checklist ก่อนปิดการ์ด

เช็คก่อนปิด:

- [ ] Acceptance criteria ใน issue card ทำครบจริง
- [ ] ถ้าการ์ดต้อง deploy บน AWS ได้ทดสอบ path จริงแล้ว
- [ ] Unit/contract tests ผ่าน
- [ ] เก็บ smoke test output แล้ว
- [ ] อัปเดต docs แล้ว
- [ ] เพิ่ม/อัปเดต evidence file แล้ว
- [ ] tick checklist ใน issue card ตามความจริง
- [ ] ไม่มี secret ถูก commit
- [ ] commit ถูก push แล้ว
- [ ] GitHub issue comment มีหลักฐานครบ
