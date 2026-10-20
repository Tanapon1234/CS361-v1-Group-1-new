import 'server-only';

import { revalidatePath } from 'next/cache';

import type { ActionState } from '@/components/manage/action-form';
import { BackendError } from '@/lib/backend/client';

export type { ActionState };

/**
 * Run a mutation and turn its outcome into an ActionState. Backend errors become the
 * backend's own message (problem+json `detail` + field errors); anything else is rethrown
 * so Next.js can handle redirects and real bugs.
 */
export async function attempt(
  work: () => Promise<unknown>,
  success = 'บันทึกเรียบร้อย'
): Promise<ActionState> {
  try {
    await work();
    // Every /manage page reads live data: refresh them all after a change
    revalidatePath('/manage', 'layout');
    return { ok: true, message: success };
  } catch (error) {
    if (error instanceof BackendError) return { ok: false, message: error.message };
    throw error;
  }
}

// --- reading FormData ---------------------------------------------------------------
// Empty inputs become null (clears a nullable column) or undefined (field left out).

export function text(form: FormData, name: string): string | null {
  const value = form.get(name);
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
}

export function requiredText(form: FormData, name: string): string {
  return text(form, name) ?? '';
}

export function num(form: FormData, name: string): number | null {
  const value = text(form, name);
  if (value === null) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function int(form: FormData, name: string): number | null {
  const value = num(form, name);
  return value === null ? null : Math.trunc(value);
}

/** Checkbox: present = true */
export function bool(form: FormData, name: string): boolean {
  return form.get(name) !== null;
}

/** <select> for a boolean filter: "true" / "false" / "" */
export function optionalBool(form: FormData, name: string): boolean | null {
  const value = text(form, name);
  return value === null ? null : value === 'true';
}

/** Drop keys whose value is undefined (PATCH: only send what the form has) */
export function compact<T extends Record<string, unknown>>(values: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(values).filter(([, value]) => value !== undefined)
  ) as Partial<T>;
}
