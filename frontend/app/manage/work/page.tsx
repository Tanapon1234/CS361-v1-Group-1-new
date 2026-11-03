import type { Metadata } from 'next';
import Link from 'next/link';

import { createPublication } from '@/app/manage/actions/academic';
import { createEntry, createSubmission, withdrawSubmission } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { EntryFields } from '@/components/manage/entry-fields';
import { PublicationFields } from '@/components/manage/publication-fields';
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
  getRound,
  listLecturers,
  listRounds,
  listRubricCategories,
  listRubricVersions,
  getRubricForm,
  listMyPublications,
  listSubmissions,
  settle,
} from '@/lib/backend/api';
import { isLecturerOnly } from '@/lib/auth/permissions';
import { getCurrentUser } from '@/lib/backend/client';
import { EDITABLE_STATUSES, VERIFICATION_LABEL, formatNumber, formatScore } from '@/lib/backend/labels';
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
  const me = await getCurrentUser();
  // A plain lecturer sees their own work only, so there is no lecturer to pick
  const own = isLecturerOnly(me) && me ? me.lecturer.lecturer_id : null;
  const lecturerId = own ?? (UUID.test(param(params.lecturer) ?? '') ? param(params.lecturer) : undefined);
  const yearFrom = intParam(params.year_from);
  const yearTo = intParam(params.year_to);
  const category = param(params.category) || undefined;
  const addRoundId = intParam(params.add_round);

  const mySheets = own ? (await listSubmissions({ lecturer_id: own })).items : [];
  const addRound = own && addRoundId ? await getRound(addRoundId) : null;
  const addSheet = addRound ? mySheets.find((item) => item.round_id === addRound.id) ?? null : null;
  const addEditable = !!addSheet && EDITABLE_STATUSES.includes(addSheet.status);
  // The rubric of that round's version, to pick the item and show which fields it needs
  const addForm = addRound && addEditable ? await getRubricForm(addRound.rubric_version_id) : null;
  const myPublications = own && addForm ? (await listMyPublications(own, { limit: MAX_PAGE })).items : [];
  const [lecturers, rounds, categories, work] = await Promise.all([
    own ? Promise.resolve(null) : listLecturers({ limit: MAX_PAGE }),
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
        title={own ? 'ผลงานรายปีของฉัน' : 'ผลงานรายปี'}
        description={
          own
            ? 'ภาระงานและผลงานตีพิมพ์ของคุณ เลือกช่วงปีการศึกษาและหมวดงานได้'
            : 'ดูภาระงานและผลงานตีพิมพ์ของอาจารย์ทีละคน เลือกช่วงปีการศึกษาและหมวดงานได้'
        }
      />

      <Section title="ค้นหา">
        <form
          className={`grid gap-3 sm:items-end ${
            own ? 'sm:grid-cols-[1fr_1fr_1.5fr_auto]' : 'sm:grid-cols-[2fr_1fr_1fr_1.5fr_auto]'
          }`}
        >
          {own ? null : (
            <Field label="อาจารย์">
              <select name="lecturer" defaultValue={lecturerId ?? ''} required className={inputClass}>
                <option value="" disabled>
                  เลือกอาจารย์
                </option>
                {lecturers?.items.map((lecturer) => (
                  <option key={lecturer.lecturer_id} value={lecturer.lecturer_id}>
                    {lecturer.name_th}
                  </option>
                ))}
              </select>
            </Field>
          )}
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

      {own ? (
        <Section title="เพิ่มผลงานของฉัน" description="เลือกว่าจะเพิ่มผลงานตีพิมพ์ หรือเพิ่มงานในใบภาระงานของรอบนั้น">
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="text-sm font-bold text-ink">ผลงานตีพิมพ์ (บทความ / งานวิจัย)</h3>
              <details className="mt-2 rounded-lg border border-line p-3">
                <summary className="cursor-pointer text-sm font-semibold text-brand">เพิ่มผลงานตีพิมพ์ใหม่</summary>
                <ActionForm action={createPublication} submitLabel="เพิ่มผลงาน" className="mt-3">
                  <PublicationFields />
                  <input type="hidden" name="lecturer_ids" value={own} />
                </ActionForm>
              </details>
            </div>
            <div>
              <h3 className="text-sm font-bold text-ink">งานที่ทำในรอบนี้ (สอน / วิจัย / บริการ ฯลฯ)</h3>
              <p className="mt-1 text-xs text-ink-muted">
                กรอกแล้วเข้าใบภาระงานของรอบนั้นทันที ระบบคำนวณคะแนนให้เอง
              </p>
              <form method="get" action="/manage/work" className="mt-2 flex flex-wrap items-end gap-2">
                <Field label="เลือกรอบ" className="min-w-52 flex-1">
                  <select name="add_round" defaultValue={addRoundId ?? ''} required className={inputClass}>
                    <option value="" disabled>
                      เลือกรอบ
                    </option>
                    {rounds.items.map((round) => (
                      <option key={round.id} value={round.id}>
                        {round.name_th}
                        {round.is_open ? ' (เปิด)' : ''}
                      </option>
                    ))}
                  </select>
                </Field>
                <button type="submit" className={secondaryButtonClass}>
                  เลือก
                </button>
              </form>
            </div>
          </div>

          {addRound ? (
            <div className="mt-6 border-t border-line pt-5">
              <h3 className="text-sm font-bold text-ink">กรอกงานในใบภาระงาน {addRound.name_th}</h3>
              {addSheet && addForm ? (
                <>
                  <p className="mt-1 mb-3 text-xs text-ink-muted">
                    ใบของคุณเป็น <StatusBadge status={addSheet.status} /> ·{' '}
                    <Link href={`/manage/submissions/${addSheet.id}`} className={linkClass}>
                      เปิดดูทั้งใบ
                    </Link>
                  </p>
                  <ActionForm
                    action={createEntry.bind(null, addSheet.id)}
                    submitLabel="เพิ่มเข้าใบภาระงาน"
                    resetOnSuccess
                  >
                    <EntryFields form={addForm} publications={myPublications} />
                  </ActionForm>
                </>
              ) : addSheet && addSheet.status === 'submitted' ? (
                <div className="space-y-3">
                  <Notice>
                    ใบของคุณในรอบนี้ส่งแล้ว และยังไม่มีใครรับเรื่อง ถ้าอยากเพิ่มหรือแก้รายการ ถอนใบกลับมาแก้ได้
                    แล้วส่งใหม่เมื่อเสร็จ
                  </Notice>
                  <ActionForm
                    inline
                    variant="secondary"
                    submitLabel="ถอนใบกลับมาแก้ไข"
                    confirmText="ถอนใบกลับมาแก้ไข? ต้องส่งใหม่อีกครั้งหลังแก้เสร็จ"
                    action={withdrawSubmission.bind(null, addSheet.id)}
                  />
                </div>
              ) : addSheet ? (
                <Notice>
                  ใบของคุณในรอบนี้อยู่ระหว่างตรวจสอบหรืออนุมัติแล้ว แก้รายการไม่ได้ ถ้าต้องแก้
                  ให้เจ้าหน้าที่หรือผู้อนุมัติตีกลับใบก่อน
                </Notice>
              ) : addRound.is_open ? (
                <ActionForm action={createSubmission} submitLabel="สร้างใบภาระงานของฉันในรอบนี้">
                  <input type="hidden" name="round_id" value={addRound.id} />
                  <p className="mb-2 text-sm text-ink-muted">
                    ยังไม่มีใบของคุณในรอบนี้ สร้างใบก่อน แล้วจะกรอกงานได้
                  </p>
                </ActionForm>
              ) : (
                <Notice>รอบนี้ปิดแล้วและคุณไม่มีใบ จึงกรอกงานเพิ่มไม่ได้</Notice>
              )}
            </div>
          ) : null}
        </Section>
      ) : null}

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
