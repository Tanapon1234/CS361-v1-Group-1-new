import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { deletePublication, updatePublication } from '@/app/manage/actions/academic';
import { ActionForm } from '@/components/manage/action-form';
import { PublicationFields } from '@/components/manage/publication-fields';
import { Badge, Notice, PageHeader, Section } from '@/components/manage/ui';
import { canManage } from '@/lib/auth/permissions';
import {
  getPublication,
  getPublicationVerification,
  listLecturerPublications,
  settle,
} from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { VERIFICATION_LABEL, formatDateTime } from '@/lib/backend/labels';
import type { VerificationStatus } from '@/types/backend';

export const metadata: Metadata = { title: 'แก้ไขผลงาน' };

const VERIFICATION_TONE: Record<VerificationStatus, string> = {
  pending: 'border-amber-200 bg-amber-50 text-amber-800',
  verified: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  rejected: 'border-brand/30 bg-brand-soft text-brand',
};

export default async function PublicationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const publicationId = Number.parseInt(id, 10);
  const [publication, me] = await Promise.all([
    Number.isFinite(publicationId) ? getPublication(publicationId) : null,
    getCurrentUser(),
  ]);
  if (!publication) notFound();

  const [verification, mine] = await Promise.all([
    settle(getPublicationVerification(publicationId)),
    me ? settle(listLecturerPublications(me.lecturer.lecturer_id)) : null,
  ]);
  const status = verification.data?.verification_status;
  const isAuthor = !!mine?.data?.items.some((p) => p.publication_id === publicationId);
  // docs/v2/permissions.md: authors or staff; a verified publication only staff
  const editable = canManage(me) || (isAuthor && status !== 'verified');

  return (
    <div className="space-y-6">
      <PageHeader
        title={publication.title}
        back={{ href: '/manage/publications', label: 'ผลงานตีพิมพ์' }}
        actions={
          <>
            {status ? <Badge className={VERIFICATION_TONE[status]}>{VERIFICATION_LABEL[status]}</Badge> : null}
            {editable ? (
              <ActionForm
                inline
                variant="danger"
                submitLabel="ลบผลงาน"
                confirmText="ลบผลงานนี้? การผูกกับอาจารย์ทุกคนจะหายไปด้วย"
                action={deletePublication.bind(null, publicationId)}
              />
            ) : null}
          </>
        }
      />
      {verification.data?.verification_note ? (
        <Notice tone={status === 'rejected' ? 'error' : 'info'}>
          หมายเหตุจากผู้ตรวจสอบ: {verification.data.verification_note}
          {verification.data.verified_at ? ` (${formatDateTime(verification.data.verified_at)})` : ''}
          {status === 'rejected' && isAuthor ? ' · แก้ไขแล้วบันทึก ผลงานจะกลับไปรอตรวจสอบอีกครั้ง' : ''}
        </Notice>
      ) : null}
      {!editable ? (
        <Notice>
          {status === 'verified' && isAuthor
            ? 'ผลงานนี้รับรองแล้ว ต้องการแก้ไขให้ติดต่อเจ้าหน้าที่'
            : 'ดูได้อย่างเดียว: แก้ไขได้เฉพาะผู้แต่งหรือเจ้าหน้าที่'}
        </Notice>
      ) : null}
      <Section title="ข้อมูลผลงาน">
        {editable ? (
          <ActionForm action={updatePublication.bind(null, publicationId)}>
            <PublicationFields publication={publication} />
          </ActionForm>
        ) : (
          <fieldset disabled className="m-0 min-w-0 border-0 p-0">
            <PublicationFields publication={publication} />
          </fieldset>
        )}
      </Section>
    </div>
  );
}
