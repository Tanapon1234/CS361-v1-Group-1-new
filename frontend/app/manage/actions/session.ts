'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { cognitoEnabled } from '@/lib/auth/cognito';
import { DEV_LECTURER_COOKIE, DEV_ROLES_COOKIE, cookieOptions } from '@/lib/auth/session';

const DEV_ROLES = new Set(['staff', 'reviewer', 'executive', 'admin']);
const WEEK = 60 * 60 * 24 * 7;

/**
 * Dev mode only (no COGNITO_CLIENT_ID): act as a lecturer, with extra roles, through the
 * X-Lecturer-Id / X-Dev-Roles headers. The backend ignores them in prod.
 */
export async function switchUser(formData: FormData) {
  if (cognitoEnabled()) redirect('/login');
  const lecturerId = formData.get('lecturer_id');
  if (typeof lecturerId !== 'string' || !/^[0-9a-f-]{36}$/i.test(lecturerId)) {
    throw new Error('Invalid lecturer id');
  }
  const roles = formData.getAll('roles').map(String).filter((role) => DEV_ROLES.has(role));
  const jar = await cookies();
  jar.set(DEV_LECTURER_COOKIE, lecturerId, cookieOptions(WEEK));
  if (roles.length) jar.set(DEV_ROLES_COOKIE, roles.join(','), cookieOptions(WEEK));
  else jar.delete(DEV_ROLES_COOKIE);
  redirect('/manage');
}

export async function signOut() {
  const jar = await cookies();
  jar.delete(DEV_LECTURER_COOKIE);
  jar.delete(DEV_ROLES_COOKIE);
  redirect('/manage/switch-user');
}
