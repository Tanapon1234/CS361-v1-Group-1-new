import type { NextRequest } from 'next/server';

import { redirectToLecturerFile } from '@/lib/backend/file-redirect';

/** GET /manage/lecturers/{id}/cv → redirect to a short-lived S3 download URL */
export async function GET(_: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  return redirectToLecturerFile((await params).id, 'cv');
}
