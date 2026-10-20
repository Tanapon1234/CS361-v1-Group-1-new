import { Field, inputClass } from '@/components/manage/ui';
import type { Department, Lecturer } from '@/types/backend';

/** Inputs shared by the create and edit lecturer forms */
export function LecturerFields({
  lecturer,
  departments,
  staff = true,
}: {
  lecturer?: Lecturer;
  departments: Department[];
  /** false: a lecturer editing themselves; rank, department, email and account stay read-only */
  staff?: boolean;
}) {
  const staffOnly = staff ? undefined : 'แก้ได้เฉพาะเจ้าหน้าที่';
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="ชื่อ (ไทย) *">
        <input name="name_th" required maxLength={255} defaultValue={lecturer?.name_th} className={inputClass} />
      </Field>
      <Field label="ชื่อ (อังกฤษ)">
        <input name="name_en" maxLength={255} defaultValue={lecturer?.name_en ?? ''} className={inputClass} />
      </Field>
      <Field label="ตำแหน่งทางวิชาการ" hint={staffOnly ?? 'ข้อความอิสระ เช่น ผู้ช่วยศาสตราจารย์ (ใช้ทำ rank ของใบภาระงาน)'}>
        <input name="rank" maxLength={100} disabled={!staff} defaultValue={lecturer?.rank ?? ''} className={inputClass} />
      </Field>
      <Field label="สาขาวิชา" hint={staffOnly ?? 'ต้องมีสาขาก่อนสร้างใบภาระงาน'}>
        <select name="department_id" disabled={!staff} defaultValue={lecturer?.department_id ?? ''} className={inputClass}>
          <option value="">— ไม่ระบุ —</option>
          {departments.map((department) => (
            <option key={department.id} value={department.id}>
              {department.code} · {department.name_th}
            </option>
          ))}
        </select>
      </Field>
      <Field label="อีเมล *" hint={staffOnly}>
        <input name="email" type="email" required disabled={!staff} defaultValue={lecturer?.email} className={inputClass} />
      </Field>
      <Field label="ห้องทำงาน">
        <input name="office" maxLength={255} defaultValue={lecturer?.office ?? ''} className={inputClass} />
      </Field>
      <Field label="โทรศัพท์">
        <input name="phone" maxLength={50} defaultValue={lecturer?.phone ?? ''} className={inputClass} />
      </Field>
      <Field label="เบอร์ต่อ">
        <input
          name="phone_extension"
          maxLength={50}
          defaultValue={lecturer?.phone_extension ?? ''}
          className={inputClass}
        />
      </Field>
      {staff ? (
        <Field
          label="Cognito sub"
          hint={lecturer ? 'เว้นว่าง = คงค่าเดิม (ระบบไม่แสดงค่าที่บันทึกไว้)' : 'บัญชีผู้ใช้ที่ผูกกับอาจารย์ (ไม่บังคับ ระบบผูกให้เองด้วยอีเมลตอนเข้าสู่ระบบครั้งแรก)'}
          className="sm:col-span-2"
        >
          <input name="cognito_sub" maxLength={64} className={inputClass} />
        </Field>
      ) : null}
    </div>
  );
}
