'use server';

import { revalidatePath } from 'next/cache';

import { backend, BackendError } from '@/lib/backend/client';
import { attempt, int, requiredText, text, type ActionState } from '@/lib/backend/form';

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

/** The assigned reviewer's verdict on a whole sheet (backend: PUT /submissions/{id}/review) */
export async function reviewSubmission(id: string, _: ActionState, form: FormData): Promise<ActionState> {
  return attempt(
    () => backend('PUT', `/submissions/${id}/review`, { body: verdict(form) }),
    'บันทึกผลตรวจใบภาระงานแล้ว'
  );
}

// --- reviewer assignment (V4 #293): who reviews whom, per round ---------------------

/** One reviewer, several reviewees: the pairs are created one by one, so a pair that
 * already exists is skipped and does not stop the others. */
export async function createReviewerAssignments(
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  const roundId = int(form, 'round_id');
  const reviewerId = requiredText(form, 'reviewer_id');
  const revieweeIds = [...new Set(form.getAll('reviewee_id').map(String))].filter(
    (id) => id && id !== reviewerId
  );
  if (roundId === null) return { ok: false, message: 'เลือกรอบประเมินก่อน' };
  if (revieweeIds.length === 0) return { ok: false, message: 'เลือกอาจารย์ที่ต้องถูกตรวจอย่างน้อย 1 คน' };

  let created = 0;
  let skipped = 0;
  const failures: string[] = [];
  for (const revieweeId of revieweeIds) {
    try {
      await backend('POST', '/reviewer-assignments', {
        body: { round_id: roundId, reviewer_id: reviewerId, reviewee_id: revieweeId },
      });
      created += 1;
    } catch (error) {
      if (!(error instanceof BackendError)) throw error;
      if (error.status === 409 && /already assigned/i.test(error.message)) skipped += 1;
      else failures.push(error.message);
    }
  }
  revalidatePath('/manage', 'layout');

  const parts = [`มอบหมายแล้ว ${created} คน`];
  if (skipped) parts.push(`ข้าม ${skipped} คนที่มีอยู่แล้ว`);
  if (failures.length) parts.push(`ไม่สำเร็จ ${failures.length} คน: ${failures[0]}`);
  return { ok: failures.length === 0, message: parts.join(' · ') };
}

export async function deleteReviewerAssignment(id: string): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/reviewer-assignments/${id}`), 'ยกเลิกการมอบหมายแล้ว');
}
