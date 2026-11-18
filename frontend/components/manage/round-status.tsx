import type { ReactNode } from 'react';

/** open: takes assignments; overdue: marked open but past its deadline; closed: not open */
export type RoundStatus = 'open' | 'overdue' | 'closed';

const STATUS: Record<RoundStatus, { label: string; hint: string; tag: string; icon: ReactNode }> = {
  open: {
    label: 'เปิดรับ',
    hint: '',
    tag: 'border-emerald-700/30 bg-emerald-50 text-emerald-900',
    icon: <path d="M3.5 8.5l3 3 6-7" />,
  },
  overdue: {
    label: 'เลยกำหนดส่ง',
    hint: 'หมดเวลาส่งแล้ว มอบหมายไม่ได้',
    tag: 'border-amber-700/30 bg-amber-50 text-amber-900',
    icon: (
      <>
        <circle cx="8" cy="8" r="5.5" />
        <path d="M8 5v3.2l2 1.3" />
      </>
    ),
  },
  closed: {
    label: 'ปิดแล้ว',
    hint: 'รอบนี้ปิดแล้ว มอบหมายไม่ได้',
    tag: 'border-zinc-400/60 bg-zinc-100 text-zinc-700',
    icon: (
      <>
        <rect x="3.5" y="7" width="9" height="6" rx="1" />
        <path d="M5.5 7V5.5a2.5 2.5 0 015 0V7" />
      </>
    ),
  },
};

export const roundStatusHint = (status: RoundStatus) => STATUS[status].hint;

/**
 * Plain status tag for an evaluation round: a small square-cornered label with a line
 * icon, so the state reads without relying on colour alone.
 */
export function RoundStatusBadge({ status }: { status: RoundStatus }) {
  const { label, tag, icon } = STATUS[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-semibold leading-none whitespace-nowrap ${tag}`}
    >
      <svg
        aria-hidden
        viewBox="0 0 16 16"
        className="size-3.5 shrink-0"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {icon}
      </svg>
      {label}
    </span>
  );
}
