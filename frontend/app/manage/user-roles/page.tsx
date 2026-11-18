import type { Metadata } from 'next';

import { grantUserRole, revokeUserRole } from '@/app/manage/actions/user-roles';
import { ActionForm } from '@/components/manage/action-form';
import { EmptyNote, Field, inputClass, Notice, PageHeader, Section, Table, Td } from '@/components/manage/ui';
import { isAdmin } from '@/lib/auth/permissions';
import { listLecturers, listUserRoles, MAX_PAGE, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDateTime, ROLE_LABEL } from '@/lib/backend/labels';

export const metadata: Metadata = { title: 'กำหนดบทบาทผู้ใช้' };

/** Roles an admin can grant. The department head comes from the head position and the
 * reviewer from a reviewer assignment; lecturer is implicit. */
const GRANTABLE = (['staff', 'admin'] as const).map((value) => ({ value, label: ROLE_LABEL[value] }));

export default async function UserRolesPage() {
  const me = await getCurrentUser();
  if (!isAdmin(me)) {
    return (
      <div className="space-y-6">
        <PageHeader title="กำหนดบทบาทผู้ใช้" />
        <Notice tone="error">หน้านี้สำหรับผู้ดูแลระบบเท่านั้น</Notice>
      </div>
    );
  }

  const [lecturers, roles] = await Promise.all([
    listLecturers({ is_active: true, limit: MAX_PAGE }),
    settle(listUserRoles()),
  ]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="กำหนดบทบาทผู้ใช้"
        description="ให้หรือถอนบทบาทเจ้าหน้าที่สาขาและผู้ดูแลระบบ มีผลทันทีโดยไม่ต้องเข้าสู่ระบบใหม่ หัวหน้าสาขาได้จากตำแหน่งหัวหน้าสาขาที่เมนู อาจารย์ → ตำแหน่งบริหาร ส่วนอาจารย์ผู้ตรวจได้จากการมอบหมายผู้ตรวจในแต่ละรอบ"
      />

      <Section title="กำหนดบทบาทใหม่">
        <ActionForm
          action={grantUserRole}
          submitLabel="กำหนด"
          resetOnSuccess
          className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
        >
          <Field label="อาจารย์">
            <select name="lecturer_id" required defaultValue="" className={inputClass}>
              <option value="" disabled>
                เลือกอาจารย์
              </option>
              {lecturers.items.map((lecturer) => (
                <option key={lecturer.lecturer_id} value={lecturer.lecturer_id}>
                  {lecturer.name_th}
                </option>
              ))}
            </select>
          </Field>
          <Field label="บทบาท">
            <select name="role" required defaultValue="" className={inputClass}>
              <option value="" disabled>
                เลือกบทบาท
              </option>
              {GRANTABLE.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </Field>
        </ActionForm>
      </Section>

      <Section title="บทบาทที่กำหนดไว้">
        {roles.error ? (
          <Notice tone="error">{roles.error}</Notice>
        ) : !roles.data?.items.length ? (
          <EmptyNote>ยังไม่มีบทบาทที่กำหนดในระบบ</EmptyNote>
        ) : (
          <Table head={['อาจารย์', 'บทบาท', 'กำหนดเมื่อ', '']}>
            {roles.data.items.map((row) => (
              <tr key={`${row.lecturer_id}-${row.role}`}>
                <Td>{row.lecturer_name_th}</Td>
                <Td>{ROLE_LABEL[row.role] ?? row.role}</Td>
                <Td className="whitespace-nowrap">{formatDateTime(row.created_at)}</Td>
                <Td>
                  <ActionForm
                    inline
                    variant="danger"
                    submitLabel="ถอน"
                    confirmText={`ถอนบทบาท ${ROLE_LABEL[row.role] ?? row.role} ของ ${row.lecturer_name_th}?`}
                    action={revokeUserRole.bind(null, row.lecturer_id, row.role)}
                  />
                </Td>
              </tr>
            ))}
          </Table>
        )}
        <p className="mt-3 text-xs text-zinc-500">
          บทบาทที่ตั้งไว้ใน Cognito group เดิมไม่แสดงที่นี่ และยังใช้งานได้จนกว่าจะลบ group นั้นใน AWS
        </p>
      </Section>
    </div>
  );
}
