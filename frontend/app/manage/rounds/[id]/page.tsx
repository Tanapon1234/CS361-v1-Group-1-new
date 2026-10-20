import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { setRoundOpen, updateRound } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { RoundFields } from '@/components/manage/round-fields';
import {
  Badge,
  EmptyNote,
  PageHeader,
  Pager,
  Section,
  Stat,
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
import {
  PAGE_SIZE,
  getRound,
  getRoundReport,
  listDepartments,
  listLecturers,
  listRoundSubmissions,
  listRubricVersions,
  MAX_PAGE,
} from '@/lib/backend/api';
import { SUBMISSION_STATUS_LABEL, formatScore } from '@/lib/backend/labels';
import type { SubmissionStatus } from '@/types/backend';

export const metadata: Metadata = { title: 'รอบประเมิน' };

export default async function RoundPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const roundId = Number.parseInt(id, 10);
  const round = Number.isFinite(roundId) ? await getRound(roundId) : null;
  if (!round) notFound();

  const departmentId = intParam(query.department_id);
  const status = param(query.status) as SubmissionStatus | undefined;
  const offset = intParam(query.offset) ?? 0;

  const [report, submissions, departments, versions, lecturers] = await Promise.all([
    getRoundReport(roundId, departmentId),
    listRoundSubmissions(roundId, { department_id: departmentId, status, offset }),
    listDepartments(),
    listRubricVersions(),
    listLecturers({ limit: MAX_PAGE }),
  ]);
  const departmentName = new Map(departments.items.map((d) => [d.id, d.name_th]));
  const lecturerName = new Map(lecturers.items.map((l) => [l.lecturer_id, l.name_th]));
  const base = `/manage/rounds/${roundId}`;

  return (
    <div className="space-y-6">
      <PageHeader
        title={round.name_th}
        back={{ href: '/manage/rounds', label: 'รอบประเมิน' }}
        actions={
          <>
            {round.is_open ? (
              <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">เปิดกรอก</Badge>
            ) : (
              <Badge>ปิด</Badge>
            )}
            <ActionForm
              inline
              variant={round.is_open ? 'danger' : 'primary'}
              submitLabel={round.is_open ? 'ปิดรอบ' : 'เปิดรอบ'}
              confirmText={round.is_open ? 'ปิดรอบ? อาจารย์จะสร้างใบใหม่ไม่ได้' : undefined}
              action={setRoundOpen.bind(null, roundId, !round.is_open)}
            />
          </>
        }
      />

      <form role="search" className="flex flex-wrap gap-2">
        <select name="department_id" defaultValue={departmentId ?? ''} className={`${inputClass} sm:w-60`} aria-label="สาขา">
          <option value="">ทุกสาขา</option>
          {departments.items.map((department) => (
            <option key={department.id} value={department.id}>{department.name_th}</option>
          ))}
        </select>
        <select name="status" defaultValue={status ?? ''} className={`${inputClass} sm:w-60`} aria-label="สถานะ">
          <option value="">ทุกสถานะ</option>
          {Object.entries(SUBMISSION_STATUS_LABEL).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <button type="submit" className={secondaryButtonClass}>กรอง</button>
      </form>

      <Section title="สรุปคะแนน" description={`ขั้นต่ำ ${formatScore(report.min_required)} คะแนน · หน่วยกิตสอนขั้นต่ำ ${formatScore(report.min_teaching_credits)}`}>
        <div className="grid gap-3 sm:grid-cols-3">
          <Stat label="ใบภาระงาน" value={report.summary.submissions} />
          <Stat label="ผ่านเกณฑ์ขั้นต่ำ" value={report.summary.meeting_min_required} />
          <Stat label="คะแนนเฉลี่ย (หลังตัดเพดาน)" value={formatScore(report.summary.average_capped_total)} />
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(report.summary.by_status).map(([key, count]) => (
            <Badge key={key}>
              {SUBMISSION_STATUS_LABEL[key as SubmissionStatus]}: {count}
            </Badge>
          ))}
        </div>
        {report.rows.length > 0 ? (
          <div className="mt-4">
            <Table head={['อาจารย์', 'สาขา', 'สถานะ', 'หน่วยกิตสอน', 'คะแนนดิบ', 'หลังตัดเพดาน', 'ผ่านเกณฑ์']}>
              {report.rows.map((row) => (
                <tr key={row.submission_id}>
                  <Td>
                    <Link href={`/manage/submissions/${row.submission_id}`} className={linkClass}>{row.name_th}</Link>
                  </Td>
                  <Td>{departmentName.get(row.department_id) ?? '–'}</Td>
                  <Td><StatusBadge status={row.status} /></Td>
                  <Td className={row.meets_min_teaching_credits ? '' : 'text-brand'}>{formatScore(row.teaching_credits)}</Td>
                  <Td>{formatScore(row.raw_total)}</Td>
                  <Td className="font-semibold">{formatScore(row.capped_total)}</Td>
                  <Td>{row.meets_min_required ? 'ผ่าน' : <span className="text-brand">ยังไม่ผ่าน</span>}</Td>
                </tr>
              ))}
            </Table>
          </div>
        ) : null}
      </Section>

      <Section title={`ใบภาระงานในรอบ (${submissions.meta.total})`}>
        {submissions.items.length === 0 ? (
          <EmptyNote>ไม่มีใบภาระงานตามเงื่อนไข</EmptyNote>
        ) : (
          <Table head={['อาจารย์', 'สาขา', 'สถานะ', 'คะแนน', '']}>
            {submissions.items.map((submission) => (
              <tr key={submission.id}>
                <Td>{lecturerName.get(submission.lecturer_id) ?? submission.lecturer_id}</Td>
                <Td>{departmentName.get(submission.department_snapshot) ?? '–'}</Td>
                <Td><StatusBadge status={submission.status} /></Td>
                <Td>{formatScore(submission.capped_total)}</Td>
                <Td>
                  <Link href={`/manage/submissions/${submission.id}`} className={linkClass}>เปิด</Link>
                </Td>
              </tr>
            ))}
          </Table>
        )}
        <Pager
          total={submissions.meta.total}
          limit={PAGE_SIZE}
          offset={offset}
          hrefFor={(next) => withQuery(base, { department_id: departmentId, status, offset: next })}
        />
      </Section>

      <Section title="แก้ไขรอบ">
        <ActionForm action={updateRound.bind(null, roundId)}>
          <RoundFields round={round} versions={versions.items} />
        </ActionForm>
      </Section>
    </div>
  );
}
