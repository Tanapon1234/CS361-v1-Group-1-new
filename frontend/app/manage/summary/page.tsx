import type { Metadata } from 'next';
import Link from 'next/link';

import { CategoryBars, CategoryLegend, YearStackedChart } from '@/components/manage/work-charts';
import { EmptyNote, Notice, PageHeader, Section, StatusBadge, intParam, linkClass } from '@/components/manage/ui';
import { getLecturerWork } from '@/lib/backend/api';
import { currentLecturerId } from '@/lib/backend/client';
import { VERIFICATION_LABEL, formatNumber, formatScore } from '@/lib/backend/labels';
import { categoryColor, summarizeWork } from '@/lib/work-summary';

export const metadata: Metadata = { title: 'สรุปผลงานของฉัน' };

export default async function WorkSummaryPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const lecturerId = await currentLecturerId();
  if (!lecturerId) {
    return (
      <div className="space-y-6">
        <PageHeader title="สรุปผลงานของฉัน" />
        <Notice>
          ต้อง <Link href="/manage/switch-user" className={linkClass}>เลือกผู้ใช้งาน</Link> ก่อน
        </Notice>
      </div>
    );
  }

  const summary = summarizeWork(await getLecturerWork(lecturerId, {}));
  const newestFirst = [...summary.years].reverse();
  const picked = intParam((await searchParams).year);
  const year = summary.years.find((y) => y.year === picked) ?? newestFirst[0];

  return (
    <div className="space-y-8">
      <PageHeader
        title="สรุปผลงานของฉัน"
        description="คะแนนภาระงานของคุณรายปีการศึกษาและรายหมวด นับเฉพาะใบที่ส่งแล้ว ใบที่ยังเป็นร่างหรือถูกตีกลับยังไม่นับ"
      />

      {!year ? (
        <EmptyNote>ยังไม่มีใบภาระงานที่ส่งแล้ว ส่งใบภาระงานแล้วสรุปจะแสดงที่นี่</EmptyNote>
      ) : (
        <>
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ['ปีการศึกษา', String(year.year)],
              ['คะแนนรวม', formatScore(year.total)],
              ['จำนวนรายการ', formatNumber(year.entryCount)],
              ['ผลงานตีพิมพ์', formatNumber(year.publications.length)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-line bg-surface px-4 py-3">
                <dt className="text-[13px] text-ink-muted">{label}</dt>
                <dd className="mt-0.5 text-2xl font-bold text-ink">{value}</dd>
              </div>
            ))}
          </dl>

          <Section title="คะแนนรายปี" description="แต่ละแท่งคือคะแนนรวมของปี แบ่งสีตามหมวด กดปีเพื่อดูรายละเอียด">
            <div className="space-y-4 rounded-2xl border border-line bg-surface p-5">
              <YearStackedChart summary={summary} selected={year.year} />
              <CategoryLegend summary={summary} years={summary.years} />
              <nav aria-label="เลือกปีการศึกษา" className="flex flex-wrap gap-2 border-t border-line-soft pt-4">
                {newestFirst.map((y) => (
                  <Link
                    key={y.year}
                    href={`/manage/summary?year=${y.year}`}
                    aria-current={y.year === year.year ? 'page' : undefined}
                    className={`inline-flex min-h-11 items-center rounded-lg border px-3.5 text-sm font-medium ${
                      y.year === year.year ? 'border-brand bg-brand text-white' : 'border-line bg-surface text-ink hover:bg-surface-alt'
                    }`}
                  >
                    {y.year}
                  </Link>
                ))}
              </nav>
            </div>
          </Section>

          <Section title={`สัดส่วนแต่ละด้าน ปี ${year.year}`}>
            {year.categories.length === 0 ? (
              <EmptyNote>ปีนี้ยังไม่มีรายการภาระงานที่ส่งแล้ว</EmptyNote>
            ) : (
              <div className="rounded-2xl border border-line bg-surface p-5">
                <CategoryBars summary={summary} year={year} />
              </div>
            )}
          </Section>

          {year.categories.length > 0 ? (
            <Section title="รายการในแต่ละหมวด" description="กดชื่อหมวดเพื่อดูรายการ">
              <div className="space-y-3">
                {year.categories.map((category) => (
                  <details key={category.code} className="group rounded-xl border border-line bg-surface">
                    <summary className="flex min-h-11 cursor-pointer items-center justify-between gap-3 px-4 py-3">
                      <span className="flex items-center gap-2 font-semibold text-ink">
                        <span
                          aria-hidden
                          className="h-3 w-3 rounded-sm"
                          style={{ background: categoryColor(category.code, summary.categories) }}
                        />
                        {category.name}
                      </span>
                      <span className="text-sm text-ink-muted">
                        {category.entries.length} รายการ · {formatScore(category.score)}
                      </span>
                    </summary>
                    <ul className="divide-y divide-line-soft border-t border-line-soft">
                      {category.entries.map((entry) => (
                        <li key={entry.entry_id} className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1 px-4 py-3 text-sm">
                          <div className="min-w-0">
                            <p className="font-medium text-ink">{entry.title || entry.item_label_th}</p>
                            <p className="text-[13px] text-ink-muted">
                              {entry.title ? `${entry.item_label_th} · ` : ''}
                              {entry.round_name_th}
                            </p>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="font-semibold text-ink">{formatScore(entry.score)}</span>
                            <StatusBadge status={entry.submission_status} />
                            <Link href={`/manage/submissions/${entry.submission_id}`} className={linkClass}>
                              เปิดใบ
                            </Link>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </details>
                ))}
              </div>
            </Section>
          ) : null}

          {year.publications.length > 0 ? (
            <Section title={`ผลงานตีพิมพ์ ปี ${year.year}`}>
              <ul className="divide-y divide-line-soft rounded-xl border border-line bg-surface">
                {year.publications.map((publication) => (
                  <li key={publication.publication_id} className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1 px-4 py-3 text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-ink">{publication.title}</p>
                      {publication.venue ? <p className="text-[13px] text-ink-muted">{publication.venue}</p> : null}
                    </div>
                    <span className="text-[13px] text-ink-muted">{VERIFICATION_LABEL[publication.verification_status]}</span>
                  </li>
                ))}
              </ul>
            </Section>
          ) : null}
        </>
      )}
    </div>
  );
}
