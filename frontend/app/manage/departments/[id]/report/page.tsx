import type { Metadata } from 'next';
import { notFound, redirect } from 'next/navigation';

import {
  EmptyNote,
  Field,
  Notice,
  PageHeader,
  Section,
  Table,
  Td,
  inputClass,
  intParam,
  linkClass,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { signsForDepartment, viewsAll } from '@/lib/auth/permissions';
import {
  getDepartmentReport,
  listDepartments,
  listLecturers,
  listRounds,
  listRubricCategories,
  listRubricVersions,
  MAX_PAGE,
  settle,
} from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatScore } from '@/lib/backend/labels';
import type {
  DepartmentReport,
  DepartmentReportCategoryRow,
  DepartmentReportMissingRow,
  RubricCategory,
} from '@/types/backend';

export const metadata: Metadata = { title: 'รายงานสาขา' };

/** Category codes and names from the newest rubric version (codes stay the same across versions) */
async function categoryOptions(): Promise<RubricCategory[]> {
  const versions = await listRubricVersions();
  const newest = versions.items.reduce<number | null>(
    (id, version) => (id === null || version.id > id ? version.id : id),
    null
  );
  return newest === null ? [] : (await listRubricCategories(newest)).items;
}

export default async function DepartmentReportPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const departmentId = Number.parseInt(id, 10);
  if (!Number.isFinite(departmentId)) notFound();

  const me = await getCurrentUser();
  // Precise cross-department scoping (staff/reviewer see only their own department, a
  // dept_chair/committee only theirs) is re-checked by the backend; this is just a gate
  // against lecturers who have no use for this page at all.
  if (!viewsAll(me) && !signsForDepartment(me)) redirect('/manage/departments');

  const query = await searchParams;
  const yearFrom = intParam(query.year_from);
  const yearTo = intParam(query.year_to);
  const categoryCode = param(query.category) || undefined;
  const lecturerId = param(query.lecturer) || undefined;

  const [departments, rounds, categories, lecturers] = await Promise.all([
    listDepartments(),
    listRounds(),
    categoryOptions(),
    listLecturers({ department_id: departmentId, is_active: true, limit: MAX_PAGE }),
  ]);
  const department = departments.items.find((item) => item.id === departmentId);
  if (!department) notFound();

  const years = [...new Set(rounds.items.map((round) => round.academic_year))].sort((a, b) => b - a);

  const report =
    yearFrom && yearTo
      ? await settle(
          getDepartmentReport(departmentId, {
            academic_year_from: yearFrom,
            academic_year_to: yearTo,
            category_code: categoryCode,
            lecturer_id: lecturerId,
          })
        )
      : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`รายงานสาขา: ${department.name_th}`}
        back={{ href: '/manage/departments', label: 'สาขาวิชา' }}
        description="สรุปคะแนนภาระงานของอาจารย์ในสาขา แยกตามปีการศึกษาและหมวดงาน"
      />

      <Section title="เลือกช่วงปีการศึกษา และกรอง">
        <form className="grid gap-3 sm:grid-cols-[1fr_1fr_1.5fr_1.5fr_auto] sm:items-end">
          <Field label="ปีการศึกษา (จาก)">
            <select name="year_from" defaultValue={yearFrom ?? ''} required className={inputClass}>
              <option value="" disabled>
                เลือกปี
              </option>
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </Field>
          <Field label="ถึง">
            <select name="year_to" defaultValue={yearTo ?? ''} required className={inputClass}>
              <option value="" disabled>
                เลือกปี
              </option>
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </Field>
          <Field label="หมวดงาน">
            <select name="category" defaultValue={categoryCode ?? ''} className={inputClass}>
              <option value="">ทุกหมวด</option>
              {categories.map((option) => (
                <option key={option.id} value={option.code}>
                  {option.code}. {option.name_th}
                </option>
              ))}
            </select>
          </Field>
          <Field label="อาจารย์">
            <select name="lecturer" defaultValue={lecturerId ?? ''} className={inputClass}>
              <option value="">ทุกคนในสาขา</option>
              {lecturers.items.map((lecturer) => (
                <option key={lecturer.lecturer_id} value={lecturer.lecturer_id}>
                  {lecturer.name_th}
                </option>
              ))}
            </select>
          </Field>
          <button type="submit" className={secondaryButtonClass}>
            ดูรายงาน
          </button>
        </form>
      </Section>

      {!report ? (
        <EmptyNote>เลือกช่วงปีการศึกษาก่อน แล้วกดดูรายงาน</EmptyNote>
      ) : report.data ? (
        <ReportResult report={report.data} departmentId={departmentId} />
      ) : (
        <Notice tone="error">{report.error}</Notice>
      )}
    </div>
  );
}

