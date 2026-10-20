'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { CURRENT_LECTURER_COOKIE } from '@/lib/backend/client';

/**
 * Temporary sign-in: pick which lecturer to act as. The backend reads it from the
 * X-Lecturer-Id header, which it ignores in prod. Replace with Cognito later.
 */
export async function switchUser(formData: FormData) {
  const lecturerId = formData.get('lecturer_id');
  if (typeof lecturerId !== 'string' || !/^[0-9a-f-]{36}$/i.test(lecturerId)) {
    throw new Error('Invalid lecturer id');
  }
  (await cookies()).set(CURRENT_LECTURER_COOKIE, lecturerId, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
  });
  redirect('/manage');
}

export async function signOut() {
  (await cookies()).delete(CURRENT_LECTURER_COOKIE);
  redirect('/manage/switch-user');
}
