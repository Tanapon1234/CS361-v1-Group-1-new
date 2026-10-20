import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { LoginForm } from '@/app/login/login-form';
import { cognitoEnabled } from '@/lib/auth/cognito';

export const metadata: Metadata = { title: 'เข้าสู่ระบบ', robots: { index: false } };

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  // Dev mode has no Cognito: pick a lecturer to act as instead
  if (!cognitoEnabled()) redirect('/manage/switch-user');

  const raw = (await searchParams).next;
  const next = typeof raw === 'string' && raw.startsWith('/') && !raw.startsWith('//') ? raw : '/manage';

  return (
    <div className="mx-auto max-w-md px-4 py-16 sm:px-6">
      <div className="rounded-xl border border-line bg-surface p-6 shadow-sm sm:p-8">
        <h1 className="flex items-center gap-2.5 text-2xl font-bold text-ink">
          <span className="h-6 w-1.5 rounded-full bg-brand" aria-hidden="true" />
          เข้าสู่ระบบ
        </h1>
        <p className="mt-2 mb-6 text-sm text-ink-muted">
          ระบบจัดการผลงานและภาระงานอาจารย์ ใช้อีเมลมหาวิทยาลัยที่เจ้าหน้าที่สร้างบัญชีให้
        </p>
        <LoginForm next={next} />
      </div>
    </div>
  );
}
