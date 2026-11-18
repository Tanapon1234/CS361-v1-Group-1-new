import Link from 'next/link';

/** Rounds and the rubric live under one menu entry; admins switch between them here */
export function RoundsRubricTabs({ current }: { current: 'rounds' | 'rubrics' }) {
  const tabs = [
    { key: 'rounds', href: '/manage/rounds', label: 'รอบประเมิน' },
    { key: 'rubrics', href: '/manage/rubrics', label: 'เกณฑ์ภาระงาน' },
  ] as const;
  return (
    <nav aria-label="รอบและเกณฑ์ภาระงาน" className="mb-6 flex gap-1 border-b border-line">
      {tabs.map((tab) => (
        <Link
          key={tab.key}
          href={tab.href}
          aria-current={tab.key === current ? 'page' : undefined}
          className={
            tab.key === current
              ? '-mb-px border-b-2 border-brand px-4 py-2.5 text-sm font-bold text-brand'
              : '-mb-px border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-ink-muted hover:text-brand'
          }
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
