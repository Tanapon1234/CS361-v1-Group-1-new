import 'server-only';

import type {
  FacultyDetail,
  FacultyDetailResponse,
  FacultyListResponse,
  FacultySummary,
} from '@/types/faculty';

/**
 * Faculty API client — the only place in the project that knows the backend URL.
 * This module is server-only (`server-only`), so it can never leak into the
 * browser bundle, and it never talks to S3 directly, per #26/#27.
 */
const API_BASE_URL = (
  process.env.BACKEND_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  ''
).replace(/\/+$/, '');

/** Public, read-only directory of the FastAPI backend (no sign-in). */
const PUBLIC_FACULTIES_PATH = '/public/v3/faculties';

/** Cache for 5 minutes before revalidating — faculty data doesn't change often */
const REVALIDATE_SECONDS = 300;

export type FacultyApiErrorKind =
  | 'config'
  | 'invalid-id'
  | 'not-found'
  | 'network'
  | 'http'
  | 'parse';

/** Distinguishes error kinds so the UI shows the real cause instead of a generic "can't connect" */
export class FacultyApiError extends Error {
  readonly kind: FacultyApiErrorKind;
  readonly status?: number;

  constructor(kind: FacultyApiErrorKind, message: string, status?: number) {
    super(message);
    this.name = 'FacultyApiError';
    this.kind = kind;
    this.status = status;
  }
}

function requireApiBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new FacultyApiError(
      'config',
      'ยังไม่ได้ตั้งค่า BACKEND_API_BASE_URL จึงยังเชื่อมต่อระบบไม่ได้'
    );
  }
  return API_BASE_URL;
}

/** Maps HTTP status → error kind so the UI can pick a message that matches the real cause */
function errorForResponse(response: Response): FacultyApiError {
  if (response.status === 400) {
    return new FacultyApiError('invalid-id', 'รูปแบบรหัสอาจารย์ไม่ถูกต้อง', 400);
  }

  if (response.status === 404) {
    return new FacultyApiError('not-found', 'ไม่พบข้อมูลอาจารย์ที่ต้องการ', 404);
  }

  return new FacultyApiError(
    'http',
    `เซิร์ฟเวอร์ตอบกลับด้วยข้อผิดพลาด (HTTP ${response.status}) กรุณาลองใหม่อีกครั้ง`,
    response.status
  );
}

async function getJson(path: string): Promise<unknown> {
  const baseUrl = requireApiBaseUrl();

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      headers: { Accept: 'application/json' },
      next: { revalidate: REVALIDATE_SECONDS, tags: ['faculties'] },
    });
  } catch {
    // Request never reached the server — e.g. network dropped or DNS didn't resolve
    throw new FacultyApiError(
      'network',
      'ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ กรุณาตรวจสอบการเชื่อมต่อแล้วลองใหม่อีกครั้ง'
    );
  }

  if (!response.ok) throw errorForResponse(response);

  try {
    return await response.json();
  } catch {
    throw new FacultyApiError(
      'parse',
      'ข้อมูลที่ได้รับจากเซิร์ฟเวอร์ไม่ถูกต้อง กรุณาแจ้งผู้ดูแลระบบ'
    );
  }
}

/** Validates the payload against the faculty contract; drop it rather than let null reach the screen */
function isFacultySummary(value: unknown): value is FacultySummary {
  if (typeof value !== 'object' || value === null) return false;

  const candidate = value as Record<string, unknown>;
  if (typeof candidate.id !== 'string' || candidate.id.length === 0) return false;

  const name = candidate.name as Record<string, unknown> | undefined;
  return typeof name === 'object' && name !== null && typeof name.th === 'string';
}

function isFacultyDetailResponse(value: unknown): value is FacultyDetailResponse {
  if (typeof value !== 'object' || value === null || !('data' in value)) return false;

  const data = (value as { data: unknown }).data;
  if (typeof data !== 'object' || data === null) return false;

  const candidate = data as Record<string, unknown>;
  return typeof candidate.id === 'string' && candidate.id.length > 0;
}

/**
 * `GET {BACKEND_API_BASE_URL}/public/v3/faculties`
 * Reads `{ "data": [...] }` per contract #22 and returns only the entries that pass validation.
 */
export async function getFaculties(): Promise<FacultySummary[]> {
  const payload = await getJson(PUBLIC_FACULTIES_PATH);

  if (
    typeof payload !== 'object' ||
    payload === null ||
    !('data' in payload) ||
    !Array.isArray((payload as FacultyListResponse).data)
  ) {
    throw new FacultyApiError('parse', 'รูปแบบข้อมูลคณาจารย์ไม่ตรงกับที่ระบบรองรับ');
  }

  return (payload as FacultyListResponse).data.filter(isFacultySummary);
}

/**
 * `GET {BACKEND_API_BASE_URL}/public/v3/faculties/{id}` for the Profile page (#27).
 * 400 → invalid-id, 404 → not-found, so the page can render the right state.
 */
export async function getFacultyDetail(id: string): Promise<FacultyDetail> {
  const payload = await getJson(`${PUBLIC_FACULTIES_PATH}/${encodeURIComponent(id)}`);

  if (!isFacultyDetailResponse(payload)) {
    throw new FacultyApiError('parse', 'รูปแบบข้อมูลอาจารย์ไม่ตรงกับที่ระบบรองรับ');
  }

  return payload.data;
}
