import type { Metadata } from 'next';
import Link from 'next/link';

import {
  EmptyNote,
  Field,
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
} from '@/components/manage/ui';
import {
  MAX_PAGE,
  getLecturerWork,
  listLecturers,
  listRounds,
  listRubricCategories,
  listRubricVersions,
} from '@/lib/backend/api';
import { formatNumber, formatScore } from '@/lib/backend/labels';
import type { LecturerWork, RubricCategory } from '@/types/backend';

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
  const year = intParam(params.year);
  const category = param(params.category) || undefined;

  const [lecturers, rounds, categories, work] = await Promise.all([
    listLecturers({ limit: MAX_PAGE }),
    listRounds(),
    categoryOptions(),
    lecturerId ? getLecturerWork(lecturerId, { academic_year: year, category }) : null,
  ]);

  const years = [
    ...new Set([...rounds.items.map((round) => round.academic_year), ...(work?.available_years ?? [])]),
  ].sort((a, b) => b - a);

  return (
    <div className="space-y-6">
      <PageHeader
        title="ผลงานรายปี"
        description="ดูภาระงานและผลงานตีพิมพ์ของอาจารย์ทีละคน เลือกปีการศึกษาและหมวดงานได้"
      />

      <Section title="ค้นหา">
        <form className="grid gap-3 sm:grid-cols-[2fr_1fr_1.5fr_auto] sm:items-end">
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
          <Field label="ปีการศึกษา">
            <select name="year" defaultValue={year ?? ''} className={inputClass}>
              <option value="">ทุกปี</option>
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

      {work ? <WorkResult work={work} /> : <EmptyNote>เลือกอาจารย์ก่อน แล้วกดค้นหา</EmptyNote>}
    </div>
  );
}

function WorkResult({ work }: { work: LecturerWork }) {
  if (work.total === 0) return <EmptyNote>ไม่พบผลงาน</EmptyNote>;

  return (
    <>
      {work.categories.map((group) => (
        <Section key={group.code} title={`${group.code}. ${group.name_th}`} description={`${group.entries.length} รายการ`}>
          <Table head={['ข้อ', 'รายการ', 'รอบ', 'จำนวน', 'คะแนน', 'สถานะใบ']}>
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
                <Td>
                  <StatusBadge status={entry.submission_status} />
                </Td>
              </tr>
            ))}
          </Table>
        </Section>
      ))}

      {work.publications.length > 0 ? (
        <Section title="ผลงานตีพิมพ์" description="จากข้อมูลวิชาการของอาจารย์ นับตามปีที่ตีพิมพ์">
          <Table head={['ชื่อผลงาน', 'ปี', 'แหล่งตีพิมพ์', 'ผู้แต่งลำดับที่']}>
            {work.publications.map((publication) => (
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
              </tr>
            ))}
          </Table>
        </Section>
      ) : null}
    </>
  );
}
