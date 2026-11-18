# V5 Automation (#320)

เป้าหมาย: สร้างหรือ deploy ระบบซ้ำได้จาก repo โดยไม่ต้องจำลำดับหรือพารามิเตอร์ด้วยมือ

## อะไรเป็น Infrastructure as Code อยู่แล้ว

| ส่วน | อยู่ที่ | เครื่องมือ |
|---|---|---|
| Aurora PostgreSQL, S3, IAM, log groups | `infra/v2/aws-foundation.yaml` | CloudFormation |
| Cognito user pool และกลุ่ม | `infra/v2/cognito.yaml` | CloudFormation |
| Lambda + API Gateway + VPC endpoints ของ backend | `infra/v2/backend-api.yaml` | CloudFormation |
| Schema ฐานข้อมูล | `database/migrations/*.sql` | `backend/scripts/apply_migrations.py` (บันทึกไฟล์ที่รันแล้วใน `schema_migration`) |
| Frontend | repo นี้ | Vercel build จาก git |

## สิ่งที่ V5 เพิ่ม

1. `scripts/deploy-all.sh` จุดเดียวที่เรียงขั้นตอน foundation, migrations, cognito, backend, smoke และหยุดทันทีที่ขั้นใดล้มเหลว
2. `.github/workflows/ci.yml` ตรวจทุก PR: ruff + pytest (backend), lint + build (frontend), `cfn-lint` ทุก template, `bash -n` ทุก script และ `deploy-all.sh --dry-run`

## วิธีใช้

```bash
cp infra/v2/parameters.dev.example.json infra/v2/parameters.dev.local.json   # กรอก VpcId, subnet (ไฟล์ *.local.json ไม่ถูก commit)
export FOUNDATION_PARAMS=infra/v2/parameters.dev.local.json
scripts/deploy-all.sh --dry-run          # ดูลำดับและ input ที่ขาด ไม่เรียก AWS
scripts/deploy-all.sh                    # deploy ทั้งหมด
scripts/deploy-all.sh --skip foundation,cognito   # deploy เฉพาะที่เปลี่ยน
```

บัญชีทดสอบ Cognito: ตั้ง `COGNITO_USERS_CSV` ชี้ไปไฟล์ `*.local.csv` (รูปแบบดู `infra/v2/cognito-users.example.csv`)

ทุกขั้น re-run ได้: `cloudformation deploy` เป็น idempotent และ migration รันเฉพาะไฟล์ที่ยังไม่เคยบันทึก

## สิ่งที่ยังเป็นขั้นตอนมือ และเหตุผล

| ขั้นตอน | เหตุผล |
|---|---|
| ใส่ VPC / subnet ใน parameter file | เป็นค่าของบัญชี AWS แต่ละทีม ไม่ควรอยู่ใน git |
| บัญชีที่ไม่รองรับ Aurora ปกติ ต้องสร้าง cluster แบบ Express เอง (`AuroraProvisioningMode=external-express`) | CloudFormation สร้างไม่ได้ในบัญชีแบบนั้น ดู `infra/v2/README.md` |
| ฐานข้อมูลที่มีข้อมูลจาก V1 อยู่แล้วต้องรัน `apply_migrations --baseline 001_base` ก่อนครั้งแรก | 001 ถูกรันโดย V1 migration แล้ว |
| ตั้งตัวแปรบน Vercel (ดู `frontend/README.md`) และเพิ่ม origin ของ Vercel ใน `WebAllowedOrigins` | Vercel ไม่อยู่ใน CloudFormation ของทีม |
| `DEV_AUTH_HEADER_ENABLED=false` ก่อนใช้งานจริง | เป็นการตัดสินใจด้านความปลอดภัยของคนที่ deploy |
| Locust กับระบบบน AWS | ใช้ credits ของทีม ดู `docs/v6-performance.md` |

## สิ่งที่ตรวจแล้วและยังไม่ได้ตรวจ

ตรวจแล้ว (ในเครื่อง): `bash -n` ทุก script, `deploy-all.sh --dry-run` ทั้งกรณี input ครบ ขาด และ `--skip` ผิดชื่อ, `cfn-lint` ทั้ง 4 template ไม่มี error (มี warning W1030 8 จุด จากค่า default ว่างของ ARN ที่ไม่ได้ใช้ในโหมดปกติ ซึ่ง CI ยกเว้นไว้)

ยังไม่ได้ตรวจ: การรัน `deploy-all.sh` จริงบน AWS (จะสร้างหรือเปลี่ยน resource จริง จึงไม่ได้รัน) และผล CI บน GitHub ซึ่งรู้ได้เมื่อ PR รัน
