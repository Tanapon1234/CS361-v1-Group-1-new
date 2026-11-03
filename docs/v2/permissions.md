# บทบาทและสิทธิ์ (V3 Secure Faculty Workspace, #214)

> **V3 ต่างจาก V2** ตั้งแต่ #291: `staff` ใน V3 ไม่มีสิทธิ์สร้าง/แก้ master data (อาจารย์, สาขา, เกณฑ์, รอบ, ตำแหน่ง) อีกแล้ว เหลือแค่ดู report (จำกัดสาขาตัวเอง) และรับเรื่องใบภาระงาน (`receiver`) เท่านั้น ทุกอย่างที่เคยเป็น `staff` เปลี่ยนเป็น `admin` V2 (legacy) ยังเป็นแบบเดิม

## บทบาท

| บทบาท | มาจาก | ใคร |
|---|---|---|
| `lecturer` | ทุกคนที่ login แล้วจับคู่กับแถวใน `lecturer` ได้ | อาจารย์ทุกคน |
| `staff` | Cognito group `staff` | เจ้าหน้าที่ประจำสาขา: ดู report ได้เฉพาะสาขาตัวเอง และรับเรื่องใบภาระงาน (`receiver`) ไม่มีสิทธิ์สร้าง/แก้ master data |
| `reviewer` | Cognito group `reviewer` | ผู้ตรวจสอบ: ดู report ได้เฉพาะสาขาตัวเอง และรับรอง/ตีกลับผลงานตีพิมพ์และหลักฐาน |
| `executive` | Cognito group `executive` | ผู้บริหาร: ดูได้ทุกอย่าง ทั้ง report ของทุกรอบและทุกสาขา |
| `admin` | Cognito group `admin` | ผู้ดูแลระบบ: ทำได้ทุกอย่าง (รวมสร้าง/แก้ master data ที่ staff ทำไม่ได้แล้ว) และดู audit log |

ตำแหน่งบริหารใน `member_position` (ไม่ใช่ Cognito group) ใช้กำหนดว่าใคร **ลงนามหรือประเมิน** อะไรได้

- `dept_chair`, `dept_committee` ของสาขา X: ดูใบภาระงานของสาขา X และลงนามขั้นของตัวเอง
- `assessor_position` ของข้อในเกณฑ์ (เช่น `exec_committee`): ให้ค่าข้อนั้นได้

ทุก endpoint ต้อง login ยกเว้น `/health` ถ้าไม่ได้ login ตอบ **401** ถ้า login แล้วแต่ไม่มีสิทธิ์ ตอบ **403**

## ตารางสิทธิ์

"ตัวเอง" = `lecturer_id` ใน path คือคนที่ login "เจ้าของ" = อาจารย์เจ้าของใบภาระงาน
"ผู้ดูทั้งหมด" = `staff`, `reviewer`, `executive`, `admin`

| กลุ่ม endpoint | อ่าน | สร้าง / แก้ / ลบ |
|---|---|---|
| `/me` | ทุกคน | – |
| `/lecturers`, `/lecturers/{id}` | ทุกคน | สร้าง, activate/deactivate: `admin` · แก้: ตัวเอง (ข้อมูลติดต่อ) หรือ `admin` (ทุก field) |
| รูป / CV ของอาจารย์ | ทุกคน | ตัวเอง, `admin` |
| การศึกษา, หัวข้อวิจัยและความเชี่ยวชาญของอาจารย์, โปรไฟล์ภายนอก | ทุกคน | ตัวเอง, `admin` |
| master หัวข้อวิจัย / ความเชี่ยวชาญ | ทุกคน | เพิ่ม: ทุกคน · แก้ / ลบ: `admin` |
| `/publications` | ทุกคน | เพิ่ม: ทุกคน (ต้องใส่ตัวเองเป็นผู้แต่ง ยกเว้น `staff`, `admin`) · แก้ / ลบ: ผู้แต่ง, `staff`, `admin` · ผลงานที่รับรองแล้ว: `staff`, `admin` เท่านั้น (ยังไม่เปลี่ยน — คนละเรื่องกับ master data) |
| การรับรองผลงาน / หลักฐาน | ผู้ดูทั้งหมด | `reviewer`, `admin` |
| `/departments`, ตำแหน่งบริหาร, เกณฑ์ (`/rubric-*`), สร้าง/แก้รอบ | ทุกคน | `admin` |
| ใบภาระงานในรอบ, report ของรอบ | เจ้าของ (self) · `dept_chair`/`dept_committee` เฉพาะสาขาตัวเอง · `staff`/`reviewer` เฉพาะสาขาตัวเอง (ของอาจารย์ที่เข้าระบบ) · `executive`/`admin` ทุกสาขา | – |
| `/departments/{id}/report` (V4) | เหมือนแถวบน (ใบภาระงานในรอบ) | – |
| `/submissions`, entries, หลักฐาน | เจ้าของ, ผู้ดูทั้งหมด, `dept_chair` / `dept_committee` ของสาขาของใบ · list ของคนทั่วไปเห็นแค่ใบตัวเอง, `staff`/`reviewer` เห็นแค่สาขาตัวเอง | เจ้าของ ตอนใบเป็น `draft` / `returned` |
| ลงนามใบ (`/approvals`) | เหมือนอ่านใบ | ผู้ส่ง: เจ้าของ · รับเรื่อง: `staff`, `admin` · หัวหน้าสาขา / กรรมการสาขา: ผู้ดำรงตำแหน่งนั้นในสาขาของใบ |
| ประเมิน (`/assessments`) | คิวของตัวเอง · ค่าที่ทุกคนให้: เจ้าของ, ผู้ดูทั้งหมด | ผู้ดำรงตำแหน่ง `assessor_position` ของข้อนั้น |
| `/lecturers/{id}/work` (ผลงานรายปี) | ตัวเอง, ผู้ดูทั้งหมด, `dept_chair` / `dept_committee` ของสาขาของอาจารย์ | – |
| audit log | `admin` | – |

## ตอนพัฒนา (ไม่ใช่ prod)

ถ้า `DEV_AUTH_HEADER_ENABLED=true` และ `ENVIRONMENT` ไม่ใช่ `prod` ใช้ header แทน Cognito ได้

- `X-Lecturer-Id: <uuid>`: ทำในนามอาจารย์คนนี้
- `X-Dev-Roles: staff,admin`: บทบาทเพิ่ม (ไม่ใส่ = `lecturer` อย่างเดียว) ใส่อย่างเดียวโดยไม่มี `X-Lecturer-Id` ได้ ใช้กับ script ที่ยังไม่มีอาจารย์ในระบบ

## ที่อยู่ในโค้ด

- ตารางนี้อยู่ใน `backend/app/v2/permissions.py` (ROUTE_RULES) router ของ `/api/v2` เช็คทุก request จากตารางนี้ เทสต์ fail ถ้ามี route ที่ไม่อยู่ในตาราง
- เรื่องที่ต้องดูข้อมูลก่อนตัดสิน (เจ้าของใบ, สาขาของใบ, ผู้แต่ง) เช็คใน service
