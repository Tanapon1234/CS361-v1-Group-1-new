import type { Metadata } from 'next';
import Link from 'next/link';

import { verifyEvidence, verifyPublication } from '@/app/manage/actions/review';
import {
  EmptyNote,
  Notice,
  PageHeader,
  Pager,
  Section,
  Table,
  Td,
  intParam,
  linkClass,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { VerdictForm } from '@/components/manage/verdict-form';
import { canReview } from '@/lib/auth/permissions';
import { listEvidenceQueue, listPublicationQueue, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { VERIFICATION_LABEL, formatDate } from '@/lib/backend/labels';
import type { VerificationStatus } from '@/types/backend';

export const metadata: Metadata = { title: 'ตรวจสอบและรับรอง' };

const STATUSES: VerificationStatus[] = ['pending', 'rejected', 'verified'];

export default async function ReviewPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const me = await getCurrentUser();
  if (!canReview(me)) {
    return (
      <div className="space-y-6">
        <PageHeader title="ตรวจสอบและรับรอง" />
        <Notice tone="error">หน้านี้สำหรับผู้ตรวจสอบเท่านั้น</Notice>
      </div>
    );
  }

  const params = await searchParams;
  const status = (STATUSES as string[]).includes(param(params.status) ?? '')
    ? (param(params.status) as VerificationStatus)
    : 'pending';
  const pubOffset = intParam(params.pub_offset) ?? 0;
  const evOffset = intParam(params.ev_offset) ?? 0;
  const [publications, evidence] = await Promise.all([
    settle(listPublicationQueue({ status, offset: pubOffset })),
    settle(listEvidenceQueue({ status, offset: evOffset })),
  ]);
  const hrefFor = (extra: Record<string, string | number | undefined>) =>
    withQuery('/manage/review', { status, pub_offset: pubOffset, ev_offset: evOffset, ...extra });

  return (
    <div className="space-y-6">
      <PageHeader
        title="ตรวจสอบและรับรอง"
        description="ผลงานตีพิมพ์และไฟล์หลักฐานที่รอผู้ตรวจสอบ เรียงจากเก่าไปใหม่ ห้ามรับรองงานของตัวเอง"
      />
      <nav aria-label="สถานะ" className="flex gap-2">
        {STATUSES.map((value) => (
          <Link
            key={value}
            href={withQuery('/manage/review', { status: value })}
            aria-current={value === status ? 'page' : undefined}
            className={value === status ? `${secondaryButtonClass} border-brand text-brand` : secondaryButtonClass}
          >
            {VERIFICATION_LABEL[value]}
          </Link>
        ))}
      </nav>

      <Section title={`ผลงานตีพิมพ์ (${publications.data?.meta.total ?? 0})`}>
        {publications.error ? (
          <Notice tone="error">{publications.error}</Notice>
        ) : publications.data?.items.length === 0 ? (
          <EmptyNote>ไม่มีผลงานในสถานะ &quot;{VERIFICATION_LABEL[status]}&quot;</EmptyNote>
        ) : (
          <Table head={['ผลงาน', 'ผู้แต่ง', 'ปี', 'ตรวจ']}>
            {publications.data?.items.map((item) => (
              <tr key={item.publication_id}>
                <Td>
                  <Link href={`/manage/publications/${item.publication_id}`} className={linkClass}>
                    {item.title}
                  </Link>
                  {item.doi ? <p className="text-xs break-all text-ink-muted">{item.doi}</p> : null}
                  {item.verification_note ? <p className="text-xs text-brand">{item.verification_note}</p> : null}
                </Td>
                <Td>{item.authors.join(', ') || '–'}</Td>
                <Td>{item.publication_year ?? '–'}</Td>
                <Td>
                  <VerdictForm action={verifyPublication.bind(null, item.publication_id)} />
                </Td>
              </tr>
            ))}
          </Table>
        )}
        {publications.data ? (
          <Pager
            total={publications.data.meta.total}
            limit={publications.data.meta.limit}
            offset={pubOffset}
            hrefFor={(next) => hrefFor({ pub_offset: next })}
          />
        ) : null}
      </Section>

      <Section title={`ไฟล์หลักฐาน (${evidence.data?.meta.total ?? 0})`} description="เฉพาะไฟล์ที่อัปโหลดเสร็จแล้ว">
        {evidence.error ? (
          <Notice tone="error">{evidence.error}</Notice>
        ) : evidence.data?.items.length === 0 ? (
          <EmptyNote>ไม่มีไฟล์ในสถานะ &quot;{VERIFICATION_LABEL[status]}&quot;</EmptyNote>
        ) : (
          <Table head={['ไฟล์', 'เจ้าของใบ', 'อัปโหลด', 'ตรวจ']}>
            {evidence.data?.items.map((item) => (
              <tr key={item.evidence_id}>
                <Td>
                  <a href={`/manage/evidence/${item.evidence_id}`} className={linkClass} target="_blank" rel="noreferrer">
                    {item.label ?? item.file_name}
                  </a>
                  <p className="text-xs text-ink-muted">
                    <Link href={`/manage/submissions/${item.submission_id}`} className={linkClass}>
                      {item.entry_title ?? 'ดูใบภาระงาน'}
                    </Link>
                  </p>
                  {item.verification_note ? <p className="text-xs text-brand">{item.verification_note}</p> : null}
                </Td>
                <Td>{item.owner_name_th}</Td>
                <Td>{formatDate(item.created_at)}</Td>
                <Td>
                  <VerdictForm action={verifyEvidence.bind(null, item.evidence_id)} />
                </Td>
              </tr>
            ))}
          </Table>
        )}
        {evidence.data ? (
          <Pager
            total={evidence.data.meta.total}
            limit={evidence.data.meta.limit}
            offset={evOffset}
            hrefFor={(next) => hrefFor({ ev_offset: next })}
          />
        ) : null}
      </Section>
    </div>
  );
}
