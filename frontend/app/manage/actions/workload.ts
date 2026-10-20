'use server';

import { redirect } from 'next/navigation';

import { backend } from '@/lib/backend/client';
import {
  attempt,
  bool,
  int,
  num,
  requiredText,
  text,
  type ActionState,
} from '@/lib/backend/form';
import type { FileInfo, UploadStart } from '@/components/manage/file-upload';
import type { EvaluationRound, EvidenceUpload, Submission } from '@/types/backend';

// --- rounds ------------------------------------------------------------------------

function roundBody(form: FormData) {
  const due = text(form, 'submit_due_at');
  return {
    rubric_version_id: int(form, 'rubric_version_id'),
    name_th: requiredText(form, 'name_th'),
    period_start: requiredText(form, 'period_start'),
    period_end: requiredText(form, 'period_end'),
    salary_effective_on: requiredText(form, 'salary_effective_on'),
    academic_year: int(form, 'academic_year'),
    semester: int(form, 'semester'),
    // <input type="datetime-local"> has no zone; the browser's local time is meant
    submit_due_at: due ? new Date(due).toISOString() : null,
    is_open: bool(form, 'is_open'),
  };
}

export async function createRound(_: ActionState, form: FormData): Promise<ActionState> {
  let created: EvaluationRound | null = null;
  const state = await attempt(async () => {
    created = await backend<EvaluationRound>('POST', '/rounds', { body: roundBody(form) });
  });
  if (created) redirect(`/manage/rounds/${(created as EvaluationRound).id}`);
  return state;
}

export async function updateRound(
  roundId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() => backend('PATCH', `/rounds/${roundId}`, { body: roundBody(form) }));
}

export async function setRoundOpen(
  roundId: number,
  open: boolean): Promise<ActionState> {
  return attempt(
    () => backend('PATCH', `/rounds/${roundId}`, { body: { is_open: open } }),
    open ? 'เปิดรอบแล้ว' : 'ปิดรอบแล้ว'
  );
}

// --- submissions -------------------------------------------------------------------

export async function createSubmission(_: ActionState, form: FormData): Promise<ActionState> {
  let created: Submission | null = null;
  const state = await attempt(async () => {
    created = await backend<Submission>('POST', '/submissions', {
      body: { round_id: int(form, 'round_id') },
    });
  });
  if (created) redirect(`/manage/submissions/${(created as Submission).id}`);
  return state;
}

export async function deleteSubmission(submissionId: string): Promise<ActionState> {
  const state = await attempt(() => backend('DELETE', `/submissions/${submissionId}`), 'ลบแล้ว');
  if (state?.ok) redirect('/manage/submissions');
  return state;
}

export async function signSubmission(
  submissionId: string,
  decision: 'approved' | 'returned',
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(
    () =>
      backend('POST', `/submissions/${submissionId}/approvals`, {
        body: { decision, comment: text(form, 'comment') },
      }),
    decision === 'approved' ? 'บันทึกการอนุมัติแล้ว' : 'ตีกลับแล้ว'
  );
}

// --- entries -----------------------------------------------------------------------

function entryBody(form: FormData): Record<string, unknown> | string {
  let details: unknown = null;
  const rawDetails = text(form, 'details_json');
  if (rawDetails) {
    try {
      details = JSON.parse(rawDetails);
    } catch {
      return 'ข้อมูลเพิ่มเติมไม่ถูกต้อง';
    }
  }
  return {
    item_id: int(form, 'item_id'),
    title: text(form, 'title'),
    publication_id: int(form, 'publication_id'),
    course_code: text(form, 'course_code'),
    section_no: text(form, 'section_no'),
    student_count: int(form, 'student_count'),
    quantity: num(form, 'quantity') ?? 1,
    participation_pct: num(form, 'participation_pct') ?? 100,
    credits: num(form, 'credits'),
    details,
    note: text(form, 'note'),
  };
}

export async function createEntry(
  submissionId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  const body = entryBody(form);
  if (typeof body === 'string') return { ok: false, message: body };
  return attempt(
    () => backend('POST', `/submissions/${submissionId}/entries`, { body }),
    'เพิ่มรายการแล้ว ระบบคำนวณคะแนนให้แล้ว'
  );
}

export async function updateEntry(
  entryId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  const body = entryBody(form);
  if (typeof body === 'string') return { ok: false, message: body };
  return attempt(() => backend('PATCH', `/entries/${entryId}`, { body }));
}

export async function deleteEntry(entryId: string): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/entries/${entryId}`), 'ลบรายการแล้ว');
}

// --- assessments -------------------------------------------------------------------

export async function putMyAssessment(
  entryId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(
    () =>
      backend('PUT', `/entries/${entryId}/assessments/me`, {
        body: { value_given: num(form, 'value_given'), comment: text(form, 'comment') },
      }),
    'บันทึกค่าประเมินแล้ว'
  );
}

export async function deleteMyAssessment(entryId: string): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/entries/${entryId}/assessments/me`), 'ถอนค่าประเมินแล้ว');
}

// --- evidence (called from the upload widget, not a form) ---------------------------

export async function startEvidenceUpload(entryId: string, file: FileInfo): Promise<UploadStart> {
  let upload: EvidenceUpload | null = null;
  const state = await attempt(async () => {
    upload = await backend<EvidenceUpload>('POST', `/entries/${entryId}/evidence`, {
      body: {
        file_name: file.name,
        mime_type: file.type,
        size_bytes: file.size,
        label: file.label,
      },
    });
  });
  if (!upload) return { ok: false, message: state?.message ?? 'ผิดพลาด' };
  const { upload_url, fields, evidence } = upload as EvidenceUpload;
  return { ok: true, url: upload_url, fields, token: evidence.id };
}

export async function finishEvidenceUpload(
  evidenceId: string,
  checksum: string | null
): Promise<ActionState> {
  return attempt(
    () =>
      backend('PATCH', `/evidence/${evidenceId}`, {
        body: { status: 'uploaded', ...(checksum ? { checksum } : {}) },
      }),
    'แนบไฟล์เรียบร้อย'
  );
}

export async function deleteEvidence(evidenceId: string): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/evidence/${evidenceId}`), 'ลบไฟล์แล้ว');
}
