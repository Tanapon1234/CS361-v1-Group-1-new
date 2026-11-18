import { NextResponse, type NextRequest } from 'next/server';

import { backendFetch } from '@/lib/backend/client';

/**
 * GET /manage/publication-evidence/{id}?publication_id=123 → follows the backend's 302
 * to the presigned S3 URL. Same pattern as /manage/evidence/{id} (entry evidence), but the
 * backend route also needs the publication id, carried here as a query param.
 */
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const publicationId = new URL(request.url).searchParams.get('publication_id');
  if (!publicationId) {
    return new NextResponse('ไม่พบ publication_id', {
      status: 400,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
  try {
    const response = await backendFetch(
      'GET',
      `/publications/${encodeURIComponent(publicationId)}/evidence/${encodeURIComponent(id)}/content`,
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
