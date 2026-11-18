import Link from 'next/link';
import type { ReactNode } from 'react';

import { createSubmission } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { RoundStatusMark, roundStatusRail } from '@/components/manage/round-status';
import type { RoundStatus } from '@/components/manage/round-status';
import { EmptyNote, buttonClass, linkClass, secondaryButtonClass } from '@/components/manage/ui';
import { SUBMISSION_STATUS_LABEL, formatDateTime, formatNumber, formatScore } from '@/lib/backend/labels';
import type { EvaluationRound, Submission, SubmissionStatus } from '@/types/backend';

/** How far a sheet has travelled (1 to 4): draft, with the reviewer, with the head, sent on */
const STEP: Record<SubmissionStatus, number> = {
  draft: 1,
  returned: 1,
  submitted: 2,
  assessing: 3,
  dept_review: 3, // the old committee step, kept for sheets already there
  dept_approved: 4,
  sent_to_faculty: 4,
};
const STEPS = 4;

const icon = 'size-4 shrink-0 text-ink-muted';

function ClockIcon() {
  return (
    <svg aria-hidden viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className={icon}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M10 5.8V10l2.8 1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function BookIcon() {
  return (
    <svg aria-hidden viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="size-4 shrink-0">
      <path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H16v12H5.5A1.5 1.5 0 0 0 4 16.5v-12Z" strokeLinejoin="round" />
      <path d="M4 16.5A1.5 1.5 0 0 0 5.5 18H16" strokeLinecap="round" />
    </svg>
  );
}

/** Four segments filled up to the sheet's current step; a returned sheet is drawn in the brand colour */
function SheetProgress({ status }: { status: SubmissionStatus }) {
  const step = STEP[status];
  const returned = status === 'returned';
  const done = status === 'dept_approved' || status === 'sent_to_faculty';
  const fill = returned ? 'bg-brand' : done ? 'bg-emerald-600' : 'bg-brand';
  return (
    <div>
      <div
        role="img"
        aria-label={`${SUBMISSION_STATUS_LABEL[status]} ขั้นที่ ${step} จาก ${STEPS}`}
        className="flex gap-1"
      >
        {Array.from({ length: STEPS }, (_, index) => (
          <span key={index} className={`h-1.5 flex-1 rounded-full ${index < step ? fill : 'bg-line'}`} />
        ))}
      </div>
      <p className="mt-2 flex flex-wrap items-baseline gap-x-2 text-sm">
        <span className={`font-semibold ${returned ? 'text-brand' : done ? 'text-emerald-800' : 'text-ink'}`}>
          {SUBMISSION_STATUS_LABEL[status]}
        </span>
        <span className="text-[13px] text-ink-muted">
          {returned ? 'แก้ไขแล้วส่งอีกครั้ง' : `ขั้นที่ ${step} จาก ${STEPS}`}
        </span>
      </p>
    </div>
  );
}

function Tile({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-line-soft bg-surface px-3 py-2">
      <p className="text-xs text-ink-muted">{label}</p>
      <p className="text-lg font-bold text-ink tabular-nums">{children}</p>
    </div>
  );
}

/**
 * One card per evaluation round: the round's status and due date, a link to its criteria, and my
 * own sheet in it (or a button to start one). Rounds already closed are listed only when I have
 * a sheet there.
 */
export function RoundSheetList({
  rounds,
  mine,
  mayCreate,
}: {
  rounds: { round: EvaluationRound; state: RoundStatus }[];
  mine: Submission[];
  mayCreate: boolean;
}) {
  const mineByRound = new Map(mine.map((submission) => [submission.round_id, submission]));
  const visible = rounds.filter(({ round, state }) => state !== 'closed' || mineByRound.has(round.id));

  if (visible.length === 0) return <EmptyNote>ยังไม่มีรอบที่เปิดให้กรอก</EmptyNote>;

  return (
    <ul className="space-y-5">
      {visible.map(({ round, state }) => {
        const submission = mineByRound.get(round.id);
        const needsAction = submission?.status === 'draft' || submission?.status === 'returned';
        return (
          <li
            key={round.id}
            className={`overflow-hidden rounded-2xl border border-line bg-surface shadow-sm ${roundStatusRail(state)}`}
          >
            <div className="px-5 pt-5 pb-4">
              <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1">
                <h3 className="text-base font-bold text-ink">{round.name_th}</h3>
                <RoundStatusMark status={state} />
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[13px] text-ink-muted">
                <span className="inline-flex items-center gap-1.5">
                  <ClockIcon />
                  {round.submit_due_at ? `ส่งภายใน ${formatDateTime(round.submit_due_at)}` : 'ไม่กำหนดวันส่ง'}
                </span>
                <Link
                  href={`/manage/rounds/${round.id}/criteria`}
                  className={`${linkClass} inline-flex items-center gap-1.5`}
                >
                  <BookIcon />
                  ดูเกณฑ์ของรอบนี้
                </Link>
              </div>
            </div>

            <div className="border-t border-line-soft bg-surface-alt px-5 py-4">
              <p className="mb-3 text-xs font-semibold text-ink-muted">ใบภาระงานของฉัน</p>
              {submission ? (
                <div className="space-y-4">
                  <SheetProgress status={submission.status} />
                  <div className="grid grid-cols-2 gap-3">
                    <Tile label="คะแนนหลังตัดเพดาน">{formatScore(submission.capped_total)}</Tile>
                    <Tile label="หน่วยกิตสอน">{formatNumber(submission.teaching_credits)}</Tile>
                  </div>
                  <Link
                    href={`/manage/submissions/${submission.id}`}
                    className={`${needsAction ? buttonClass : secondaryButtonClass} min-h-11 w-full px-4 sm:w-auto`}
                  >
                    {submission.status === 'draft' ? 'กรอกต่อ' : submission.status === 'returned' ? 'แก้ไขใบที่ถูกตีกลับ' : 'เปิดใบภาระงาน'}
                  </Link>
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-line bg-surface px-4 py-4 text-center">
                  <p className="text-sm text-ink-muted">ยังไม่ได้เริ่มกรอก</p>
                  {mayCreate && state !== 'closed' ? (
                    <div className="mt-3 flex justify-center">
                      <ActionForm inline large action={createSubmission} submitLabel="เริ่มกรอกภาระงาน">
                        <input type="hidden" name="round_id" value={round.id} />
                      </ActionForm>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
