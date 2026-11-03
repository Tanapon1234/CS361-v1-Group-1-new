import { NextResponse, type NextRequest } from 'next/server';

import { backendFetch } from '@/lib/backend/client';

/**
 * GET /manage/departments/{id}/report/csv → proxies the backend's `?format=csv`.
 * A plain link can't carry the caller's auth headers, so this keeps the backend call
 * server-side and streams the CSV body straight through.
 */
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const search = new URL(request.url).searchParams;
  try {
    const response = await backendFetch('GET', `/departments/${encodeURIComponent(id)}/report`, {
      query: {
        academic_year_from: search.get('academic_year_from'),
        academic_year_to: search.get('academic_year_to'),
        format: 'csv',
      },
    });
    if (!response.ok) {
      const problem = (await response.json().catch(() => null)) as { detail?: string } | null;
      return new NextResponse(problem?.detail ?? `ดาวน์โหลดไม่สำเร็จ (HTTP ${response.status})`, {
        status: response.status,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }
    const body = await response.text();
    return new NextResponse(body, {
      status: 200,
      headers: {
        'Content-Type': response.headers.get('content-type') ?? 'text/csv',
        'Content-Disposition': response.headers.get('content-disposition') ?? 'attachment; filename="report.csv"',
      },
    });
  } catch (error) {
    return new NextResponse(error instanceof Error ? error.message : 'ดาวน์โหลดไม่สำเร็จ', {
      status: 502,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}
