import 'server-only';

import { redirect } from 'next/navigation';

import { isLecturerOnly } from '@/lib/auth/permissions';
import { getCurrentUser } from '@/lib/backend/client';
import type { Me } from '@/types/backend';

/**
 * Pages a plain lecturer has no use for (directory, master data, rubric). The sidebar
 * hides them; this stops a typed URL. The backend still checks every call.
 */
export async function leaveIfLecturerOnly(): Promise<Me | null> {
  const me = await getCurrentUser().catch(() => null);
  if (isLecturerOnly(me)) redirect('/manage');
  return me;
}

/** A plain lecturer may open only their own lecturer pages */
export async function keepToSelf(lecturerId: string): Promise<void> {
  const me = await getCurrentUser().catch(() => null);
  if (me && isLecturerOnly(me) && me.lecturer.lecturer_id !== lecturerId) {
    redirect(`/manage/lecturers/${me.lecturer.lecturer_id}`);
  }
}

/** The directory of lecturers is not for a plain lecturer: send them to their own profile */
export async function leaveToOwnProfile(): Promise<void> {
  const me = await getCurrentUser().catch(() => null);
  if (me && isLecturerOnly(me)) redirect(`/manage/lecturers/${me.lecturer.lecturer_id}`);
}
