import 'server-only';

import { cookies } from 'next/headers';
import { cache } from 'react';

import { cognitoEnabled } from '@/lib/auth/cognito';
import { DEV_LECTURER_COOKIE, DEV_ROLES_COOKIE, ID_TOKEN_COOKIE } from '@/lib/auth/session';
import type { Me, ProblemDetail } from '@/types/backend';

/**
 * Client for the FastAPI backend (`backend/`, every path under `/api/v2`).
 *
 * Server-only: pages fetch in Server Components and change data in Server Actions, so the
 * backend URL and the caller's token never reach the browser. Requests are never cached:
 * this area shows working data that changes with every action.
 *
 * The caller: `Authorization: Bearer <Cognito ID token>` after signing in, or in dev mode
 * (no COGNITO_CLIENT_ID) the X-Lecturer-Id / X-Dev-Roles picked on /manage/switch-user.
 */
const BACKEND_API_BASE_URL = (process.env.BACKEND_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/+$/,
  ''
);


export class BackendError extends Error {
  readonly status: number;
  readonly problem: ProblemDetail | null;

  constructor(status: number, message: string, problem: ProblemDetail | null = null) {
    super(message);
    this.name = 'BackendError';
    this.status = status;
    this.problem = problem;
  }
}

/** A message a person can act on, built from the backend's problem+json body */
function messageFor(status: number, problem: ProblemDetail | null): string {
  if (status === 501) return 'ส่วนนี้ของระบบยังไม่เปิดใช้งาน (backend ยังไม่ได้ implement)';
  if (status === 401) {
    return cognitoEnabled()
      ? 'เซสชันหมดอายุหรือยังไม่ได้เข้าสู่ระบบ กรุณาเข้าสู่ระบบใหม่'
      : 'กรุณาเลือกผู้ใช้งานก่อน (เมนู "สลับผู้ใช้")';
  }
  if (status === 403) {
    return problem?.detail ? `คุณไม่มีสิทธิ์ทำรายการนี้ (${problem.detail})` : 'คุณไม่มีสิทธิ์ทำรายการนี้';
  }
  if (!problem) return `เซิร์ฟเวอร์ตอบกลับด้วยข้อผิดพลาด (HTTP ${status})`;
  const fields = problem.errors?.map((e) => `${e.field.replace(/^body\./, '')}: ${e.message}`);
  return [problem.detail ?? problem.title, ...(fields ?? [])].join(' · ');
}

/** Headers that say who is calling */
async function callerHeaders(): Promise<Record<string, string>> {
  const jar = await cookies();
  if (cognitoEnabled()) {
    const token = jar.get(ID_TOKEN_COOKIE)?.value;
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
  const lecturerId = jar.get(DEV_LECTURER_COOKIE)?.value;
  const roles = jar.get(DEV_ROLES_COOKIE)?.value;
  return {
    ...(lecturerId && /^[0-9a-f-]{36}$/i.test(lecturerId) ? { 'X-Lecturer-Id': lecturerId } : {}),
    ...(roles ? { 'X-Dev-Roles': roles } : {}),
  };
}

type Query = Record<string, string | number | boolean | null | undefined>;

interface RequestOptions {
  query?: Query;
  body?: unknown;
  headers?: Record<string, string>;
}

function buildUrl(path: string, query?: Query): string {
  const url = new URL(`${BACKEND_API_BASE_URL}/api/v2${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

/** Raw request; the caller handles the Response (used for redirects). */
export async function backendFetch(
  method: string,
  path: string,
  { query, body, headers }: RequestOptions = {},
  init: RequestInit = {}
): Promise<Response> {
  const caller = await callerHeaders();
  try {
    return await fetch(buildUrl(path, query), {
      method,
      cache: 'no-store',
      headers: {
        Accept: 'application/json',
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...caller,
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      ...init,
    });
  } catch {
    throw new BackendError(
      0,
      `เชื่อมต่อ backend ไม่ได้ (${BACKEND_API_BASE_URL}) กรุณาตรวจสอบว่าเปิด backend อยู่ และตั้ง BACKEND_API_BASE_URL ถูกต้อง`
    );
  }
}

export async function backend<T>(
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const response = await backendFetch(method, path, options);
  if (response.status === 204) return undefined as T;

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const problem = (payload as ProblemDetail | null) ?? null;
    throw new BackendError(response.status, messageFor(response.status, problem), problem);
  }
  return payload as T;
}

/** GET that turns "not found" into null instead of an error */
export async function backendOrNull<T>(path: string, query?: Query): Promise<T | null> {
  try {
    return await backend<T>('GET', path, { query });
  } catch (error) {
    if (error instanceof BackendError && error.status === 404) return null;
    throw error;
  }
}

/** The signed-in user (GET /me), once per request; null when nobody is signed in */
export const getCurrentUser = cache(async (): Promise<Me | null> => {
  try {
    return await backend<Me>('GET', '/me');
  } catch (error) {
    if (error instanceof BackendError && (error.status === 401 || error.status === 403)) {
      return null;
    }
    throw error;
  }
});

export async function currentLecturerId(): Promise<string | null> {
  return (await getCurrentUser())?.lecturer.lecturer_id ?? null;
}
