import type { Metadata } from 'next';
import Link from 'next/link';

import { createSubmission } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import {
  EmptyNote,
  Field,
  PageHeader,
  Pager,
  Section,
  StatusBadge,
  Table,
  Td,
  inputClass,
  intParam,
  linkClass,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { MAX_PAGE, PAGE_SIZE, listLecturers, listRounds, listSubmissions } from '@/lib/backend/api';
import { currentLecturerId } from '@/lib/backend/client';
import { SUBMISSION_STATUS_LABEL, formatDateTime, formatScore } from '@/lib/backend/labels';
import type { SubmissionStatus } from '@/types/backend';

export const metadata: Metadata = { title: 'ใบภาระงาน' };

export default async function SubmissionsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const me = await currentLecturerId();
  const scope = param(params.scope) === 'all' ? 'all' : 'mine';
  const roundId = intParam(params.round_id);
  const status = param(params.status) as SubmissionStatus | undefined;
  const offset = intParam(params.offset) ?? 0;

  const [rounds, lecturers, submissions] = await Promise.all([
    listRounds(),
    listLecturers({ limit: MAX_PAGE }),
    me
      ? listSubmissions({
          round_id: roundId,
          status: status || undefined,
          lecturer_id: scope === 'mine' ? me : undefined,
          offset,
        })
      : Promise.resolve(null),
  ]);
  const roundName = new Map(rounds.items.map((round) => [round.id, round.name_th]));
  const lecturerName = new Map(lecturers.items.map((l) => [l.lecturer_id, l.name_th]));
  const openRounds = rounds.items.filter((round) => round.is_open);

  return (
    <div className="space-y-6">
      <PageHeader title="ใบภาระงาน" description="กรอกภาระงานประจำภาค แนบหลักฐาน และติดตามการอนุมัติ" />

      {!me ? (
        <EmptyNote>
          ต้อง <Link href="/manage/switch-user" className={linkClass}>เลือกผู้ใช้งาน</Link> ก่อน
        </EmptyNote>
      ) : (
        <>
          <Section title="สร้างใบภาระงานของฉัน">
            {openRounds.length === 0 ? (
              <EmptyNote>ยังไม่มีรอบที่เปิดให้กรอก</EmptyNote>
            ) : (
              <ActionForm action={createSubmission} submitLabel="สร้างใบ" className="flex flex-wrap items-end gap-3">
                <Field label="รอบประเมิน" className="min-w-60">
                  <select name="round_id" required className={inputClass}>
                    {openRounds.map((round) => (
                      <option key={round.id} value={round.id}>{round.name_th}</option>
                    ))}
                  </select>
                </Field>
              </ActionForm>
            )}
          </Section>

          <Section title={scope === 'mine' ? 'ใบของฉัน' : 'ใบทั้งหมด'}>
            <form role="search" className="mb-4 flex flex-wrap gap-2">
              <select name="scope" defaultValue={scope} className={`${inputClass} sm:w-44`} aria-label="ขอบเขต">
                <option value="mine">เฉพาะของฉัน</option>
                <option value="all">ทั้งหมด</option>
              </select>
              <select name="round_id" defaultValue={roundId ?? ''} className={`${inputClass} sm:w-56`} aria-label="รอบ">
                <option value="">ทุกรอบ</option>
                {rounds.items.map((round) => (
                  <option key={round.id} value={round.id}>{round.name_th}</option>
                ))}
              </select>
              <select name="status" defaultValue={status ?? ''} className={`${inputClass} sm:w-56`} aria-label="สถานะ">
                <option value="">ทุกสถานะ</option>
                {Object.entries(SUBMISSION_STATUS_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <button type="submit" className={secondaryButtonClass}>กรอง</button>
            </form>

            {!submissions || submissions.items.length === 0 ? (
              <EmptyNote>ไม่พบใบภาระงาน</EmptyNote>
            ) : (
              <Table head={['อาจารย์', 'รอบ', 'สถานะ', 'คะแนนหลังตัดเพดาน', 'ส่งเมื่อ', '']}>
                {submissions.items.map((submission) => (
                  <tr key={submission.id}>
                    <Td className="font-medium text-ink">{lecturerName.get(submission.lecturer_id) ?? '–'}</Td>
                    <Td>{roundName.get(submission.round_id) ?? `#${submission.round_id}`}</Td>
                    <Td><StatusBadge status={submission.status} /></Td>
                    <Td>{formatScore(submission.capped_total)}</Td>
                    <Td>{formatDateTime(submission.submitted_at)}</Td>
                    <Td>
                      <Link href={`/manage/submissions/${submission.id}`} className={linkClass}>เปิด</Link>
                    </Td>
                  </tr>
                ))}
              </Table>
            )}
            {submissions ? (
              <Pager
                total={submissions.meta.total}
                limit={PAGE_SIZE}
                offset={offset}
                hrefFor={(next) =>
                  withQuery('/manage/submissions', { scope, round_id: roundId, status, offset: next })
                }
              />
            ) : null}
          </Section>
        </>
      )}
    </div>
  );
}
