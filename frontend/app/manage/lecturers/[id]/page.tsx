import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import {
  createPosition,
  deletePosition,
  endPosition,
  setLecturerActive,
  updateLecturer,
} from '@/app/manage/actions/people';
import { ActionForm } from '@/components/manage/action-form';
import { LecturerFields } from '@/components/manage/lecturer-fields';
import { LecturerHeader } from '@/components/manage/lecturer-tabs';
import { EmptyNote, Field, Section, Table, Td, inputClass } from '@/components/manage/ui';
import { canEditLecturer, canManage } from '@/lib/auth/permissions';
import { getLecturer, listDepartments, listPositions } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { DEPARTMENT_POSITIONS, POSITION_LABEL, formatDate } from '@/lib/backend/labels';
import type { PositionCode } from '@/types/backend';

export const metadata: Metadata = { title: 'ข้อมูลอาจารย์' };

export default async function LecturerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const lecturer = await getLecturer(id);
  if (!lecturer) notFound();

  const [departments, positions, me] = await Promise.all([
    listDepartments(),
    listPositions(id),
    getCurrentUser(),
  ]);
  const manage = canManage(me);
  const editable = canEditLecturer(me, id);
  const departmentName = new Map(departments.items.map((d) => [d.id, d.name_th]));
  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="space-y-6">
      <LecturerHeader lecturer={lecturer} current={`/manage/lecturers/${id}`} />

      <Section
        title="ข้อมูลทั่วไป"
        actions={
          manage ? (
            <ActionForm
              inline
              variant={lecturer.is_active ? 'danger' : 'secondary'}
              action={setLecturerActive.bind(null, id, !lecturer.is_active)}
              submitLabel={lecturer.is_active ? 'ปิดใช้งาน' : 'เปิดใช้งาน'}
              confirmText={lecturer.is_active ? 'ปิดใช้งานอาจารย์ท่านนี้?' : undefined}
            />
          ) : null
        }
      >
        {editable ? (
          <ActionForm action={updateLecturer.bind(null, id)}>
            <LecturerFields lecturer={lecturer} departments={departments.items} staff={manage} />
          </ActionForm>
        ) : (
          <fieldset disabled className="m-0 min-w-0 border-0 p-0">
            <LecturerFields lecturer={lecturer} departments={departments.items} staff={false} />
          </fieldset>
        )}
      </Section>

      <Section
        title="ตำแหน่งบริหาร"
        description="ใช้ทั้งเป็นสิทธิ์ผู้ประเมิน/ผู้ลงนาม และเป็นข้อมูลภาระงานข้อ 3.1/3.2 · ตำแหน่งระดับสาขาต้องระบุสาขา"
      >
        {positions.items.length === 0 ? (
          <EmptyNote>ยังไม่มีตำแหน่ง</EmptyNote>
        ) : (
          <Table head={['ตำแหน่ง', 'สาขา', 'เริ่ม', 'สิ้นสุด', '']}>
            {positions.items.map((position) => (
              <tr key={position.id}>
                <Td className="font-medium text-ink">{POSITION_LABEL[position.position]}</Td>
                <Td>{position.department_id ? departmentName.get(position.department_id) : 'ระดับคณะ'}</Td>
                <Td>{formatDate(position.start_date)}</Td>
                <Td>
                  {!manage ? (
                    position.end_date ? formatDate(position.end_date) : 'ยังดำรงตำแหน่ง'
                  ) : (
                    <ActionForm
                      action={endPosition.bind(null, id, position.id)}
                      submitLabel="บันทึก"
                      variant="secondary"
                      className="flex flex-wrap items-center gap-2"
                    >
                      <input
                        type="date"
                        name="end_date"
                        defaultValue={position.end_date ?? ''}
                        aria-label="วันสิ้นสุดวาระ (เว้นว่าง = ยังดำรงตำแหน่ง)"
                        className={`${inputClass} w-40`}
                      />
                    </ActionForm>
                  )}
                </Td>
                <Td>
                  {manage ? (
                    <ActionForm
                      inline
                      variant="danger"
                      action={deletePosition.bind(null, id, position.id)}
                      submitLabel="ลบ"
                      confirmText="ลบเฉพาะกรณีบันทึกผิด ถ้าหมดวาระให้ใส่วันสิ้นสุดแทน ยืนยันลบ?"
                    />
                  ) : null}
                </Td>
              </tr>
            ))}
          </Table>
        )}

        {manage ? (
          <ActionForm
            action={createPosition.bind(null, id)}
            submitLabel="แต่งตั้ง"
            resetOnSuccess
            className="mt-6 space-y-4 border-t border-line-soft pt-6"
          >
            <div className="grid gap-4 sm:grid-cols-4">
              <Field label="ตำแหน่ง">
                <select name="position" required className={inputClass}>
                  {(Object.keys(POSITION_LABEL) as PositionCode[]).map((code) => (
                    <option key={code} value={code}>
                      {POSITION_LABEL[code]}
                      {DEPARTMENT_POSITIONS.includes(code) ? ' (ระดับสาขา)' : ''}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="สาขา (เฉพาะตำแหน่งระดับสาขา)">
                <select name="department_id" defaultValue={lecturer.department_id ?? ''} className={inputClass}>
                  <option value="">— ระดับคณะ —</option>
                  {departments.items.map((department) => (
                    <option key={department.id} value={department.id}>
                      {department.name_th}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="เริ่มวาระ">
                <input type="date" name="start_date" required defaultValue={today} className={inputClass} />
              </Field>
              <Field label="สิ้นสุดวาระ (ถ้ามี)">
                <input type="date" name="end_date" className={inputClass} />
              </Field>
            </div>
          </ActionForm>
        ) : null}
      </Section>
    </div>
  );
}
