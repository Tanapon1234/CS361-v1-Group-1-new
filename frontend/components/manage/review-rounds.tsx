import Link from 'next/link';

import { RoundStatusMark, roundStatusRail } from '@/components/manage/round-status';
import type { RoundStatus } from '@/components/manage/round-status';
import { Badge, EmptyNote, StatusBadge, buttonClass, secondaryButtonClass } from '@/components/manage/ui';
import type { EvaluationRound, MyReviewAssignment } from '@/types/backend';

/**
 * The reviewer's own work, one card per evaluation round (newest first): the lecturers assigned
 * to them in that round, each with the sheet, its verdict and what is still waiting.
 */
export function ReviewRounds({
  rounds,
  assignments,
}: {
  rounds: { round: EvaluationRound; state: RoundStatus }[];
  assignments: MyReviewAssignment[];
}) {
  if (assignments.length === 0) {
    return <EmptyNote>ตอนนี้ยังไม่มีอาจารย์ที่ต้องตรวจ</EmptyNote>;
  }
  const byRound = new Map<number, MyReviewAssignment[]>();
  for (const assignment of assignments) {
    byRound.set(assignment.round_id, [...(byRound.get(assignment.round_id) ?? []), assignment]);
  }
  const ordered = [...byRound.entries()].sort(([a], [b]) => b - a);

  return (
    <ul className="space-y-5">
      {ordered.map(([roundId, people]) => {
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
            <p className="px-5 pb-3 text-[13px] text-ink-muted">ต้องตรวจ {people.length} คน · รอคุณตรวจ {people.filter((p) => p.submission_status === 'submitted').length} ใบ</p>

            <ul className="divide-y divide-line-soft border-t border-line-soft bg-surface-alt">
              {people.map((person) => (
                <li key={person.reviewee_id} className="space-y-3 px-5 py-4">
                  <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5">
                    <p className="font-semibold text-ink">{person.reviewee_name_th}</p>
                    {person.submission_status ? (
                      <StatusBadge status={person.submission_status} />
                    ) : (
                      <Badge>ยังไม่ได้ส่งใบ</Badge>
                    )}
                  </div>

                  {person.submission_id && person.submission_status !== 'draft' ? (
                    <Link
                      href={`/manage/submissions/${person.submission_id}`}
                      className={`${person.submission_status === 'submitted' ? buttonClass : secondaryButtonClass} min-h-11 w-full px-4 sm:w-auto`}
                    >
                      {person.submission_status === 'submitted' ? 'ตรวจใบนี้' : 'เปิดใบภาระงาน'}
                    </Link>
                  ) : (
                    <p className="text-[13px] text-ink-muted">
                      {person.submission_status === 'draft'
                        ? 'ใบยังเป็นร่าง ตรวจได้เมื่อเจ้าของใบส่งแล้ว'
                        : 'รอเจ้าของใบสร้างและส่งใบก่อนจึงจะตรวจใบได้'}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </li>
        );
      })}
    </ul>
  );
}
