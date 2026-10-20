import type { NextRequest } from 'next/server';

import { redirectToLecturerFile } from '@/lib/backend/file-redirect';

/** GET /manage/lecturers/{id}/profile-image → redirect to the image (S3 or the old V1 URL) */
export async function GET(_: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  return redirectToLecturerFile((await params).id, 'profile-image');
}
