import type { Metadata } from 'next';

import { createDepartment, updateDepartment } from '@/app/manage/actions/people';
import { ActionForm } from '@/components/manage/action-form';
import { Checkbox, EmptyNote, Field, PageHeader, Section, inputClass } from '@/components/manage/ui';
import { leaveIfLecturerOnly } from '@/lib/auth/guards';
import { canManage } from '@/lib/auth/permissions';
import { listDepartments } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'สาขาวิชา' };

export default async function DepartmentsPage() {
  await leaveIfLecturerOnly();
  const [departments, me] = await Promise.all([listDepartments(), getCurrentUser()]);
  const manage = canManage(me);

  return (
    <div className="space-y-6">
      <PageHeader
        title="สาขาวิชา"
        description="master กลางที่อาจารย์ ตำแหน่งบริหาร และใบภาระงานอ้างถึง · ปิดสาขาแทนการลบ"
      />

      {manage ? (
        <Section title="เพิ่มสาขา">
          <ActionForm action={createDepartment} submitLabel="เพิ่มสาขา" resetOnSuccess className="flex flex-wrap items-end gap-3">
            <Field label="รหัส" className="w-32">
              <input name="code" required maxLength={10} placeholder="CS" className={inputClass} />
            </Field>
            <Field label="ชื่อสาขา" className="min-w-60 flex-1">
              <input name="name_th" required maxLength={150} placeholder="วิทยาการคอมพิวเตอร์" className={inputClass} />
            </Field>
          </ActionForm>
        </Section>
      ) : null}

      <Section title={`สาขาทั้งหมด (${departments.meta.total})`}>
        {departments.items.length === 0 ? (
          <EmptyNote>ยังไม่มีสาขา</EmptyNote>
        ) : (
          <ul className="divide-y divide-line-soft">
            {departments.items.map((department) => (
              <li key={department.id} className="py-3">
                {!manage ? (
                  <p className="text-sm">
                    <span className="font-semibold text-ink">{department.code}</span> {department.name_th}
                    {department.is_active ? null : <span className="text-ink-muted"> (ปิดใช้)</span>}
                  </p>
                ) : (
                  <ActionForm
                    action={updateDepartment.bind(null, department.id)}
                    variant="secondary"
                    className="flex flex-wrap items-center gap-3"
                  >
                    <input name="code" required maxLength={10} defaultValue={department.code} className={`${inputClass} w-28`} aria-label="รหัส" />
                    <input name="name_th" required maxLength={150} defaultValue={department.name_th} className={`${inputClass} min-w-60 flex-1`} aria-label="ชื่อสาขา" />
                    <Checkbox name="is_active" label="เปิดใช้" defaultChecked={department.is_active} />
                  </ActionForm>
                )}
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}
