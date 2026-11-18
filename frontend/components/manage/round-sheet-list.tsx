import Link from 'next/link';

import { createSubmission } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { RoundStatusMark, roundStatusRail } from '@/components/manage/round-status';
import type { RoundStatus } from '@/components/manage/round-status';
import { EmptyNote, StatusBadge, secondaryButtonClass } from '@/components/manage/ui';
import { formatDateTime, formatNumber, formatScore } from '@/lib/backend/labels';
import type { EvaluationRound, Submission } from '@/types/backend';

/**
 * One card per evaluation round: the round's status and due date, and my own sheet in it
 * (or a button to start one). Rounds already closed are listed only when I have a sheet there.
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
    <ul className="space-y-4">
      {visible.map(({ round, state }) => {
        const submission = mineByRound.get(round.id);
        return (
          <li key={round.id} className={`rounded-xl border border-line ${roundStatusRail(state)}`}>
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 px-4 pt-4">
              <p className="font-semibold text-ink">{round.name_th}</p>
              <RoundStatusMark status={state} />
            </div>
            <p className="px-4 text-[13px] text-ink-muted">
              {round.submit_due_at ? `ส่งภายใน ${formatDateTime(round.submit_due_at)}` : 'ไม่กำหนดวันส่ง'}
            </p>

            <div className="mt-3 border-t border-line-soft bg-surface-alt px-4 py-3">
              <p className="text-xs font-medium text-ink-muted">ใบภาระงานของฉัน</p>
              {submission ? (
                <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0 space-y-1">
                    <StatusBadge status={submission.status} />
                    <p className="text-[13px] text-ink-muted">
                      คะแนน {formatScore(submission.capped_total)} · หน่วยกิตสอน{' '}
                      {formatNumber(submission.teaching_credits)}
                    </p>
                  </div>
                  <Link href={`/manage/submissions/${submission.id}`} className={`${secondaryButtonClass} min-h-11 px-4`}>
                    เปิดใบภาระงาน
                  </Link>
                </div>
              ) : (
                <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm text-ink">ยังไม่ได้เริ่มกรอก</p>
                  {mayCreate && state !== 'closed' ? (
                    <ActionForm inline large action={createSubmission} submitLabel="เริ่มกรอกภาระงาน">
                      <input type="hidden" name="round_id" value={round.id} />
                    </ActionForm>
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
