import type { Metadata } from 'next';

import { createReviewerAssignment, deleteReviewerAssignment } from '@/app/manage/actions/review';
import { ActionForm } from '@/components/manage/action-form';
import { EmptyNote, Field, inputClass, Notice, PageHeader, Section, Table, Td } from '@/components/manage/ui';
import { isExecutive } from '@/lib/auth/permissions';
import { listLecturers, listReviewerAssignments, listRounds, MAX_PAGE, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDateTime } from '@/lib/backend/labels';

export const metadata: Metadata = { title: 'มอบหมายผู้ตรวจ' };

export default async function ReviewAssignmentsPage() {
  const me = await getCurrentUser();
  if (!isExecutive(me)) {
    return (
      <div className="space-y-6">
        <PageHeader title="มอบหมายผู้ตรวจ" />
        <Notice tone="error">หน้านี้สำหรับผู้บริหารเท่านั้น</Notice>
      </div>
    );
  }

  const [lecturers, rounds, assignments] = await Promise.all([
    listLecturers({ is_active: true, limit: MAX_PAGE }),
    listRounds(true),
    settle(listReviewerAssignments()),
  ]);
  // A round past its submit_due_at no longer takes new assignments (the backend refuses too)
  const now = Date.now();
  const assignableRounds = rounds.items.filter(
    (round) => !round.submit_due_at || new Date(round.submit_due_at).getTime() > now
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="มอบหมายผู้ตรวจ"
        description="กำหนดว่าผู้ตรวจสอบคนไหนดูแลผลงาน/หลักฐานของอาจารย์คนไหน ในรอบประเมินใด อาจารย์หนึ่งคนมีผู้ตรวจได้หลายคน การมอบหมายมีผลจนกว่ารอบจะปิดหรือหมดเวลาส่ง"
      />

      <Section title="มอบหมายใหม่">
        <ActionForm
          action={createReviewerAssignment}
          submitLabel="มอบหมาย"
          resetOnSuccess
          className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end"
        >
          <Field label="รอบประเมิน">
            <select name="round_id" required defaultValue="" className={inputClass}>
              <option value="" disabled>
                เลือกรอบ
              </option>
              {assignableRounds.map((round) => (
                <option key={round.id} value={round.id}>
                  {round.name_th}
                </option>
              ))}
            </select>
          </Field>
          <Field label="ผู้ตรวจสอบ (reviewer)">
            <select name="reviewer_id" required className={inputClass}>
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
          <Field label="อาจารย์ที่ต้องถูกตรวจ (reviewee)">
            <select name="reviewee_id" required className={inputClass}>
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
        </ActionForm>
      </Section>

      <Section title="การมอบหมายทั้งหมด">
        {assignments.error ? (
          <Notice tone="error">{assignments.error}</Notice>
        ) : !assignments.data?.items.length ? (
          <EmptyNote>ยังไม่มีการมอบหมายในรอบที่เปิดอยู่</EmptyNote>
        ) : (
          <Table head={['รอบ', 'ผู้ตรวจสอบ', 'อาจารย์ที่ถูกตรวจ', 'มอบหมายเมื่อ', '']}>
            {assignments.data.items.map((assignment) => (
              <tr key={assignment.id}>
                <Td>{assignment.round_name_th}</Td>
                <Td>{assignment.reviewer_name_th}</Td>
                <Td>{assignment.reviewee_name_th}</Td>
                <Td className="whitespace-nowrap">{formatDateTime(assignment.created_at)}</Td>
                <Td>
                  <ActionForm
                    inline
                    variant="danger"
                    submitLabel="ยกเลิก"
                    confirmText={`ยกเลิกการมอบหมาย ${assignment.reviewer_name_th} ตรวจ ${assignment.reviewee_name_th} (${assignment.round_name_th})?`}
                    action={deleteReviewerAssignment.bind(null, assignment.id)}
                  />
                </Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>
    </div>
  );
}
