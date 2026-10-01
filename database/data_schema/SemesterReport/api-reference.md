# API Reference — ระบบบันทึกภาระงานอาจารย์

REST over HTTPS | Auth: AWS Cognito (Bearer JWT) | Content-Type: `application/json`

## 1. ผู้ใช้และตำแหน่ง

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/me` | โปรไฟล์ตัวเอง + ตำแหน่งที่ถืออยู่ + สิทธิ์ในรอบปัจจุบัน | ทุกคน |
| GET | `/departments` | รายการสาขา | ทุกคน |
| POST | `/departments` | เพิ่มสาขา | admin |
| PATCH | `/departments/{id}` | แก้ชื่อ หรือปิด `is_active` | admin |
| GET | `/faculty-members?department=1&active=true` | รายชื่ออาจารย์ | ทุกคน |
| POST | `/faculty-members` | เพิ่ม (ผูก `cognito_sub`) | admin |
| GET | `/faculty-members/{id}` | รายคน | ทุกคน |
| PATCH | `/faculty-members/{id}` | แก้ rank, สาขา, `is_active` | admin |
| GET | `/faculty-members/{id}/positions` | ประวัติตำแหน่ง | admin, เจ้าตัว |
| POST | `/faculty-members/{id}/positions` | แต่งตั้ง | admin |
| PATCH | `/positions/{id}` | ปิดวาระ (ใส่ `end_date`) | admin |
| DELETE | `/positions/{id}` | ลบกรณีบันทึกผิด | admin |

---

## 2. เกณฑ์ภาระงาน

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/rubric-versions` | รายการฉบับเกณฑ์ | admin |
| POST | `/rubric-versions` | สร้างฉบับใหม่ (ส่ง `source_version_id` เพื่อก๊อปจากฉบับเก่า) | admin |
| GET | `/rubric-versions/{id}` | หัวข้อมูลฉบับ | admin |
| PATCH | `/rubric-versions/{id}` | แก้ได้เฉพาะฉบับที่ยังไม่มีรอบไหนใช้ | admin |
| **GET** | **`/rubric-versions/{id}/form`** | **ต้นไม้ทั้งฉบับ: category → section → item ในก้อนเดียว** | ทุกคน |
| GET | `/rubric-versions/{id}/categories` | หมวด 1-5 | admin |
| GET | `/rubric-categories/{id}/sections` | ข้อย่อยในหมวด | admin |
| POST | `/rubric-categories/{id}/sections` | เพิ่มข้อย่อย | admin |
| PATCH | `/rubric-sections/{id}` | แก้ชื่อ เพดาน จำนวนแถวสูงสุด | admin |
| DELETE | `/rubric-sections/{id}` | ลบ | admin |
| GET | `/rubric-sections/{id}/items` | ตัวเลือกในข้อ | admin |
| POST | `/rubric-sections/{id}/items` | เพิ่มตัวเลือก | admin |
| PATCH | `/rubric-items/{id}` | แก้น้ำหนัก หรือปิด `is_active` | admin |
| DELETE | `/rubric-items/{id}` | ลบ (ได้เฉพาะที่ยังไม่มี entry อ้างถึง) | admin |

`/form` เป็นเส้นที่หน้าเว็บเรียกบ่อยที่สุด ถ้าให้ frontend ไปไล่เรียก 3 ชั้นเองจะได้ request เป็นสิบ ก้อนนี้ cache ได้ยาวเพราะเกณฑ์ไม่เปลี่ยนระหว่างรอบ

---

