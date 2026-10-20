import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { setRoundOpen, updateRound } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { RoundFields } from '@/components/manage/round-fields';
import {
  Badge,
  EmptyNote,
  Notice,
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
import { createSubmission } from '@/app/manage/actions/workload';
import { canManage, signsForDepartment, viewsAll } from '@/lib/auth/permissions';
import {
  PAGE_SIZE,
  getRound,
  getRoundReport,
  listDepartments,
  listLecturers,
  listRoundSubmissions,
  listRubricVersions,
  listSubmissions,
  MAX_PAGE,
  settle,
} from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
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

  const me = await getCurrentUser();
  const manage = canManage(me);
  // Scores of the whole round: viewers, or a chair / committee for their department
  const seesReport = viewsAll(me) || signsForDepartment(me);
  // Anyone without the round report only sees where their own sheet stands in this round
  const mySheet = !seesReport && me
    ? (await listSubmissions({ round_id: roundId, lecturer_id: me.lecturer.lecturer_id })).items[0] ?? null
    : null;
  const [report, submissions, departments, versions, lecturers] = await Promise.all([
    seesReport ? settle(getRoundReport(roundId, departmentId)) : null,
    seesReport
      ? settle(listRoundSubmissions(roundId, { department_id: departmentId, status, offset }))
      : null,
    listDepartments(),
    listRubricVersions(),
    listLecturers({ limit: MAX_PAGE }),
  ]);
  const reportData = report?.data;
  const submissionsData = submissions?.data;
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
            {manage ? (
              <ActionForm
                inline
                variant={round.is_open ? 'danger' : 'primary'}
                submitLabel={round.is_open ? 'ปิดรอบ' : 'เปิดรอบ'}
                confirmText={round.is_open ? 'ปิดรอบ? อาจารย์จะสร้างใบใหม่ไม่ได้' : undefined}
                action={setRoundOpen.bind(null, roundId, !round.is_open)}
              />
            ) : null}
          </>
        }
      />

      {seesReport ? (
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
      ) : null}

      {!seesReport ? (
        <Section title="ใบภาระงานของฉันในรอบนี้" description="รอบนี้ดูได้อย่างเดียว คุณแก้ไขได้เฉพาะใบของตัวเอง">
          {mySheet ? (
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <StatusBadge status={mySheet.status} />
              <span className="text-ink-muted">คะแนนหลังตัดเพดาน {formatScore(mySheet.capped_total)}</span>
              <Link href={`/manage/submissions/${mySheet.id}`} className={linkClass}>
                เปิดใบภาระงาน
              </Link>
            </div>
          ) : round.is_open ? (
            <ActionForm action={createSubmission} submitLabel="สร้างใบภาระงานของฉัน">
              <input type="hidden" name="round_id" value={roundId} />
              <p className="text-sm text-ink-muted">ยังไม่มีใบของคุณในรอบนี้</p>
            </ActionForm>
          ) : (
            <EmptyNote>ไม่มีใบของคุณในรอบนี้ และรอบนี้ปิดแล้ว</EmptyNote>
          )}
        </Section>
      ) : !reportData || !submissionsData ? (
        <Notice tone="error">{report?.error ?? submissions?.error}</Notice>
      ) : (
        <>
          <Section title="สรุปคะแนน" description={`ขั้นต่ำ ${formatScore(reportData.min_required)} คะแนน · หน่วยกิตสอนขั้นต่ำ ${formatScore(reportData.min_teaching_credits)}`}>
            <div className="grid gap-3 sm:grid-cols-3">
              <Stat label="ใบภาระงาน" value={reportData.summary.submissions} />
              <Stat label="ผ่านเกณฑ์ขั้นต่ำ" value={reportData.summary.meeting_min_required} />
              <Stat label="คะแนนเฉลี่ย (หลังตัดเพดาน)" value={formatScore(reportData.summary.average_capped_total)} />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {Object.entries(reportData.summary.by_status).map(([key, count]) => (
                <Badge key={key}>
                  {SUBMISSION_STATUS_LABEL[key as SubmissionStatus]}: {count}
                </Badge>
              ))}
            </div>
            {reportData.rows.length > 0 ? (
              <div className="mt-4">
                <Table head={['อาจารย์', 'สาขา', 'สถานะ', 'หน่วยกิตสอน', 'คะแนนดิบ', 'หลังตัดเพดาน', 'ผ่านเกณฑ์']}>
                  {reportData.rows.map((row) => (
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

          <Section title={`ใบภาระงานในรอบ (${submissionsData.meta.total})`}>
            {submissionsData.items.length === 0 ? (
              <EmptyNote>ไม่มีใบภาระงานตามเงื่อนไข</EmptyNote>
            ) : (
              <Table head={['อาจารย์', 'สาขา', 'สถานะ', 'คะแนน', '']}>
                {submissionsData.items.map((submission) => (
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
              total={submissionsData.meta.total}
              limit={PAGE_SIZE}
              offset={offset}
              hrefFor={(next) => withQuery(base, { department_id: departmentId, status, offset: next })}
            />
          </Section>
        </>
      )}

      {manage ? (
        <Section title="แก้ไขรอบ">
          <ActionForm action={updateRound.bind(null, roundId)}>
            <RoundFields round={round} versions={versions.items} />
          </ActionForm>
        </Section>
      ) : null}
    </div>
  );
}
