'use client';

import { useActionState } from 'react';

import { chooseNewPassword, login, type LoginState } from '@/app/login/actions';
import { Field, Notice, buttonClass, inputClass } from '@/components/manage/ui';

/** Email + password; on a first sign-in Cognito asks for a new password first */
export function LoginForm({ next }: { next: string }) {
  const [state, action, pending] = useActionState(
    (previous: LoginState, form: FormData) =>
      previous?.step === 'new-password' ? chooseNewPassword(previous, form) : login(previous, form),
    null
  );

  if (state?.step === 'new-password') {
    return (
      <form action={action} className="space-y-4">
        <Notice>เข้าสู่ระบบครั้งแรก กรุณาตั้งรหัสผ่านใหม่ (อย่างน้อย 10 ตัว มีตัวพิมพ์เล็ก ใหญ่ และตัวเลข)</Notice>
        {state.error ? <Notice tone="error">{state.error}</Notice> : null}
        <input type="hidden" name="next" value={next} />
        <Field label="รหัสผ่านใหม่">
          <input name="new_password" type="password" required minLength={10} autoComplete="new-password" className={inputClass} />
        </Field>
        <Field label="ยืนยันรหัสผ่านใหม่">
          <input name="confirm_password" type="password" required minLength={10} autoComplete="new-password" className={inputClass} />
        </Field>
        <button type="submit" disabled={pending} className={`${buttonClass} w-full`}>
          {pending ? 'กำลังบันทึก…' : 'ตั้งรหัสผ่านและเข้าสู่ระบบ'}
        </button>
      </form>
    );
  }

  return (
    <form action={action} className="space-y-4">
      {state?.error ? <Notice tone="error">{state.error}</Notice> : null}
      <input type="hidden" name="next" value={next} />
      <Field label="อีเมล">
        <input name="email" type="email" required autoComplete="username" defaultValue={state?.email} className={inputClass} />
      </Field>
      <Field label="รหัสผ่าน">
        <input name="password" type="password" required autoComplete="current-password" className={inputClass} />
      </Field>
      <button type="submit" disabled={pending} className={`${buttonClass} w-full`}>
        {pending ? 'กำลังเข้าสู่ระบบ…' : 'เข้าสู่ระบบ'}
      </button>
    </form>
  );
}
