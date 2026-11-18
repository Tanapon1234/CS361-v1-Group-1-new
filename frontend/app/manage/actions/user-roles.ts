'use server';

import { backend } from '@/lib/backend/client';
import { attempt, requiredText, type ActionState } from '@/lib/backend/form';

// --- roles an admin grants in the app: staff, executive, admin (reviewer is derived) ---

export async function grantUserRole(_: ActionState, form: FormData): Promise<ActionState> {
  return attempt(
    () =>
      backend('POST', '/user-roles', {
        body: { lecturer_id: requiredText(form, 'lecturer_id'), role: requiredText(form, 'role') },
      }),
    'กำหนดบทบาทแล้ว'
  );
}

export async function revokeUserRole(lecturerId: string, role: string): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/user-roles/${lecturerId}/${role}`), 'ถอนบทบาทแล้ว');
}
