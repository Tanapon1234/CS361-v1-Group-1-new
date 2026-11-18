import { reviewSubmission } from '@/app/manage/actions/review';
import { Badge, Notice, Section } from '@/components/manage/ui';
import { VerdictForm } from '@/components/manage/verdict-form';
import { VERIFICATION_LABEL, formatDateTime } from '@/lib/backend/labels';
import type { SubmissionReview, SubmissionStatus } from '@/types/backend';

const TONE: Record<SubmissionReview['status'], string> = {
  pending: 'border-line bg-surface-alt text-ink-muted',
  verified: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  rejected: 'border-brand/30 bg-brand-soft text-brand',
};

/**
 * The reviewer's verdict on the whole sheet. Everyone who can see the sheet sees the verdict
 * and its note; only the assigned reviewer gets the form, and only once the sheet is submitted.
 */
export function SheetReviewPanel({
  submissionId,
  status,
  review,
  isAssignedReviewer,
}: {
  submissionId: string;
  status: SubmissionStatus;
  review: SubmissionReview | null;
  isAssignedReviewer: boolean;
}) {
  const judged = review && review.status !== 'pending';
  if (!judged && !isAssignedReviewer) return null;

  return (
    <Section
      title="ผลตรวจใบภาระงาน"
      description="ผู้ตรวจดูว่าใบครบถ้วนและหลักฐานตรงกับที่กรอกหรือไม่ (ไม่เปลี่ยนสถานะของใบ)"
    >
      <div className="space-y-4">
        {review ? (
          <div className="space-y-1.5">
            <Badge className={TONE[review.status]}>{VERIFICATION_LABEL[review.status]}</Badge>
            {review.note ? <p className="text-sm text-ink">{review.note}</p> : null}
            {judged && review.reviewed_at ? (
              <p className="text-[13px] text-ink-muted">ตรวจเมื่อ {formatDateTime(review.reviewed_at)}</p>
            ) : null}
          </div>
        ) : null}

        {isAssignedReviewer ? (
          status === 'draft' ? (
            <Notice>ใบนี้ยังเป็นร่าง รอเจ้าของใบส่งก่อนจึงจะตรวจได้</Notice>
          ) : (
            <div>
              <p className="mb-2 text-sm font-semibold text-ink">บันทึกผลตรวจของคุณ</p>
              <VerdictForm action={reviewSubmission.bind(null, submissionId)} />
            </div>
          )
        ) : null}
      </div>
    </Section>
  );
}