## 3. รอบประเมิน

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/rounds?is_open=true` | รายการรอบ | ทุกคน |
| POST | `/rounds` | เปิดรอบใหม่ | admin |
| GET | `/rounds/{id}` | รายละเอียดรอบ | ทุกคน |
| PATCH | `/rounds/{id}` | แก้วันที่ หรือ `is_open` | admin |
| GET | `/rounds/{id}/submissions?department=1&status=dept_review` | ใบทั้งหมดในรอบ | หัวหน้าสาขา, คณะ |
| GET | `/rounds/{id}/report?department=1` | สรุปคะแนนทั้งสาขา สำหรับหน้า dashboard | หัวหน้าสาขา, คณะ |

เปิดปิดรอบใช้ PATCH ไม่ใช่ `/rounds/{id}/open` เพราะ `is_open` เป็นแค่ boolean ไม่ต้องเก็บประวัติ

---

## 4. ฟอร์ม

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/submissions?round=3&member=a3f8` | รายการใบ (กรองตามสิทธิ์ผู้เรียกอัตโนมัติ) | ทุกคน |
| POST | `/submissions` | สร้างใบของตัวเอง (ส่ง `round_id`) | อาจารย์ |
| GET | `/submissions/{id}` | ใบเดียวพร้อม entry ทั้งหมด | เจ้าของ, กรรมการ |
| DELETE | `/submissions/{id}` | ลบได้เฉพาะ `draft` | เจ้าของ |
| GET | `/submissions/{id}/summary` | ยอดสดรายหมวด + ผลตรวจเงื่อนไข (หน่วยกิต ≥ 6, เพดาน) | เจ้าของ |
| GET | `/submissions/{id}/totals` | ยอดที่ freeze ไว้ตอนส่ง | ทุกคนที่เห็นใบ |
| GET | `/submissions/{id}/pdf` | ออกฟอร์มเป็น PDF ตามแบบกระดาษ | ทุกคนที่เห็นใบ |

`summary` กับ `totals` ต่างกันตรงที่อันแรกคำนวณสดจาก entry (ใช้ตอนกรอก) อันหลังอ่านจาก `submission_category_total` ที่ล็อกไว้แล้ว (ใช้ตอนตรวจและออกเอกสาร)

---

## 5. การส่งและอนุมัติ

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/submissions/{id}/approvals` | ประวัติการส่ง ตีกลับ และเซ็นทั้งหมด | ทุกคนที่เห็นใบ |
| POST | `/submissions/{id}/approvals` | ส่ง / รับ / ตีกลับ / อนุมัติ | ตามตำแหน่ง |

เส้นเดียวจบทุกการเปลี่ยนสถานะ เพราะทุกอย่างคือการเพิ่มแถวใน `submission_approval` เหมือนกันหมด

```json
POST /submissions/8c1f.../approvals
{"decision": "returned", "comment": "ข้อ 2.3.1 ขาดเอกสาร Quartile"}
```

`role` ระบบเติมเองจากตำแหน่งของผู้เรียก ไม่รับจาก body

**ทางเลือก** ถ้าอยากให้ชื่อสื่อกว่านี้ แยก `POST /submissions/{id}/submission` (singleton) สำหรับการส่งโดยเฉพาะ แล้วให้ `/approvals` เหลือไว้สำหรับกรรมการอย่างเดียว รับได้ทั้งสองแบบ

---

## 6. รายการในฟอร์ม

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/submissions/{id}/entries?section=2.3.1` | รายการที่กรอกไว้ | เจ้าของ, กรรมการ |
| POST | `/submissions/{id}/entries` | เพิ่มหนึ่งบรรทัด | เจ้าของ |
| GET | `/entries/{id}` | บรรทัดเดียว | เจ้าของ, กรรมการ |
| PATCH | `/entries/{id}` | แก้ (เฉพาะ `draft`) | เจ้าของ |
| DELETE | `/entries/{id}` | ลบ (เฉพาะ `draft`) | เจ้าของ |

ตอบกลับทุกครั้งแนบ `score` ที่เซิร์ฟเวอร์คำนวณแล้ว ห้ามให้ frontend คำนวณเองแล้วส่งมา ไม่งั้นสูตรจะมีสองที่

```json
POST /submissions/8c1f.../entries
{
  "item_id": 1,
  "course_code": "CS222",
  "student_count": 60,
  "quantity": 3,
  "credits": 3.0,
  "details": {"hours": 45}
}
→ 201 {"id": "e001...", "score": 200.0, "weight_applied": 1.0}
```

---

