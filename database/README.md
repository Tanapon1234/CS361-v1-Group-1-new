# V2 Database Baseline

โฟลเดอร์นี้เก็บ SQL baseline สำหรับ V2 Faculty Output Repository

ไฟล์หลัก:

- `migrations/001_base.sql` - schema baseline สำหรับ Aurora PostgreSQL
- `seeds/001_master_data.sql` - seed master data สำหรับ work category และ work type

---

## How To Review

การ์ด #47 ยังไม่ต้อง deploy database จริง

สิ่งที่ reviewer ควรตรวจ:

- table หลักครบตาม `docs/v2/erd.md`
- constraints สำคัญครบ เช่น visibility, status, public slug, contribution percent
- index รองรับ query หลัก เช่น faculty, period, category, type, visibility, status, DOI, source idempotency
- seed master data พอสำหรับ API และ frontend filter
- ไม่มี table ที่ copy แบบฟอร์มภาระงาน 1:1

---

## Expected Execution Order

เมื่อถึงการ์ด deploy/migration จริง ให้รันตามลำดับ:

```text
database/migrations/001_base.sql
database/seeds/001_master_data.sql
```

---

## Scope Boundary

SQL ชุดนี้เป็น baseline ที่ review ได้ ไม่ใช่ production deployment automation

ยังไม่รวม:

- Aurora provisioning
- RDS Data API setup
- database user/secret provisioning
- migration runner
- demo dataset หลายปี
- scoring engine
- official workload report generation

