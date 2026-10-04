# Lecturer Education API

สัญญา API สำหรับเรียกดู เพิ่ม และดูรายละเอียดประวัติการศึกษาของอาจารย์ใน V2

> สถานะ: เตรียม handler, validation, service, DAO, automated tests และ Postman collection แล้ว ยังไม่ได้เชื่อม API Gateway หรือ frontend

## Endpoint

### List lecturer educations

```http
GET /api/v2/lecturers/{lecturerId}/educations
```

คืนรายการประวัติการศึกษาของ lecturer ที่มีสถานะ `ACTIVE` เรียงตาม `display_order` จากน้อยไปมาก; กรณีลำดับเท่ากันจะเรียงตาม `created_at` และ `id` เพื่อให้ผลลัพธ์คงที่ ไม่มี pagination

ตัวอย่าง response `200 OK`:

```json
{
  "items": [
    {
      "id": "edu_...",
      "faculty_id": "fac_prapaporn-rattanatamrong",
      "degree": "Ph.D.",
      "field_of_study": "Computer Science",
      "institution": "Example University",
      "country": "Thailand",
      "graduation_year": 2560,
      "display_order": 0,
      "created_at": "2026-10-05 00:00:00+00",
      "updated_at": "2026-10-05 00:00:00+00"
    }
  ],
  "meta": {
    "count": 1
  }
}
```

หาก lecturer ยังไม่มีประวัติ จะคืน `200 OK` พร้อม `items: []` และ `meta.count: 0`

### Get lecturer education detail

```http
GET /api/v2/lecturers/{lecturerId}/educations/{educationId}
```

คืนรายการ education รายการเดียว โดยต้องเป็นของ lecturer ที่ระบุและ lecturer ต้องมีสถานะ `ACTIVE`. `educationId` ใช้ค่า `faculty_education.id`.

ตัวอย่าง response `200 OK`:

```json
{
  "data": {
    "id": "edu_...",
    "faculty_id": "fac_prapaporn-rattanatamrong",
    "degree": "Ph.D.",
    "field_of_study": "Computer Science",
    "institution": "Example University",
    "country": "Thailand",
    "graduation_year": 2560,
    "display_order": 0,
    "created_at": "2026-10-05 00:00:00+00",
    "updated_at": "2026-10-05 00:00:00+00"
  }
}
```

หากไม่พบ lecturer หรือ lecturer ไม่ active จะคืน `404 LECTURER_NOT_FOUND`; หากไม่พบ education ที่ตรงกับทั้ง `lecturerId` และ `educationId` จะคืน `404 EDUCATION_NOT_FOUND`.

### Create lecturer education

```http
POST /api/v2/lecturers/{lecturerId}/educations
Content-Type: application/json
```

`lecturerId` ใช้ค่า `faculty.id` จากฐานข้อมูล V2 เช่น `fac_prapaporn-rattanatamrong` และจะบันทึกลง `faculty_education.faculty_id`

## Request

ส่งข้อมูลการศึกษาอย่างน้อยหนึ่ง field:

```json
{
  "degree": "Ph.D.",
  "field_of_study": "Computer Science",
  "institution": "Example University",
  "country": "Thailand",
  "graduation_year": 2560
}
```

| Field | Required | Validation | Database field |
|---|---|---|---|
| `degree` | อย่างน้อยหนึ่งในกลุ่มข้อมูลการศึกษา | string หรือ null; trim ช่องว่างหัวท้าย | `faculty_education.degree` |
| `field_of_study` | อย่างน้อยหนึ่งในกลุ่มข้อมูลการศึกษา | string หรือ null; trim ช่องว่างหัวท้าย | `faculty_education.field_of_study` |
| `institution` | อย่างน้อยหนึ่งในกลุ่มข้อมูลการศึกษา | string หรือ null; trim ช่องว่างหัวท้าย | `faculty_education.institution` |
| `country` | อย่างน้อยหนึ่งในกลุ่มข้อมูลการศึกษา | string หรือ null; trim ช่องว่างหัวท้าย | `faculty_education.country` |
| `graduation_year` | อย่างน้อยหนึ่งในกลุ่มข้อมูลการศึกษา | integer ตั้งแต่ 1 ถึง 9999 | `faculty_education.graduation_year` |
| `display_order` | ไม่บังคับ | integer ตั้งแต่ 0 ขึ้นไป; หากไม่ส่งจะกำหนดลำดับถัดไป | `faculty_education.display_order` |

ไม่รับ field อื่น เช่น `id` หรือ `faculty_id`; server สร้าง education ID เองและใช้ `lecturerId` จาก path เป็นเจ้าของข้อมูล

## Responses

สร้างสำเร็จคืน `201 Created` พร้อม `Location` header:

```json
{
  "data": {
    "id": "edu_...",
    "faculty_id": "fac_prapaporn-rattanatamrong",
    "degree": "Ph.D.",
    "field_of_study": "Computer Science",
    "institution": "Example University",
    "country": "Thailand",
    "graduation_year": 2560,
    "display_order": 0,
    "created_at": "2026-10-05 00:00:00+00",
    "updated_at": "2026-10-05 00:00:00+00"
  }
}
```

| Status | Code | เงื่อนไข |
|---:|---|---|
| 200 | — | GET สำเร็จ; คืนรายการและจำนวน |
| 200 | — | GET detail สำเร็จ; คืน education ใน `data` |
| 201 | — | POST สร้างรายการสำเร็จ; คืน education ที่สร้างพร้อม `Location` |
| 400 | `VALIDATION_ERROR` | ID ใน path หรือ request body ไม่ผ่าน validation |
| 404 | `LECTURER_NOT_FOUND` | ไม่พบ lecturer หรือ lecturer ไม่ได้อยู่ในสถานะ `ACTIVE` |
| 404 | `EDUCATION_NOT_FOUND` | ไม่พบ education ที่อยู่ภายใต้ lecturer ที่ระบุ |
| 404 | `NOT_FOUND` | path ไม่ตรงกับ endpoint |
| 405 | `METHOD_NOT_ALLOWED` | method ไม่รองรับ; collection ส่ง `Allow: GET, POST`, detail ส่ง `Allow: GET` |
| 500 | `INTERNAL_ERROR` | เกิดข้อผิดพลาดภายใน โดยไม่ส่งรายละเอียดฐานข้อมูลกลับไปยัง client |

สำหรับ POST, DAO ใช้ RDS Data API transaction: lock แถว lecturer ที่ active, กำหนด `display_order` ถ้าไม่ได้ระบุ, insert ลง `faculty_education`, แล้ว commit; เมื่อเกิดข้อผิดพลาดจะ rollback

Postman collection สำหรับ GET list, GET detail, POST และ validation error อยู่ที่ [`postman/lecturer-education-create.postman_collection.json`](../../postman/lecturer-education-create.postman_collection.json) ตั้งค่า `baseUrl`, `lecturerId` และ `educationId` (ID ที่มีอยู่ของ lecturer นั้น) ก่อนใช้ หลังเชื่อม HTTP route แล้ว
