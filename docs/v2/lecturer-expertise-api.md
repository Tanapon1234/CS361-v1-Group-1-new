# Lecturer Expertise Mapping API

เอกสารนี้อธิบาย API สำหรับอ่านและจัดการรายการ expertise ของ lecturer ตาม Issue #151

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v2/lecturers/{lecturerId}/expertise` | อ่านรายการ expertise ของ lecturer |
| `PUT` | `/api/v2/lecturers/{lecturerId}/expertise` | แทนที่รายการ expertise ทั้งหมด |
| `DELETE` | `/api/v2/lecturers/{lecturerId}/expertise/{expertiseId}` | นำ expertise หนึ่งรายการออกจาก lecturer |

IDs ใช้ชนิด string ตาม schema V2 ซึ่งกำหนด primary key เป็น `text` เช่น `fac_1` และ `exp_1`.

## `GET /api/v2/lecturers/{lecturerId}/expertise`

Response เมื่อเชื่อม persistence แล้ว:

```json
{
  "items": [
    {
      "id": "exp_1",
      "faculty_id": "fac_1",
      "value": "Data Mining",
      "visibility": "PUBLIC"
    }
  ],
  "meta": {
    "count": 1
  }
}
```

แต่ละ item ใช้ DTO เดียวกับ expertise API และ `id` เป็น ID ของแถว expertise ใน `faculty_interest`.

## `PUT /api/v2/lecturers/{lecturerId}/expertise`

แทนที่รายการ expertise ทั้งหมดของ lecturer ด้วย IDs ที่ส่งมา:

```http
PUT /api/v2/lecturers/fac_1/expertise
Content-Type: application/json
```

```json
{
  "expertiseIds": ["exp_1", "exp_2"]
}
```

กติกา validation:

- body ต้องเป็น JSON object ที่มี `expertiseIds` เท่านั้น
- `expertiseIds` ต้องเป็น array ของ string IDs ที่ไม่ว่าง
- ตัดช่องว่างหัวท้ายของแต่ละ ID
- ปฏิเสธ ID ซ้ำหลังตัดช่องว่าง
- ยอมรับ array ว่างเพื่อแทนที่รายการทั้งหมดด้วยรายการว่าง

Response เมื่อเชื่อม persistence แล้วใช้ envelope `items` และ `meta.count` เช่นเดียวกับ GET.
Body ที่ไม่ถูกต้องตอบ `400 INVALID_BODY`.

## `DELETE /api/v2/lecturers/{lecturerId}/expertise/{expertiseId}`

นำ expertise ที่ระบุออกจาก lecturer และเมื่อสำเร็จตอบ `204 No Content` โดยไม่มี response body.

## Response and Error Behavior

| Status | Code | Meaning |
|---:|---|---|
| `200` | — | GET หรือ PUT สำเร็จ |
| `204` | — | ลบ mapping สำเร็จ ไม่มี response body |
| `400` | `INVALID_BODY` | body ของ PUT ไม่ถูกต้อง |
| `404` | `NOT_FOUND` | ไม่พบ route |
| `405` | `METHOD_NOT_ALLOWED` | method ไม่รองรับบน route |
| `501` | `NOT_IMPLEMENTED` | persistence ยังไม่ได้เชื่อมต่อ |
| `500` | `INTERNAL_ERROR` | เกิดข้อผิดพลาดที่ไม่คาดหมาย |

Error response ใช้รูปแบบ:

```json
{
  "error": {
    "code": "INVALID_BODY",
    "message": "Request body must contain only expertiseIds",
    "details": {
      "field": "expertiseIds"
    }
  }
}
```

## Persistence Boundary

V2 schema เก็บ expertise เป็นแถวใน `faculty_interest` โดยระบุ `interest_type='EXPERTISE'`; `faculty_id` อ้างถึง lecturer และ `id` เป็น text primary key. ข้อจำกัด unique `(faculty_id, interest_type, value)` ป้องกัน expertise value ซ้ำสำหรับ lecturer เดียวกัน.

API ในชุดนี้เป็น scaffold: DAO แสดง persistence boundary แต่ยังไม่เชื่อมฐานข้อมูล ดังนั้น GET, PUT และ DELETE จะตอบ `501 NOT_IMPLEMENTED` เมื่อเรียก controller โดยไม่มี DAO implementation. Authentication/login ยังไม่ได้เชื่อมใน API scaffold นี้.
