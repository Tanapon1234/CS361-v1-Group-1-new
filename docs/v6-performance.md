# V6 Performance & Cost: รายงานระดับสาขา (#319)

เลือก critical path หนึ่งเส้นคือ **รายงานสาขา** `GET /api/v3/departments/{id}/report` (FR7, FR8) เพราะเป็น read ที่หนักที่สุด รวมข้อมูลหลายอาจารย์หลายปีการศึกษาในคำขอเดียว

## วิธีวัด

ข้อมูลทดสอบ: อาจารย์ 400 คนในสาขา CS, ใบภาระงาน 5 ปีการศึกษา (2568-2572), 5 หมวดต่อใบ, ราว 9,000 แถว category total และอาจารย์ 1 ใน 10 ไม่มีข้อมูล (ให้รายการ `missing` มีเนื้อหา) สร้างและลบด้วย `scripts/loadtest/seed.py` ซึ่งแท็กทุกแถวด้วยอีเมล `loadtest-*@loadtest.invalid` จึงลบได้ครบโดยไม่แตะข้อมูลจริง

โหลด: Locust ใน `scripts/loadtest/locustfile.py` ผู้ใช้ 30 คน 60 วินาที ใช้บัญชีทดสอบ 10 บัญชี สัดส่วนอ่านต่อเขียนประมาณ 80:20

| การกระทำ | endpoint | น้ำหนัก |
|---|---|---|
| หน้ารายการ | `GET /submissions?lecturer_id=` | 6 |
| หน้ารายละเอียด | `GET /submissions/{id}` | 5 |
| รายงานสาขา | `GET /departments/{id}/report` | 5 |
| บันทึกข้อมูล | `POST /submissions/{id}/entries` | 4 |

ก่อนและหลังใช้ข้อมูล, เครื่อง, จำนวน worker (1) และ DB เดียวกัน ก่อนแต่ละรอบ seed ใหม่ และโค้ด "ก่อน" รันจาก `develop` ก่อนแก้

## Bottleneck ที่พบ

1. SQL ของรายงานเองเร็ว (`EXPLAIN ANALYZE` ราว 40 ms, ใช้ index ทั้งหมด) จึงไม่ต้องเพิ่ม index
2. query หลักรวมการสร้าง entity ใช้ 97-198 ms ขณะที่ SQL ล้วนใช้ราว 40 ms ส่วนต่างคือการสร้าง object `Lecturer` ทั้งแถว (15 คอลัมน์) ซ้ำให้ทุกแถวของรายงาน ทั้งที่ใช้แค่ `lecturer_id` กับ `name_th`
3. รายการ `missing` ยิง query หนึ่งครั้งต่อปีการศึกษา ในช่วง 5 ปีคือ 5 ครั้ง บน Aurora ผ่าน Lambda ใน VPC แต่ละ round trip แพงกว่าบนเครื่องนี้

## สิ่งที่แก้

- `list_department_category_totals` เลือกเฉพาะ 7 คอลัมน์ที่รายงานใช้ แทนที่จะโหลด entity
- `find_lecturers_with_department_data` รับช่วงปีและคืน `(lecturer_id, year)` ใน query เดียว
- ไม่เปลี่ยน API, DTO หรือ migration และไม่เพิ่ม resource

## ผลก่อน-หลัง

เครื่องเดียวกัน PostgreSQL local (ไม่ใช่ Aurora) รอบละหนึ่งครั้ง ตัวเลขดิบอยู่ใน `evidence/v6/`

| ตัวชี้วัด | ก่อน | หลัง |
|---|---:|---:|
| SQL ต่อ request ของรายงาน | 14 | 10 |
| รายงาน request เดี่ยว (median, warm) | 198 ms | 134 ms |
| รายงานภายใต้ 30 ผู้ใช้ (median / p95) | 1,800 / 2,800 ms | 440 / 1,100 ms |
| รายงาน ค่าเฉลี่ย | 1,732 ms | 497 ms |
| ทุก endpoint รวม (median / p95) | 750 / 2,200 ms | 190 / 780 ms |
| throughput รวม | 13.6 req/s | 19.1 req/s |
| failure | 0 | 0 |

ตัวเลข endpoint อื่นที่เร็วขึ้น (เช่น หน้ารายการ 590 เป็น 140 ms median) ไม่ได้มาจากการแก้โค้ดของ endpoint นั้น แต่เพราะ worker เดียวไม่ต้องใช้ CPU กับรายงานที่หนักอยู่ตลอด นี่คือผลข้างเคียงที่ตรวจสอบได้จากการวัด ไม่ใช่การปรับปรุงเฉพาะ endpoint นั้น

ตรวจความถูกต้อง: response ของรายงานก่อนและหลังเท่ากันทุกแถว (5,000 แถว `rows` และ 310 แถว `missing`) เมื่อไม่นับ `lecturer_id` ที่สุ่มใหม่ทุกครั้งที่ seed

## ผลต่อต้นทุน

- ไม่เพิ่ม resource ไม่เพิ่ม index ไม่เพิ่ม storage
- Lambda คิดตามระยะเวลา x หน่วยความจำ (ตั้งไว้ 1,024 MB) เวลาต่อ request ของรายงานลดราว 32% (198 เหลือ 134 ms) ค่า GB-วินาทีต่อ request ลดตามกันโดยประมาณ
- Aurora Serverless v2 คิดตาม ACU การลด query ต่อ request ลดงานของ DB เล็กน้อย ตัวเลข ACU จริงยังไม่ได้วัด

## ข้อจำกัดและข้อสังเกต

- วัดบน PostgreSQL local ไม่ใช่ Aurora และ Lambda จึงบอกได้เฉพาะการเปลี่ยนแปลงสัมพัทธ์ ยังไม่มี cold start, latency ของเครือข่าย VPC หรือ ACU scaling
- รอบละหนึ่งครั้ง ตัวเลขอาจแกว่งตามเครื่อง ควรรันซ้ำก่อนอ้างตัวเลขเป๊ะ
- ยังไม่ได้รัน Locust กับระบบที่ deploy บน AWS ต้องใช้ URL และ credits ของทีม ดูวิธีรันที่หัวไฟล์ `locustfile.py` (ใช้ `LOADTEST_TOKENS` กับ Cognito)
- พบว่าข้อมูล 9,000 แถวถูกตัดที่ `MAX_REPORT_ROWS = 5000` โดยไม่มีสัญญาณบอกผู้ใช้ ซึ่งทำให้ยอดรวมไม่ครบถ้วนเมื่อสาขาใหญ่ขึ้น ไม่ได้แก้ใน PR นี้ เพราะต้องตัดสินใจเรื่อง pagination หรือการสรุปฝั่ง DB ควรเปิด issue แยก

## วิธีรันซ้ำ

```bash
cd backend
uv run python ../scripts/loadtest/seed.py seed --database-url postgresql://USER:PASS@HOST:PORT/DBNAME
uv run --with locust locust -f ../scripts/loadtest/locustfile.py --host http://127.0.0.1:8000 \
  --headless -u 30 -r 10 -t 60s --csv result
uv run python ../scripts/loadtest/seed.py cleanup --database-url postgresql://USER:PASS@HOST:PORT/DBNAME
```

ชี้ `--database-url` ไปที่ฐานข้อมูลพัฒนาหรือทดสอบเท่านั้น ห้ามชี้ไปข้อมูลจริง
