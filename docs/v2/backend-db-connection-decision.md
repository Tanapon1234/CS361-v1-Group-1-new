# การตัดสินใจ: FastAPI backend ต่อ Aurora ด้วยวิธีไหน (#197)

สถานะ: **เสนอ รอทีมยืนยัน**

## โจทย์

backend (`backend/app/`) ใช้ SQLModel + psycopg ต่อ PostgreSQL ตรง ตอน deploy ขึ้น AWS มีทางเลือก 2 ทาง

| | A. Lambda ใน VPC + psycopg | B. Lambda นอก VPC + RDS Data API |
|---|---|---|
| โค้ดที่ต้องแก้ | แทบไม่มี: เพิ่มการอ่านรหัสผ่านจาก Secrets Manager ตอนเปิด connection | เปลี่ยน driver เป็น `sqlalchemy-aurora-data-api` และแก้การแปลง error ทุกจุด |
| พฤติกรรม PostgreSQL | ครบ: trigger, enum, JSONB, `sqlstate` ของ error | driver ส่ง error เป็น `DatabaseError` ไม่ใช่ `IntegrityError` → ชื่อซ้ำ / FK / trigger ล็อก entry จะกลายเป็น 500 แทน 409/400, timestamp ถูกตัดเหลือ ms, ทดสอบในเครื่องไม่ได้ |
| network | Lambda อยู่ใน private subnet เดียวกับ Aurora ต้องมี VPC endpoint ของ S3 (gateway, ฟรี) และ Secrets Manager (interface, ~0.01 USD/ชม./AZ) | ไม่ต้องมี VPC |
| cold start | +1-2 วินาทีตอนสร้าง ENI ครั้งแรก (Lambda รุ่นใหม่เร็วขึ้นมากแล้ว) | เร็ว แต่ทุก query เป็น HTTPS call (ช้ากว่าต่อ query) |
| รหัสผ่านหมุน (rotation) | อ่าน secret ใหม่ทุก 5 นาที (`DB_SECRET_ARN`) | Data API จัดการให้ |
| ค่าใช้จ่ายเพิ่ม | interface endpoint 2 AZ ประมาณ 15 USD/เดือน | ไม่มี |

## ข้อเสนอ: A. Lambda ใน VPC + psycopg

- business rule หลายข้ออาศัย error ของ PostgreSQL (unique, FK, trigger `check_violation` ของ `submission_entry`) ถ้าใช้ Data API ต้องแก้หลายจุดและทดสอบในเครื่องไม่ได้
- เทสต์ทั้งหมด (รวม integration) รันกับ psycopg อยู่แล้ว ของที่ deploy จะตรงกับที่ทดสอบ
- โค้ดที่เพิ่ม: `DB_SECRET_ARN` ใน `app/core/config.py` ถ้าตั้งไว้ `app/core/database.py` จะอ่าน username / password (และ host / port ถ้ามีใน secret) จาก Secrets Manager ทุกครั้งที่เปิด connection ใหม่ โดย cache ไว้ 5 นาที

## ถ้า account ใช้ VPC ไม่ได้

บาง account (เช่นที่ต้องใช้ Aurora Express Configuration ใน `aws-foundation.yaml`) อาจสร้าง Lambda ใน VPC หรือ VPC endpoint ไม่ได้ ให้ใช้ทาง B แทน:

1. เพิ่ม `sqlalchemy-aurora-data-api` และสร้าง engine ด้วย `postgresql+auroradataapi://:@/{DB_NAME}` + `connect_args={"aurora_cluster_arn": ..., "secret_arn": ...}`
2. แก้ `app/v2/services/db_errors.py` ให้รู้จัก error ของ `aurora_data_api` (ชื่อ class เช่น `UNIQUE_VIOLATION`)
3. รัน integration test กับ Aurora dev (ไม่ใช่ PostgreSQL ในเครื่อง)

## ผลต่อการ์ดอื่น

- #198 รัน migration: Aurora อยู่ใน private subnet จึงใช้ RDS Data API รันไฟล์ SQL (`scripts/apply_v2_migrations.py`) ไม่ต้องมีเครื่องใน VPC
- #199 deploy: template `infra/v2/backend-api.yaml` สร้าง Lambda ใน VPC + VPC endpoint + API Gateway
