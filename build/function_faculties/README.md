# Faculty Read API (Lambda + S3 serving/*)

Read-only API ที่อ่านข้อมูลจาก S3 `serving/*` เท่านั้น ไม่มี code path สำหรับ mutation

## Endpoints

| Method | Path | S3 object | Response |
|---|---|---|---|
| GET | `/api/v1/faculties` | `{SERVING_PREFIX}/faculties.json` | `{"data": [...]}` |
| GET | `/api/v1/faculties/{id}` | `{SERVING_PREFIX}/faculties/{id}.json` | `{"data": {...}}` |

List ทำ GetObject ครั้งเดียว ไม่มี loop อ่าน detail ทุกไฟล์ (มี unit test บังคับไว้:
`test_does_not_read_detail_objects`)

## Status codes

| Status | Error code | เมื่อไหร่ |
|---|---|---|
| 200 | – | สำเร็จ |
| 400 | `INVALID_FACULTY_ID` | id ผิดรูปแบบ / `../` / `/` / `\` / control char / ว่าง |
| 404 | `FACULTY_NOT_FOUND` | detail `NoSuchKey` หรือ `{"data": null}` |
| 404 | `ROUTE_NOT_FOUND` | path ไม่ตรง route |
| 405 | `METHOD_NOT_ALLOWED` | method อื่นที่ไม่ใช่ GET (มี header `Allow: GET`) |
| 500 | `INTERNAL_ERROR` | `faculties.json` หาย, JSON เสีย, AccessDenied, S3 error |

หมายเหตุ: `faculties.json` หาย → **500** (ถือเป็น infrastructure ไม่ใช่ user input)
ส่วน detail หาย → **404**

Error body:

```json
{ "error": { "code": "FACULTY_NOT_FOUND", "message": "Faculty not found." } }
```

ไม่มี traceback / bucket name / S3 key / exception payload หลุดออก public response
(ทดสอบใน `test_security.TestResponseLeakage`)

## Faculty ID validation

```
^[a-z0-9]+(?:-[a-z0-9]+)*$     max 64 chars
```

Reject: empty/whitespace, `..`, `/`, `\`, control characters (`\x00`–`\x1f`, `\x7f`),
uppercase, `_`, `.`, leading/trailing `-`, `--` ซ้อน และ percent-encoded input
(`%2e%2e%2f`, `%2f`, `%5c`) — เพื่อกัน double-decoding ที่ API Gateway decode มาแล้วรอบหนึ่ง

Validation ทำ **ก่อน** เรียก S3 เสมอ (test ยืนยันว่า S3 ไม่ถูกเรียกเลยเมื่อ id ไม่ผ่าน)

## Structure

```
backend/
├── lambda/
│   ├── handler.py           # routing, method check, error → HTTP mapping
│   ├── faculty_service.py   # domain: list / detail, JSON shape handling
│   ├── s3_repository.py     # read-only S3 (get_object only), key guarding
│   ├── validation.py        # faculty id validation
│   ├── responses.py         # response envelope + public error codes
│   ├── events/              # sample events สำหรับ aws lambda invoke
│   └── tests/               # 62 unit tests (fake S3, ไม่แตะ AWS)
├── infra/lambda-s3-readonly-policy.json
└── scripts/smoke_test.sh    # real invoke กับ S3 จริง
```

## Environment variables (แยกตาม env)

| Variable | Required | Default | หมายเหตุ |
|---|---|---|---|
| `DATA_BUCKET_NAME` | ✅ | – | ต่าง bucket ต่อ env |
| `SERVING_PREFIX` | – | `serving` | |
| `LOG_LEVEL` | – | `INFO` | |
| `ENVIRONMENT` | – | `unknown` | ใช้ใน log context เท่านั้น |

โค้ดไม่ hardcode ชื่อ bucket เลย — แยก env ด้วยการตั้งค่า `DATA_BUCKET_NAME` ต่อ
Lambda function/alias เช่น

```bash
# dev
DATA_BUCKET_NAME=cs361-v1-faculty-data-g1-334177992720-ap-southeast-1-an
SERVING_PREFIX=serving
LOG_LEVEL=DEBUG
ENVIRONMENT=dev

# prod
DATA_BUCKET_NAME=cs361-v1-faculty-data-g1-334177992720-ap-southeast-1-an
SERVING_PREFIX=serving
LOG_LEVEL=INFO
ENVIRONMENT=prod
```

ถ้า `DATA_BUCKET_NAME` ไม่ถูกตั้ง → 500 (ไม่ crash แบบ leak stack trace)

## Security boundary

- `s3_repository.py` เรียกเฉพาะ `client.get_object` — มี test ที่ assert ว่า set ของ
  method ที่ถูกเรียกเท่ากับ `{"get_object"}` เป๊ะ
- ทุก key ถูก join ใต้ `SERVING_PREFIX` และตรวจซ้ำว่าไม่มี `..`, `\`, `//`, ไม่ absolute
  และยังขึ้นต้นด้วย prefix เดิม → `source/*` เข้าไม่ถึง
- ไม่มี route/handler สำหรับ POST/PUT/PATCH/DELETE (405 ก่อนแตะ S3)
- IAM policy ใน `infra/` ให้แค่ `s3:GetObject` บน `serving/*` + explicit Deny ทุก write

Defense in depth = no mutation route + no mutation code + no write permission

## Logging

Log: env, method, path, action, validated faculty id, success/failure, internal error type
(เช่น `error_code=AccessDenied`)
ไม่ log: credentials, secrets, raw source dataset, full exception payload ใน response
`logger.exception` ใช้เฉพาะ unhandled error และอยู่ใน CloudWatch เท่านั้น

## Run tests

```bash
cd backend/lambda
DATA_BUCKET_NAME=dummy python3 -m unittest discover -s tests -t tests -v
# หรือ
python3 -m pytest tests -q
```

ปัจจุบัน: 62 tests ผ่านทั้งหมด ครอบคลุม
list (success / empty / missing file / invalid JSON / S3 permission error),
detail (existing / unknown / invalid id / missing object / invalid JSON / missing optional field),
security (`../`, slash, backslash, source-path attempt, unsupported method, no write code path)

## Deploy + real invoke (ต้องทำก่อน close)

```bash
cd backend/lambda
zip -r ../function.zip . -x 'tests/*' 'events/*' '__pycache__/*'

aws lambda update-function-code \
  --function-name cs361-faculty-api-dev \
  --zip-file fileb://../function.zip \
  --region ap-southeast-1

aws lambda update-function-configuration \
  --function-name cs361-faculty-api-dev \
  --handler handler.lambda_handler \
  --environment "Variables={DATA_BUCKET_NAME=cs361-v1-faculty-data-g1-334177992720-ap-southeast-1-an,SERVING_PREFIX=serving,LOG_LEVEL=INFO,ENVIRONMENT=dev}" \
  --region ap-southeast-1

FUNCTION_NAME=cs361-faculty-api-dev FACULTY_ID=<id ที่มีจริงใน serving/faculties/> \
  ../scripts/smoke_test.sh
```

`smoke_test.sh` ยิงจริง 5 เคส: List 200, Detail 200, unknown 404, invalid id 400,
method 405 — ถ้าเคสไหน status ไม่ตรง script จะ exit non-zero
