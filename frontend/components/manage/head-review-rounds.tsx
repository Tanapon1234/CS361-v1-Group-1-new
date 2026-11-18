import Link from 'next/link';

import { RoundStatusMark, roundStatusRail } from '@/components/manage/round-status';
import type { RoundStatus } from '@/components/manage/round-status';
import { EmptyNote, StatusBadge, buttonClass } from '@/components/manage/ui';
import type { EvaluationRound, Submission } from '@/types/backend';

export interface HeadSheet {
  submission: Submission;
  lecturerName: string;
  /** No reviewer is assigned in this round, so the head checks it first */
  noReviewer: boolean;
}

/** What waits for the department head, one card per evaluation round (newest first). */
export function HeadReviewRounds({
  rounds,
  sheets,
}: {
  rounds: { round: EvaluationRound; state: RoundStatus }[];
  sheets: HeadSheet[];
}) {
  if (sheets.length === 0) {
    return <EmptyNote>ตอนนี้ไม่มีใบที่รอหัวหน้าสาขาตรวจ</EmptyNote>;
  }
  const byRound = new Map<number, HeadSheet[]>();
  for (const sheet of sheets) {
    const id = sheet.submission.round_id;
    byRound.set(id, [...(byRound.get(id) ?? []), sheet]);
  }
  const ordered = [...byRound.entries()].sort(([a], [b]) => b - a);

  return (
    <ul className="space-y-5">
      {ordered.map(([roundId, items]) => {
        const found = rounds.find(({ round }) => round.id === roundId);
        return (
          <li
            key={roundId}
            className={`overflow-hidden rounded-2xl border border-line bg-surface shadow-sm ${found ? roundStatusRail(found.state) : 'border-l-4 border-l-zinc-300'}`}
          >
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 px-5 pt-5 pb-3">
              <h3 className="text-base font-bold text-ink">{found?.round.name_th ?? `รอบ #${roundId}`}</h3>
              {found ? <RoundStatusMark status={found.state} /> : null}
            </div>
            <p className="px-5 pb-3 text-[13px] text-ink-muted">รอคุณตรวจ {items.length} ใบ</p>
            <ul className="divide-y divide-line-soft border-t border-line-soft bg-surface-alt">
              {items.map(({ submission, lecturerName, noReviewer }) => (
                <li key={submission.id} className="space-y-3 px-5 py-4">
                  <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5">
                    <p className="font-semibold text-ink">{lecturerName}</p>
                    <StatusBadge status={submission.status} />
                  </div>
                  {noReviewer ? (
                    <p className="text-[13px] text-ink-muted">รอบนี้ไม่มีผู้ตรวจ หัวหน้าสาขาตรวจแทน</p>
                  ) : null}
                  <Link
                    href={`/manage/submissions/${submission.id}`}
                    className={`${buttonClass} min-h-11 w-full px-4 sm:w-auto`}
                  >
                    ตรวจใบนี้
                  </Link>
                </li>
              ))}
            </ul>
          </li>
        );
      })}
    </ul>
  );
}
