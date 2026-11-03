import type { Metadata } from 'next';
import Link from 'next/link';

import {
  EmptyNote,
  Field,
  Notice,
  PageHeader,
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
import {
  MAX_PAGE,
  getLecturerWork,
  listLecturers,
  listRounds,
  listRubricCategories,
  listRubricVersions,
  settle,
} from '@/lib/backend/api';
import { VERIFICATION_LABEL, formatNumber, formatScore } from '@/lib/backend/labels';
import type { LecturerWork, RubricCategory, WorkYearGroup } from '@/types/backend';

export const metadata: Metadata = { title: 'ผลงานรายปี' };

const UUID = /^[0-9a-f-]{36}$/i;

/** Category codes and names from the newest rubric version (codes stay the same across versions) */
async function categoryOptions(): Promise<RubricCategory[]> {
  const versions = await listRubricVersions();
  const newest = versions.items.reduce<number | null>(
    (id, version) => (id === null || version.id > id ? version.id : id),
    null
  );
  return newest === null ? [] : (await listRubricCategories(newest)).items;
}

export default async function LecturerWorkPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const lecturerId = UUID.test(param(params.lecturer) ?? '') ? param(params.lecturer) : undefined;
  const yearFrom = intParam(params.year_from);
  const yearTo = intParam(params.year_to);
  const category = param(params.category) || undefined;

  const [lecturers, rounds, categories, work] = await Promise.all([
    listLecturers({ limit: MAX_PAGE }),
    listRounds(),
    categoryOptions(),
    // A failed search must look different from an empty one, so it does not throw
    lecturerId
      ? settle(
          getLecturerWork(lecturerId, {
            academic_year_from: yearFrom,
            academic_year_to: yearTo,
            category,
          })
        )
      : null,
  ]);

  const years = [
    ...new Set([...rounds.items.map((round) => round.academic_year), ...(work?.data?.available_years ?? [])]),
  ].sort((a, b) => b - a);

  return (
    <div className="space-y-6">
      <PageHeader
        title="ผลงานรายปี"
        description="ดูภาระงานและผลงานตีพิมพ์ของอาจารย์ทีละคน เลือกช่วงปีการศึกษาและหมวดงานได้"
      />

      <Section title="ค้นหา">
        <form className="grid gap-3 sm:grid-cols-[2fr_1fr_1fr_1.5fr_auto] sm:items-end">
          <Field label="อาจารย์">
            <select name="lecturer" defaultValue={lecturerId ?? ''} required className={inputClass}>
              <option value="" disabled>
                เลือกอาจารย์
              </option>
              {lecturers.items.map((lecturer) => (
                <option key={lecturer.lecturer_id} value={lecturer.lecturer_id}>
                  {lecturer.name_th}
                </option>
              ))}
            </select>
          </Field>
          <Field label="ปีการศึกษา (จาก)">
            <select name="year_from" defaultValue={yearFrom ?? ''} className={inputClass}>
              <option value="">ไม่กำหนด</option>
              {years.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </Field>
          <Field label="ถึง">
            <select name="year_to" defaultValue={yearTo ?? ''} className={inputClass}>
              <option value="">ไม่กำหนด</option>
              {years.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </Field>
          <Field label="หมวดงาน">
            <select name="category" defaultValue={category ?? ''} className={inputClass}>
              <option value="">ทุกหมวด</option>
              {categories.map((option) => (
                <option key={option.id} value={option.code}>
                  {option.code}. {option.name_th}
                </option>
              ))}
            </select>
          </Field>
          <button type="submit" className={secondaryButtonClass}>
            ค้นหา
          </button>
        </form>
      </Section>

      {!work ? (
        <EmptyNote>เลือกอาจารย์ก่อน แล้วกดค้นหา</EmptyNote>
      ) : work.data ? (
        <WorkResult work={work.data} />
      ) : (
        <Notice tone="error">
          <p className="font-semibold">โหลดผลงานไม่สำเร็จ ผลนี้ไม่ได้แปลว่าไม่มีผลงาน</p>
          <p className="mt-1">{work.error}</p>
          <a
            href={withQuery('/manage/work', {
              lecturer: lecturerId,
              year_from: yearFrom,
              year_to: yearTo,
              category,
            })}
            className={`${linkClass} mt-2 inline-block`}
          >
            ลองอีกครั้ง
          </a>
        </Notice>
      )}
    </div>
  );
}

/** "งานวิชาการของ อ.ก ในปีการศึกษา 2566-2568": what was searched, in words */
function describe(work: LecturerWork): string {
  const what = work.filters.category_name_th ?? (work.filters.category ? `หมวด ${work.filters.category}` : 'ผลงาน');
  const { academic_year_from: from, academic_year_to: to } = work.filters;
  const when =
    from && to
      ? from === to
        ? `ในปีการศึกษา ${from}`
        : `ในปีการศึกษา ${from}-${to}`
      : from
        ? `ตั้งแต่ปีการศึกษา ${from}`
        : to
          ? `ถึงปีการศึกษา ${to}`
          : 'ในทุกปีการศึกษา';
  return `${what}ของ ${work.lecturer_name_th} ${when}`;
}

function WorkResult({ work }: { work: LecturerWork }) {
  if (work.total === 0) return <NoWork work={work} />;

  return (
    <>
      <p role="status" className="text-sm text-ink-muted">
        พบ{describe(work)} {work.total} รายการ
      </p>
      {work.years.map((year) => (
        <YearResult key={year.academic_year} year={year} />
      ))}
    </>
  );
}

function YearResult({ year }: { year: WorkYearGroup }) {
  return (
    <Section
      title={`ปีการศึกษา ${year.academic_year}`}
      description={`คะแนนรวม ${formatScore(year.total_score)}`}
    >
      <div className="space-y-4">
        {year.categories.map((group) => (
          <Section
            key={group.code}
            title={`${group.code}. ${group.name_th}`}
            description={`${group.entries.length} รายการ · คะแนนรวม ${formatScore(group.total_score)}`}
          >
            <Table head={['ข้อ', 'รายการ', 'รอบ', 'จำนวน', 'คะแนน', 'หลักฐาน', 'สถานะใบ']}>
              {group.entries.map((entry) => (
                <tr key={entry.entry_id}>
                  <Td className="whitespace-nowrap">
                    {entry.section_code} {entry.item_label_th}
                  </Td>
                  <Td className="text-ink">
                    {[entry.course_code, entry.title].filter(Boolean).join(' ') || '–'}
                  </Td>
                  <Td className="whitespace-nowrap">
                    <Link href={`/manage/submissions/${entry.submission_id}`} className={linkClass}>
                      {entry.round_name_th}
                    </Link>
                  </Td>
                  <Td>{formatNumber(entry.quantity)}</Td>
                  <Td>{formatScore(entry.score)}</Td>
                  <Td>{entry.evidence_count > 0 ? `${entry.evidence_count} ไฟล์` : '–'}</Td>
                  <Td>
                    <StatusBadge status={entry.submission_status} />
                  </Td>
                </tr>
              ))}
            </Table>
          </Section>
        ))}

        {year.publications.length > 0 ? (
          <Section title="ผลงานตีพิมพ์" description="จากข้อมูลวิชาการของอาจารย์ นับตามปีที่ตีพิมพ์">
            <Table head={['ชื่อผลงาน', 'ปี', 'แหล่งตีพิมพ์', 'ผู้แต่งลำดับที่', 'การรับรอง']}>
              {year.publications.map((publication) => (
                <tr key={publication.publication_id}>
                  <Td>
                    <Link href={`/manage/publications/${publication.publication_id}`} className={linkClass}>
                      {publication.title}
                    </Link>
                  </Td>
                  <Td className="whitespace-nowrap">
                    {publication.academic_year ?? '–'}
                    {publication.publication_year ? ` (${publication.publication_year})` : ''}
                  </Td>
                  <Td>{publication.venue ?? '–'}</Td>
                  <Td>{publication.author_order ?? '–'}</Td>
                  <Td>{VERIFICATION_LABEL[publication.verification_status]}</Td>
                </tr>
              ))}
            </Table>
          </Section>
        ) : null}
      </div>
    </Section>
  );
}

/** Empty result: say exactly what found nothing, and where this lecturer does have work */
function NoWork({ work }: { work: LecturerWork }) {
  const { academic_year_from: from, academic_year_to: to } = work.filters;
  const otherYears = work.available_years.filter(
    (year) => (from !== null && year < from) || (to !== null && year > to)
  );
  const hrefFor = (year: number) =>
    // Year links drop the category: those years have data in some category, not necessarily this one
    withQuery('/manage/work', { lecturer: work.lecturer_id, year_from: year, year_to: year });

  return (
    <div role="status" className="rounded-xl border border-dashed border-line bg-surface px-5 py-8 text-center">
      <p className="font-semibold text-ink">ไม่พบ{describe(work)}</p>
      {work.available_years.length === 0 ? (
        <p className="mt-2 text-sm text-ink-muted">อาจารย์คนนี้ยังไม่มีภาระงานหรือผลงานตีพิมพ์ในระบบเลย</p>
      ) : otherYears.length > 0 ? (
        <div className="mt-3 text-sm text-ink-muted">
          <p>ปีการศึกษาที่อาจารย์คนนี้มีข้อมูล (ทุกหมวด):</p>
          <ul className="mt-2 flex flex-wrap justify-center gap-2">
            {otherYears.map((year) => (
              <li key={year}>
                <Link href={hrefFor(year)} className={secondaryButtonClass}>
                  {year}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {work.filters.category ? (
        <p className="mt-3 text-sm">
          <Link
            href={withQuery('/manage/work', {
              lecturer: work.lecturer_id,
              year_from: from,
              year_to: to,
            })}
            className={linkClass}
          >
            ดูทุกหมวดของช่วงปีนี้
          </Link>
        </p>
      ) : null}
    </div>
  );
}
