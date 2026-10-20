'use client';

import { useEffect } from 'react';

import { buttonClass, Notice } from '@/components/manage/ui';

/**
 * Error boundary for every /manage page. Messages come from lib/backend/client.ts,
 * so they say what actually went wrong (backend down, 501, validation...).
 */
export default function ManageError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  /** Next.js 16 passes `retry` (formerly `reset`) */
  retry: () => void;
}) {
  useEffect(() => {
    console.error('[manage] page failed:', error);
  }, [error]);

  return (
    <div className="space-y-4">
      <Notice tone="error">{error.message || 'เกิดข้อผิดพลาด'}</Notice>
      <button type="button" onClick={retry} className={buttonClass}>
        ลองอีกครั้ง
      </button>
    </div>
  );
}
