import type { Metadata } from 'next';

import { createReviewerAssignments, deleteReviewerAssignment } from '@/app/manage/actions/review';
import { ActionForm } from '@/components/manage/action-form';
import { ReviewerAssignForm } from '@/components/manage/reviewer-assign-form';
import { Badge, EmptyNote, Notice, PageHeader, Section } from '@/components/manage/ui';
import { isExecutive } from '@/lib/auth/permissions';
import { listAssignableRounds, listLecturers, listReviewerAssignments, MAX_PAGE, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDate, formatDateTime } from '@/lib/backend/labels';
import type { ReviewerAssignment } from '@/types/backend';

export const metadata: Metadata = { title: 'มอบหมายผู้ตรวจ' };

/** One card per reviewer, so a phone shows who reviews whom without a wide table */
function groupByReviewer(assignments: ReviewerAssignment[]) {
  const groups = new Map<string, { name: string; rows: ReviewerAssignment[] }>();
  for (const assignment of assignments) {
    const group = groups.get(assignment.reviewer_id) ?? { name: assignment.reviewer_name_th, rows: [] };
    group.rows.push(assignment);
    groups.set(assignment.reviewer_id, group);
  }
  return [...groups.entries()]
    .map(([id, group]) => ({ id, ...group }))
    .sort((a, b) => a.name.localeCompare(b.name, 'th'));
}

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

  const [lecturers, assignableRounds, assignments] = await Promise.all([
    listLecturers({ is_active: true, limit: MAX_PAGE }),
    listAssignableRounds(),
    settle(listReviewerAssignments()),
  ]);
  const groups = groupByReviewer(assignments.data?.items ?? []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="มอบหมายผู้ตรวจ"
        description="เลือกผู้ตรวจสอบ 1 คน แล้วติ๊กอาจารย์ที่ต้องถูกตรวจได้หลายคนในรอบประเมินเดียวกัน การมอบหมายมีผลจนกว่ารอบจะปิดหรือหมดเวลาส่ง"
      />

      <Section title="มอบหมายใหม่">
        <ReviewerAssignForm
          action={createReviewerAssignments}
          lecturers={lecturers.items.map((lecturer) => ({
            id: lecturer.lecturer_id,
            name: lecturer.name_th,
            email: lecturer.email,
          }))}
          rounds={assignableRounds.map((round) => ({
            id: round.id,
            name: round.name_th,
            period: `${formatDate(round.period_start)} – ${formatDate(round.period_end)}`,
            deadline: round.submit_due_at
              ? `ส่งภายใน ${formatDateTime(round.submit_due_at)}`
              : 'ไม่กำหนดวันส่ง',
          }))}
        />
      </Section>

      <Section title="การมอบหมายทั้งหมด" description="เฉพาะรอบที่ยังเปิดรับอยู่">
        {assignments.error ? (
          <Notice tone="error">{assignments.error}</Notice>
        ) : groups.length === 0 ? (
          <EmptyNote>ยังไม่มีการมอบหมายในรอบที่เปิดอยู่</EmptyNote>
        ) : (
          <div className="space-y-4">
            {groups.map((group) => (
              <article key={group.id} className="overflow-hidden rounded-xl border border-line">
                <header className="flex items-center justify-between gap-3 bg-surface-alt px-4 py-3">
                  <div className="min-w-0">
                    <p className="text-xs text-ink-muted">ผู้ตรวจสอบ</p>
                    <p className="truncate font-semibold text-ink">{group.name}</p>
                  </div>
                  <Badge>{group.rows.length} คน</Badge>
                </header>
                <ul className="divide-y divide-line-soft">
                  {group.rows.map((assignment) => (
                    <li key={assignment.id} className="flex min-h-14 items-center justify-between gap-3 px-4 py-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm text-ink">{assignment.reviewee_name_th}</p>
                        <p className="truncate text-xs text-ink-muted">{assignment.round_name_th}</p>
                      </div>
                      <ActionForm
                        inline
                        large
                        variant="danger"
                        submitLabel="ยกเลิก"
                        confirmText={`ยกเลิกการมอบหมาย ${assignment.reviewer_name_th} ตรวจ ${assignment.reviewee_name_th} (${assignment.round_name_th})?`}
                        action={deleteReviewerAssignment.bind(null, assignment.id)}
                      />
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
