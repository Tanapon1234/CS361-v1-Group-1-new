'use server';

import { redirect } from 'next/navigation';

import { backend } from '@/lib/backend/client';
import { attempt, bool, int, requiredText, text, type ActionState } from '@/lib/backend/form';
import { DEPARTMENT_POSITIONS } from '@/lib/backend/labels';
import type { Department, Lecturer } from '@/types/backend';

// --- lecturers ---------------------------------------------------------------------

function lecturerBody(form: FormData) {
  return {
    name_th: requiredText(form, 'name_th'),
    name_en: text(form, 'name_en'),
    rank: text(form, 'rank'),
    department_id: int(form, 'department_id'),
    office: text(form, 'office'),
    phone: text(form, 'phone'),
    phone_extension: text(form, 'phone_extension'),
    email: requiredText(form, 'email'),
    cognito_sub: text(form, 'cognito_sub'),
  };
}

export async function createLecturer(_: ActionState, form: FormData): Promise<ActionState> {
  let created: Lecturer | null = null;
  const state = await attempt(async () => {
    created = await backend<Lecturer>('POST', '/lecturers', { body: lecturerBody(form) });
  });
  if (created) redirect(`/manage/lecturers/${(created as Lecturer).lecturer_id}`);
  return state;
}

export async function updateLecturer(
  lecturerId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  const body: Record<string, unknown> = lecturerBody(form);
  // An empty box keeps the current Cognito link; it is write-only so we cannot show it
  if (body.cognito_sub === null) delete body.cognito_sub;
  return attempt(() => backend('PATCH', `/lecturers/${lecturerId}`, { body }));
}

export async function setLecturerActive(
  lecturerId: string,
  active: boolean): Promise<ActionState> {
  return attempt(
    () => backend('POST', `/lecturers/${lecturerId}/${active ? 'activate' : 'deactivate'}`),
    active ? 'เปิดใช้งานแล้ว' : 'ปิดใช้งานแล้ว'
  );
}

// --- departments --------------------------------------------------------------------

export async function createDepartment(_: ActionState, form: FormData): Promise<ActionState> {
  return attempt(
    () =>
      backend<Department>('POST', '/departments', {
        body: { code: requiredText(form, 'code'), name_th: requiredText(form, 'name_th') },
      }),
    'เพิ่มสาขาแล้ว'
  );
}

export async function updateDepartment(
  departmentId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PATCH', `/departments/${departmentId}`, {
      body: {
        code: requiredText(form, 'code'),
        name_th: requiredText(form, 'name_th'),
        is_active: bool(form, 'is_active'),
      },
    })
  );
}

// --- positions ----------------------------------------------------------------------

export async function createPosition(
  lecturerId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  const position = requiredText(form, 'position');
  // Faculty-level positions never belong to a department
  const isDepartmentLevel = (DEPARTMENT_POSITIONS as readonly string[]).includes(position);
  return attempt(
    () =>
      backend('POST', `/lecturers/${lecturerId}/positions`, {
        body: {
          position,
          department_id: isDepartmentLevel ? int(form, 'department_id') : null,
          start_date: requiredText(form, 'start_date'),
          end_date: text(form, 'end_date'),
        },
      }),
    'แต่งตั้งแล้ว'
  );
}

export async function endPosition(
  lecturerId: string,
  positionId: string,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(
    () =>
      backend('PATCH', `/lecturers/${lecturerId}/positions/${positionId}`, {
        body: { end_date: text(form, 'end_date') },
      }),
    'บันทึกวันสิ้นสุดวาระแล้ว'
  );
}

export async function deletePosition(
  lecturerId: string,
  positionId: string): Promise<ActionState> {
  return attempt(
    () => backend('DELETE', `/lecturers/${lecturerId}/positions/${positionId}`),
    'ลบแล้ว'
  );
}
