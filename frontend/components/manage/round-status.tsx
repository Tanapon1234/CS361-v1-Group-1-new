/** open: takes assignments; overdue: marked open but past its deadline; closed: not open */
export type RoundStatus = 'open' | 'overdue' | 'closed';

const STATUS: Record<
  RoundStatus,
  { label: string; hint: string; text: string; dot: string; rail: string }
> = {
  open: {
    label: 'เปิดรับ',
    hint: '',
    text: 'text-emerald-800',
    dot: 'bg-emerald-600 shadow-[0_0_0_3px_rgb(5_150_105/0.18)]',
    rail: 'border-l-emerald-700',
  },
  overdue: {
    label: 'เลยกำหนดส่ง',
    hint: 'หมดเวลาส่งแล้ว มอบหมายไม่ได้',
    text: 'text-amber-800',
    dot: 'bg-amber-600 shadow-[0_0_0_3px_rgb(217_119_6/0.18)]',
    rail: 'border-l-amber-600',
  },
  closed: {
    label: 'ปิดแล้ว',
    hint: 'รอบนี้ปิดแล้ว มอบหมายไม่ได้',
    text: 'text-zinc-600',
    // hollow ring: the round is not live
    dot: 'border-[1.5px] border-zinc-400 bg-transparent',
    rail: 'border-l-zinc-300',
  },
};

export const roundStatusHint = (status: RoundStatus) => STATUS[status].hint;

/** Colour of the left edge of a round row or fold: the state as structure, not a tag */
export const roundStatusRail = (status: RoundStatus) => `border-l-4 ${STATUS[status].rail}`;

/**
 * A round's state as a dot and a word, no box around it. The word always carries the
 * meaning (the dot is decoration), and the text colours keep at least 4.5:1 on white.
 */
export function RoundStatusMark({ status }: { status: RoundStatus }) {
  const { label, text, dot } = STATUS[status];
  return (
    <span className={`inline-flex items-center gap-2 text-sm font-medium whitespace-nowrap ${text}`}>
      <span aria-hidden className={`size-2 shrink-0 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
