import type { Metadata } from 'next';

import { createReviewerAssignments, deleteReviewerAssignment } from '@/app/manage/actions/review';
import { ActionForm } from '@/components/manage/action-form';
import { ReviewerAssignForm } from '@/components/manage/reviewer-assign-form';
import { Badge, EmptyNote, Notice, PageHeader, Section } from '@/components/manage/ui';
import { isExecutive } from '@/lib/auth/permissions';
import { listLecturers, listReviewerAssignments, listRoundsWithState, MAX_PAGE, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDate, formatDateTime } from '@/lib/backend/labels';
import type { ReviewerAssignment } from '@/types/backend';

export const metadata: Metadata = { title: 'มอบหมายผู้ตรวจ' };

/** Round first, then one card per reviewer inside it, so a phone reads "in this round, who reviews whom".
 * `roundOrder` is the newest-first order of the rounds list. */
function groupByRound(assignments: ReviewerAssignment[], roundOrder: Map<number, number>) {
  const rounds = new Map<number, { name: string; reviewers: Map<string, { name: string; rows: ReviewerAssignment[] }> }>();
  for (const assignment of assignments) {
    const round = rounds.get(assignment.round_id) ?? { name: assignment.round_name_th, reviewers: new Map() };
    const reviewer = round.reviewers.get(assignment.reviewer_id) ?? { name: assignment.reviewer_name_th, rows: [] };
    reviewer.rows.push(assignment);
    round.reviewers.set(assignment.reviewer_id, reviewer);
    rounds.set(assignment.round_id, round);
  }
  return [...rounds.entries()]
    .map(([id, round]) => ({
      id,
      name: round.name,
      pairs: [...round.reviewers.values()].reduce((sum, reviewer) => sum + reviewer.rows.length, 0),
      reviewers: [...round.reviewers.entries()]
        .map(([reviewerId, reviewer]) => ({ id: reviewerId, ...reviewer }))
        .sort((x, y) => x.name.localeCompare(y.name, 'th')),
    }))
    .sort((x, y) => (roundOrder.get(x.id) ?? 1e9) - (roundOrder.get(y.id) ?? 1e9));
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

  const [lecturers, rounds, assignments] = await Promise.all([
    listLecturers({ is_active: true, limit: MAX_PAGE }),
    listRoundsWithState(),
    settle(listReviewerAssignments()),
  ]);
  const roundOrder = new Map(rounds.map(({ round }, index) => [round.id, index]));
  const groups = groupByRound(assignments.data?.items ?? [], roundOrder);

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
          rounds={rounds.map(({ round, state }) => ({
            id: round.id,
            name: round.name_th,
            state,
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
            {groups.map((round, index) => (
              // Newest round open, the others folded: the summary still says how many pairs are inside
              <details key={round.id} open={index === 0} className="group overflow-hidden rounded-xl border border-line">
                <summary className="flex cursor-pointer list-none items-start justify-between gap-3 bg-surface-alt px-4 py-4">
                  <div className="min-w-0">
                    <p className="font-bold text-ink">{round.name}</p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5">
                      <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">
                        <span aria-hidden className="mr-1.5 size-1.5 rounded-full bg-emerald-500" />
                        เปิดรับ
                      </Badge>
                      <span className="text-xs text-ink-muted">
                        {round.pairs} คู่ · ผู้ตรวจ {round.reviewers.length} คน
                      </span>
                    </div>
                  </div>
                  <span aria-hidden className="mt-1 shrink-0 text-ink-muted transition-transform group-open:rotate-180">
                    ▾
                  </span>
                </summary>
                <div className="space-y-3 p-3 sm:p-4">
                  {round.reviewers.map((reviewer) => (
                    <article key={reviewer.id} className="overflow-hidden rounded-lg border border-line-soft">
                      <header className="flex items-center justify-between gap-3 border-b border-line-soft px-4 py-3">
                        <div className="min-w-0">
                          <p className="text-xs text-ink-muted">ผู้ตรวจสอบ</p>
                          <p className="truncate font-semibold text-ink">{reviewer.name}</p>
                        </div>
                        <Badge>{reviewer.rows.length} คน</Badge>
                      </header>
                      <ul className="divide-y divide-line-soft">
                        {reviewer.rows.map((assignment) => (
                          <li key={assignment.id} className="flex min-h-14 items-center justify-between gap-3 px-4 py-2">
                            <p className="min-w-0 text-sm text-ink">{assignment.reviewee_name_th}</p>
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
              </details>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
