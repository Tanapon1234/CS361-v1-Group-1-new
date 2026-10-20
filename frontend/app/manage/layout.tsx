import type { Metadata } from 'next';
import Link from 'next/link';
import type { ReactNode } from 'react';

import { logout } from '@/app/login/actions';
import { signOut } from '@/app/manage/actions/session';
import { ManageSidebar } from '@/components/manage/sidebar';
import { secondaryButtonClass } from '@/components/manage/ui';
import { cognitoEnabled } from '@/lib/auth/cognito';
import { BackendError, getCurrentUser } from '@/lib/backend/client';
import type { Me } from '@/types/backend';

export const metadata: Metadata = {
  title: { default: 'ระบบจัดการ', template: '%s | ระบบจัดการ' },
  robots: { index: false },
};

const ROLE_LABEL: Record<string, string> = {
  staff: 'เจ้าหน้าที่',
  reviewer: 'ผู้ตรวจสอบ',
  executive: 'ผู้บริหาร',
  admin: 'ผู้ดูแลระบบ',
};

/** Who is signed in, shown on every /manage page */
async function CurrentUserBar() {
  const cognito = cognitoEnabled();
  let me: Me | null = null;
  let problem: string | null = null;
  try {
    me = await getCurrentUser();
  } catch (error) {
    problem = error instanceof BackendError ? error.message : 'โหลดข้อมูลผู้ใช้ไม่สำเร็จ';
  }
  const roles = (me?.roles ?? []).filter((role) => role in ROLE_LABEL).map((role) => ROLE_LABEL[role]);

  return (
    <div className="border-b border-line bg-surface-alt">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 text-sm sm:px-6">
        <p className="text-ink-muted">
          {problem ? (
            <span className="text-brand">{problem}</span>
          ) : me ? (
            <>
              {cognito ? 'เข้าสู่ระบบในชื่อ' : 'กำลังใช้งานในชื่อ'}{' '}
              <strong className="text-ink">{me.lecturer.name_th}</strong>
              {roles.length ? <span> · {roles.join(', ')}</span> : null}
            </>
          ) : cognito ? (
            'ยังไม่ได้เข้าสู่ระบบ'
          ) : (
            'ยังไม่ได้เลือกผู้ใช้งาน'
          )}
        </p>
        <div className="flex gap-2">
          {cognito ? (
            me ? (
              <form action={logout}>
                <button type="submit" className={secondaryButtonClass}>
                  ออกจากระบบ
                </button>
              </form>
            ) : (
              <Link href="/login" className={secondaryButtonClass}>
                เข้าสู่ระบบ
              </Link>
            )
          ) : (
            <>
              <Link href="/manage/switch-user" className={secondaryButtonClass}>
                {me ? 'สลับผู้ใช้' : 'เลือกผู้ใช้งาน'}
              </Link>
              {me ? (
                <form action={signOut}>
                  <button type="submit" className={secondaryButtonClass}>
                    ออกจากระบบ
                  </button>
                </form>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ManageLayout({ children }: { children: ReactNode }) {
  return (
    <div>
      <CurrentUserBar />
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:grid lg:grid-cols-[14rem_minmax(0,1fr)] lg:gap-8 lg:py-10">
        <aside className="mb-6 lg:mb-0">
          <ManageSidebar />
        </aside>
        <div className="min-w-0">{children}</div>
      </div>
    </div>
  );
}
