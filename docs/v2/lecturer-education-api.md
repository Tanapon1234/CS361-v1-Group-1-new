# Lecturer Education POST API

สัญญา API สำหรับเพิ่มประวัติการศึกษาของอาจารย์ใน V2

> สถานะ: เตรียม handler, validation, service, DAO, automated tests และ Postman collection แล้ว ยังไม่ได้เชื่อม API Gateway หรือ frontend

## Endpoint

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
| 400 | `VALIDATION_ERROR` | lecturer ID หรือ request body ไม่ผ่าน validation |
| 404 | `LECTURER_NOT_FOUND` | ไม่พบอาจารย์หรืออาจารย์ไม่ได้อยู่ในสถานะ `ACTIVE` |
| 404 | `NOT_FOUND` | path ไม่ตรงกับ endpoint |
| 405 | `METHOD_NOT_ALLOWED` | method ไม่ใช่ POST; response ส่ง `Allow: POST` |
| 500 | `INTERNAL_ERROR` | เกิดข้อผิดพลาดภายใน โดยไม่ส่งรายละเอียดฐานข้อมูลกลับไปยัง client |

DAO ใช้ RDS Data API transaction: lock แถว lecturer ที่ active, กำหนด `display_order` ถ้าไม่ได้ระบุ, insert ลง `faculty_education`, แล้ว commit; เมื่อเกิดข้อผิดพลาดจะ rollback

Postman collection สำหรับ request POST และ validation error อยู่ที่ [`postman/lecturer-education-create.postman_collection.json`](../../postman/lecturer-education-create.postman_collection.json) ตั้งค่า `baseUrl` และ `lecturerId` ก่อนใช้ หลังเชื่อม HTTP route แล้ว
