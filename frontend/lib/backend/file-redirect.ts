import 'server-only';

import { NextResponse } from 'next/server';

import { BackendError, backend } from '@/lib/backend/client';
import type { FileDownload } from '@/types/backend';

/** Redirect to the short-lived S3 URL the backend signs for a lecturer's image or CV */
export async function redirectToLecturerFile(id: string, kind: 'profile-image' | 'cv') {
  try {
    const file = await backend<FileDownload>('GET', `/lecturers/${encodeURIComponent(id)}/${kind}`);
    return NextResponse.redirect(file.download_url);
  } catch (error) {
    const message = error instanceof BackendError ? error.message : 'ดาวน์โหลดไม่สำเร็จ';
    const status = error instanceof BackendError && error.status >= 400 ? error.status : 502;
    return new NextResponse(message, { status, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  }
}
