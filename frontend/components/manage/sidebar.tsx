'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

/** What the signed-in user may use (from lib/auth/permissions.ts, computed on the server) */
export interface SidebarAccess {
  assess: boolean;
  review: boolean;
  admin: boolean;
}

interface Item {
  href: string;
  label: string;
  /** Shown only when this access flag is on */
  needs?: keyof SidebarAccess;
}

const GROUPS: { title: string; items: Item[] }[] = [
  { title: '', items: [{ href: '/manage', label: 'ภาพรวมของฉัน' }] },
  {
    title: 'ภาระงานประจำภาค',
    items: [
      { href: '/manage/submissions', label: 'ใบภาระงาน' },
      { href: '/manage/assessments', label: 'งานประเมินของฉัน', needs: 'assess' },
      { href: '/manage/rounds', label: 'รอบประเมิน' },
      { href: '/manage/rubrics', label: 'เกณฑ์ภาระงาน' },
    ],
  },
  {
    title: 'ตรวจสอบ',
    items: [
      { href: '/manage/review', label: 'ตรวจสอบและรับรอง', needs: 'review' },
      { href: '/manage/audit', label: 'ประวัติการแก้ไข', needs: 'admin' },
    ],
  },
  {
    title: 'ข้อมูลอาจารย์',
    items: [
      { href: '/manage/lecturers', label: 'อาจารย์' },
      { href: '/manage/work', label: 'ผลงานรายปี' },
      { href: '/manage/departments', label: 'สาขาวิชา' },
      { href: '/manage/publications', label: 'ผลงานตีพิมพ์' },
      { href: '/manage/research-interests', label: 'หัวข้อวิจัย' },
      { href: '/manage/expertise', label: 'ความเชี่ยวชาญ' },
    ],
  },
];

export function ManageSidebar({ access }: { access: SidebarAccess }) {
  const groups = GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.needs || access[item.needs]),
  })).filter((group) => group.items.length > 0);
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === '/manage' ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <nav
      aria-label="เมนูระบบจัดการ"
      className="overflow-x-auto rounded-xl border border-line bg-surface-alt p-2 lg:sticky lg:top-28"
    >
      <div className="flex min-w-max gap-4 lg:block lg:min-w-0 lg:space-y-4">
        {groups.map((group) => (
          <div key={group.title || 'home'}>
            {group.title ? (
              <p className="hidden px-3 pb-1 text-xs font-bold tracking-wide text-ink-muted uppercase lg:block">
                {group.title}
              </p>
            ) : null}
            <ul className="flex gap-1 lg:block lg:space-y-0.5">
              {group.items.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={isActive(item.href) ? 'page' : undefined}
                    className={
                      isActive(item.href)
                        ? 'block rounded-lg bg-brand-soft px-3 py-2 text-sm font-bold whitespace-nowrap text-brand'
                        : 'block rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap text-ink-muted transition-colors hover:bg-brand-soft hover:text-brand'
                    }
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </nav>
  );
}
