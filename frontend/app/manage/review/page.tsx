import type { Metadata } from 'next';

import { Notice, PageHeader, Section } from '@/components/manage/ui';
import { ReviewRounds } from '@/components/manage/review-rounds';
import { canReview } from '@/lib/auth/permissions';
import { listMyReviewAssignments, listRoundsWithState, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'ตรวจสอบและรับรอง' };

export default async function ReviewPage() {
  const me = await getCurrentUser();
  if (!canReview(me)) {
    return (
      <div className="space-y-6">
        <PageHeader title="ตรวจสอบและรับรอง" />
        <Notice tone="error">หน้านี้สำหรับอาจารย์ผู้ตรวจเท่านั้น</Notice>
      </div>
    );
  }

  const [assignments, rounds] = await Promise.all([settle(listMyReviewAssignments()), listRoundsWithState()]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="ตรวจสอบและรับรอง"
        description="อาจารย์ที่คุณต้องตรวจ แยกตามรอบประเมิน เปิดใบภาระงานเพื่อดูรายการและหลักฐาน แล้วบันทึกผลตรวจใบ ห้ามตรวจใบของตัวเอง"
      />
      <Section title="ที่ต้องตรวจตามรอบ">
        {assignments.error ? (
          <Notice tone="error">{assignments.error}</Notice>
        ) : (
          <ReviewRounds rounds={rounds} assignments={assignments.data?.items ?? []} />
        )}
      </Section>
    </div>
  );
}
