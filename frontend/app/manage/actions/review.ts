'use server';

import { backend } from '@/lib/backend/client';
import { attempt, text, type ActionState } from '@/lib/backend/form';

/** A reviewer's verdict on a publication or an evidence file (backend: PUT .../verification) */
function verdict(form: FormData) {
  const status = text(form, 'status');
  return { status, note: text(form, 'note') };
}

export async function verifyPublication(id: number, _: ActionState, form: FormData): Promise<ActionState> {
  return attempt(
    () => backend('PUT', `/publications/${id}/verification`, { body: verdict(form) }),
    'บันทึกผลแล้ว'
  );
}

export async function verifyEvidence(id: string, _: ActionState, form: FormData): Promise<ActionState> {
  return attempt(
    () => backend('PUT', `/evidence/${id}/verification`, { body: verdict(form) }),
    'บันทึกผลแล้ว'
  );
}
