'use server';

import { redirect } from 'next/navigation';

import { backend } from '@/lib/backend/client';
import { attempt, int, requiredText, text, type ActionState } from '@/lib/backend/form';
import type { FileInfo, UploadStart } from '@/components/manage/file-upload';
import type { Lecturer, Publication, UploadPresign } from '@/types/backend';

/** Lecturer academic profile + the shared master lists (research interests, expertise, publications). */

function ids(form: FormData, name: string): number[] {
  return form
    .getAll(name)
    .map((value) => Number(value))
    .filter((value) => Number.isInteger(value) && value > 0);
}

// --- research interests ------------------------------------------------------------

export async function replaceLecturerResearchInterests(
  lecturerId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PUT', `/lecturers/${lecturerId}/research-interests`, {
      body: { research_interest_ids: ids(form, 'research_interest_ids') },
    })
  );
}

export async function createResearchInterest(_: ActionState, form: FormData): Promise<ActionState> {
  return attempt(
    () => backend('POST', '/research-interests', { body: { name: requiredText(form, 'name') } }),
    'เพิ่มแล้ว'
  );
}

export async function renameResearchInterest(
  id: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PATCH', `/research-interests/${id}`, { body: { name: requiredText(form, 'name') } })
  );
}

export async function deleteResearchInterest(id: number): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/research-interests/${id}`), 'ลบแล้ว');
}

// --- expertise ---------------------------------------------------------------------

export async function replaceLecturerExpertise(
  lecturerId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PUT', `/lecturers/${lecturerId}/expertise`, {
      body: { expertise_ids: ids(form, 'expertise_ids') },
    })
  );
}

export async function createExpertise(_: ActionState, form: FormData): Promise<ActionState> {
  return attempt(
    () =>
      backend('POST', '/expertise', { body: { description: requiredText(form, 'description') } }),
    'เพิ่มแล้ว'
  );
}

export async function updateExpertise(
  id: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PATCH', `/expertise/${id}`, {
      body: { description: requiredText(form, 'description') },
    })
  );
}

export async function deleteExpertise(id: number): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/expertise/${id}`), 'ลบแล้ว');
}

// --- education ---------------------------------------------------------------------

function educationBody(form: FormData) {
  return {
    degree: text(form, 'degree'),
    field: text(form, 'field'),
    institution: text(form, 'institution'),
    country: text(form, 'country'),
    graduation_year: text(form, 'graduation_year'),
  };
}

export async function createEducation(
  lecturerId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(
    () => backend('POST', `/lecturers/${lecturerId}/educations`, { body: educationBody(form) }),
    'เพิ่มแล้ว'
  );
}

export async function updateEducation(
  lecturerId: string,
  educationId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PATCH', `/lecturers/${lecturerId}/educations/${educationId}`, {
      body: educationBody(form),
    })
  );
}

export async function deleteEducation(
  lecturerId: string,
  educationId: number): Promise<ActionState> {
  return attempt(
    () => backend('DELETE', `/lecturers/${lecturerId}/educations/${educationId}`),
    'ลบแล้ว'
  );
}

// --- publication profiles ----------------------------------------------------------

export async function createPublicationProfile(
  lecturerId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(
    () =>
      backend('POST', `/lecturers/${lecturerId}/publication-profiles`, {
        body: { provider: requiredText(form, 'provider'), url: requiredText(form, 'url') },
      }),
    'เพิ่มแล้ว'
  );
}

export async function updatePublicationProfile(
  lecturerId: string,
  profileId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PATCH', `/lecturers/${lecturerId}/publication-profiles/${profileId}`, {
      body: { provider: requiredText(form, 'provider'), url: requiredText(form, 'url') },
    })
  );
}

export async function deletePublicationProfile(
  lecturerId: string,
  profileId: number): Promise<ActionState> {
  return attempt(
    () => backend('DELETE', `/lecturers/${lecturerId}/publication-profiles/${profileId}`),
    'ลบแล้ว'
  );
}

// --- publications ------------------------------------------------------------------

function publicationBody(form: FormData) {
  return {
    title: requiredText(form, 'title'),
    publication_year: int(form, 'publication_year'),
    venue: text(form, 'venue'),
    volume: text(form, 'volume'),
    pages: text(form, 'pages'),
    doi: text(form, 'doi'),
    citation_text: text(form, 'citation_text'),
  };
}

export async function createPublication(_: ActionState, form: FormData): Promise<ActionState> {
  let created: Publication | null = null;
  const state = await attempt(async () => {
    created = await backend<Publication>('POST', '/publications', { body: publicationBody(form) });
  });
  if (created) redirect(`/manage/publications/${(created as Publication).publication_id}`);
  return state;
}

export async function updatePublication(
  id: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() => backend('PATCH', `/publications/${id}`, { body: publicationBody(form) }));
}

export async function deletePublication(id: number): Promise<ActionState> {
  const state = await attempt(() => backend('DELETE', `/publications/${id}`), 'ลบแล้ว');
  if (state?.ok) redirect('/manage/publications');
  return state;
}

// --- profile image / CV (presigned S3 upload) ---------------------------------------

export type LecturerFileKind = 'profile-image' | 'cv';

export async function startLecturerFileUpload(
  lecturerId: string,
  kind: LecturerFileKind,
  file: FileInfo
): Promise<UploadStart> {
  let upload: UploadPresign | null = null;
  const state = await attempt(async () => {
    upload = await backend<UploadPresign>('POST', `/lecturers/${lecturerId}/${kind}/presign`, {
      body: { content_type: file.type, size_bytes: file.size },
    });
  });
  if (!upload) return { ok: false, message: state?.message ?? 'ผิดพลาด' };
  const { upload_url, fields, object_key } = upload as UploadPresign;
  return { ok: true, url: upload_url, fields, token: object_key };
}

export async function finishLecturerFileUpload(
  lecturerId: string,
  kind: LecturerFileKind,
  objectKey: string
): Promise<ActionState> {
  return attempt(
    () =>
      backend<Lecturer>('POST', `/lecturers/${lecturerId}/${kind}/complete`, {
        body: { object_key: objectKey },
      }),
    'อัปโหลดเรียบร้อย'
  );
}

export async function deleteLecturerFile(
  lecturerId: string,
  kind: LecturerFileKind): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/lecturers/${lecturerId}/${kind}`), 'ลบไฟล์แล้ว');
}
