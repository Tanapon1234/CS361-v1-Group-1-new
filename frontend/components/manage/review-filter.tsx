import Link from 'next/link';

import type { MyReviewAssignment } from '@/types/backend';

export type ReviewFilter = 'waiting' | 'returned' | 'forwarded' | 'unsent' | 'all';

const FILTERS: { key: ReviewFilter; label: string; match: (a: MyReviewAssignment) => boolean }[] = [
  { key: 'waiting', label: 'รอตรวจ', match: (a) => a.submission_status === 'submitted' },
  { key: 'returned', label: 'ตีกลับแล้ว', match: (a) => a.submission_status === 'returned' },
  {
    key: 'forwarded',
    label: 'ส่งต่อแล้ว',
    match: (a) =>
      ['assessing', 'dept_review', 'dept_approved', 'sent_to_faculty'].includes(a.submission_status ?? ''),
  },
  {
    key: 'unsent',
    label: 'ยังไม่ส่งใบ',
    match: (a) => !a.submission_status || a.submission_status === 'draft',
  },
  { key: 'all', label: 'ทั้งหมด', match: () => true },
];

export function parseReviewFilter(value: string | undefined): ReviewFilter {
  return FILTERS.find((f) => f.key === value)?.key ?? 'waiting';
}

export function applyReviewFilter(assignments: MyReviewAssignment[], key: ReviewFilter) {
  const filter = FILTERS.find((f) => f.key === key) ?? FILTERS[0];
  return assignments.filter(filter.match);
}

/** Status choices for the reviewer's list; the choice lives in the URL (?status=) */
export function ReviewFilterTabs({
  active,
  assignments,
}: {
  active: ReviewFilter;
  assignments: MyReviewAssignment[];
}) {
  return (
    <nav aria-label="กรองตามสถานะ" className="mb-4 flex flex-wrap gap-2">
      {FILTERS.map((filter) => {
        const count = assignments.filter(filter.match).length;
        const current = filter.key === active;
        return (
          <Link
            key={filter.key}
            href={filter.key === 'waiting' ? '/manage/review' : `/manage/review?status=${filter.key}`}
            aria-current={current ? 'page' : undefined}
            className={`inline-flex min-h-11 items-center gap-1.5 rounded-lg border px-3.5 text-sm font-medium ${
              current ? 'border-brand bg-brand text-white' : 'border-line bg-surface text-ink hover:bg-surface-alt'
            }`}
          >
            {filter.label}
            <span className={current ? 'text-white/80' : 'text-ink-muted'}>{count}</span>
          </Link>
        );
      })}
    </nav>
  );
}
