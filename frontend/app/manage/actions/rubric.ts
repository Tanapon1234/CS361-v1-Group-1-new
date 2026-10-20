'use server';

import { redirect } from 'next/navigation';

import { backend } from '@/lib/backend/client';
import { attempt, bool, int, num, requiredText, text, type ActionState } from '@/lib/backend/form';
import type { RubricVersion } from '@/types/backend';

// --- versions ----------------------------------------------------------------------

export async function createRubricVersion(_: ActionState, form: FormData): Promise<ActionState> {
  let created: RubricVersion | null = null;
  const body: Record<string, unknown> = {
    code: requiredText(form, 'code'),
    approved_meeting: text(form, 'approved_meeting'),
    approved_on: text(form, 'approved_on'),
    source_version_id: int(form, 'source_version_id'),
  };
  for (const name of ['base_points', 'overall_cap', 'min_required', 'min_teaching_credits']) {
    const value = num(form, name);
    if (value !== null) body[name] = value;
  }
  const state = await attempt(async () => {
    created = await backend<RubricVersion>('POST', '/rubric-versions', { body });
  });
  if (created) redirect(`/manage/rubrics/${(created as RubricVersion).id}`);
  return state;
}

export async function updateRubricVersion(
  versionId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PATCH', `/rubric-versions/${versionId}`, {
      body: {
        code: requiredText(form, 'code'),
        approved_meeting: text(form, 'approved_meeting'),
        approved_on: text(form, 'approved_on'),
        base_points: num(form, 'base_points'),
        overall_cap: num(form, 'overall_cap'),
        min_required: num(form, 'min_required'),
        min_teaching_credits: num(form, 'min_teaching_credits'),
        is_active: bool(form, 'is_active'),
      },
    })
  );
}

// --- categories / sections ---------------------------------------------------------

export async function createCategory(
  versionId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(
    () =>
      backend('POST', `/rubric-versions/${versionId}/categories`, {
        body: {
          code: requiredText(form, 'code'),
          name_th: requiredText(form, 'name_th'),
          cap: num(form, 'cap'),
          sort_order: int(form, 'sort_order') ?? 0,
        },
      }),
    'เพิ่มหมวดแล้ว'
  );
}

function sectionBody(form: FormData) {
  return {
    code: requiredText(form, 'code'),
    name_th: requiredText(form, 'name_th'),
    parent_id: int(form, 'parent_id'),
    cap: num(form, 'cap'),
    max_entries: int(form, 'max_entries'),
    sort_order: int(form, 'sort_order') ?? 0,
  };
}

export async function createSection(
  categoryId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(
    () => backend('POST', `/rubric-categories/${categoryId}/sections`, { body: sectionBody(form) }),
    'เพิ่มข้อแล้ว'
  );
}

export async function updateSection(
  sectionId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  return attempt(() =>
    backend('PATCH', `/rubric-sections/${sectionId}`, { body: sectionBody(form) })
  );
}

export async function deleteSection(sectionId: number): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/rubric-sections/${sectionId}`), 'ลบแล้ว');
}

// --- items -------------------------------------------------------------------------

/** Parse the item form; field_schema is typed as JSON in a textarea */
function itemBody(form: FormData): Record<string, unknown> | string {
  let fieldSchema: unknown = null;
  const rawSchema = text(form, 'field_schema');
  if (rawSchema) {
    try {
      fieldSchema = JSON.parse(rawSchema);
    } catch {
      return 'field_schema ต้องเป็น JSON ที่ถูกต้อง เช่น {"hours": {"type": "int", "required": true}}';
    }
  }
  const ranged = text(form, 'weight_mode') === 'ranged';
  return {
    label_th: requiredText(form, 'label_th'),
    weight_mode: ranged ? 'ranged' : 'fixed',
    weight: ranged ? null : num(form, 'weight'),
    weight_min: ranged ? num(form, 'weight_min') : null,
    weight_max: ranged ? num(form, 'weight_max') : null,
    range_basis: ranged ? text(form, 'range_basis') : null,
    assessor_position: ranged ? text(form, 'assessor_position') : null,
    assessment_agg: ranged ? (text(form, 'assessment_agg') ?? 'single') : 'none',
    unit: requiredText(form, 'unit'),
    unit_divisor: num(form, 'unit_divisor') ?? 1,
    uses_participation: bool(form, 'uses_participation'),
    counts_teaching_credit: bool(form, 'counts_teaching_credit'),
    once_per_round: bool(form, 'once_per_round'),
    tier_min: int(form, 'tier_min'),
    tier_max: int(form, 'tier_max'),
    field_schema: fieldSchema,
    is_active: bool(form, 'is_active'),
  };
}

export async function createItem(
  sectionId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  const body = itemBody(form);
  if (typeof body === 'string') return { ok: false, message: body };
  return attempt(
    () => backend('POST', `/rubric-sections/${sectionId}/items`, { body }),
    'เพิ่มตัวเลือกแล้ว'
  );
}

export async function updateItem(
  itemId: number,
  _: ActionState,
  form: FormData
): Promise<ActionState> {
  const body = itemBody(form);
  if (typeof body === 'string') return { ok: false, message: body };
  return attempt(() => backend('PATCH', `/rubric-items/${itemId}`, { body }));
}

export async function setItemActive(
  itemId: number,
  active: boolean): Promise<ActionState> {
  return attempt(
    () => backend('PATCH', `/rubric-items/${itemId}`, { body: { is_active: active } }),
    active ? 'เปิดใช้แล้ว' : 'ปิดใช้แล้ว'
  );
}

export async function deleteItem(itemId: number): Promise<ActionState> {
  return attempt(() => backend('DELETE', `/rubric-items/${itemId}`), 'ลบแล้ว');
}