## 7. การประเมินของผู้บริหาร

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/assessments?round=3&status=pending` | คิวงานของผู้ประเมิน | ผู้มีตำแหน่ง |
| GET | `/entries/{id}/assessments` | ค่าที่แต่ละคนให้ | ผู้ประเมิน, admin |
| PUT | `/entries/{id}/assessments/me` | ให้หรือแก้ค่าของตัวเอง | ผู้มีสิทธิ์ตามตำแหน่ง |
| DELETE | `/entries/{id}/assessments/me` | ถอนค่าที่ให้ไว้ | เจ้าของค่า |

ใช้ PUT กับ `/me` เพราะตารางมี unique `(entry_id, assessor_id)` อยู่แล้ว คนหนึ่งให้ได้ค่าเดียว PUT จึงเป็น idempotent พอดี เรียกซ้ำกี่ครั้งผลเหมือนเดิม และ client ไม่ต้องรู้ id ของแถว

---

## 8. หลักฐาน

| Method | Path | ทำอะไร | ใคร |
|---|---|---|---|
| GET | `/entries/{id}/evidence` | รายการไฟล์ | เจ้าของ, กรรมการ |
| POST | `/entries/{id}/evidence` | จองที่ สร้างแถว `pending` คืน presigned PUT URL | เจ้าของ |
| PATCH | `/evidence/{id}` | ยืนยันอัปโหลดเสร็จ ส่ง `status`, `checksum`, `size_bytes` | เจ้าของ |
| GET | `/evidence/{id}/content` | 302 ไป presigned GET URL | ผู้มีสิทธิ์เห็นใบ |
| DELETE | `/evidence/{id}` | ลบทั้งแถวและ object ใน S3 | เจ้าของ |

ไฟล์ไม่เคยวิ่งผ่าน API เลย ขึ้นและลงตรงกับ S3 ทั้งคู่ API ออกแต่ใบอนุญาตชั่วคราว

```
1. POST /entries/e011/evidence  → 201 {id, upload_url, expires_in: 900}
2. PUT  {upload_url}            → อัปตรงเข้า S3
3. PATCH /evidence/{id}         → {"status": "uploaded", "checksum": "...", "size_bytes": 842113}
```

---

## 9. ทะเบียน (อนาคต)

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/course-offerings?code=CS222&academic_year=2567&semester=2` | พร็อกซีอ่านจากทะเบียน คืนหน่วยกิตและจำนวน นศ. |

ทำเป็นเส้นอ่านอย่างเดียวแล้วให้ client เอาค่าไป PATCH ลง entry เองดีกว่าทำเป็น `POST /entries/{id}/sync` เพราะไม่ต้องสร้างคำกริยาใน path และระบบทะเบียนล่มก็ไม่ทำให้ฟอร์มพัง

---

## รหัสสถานะที่ใช้

| Code | ใช้เมื่อ |
|---|---|
| 200 | สำเร็จ |
| 201 | สร้างสำเร็จ แนบ `Location` header |
| 204 | ลบสำเร็จ ไม่มี body |
| 400 | รูปแบบ request ผิด |
| 401 | ไม่มี token หรือ token หมดอายุ |
| 403 | มีสิทธิ์ไม่พอ เช่น ไม่ใช่ผู้ประเมินของสาขานี้ |
| 404 | ไม่พบ หรือไม่มีสิทธิ์เห็น (ไม่แยกสองกรณีเพื่อไม่ให้เดาข้อมูลได้) |
| **409** | **พยายามแก้ใบที่ไม่ใช่ `draft` หรือสร้างใบซ้ำในรอบเดิม** |
| **422** | **ข้อมูลไม่ผ่าน validation ของ `field_schema` หรือค่าเกินช่วงของ item** |
| 429 | เรียกถี่เกิน |

แยก 409 กับ 422 ให้ชัด เพราะหน้าเว็บต้องแสดงคนละแบบ อันแรกคือ "แก้ไม่ได้แล้ว" อันหลังคือ "กรอกใหม่"

---

## ข้อตกลงอื่น

**Concurrency** — `PATCH /entries/{id}` และ `PATCH /evidence/{id}` รับ `If-Match` กับ ETag เพราะอาจารย์เปิดสองแท็บแล้วแก้พร้อมกันได้

**Pagination** — รายการที่ยาวได้ใช้ cursor: `?limit=50&cursor=...` ตอบกลับใส่ `next_cursor` ไม่ใช้ offset เพราะข้อมูลเพิ่มระหว่างเลื่อนหน้าได้

**Error body**

```json
{
  "error": "submission_locked",
  "message": "แก้ไขไม่ได้เพราะฟอร์มส่งไปแล้ว",
  "details": {"status": "dept_approved"}
}
```

`error` เป็น machine-readable ให้ frontend เอาไปแยกเคส `message` เป็นภาษาไทยไว้แสดงผลตรง ๆ

**Versioning** — ขึ้นต้นทุกเส้นด้วย `/v1` เผื่อวันที่ต้องเปลี่ยนรูปแบบ response โดยไม่พังของเดิม
