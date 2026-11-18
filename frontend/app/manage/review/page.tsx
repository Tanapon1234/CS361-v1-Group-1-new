import type { Metadata } from 'next';

import { HeadReviewRounds } from '@/components/manage/head-review-rounds';
import type { HeadSheet } from '@/components/manage/head-review-rounds';
import { Notice, PageHeader, Section } from '@/components/manage/ui';
import { ReviewRounds } from '@/components/manage/review-rounds';
import { canOpenReviewPage, canReview, isDeptChair } from '@/lib/auth/permissions';
import {
  MAX_PAGE,
  listLecturers,
  listMyReviewAssignments,
  listReviewerAssignments,
  listRoundsWithState,
  listSubmissions,
  settle,
} from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import type { Me } from '@/types/backend';

export const metadata: Metadata = { title: 'ตรวจสอบและรับรอง' };

/** Sheets waiting for the department head: assessing ones, and submitted ones nobody reviews */
async function headSheets(me: Me): Promise<HeadSheet[]> {
  const departments = new Set(
    me.positions.filter((held) => held.position === 'dept_chair').map((held) => held.department_id)
  );
  const [assessing, submitted, assigned, lecturers] = await Promise.all([
    listSubmissions({ status: 'assessing' }),
    listSubmissions({ status: 'submitted' }),
    listReviewerAssignments(),
    listLecturers({ limit: MAX_PAGE }),
  ]);
  const reviewed = new Set(assigned.items.map((a) => `${a.reviewee_id}:${a.round_id}`));
  const names = new Map(lecturers.items.map((l) => [l.lecturer_id, l.name_th]));
  const mine = (s: { lecturer_id: string; department_snapshot: number }) =>
    s.lecturer_id !== me.lecturer.lecturer_id && departments.has(s.department_snapshot);

  return [
    ...assessing.items.filter(mine).map((submission) => ({ submission, noReviewer: false })),
    ...submitted.items
      .filter(mine)
      .filter((s) => !reviewed.has(`${s.lecturer_id}:${s.round_id}`))
      .map((submission) => ({ submission, noReviewer: true })),
  ].map(({ submission, noReviewer }) => ({
    submission,
    noReviewer,
    lecturerName: names.get(submission.lecturer_id) ?? submission.lecturer_id,
  }));
}

export default async function ReviewPage() {
  const me = await getCurrentUser();
  if (!me || !canOpenReviewPage(me)) {
    return (
      <div className="space-y-6">
        <PageHeader title="ตรวจสอบและรับรอง" />
        <Notice tone="error">หน้านี้สำหรับอาจารย์ผู้ตรวจและหัวหน้าสาขาเท่านั้น</Notice>
      </div>
    );
  }

  const asReviewer = canReview(me);
  const asHead = isDeptChair(me);
  const [assignments, head, rounds] = await Promise.all([
    asReviewer ? settle(listMyReviewAssignments()) : null,
    asHead ? settle(headSheets(me)) : null,
    listRoundsWithState(),
  ]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="ตรวจสอบและรับรอง"
        description="ใบภาระงานที่รอคุณตรวจ แยกตามบทบาท ผู้ตรวจรับรองแล้วส่งต่อหัวหน้าสาขา หัวหน้าสาขารับรองแล้วส่งต่อคณะ"
      />
      {assignments ? (
        <Section title="ที่ต้องตรวจในฐานะผู้ตรวจ" description="อาจารย์ที่ได้รับมอบหมายให้คุณตรวจ แยกตามรอบประเมิน">
          {assignments.error ? (
            <Notice tone="error">{assignments.error}</Notice>
          ) : (
            <ReviewRounds rounds={rounds} assignments={assignments.data?.items ?? []} />
          )}
        </Section>
      ) : null}
      {head ? (
        <Section title="ที่ต้องตรวจในฐานะหัวหน้าสาขา" description="ใบในสาขาของคุณที่ผู้ตรวจรับรองแล้ว รอคุณรับรองและส่งต่อคณะ">
          {head.error ? <Notice tone="error">{head.error}</Notice> : <HeadReviewRounds
              rounds={rounds}
              sheets={(head.data ?? []).filter(
                ({ submission }) => rounds.find(({ round }) => round.id === submission.round_id)?.state !== 'closed'
              )}
            />}
        </Section>
      ) : null}
    </div>
  );
}
