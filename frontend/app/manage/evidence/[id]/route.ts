import { NextResponse, type NextRequest } from 'next/server';

import { backendFetch } from '@/lib/backend/client';

/**
 * GET /manage/evidence/{id} → follows the backend's 302 to the presigned S3 URL.
 * The backend URL stays on the server; the browser only ever sees S3.
 */
export async function GET(_: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const response = await backendFetch(
      'GET',
      `/evidence/${encodeURIComponent(id)}/content`,
      {},
      { redirect: 'manual' }
    );
    const location = response.headers.get('location');
    if (response.status >= 300 && response.status < 400 && location) {
      return NextResponse.redirect(location);
    }
    const problem = (await response.json().catch(() => null)) as { detail?: string } | null;
    return new NextResponse(problem?.detail ?? `ดาวน์โหลดไม่สำเร็จ (HTTP ${response.status})`, {
      status: response.status,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  } catch (error) {
    return new NextResponse(error instanceof Error ? error.message : 'ดาวน์โหลดไม่สำเร็จ', {
      status: 502,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}