function ReportResult({ report, departmentId }: { report: DepartmentReport; departmentId: number }) {
  const lecturers = groupByLecturer(report.rows);
  const missingByYear = groupMissingByYear(report.missing);
  const when =
    report.academic_year_from === report.academic_year_to
      ? `ปีการศึกษา ${report.academic_year_from}`
      : `ปีการศึกษา ${report.academic_year_from}-${report.academic_year_to}`;

  return (
    <>
      <p className="text-sm text-ink-muted">
        {when}
        {' · '}
        <a
          href={withQuery(`/manage/departments/${departmentId}/report/csv`, {
            academic_year_from: report.academic_year_from,
            academic_year_to: report.academic_year_to,
            category_code: report.category_code,
            lecturer_id: report.lecturer_id,
          })}
          className={linkClass}
        >
          ดาวน์โหลด CSV
        </a>
      </p>

      {lecturers.length === 0 ? (
        <EmptyNote>ไม่พบข้อมูลในช่วงปีนี้</EmptyNote>
      ) : (
        lecturers.map((lecturer) => (
          <Section
            key={lecturer.lecturer_id}
            title={lecturer.name_th}
            description={`คะแนนรวม ${formatScore(lecturer.totalCapped)}`}
          >
            <Table head={['ปีการศึกษา', 'หมวด', 'คะแนนดิบ', 'คะแนนหลังตัดเพดาน']}>
              {lecturer.rows.map((row) => (
                <tr key={`${row.academic_year}-${row.category_code}`}>
                  <Td>{row.academic_year}</Td>
                  <Td>
                    {row.category_code}. {row.category_name_th}
                  </Td>
                  <Td>{formatScore(row.raw_score)}</Td>
                  <Td>{formatScore(row.capped_score)}</Td>
                </tr>
              ))}
            </Table>
          </Section>
        ))
      )}

      {missingByYear.length > 0 ? (
        <Section title="ยังไม่มีข้อมูล" description="อาจารย์ที่ยังไม่มีใบส่งในปีนั้น">
          <ul className="space-y-3 text-sm">
            {missingByYear.map(({ academic_year, names }) => (
              <li key={academic_year}>
                <span className="font-semibold text-ink">ปีการศึกษา {academic_year}:</span>{' '}
                <span className="text-ink-muted">{names.join(', ')}</span>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}
    </>
  );
}

function groupByLecturer(rows: DepartmentReportCategoryRow[]) {
  const map = new Map<
    string,
    { lecturer_id: string; name_th: string; rows: DepartmentReportCategoryRow[]; totalCapped: number }
  >();
  for (const row of rows) {
    const existing = map.get(row.lecturer_id);
    if (existing) {
      existing.rows.push(row);
      existing.totalCapped += row.capped_score;
    } else {
      map.set(row.lecturer_id, {
        lecturer_id: row.lecturer_id,
        name_th: row.name_th,
        rows: [row],
        totalCapped: row.capped_score,
      });
    }
  }
  return [...map.values()].sort((a, b) => a.name_th.localeCompare(b.name_th));
}

function groupMissingByYear(missing: DepartmentReportMissingRow[]) {
  const map = new Map<number, string[]>();
  for (const row of missing) {
    const names = map.get(row.academic_year) ?? [];
    names.push(row.name_th);
    map.set(row.academic_year, names);
  }
  return [...map.entries()]
    .map(([academic_year, names]) => ({ academic_year, names }))
    .sort((a, b) => b.academic_year - a.academic_year);
}
