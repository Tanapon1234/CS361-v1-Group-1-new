import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { itemSummary } from '@/components/manage/rubric-summary';
import { Badge, EmptyNote, PageHeader, Section, Stat, linkClass } from '@/components/manage/ui';
import { isAdmin, isLecturerOnly } from '@/lib/auth/permissions';
import { getRound, getRubricForm } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDate, formatNumber } from '@/lib/backend/labels';
import type { RubricFormSection } from '@/types/backend';

export const metadata: Metadata = { title: 'เกณฑ์ของรอบ' };

function SectionView({ section }: { section: RubricFormSection }) {
  const items = section.items.filter((item) => item.is_active);
  return (
    <div className="rounded-lg border border-line-soft p-3">
      <div className="flex flex-wrap items-baseline gap-2">
        <p className="font-semibold text-ink">
          {section.code} {section.name_th}
        </p>
        {section.cap !== null ? <Badge>เพดาน {formatNumber(section.cap)}</Badge> : null}
        {section.max_entries !== null ? <Badge>ไม่เกิน {section.max_entries} แถว</Badge> : null}
      </div>
      {items.length > 0 ? (
        <ul className="mt-2 space-y-1.5">
          {items.map((item) => (
            <li key={item.id} className="rounded-lg bg-surface-alt px-3 py-2">
              <p className="font-medium text-ink">{item.label_th}</p>
              <p className="text-[13px] text-ink-muted">{itemSummary(item)}</p>
            </li>
          ))}
        </ul>
      ) : null}
      {section.children.length > 0 ? (
        <div className="mt-3 space-y-3 border-l-2 border-line-soft pl-3">
          {section.children.map((child) => (
            <SectionView key={child.id} section={child} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** Read-only criteria of the rubric version a round uses; open to every signed-in user */
export default async function RoundCriteriaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const roundId = Number.parseInt(id, 10);
  const round = Number.isFinite(roundId) ? await getRound(roundId) : null;
  if (!round) notFound();
  const [form, me] = await Promise.all([getRubricForm(round.rubric_version_id), getCurrentUser()]);
  if (!form) notFound();

  return (
    <div className="space-y-6">
      <PageHeader
        title={`เกณฑ์ของ${round.name_th}`}
        description={`ฉบับ ${form.code}${form.approved_meeting ? ` · อนุมัติ ${form.approved_meeting}` : ''}${form.approved_on ? ` (${formatDate(form.approved_on)})` : ''}`}
        back={
          isLecturerOnly(me)
            ? { href: '/manage/submissions', label: 'ใบภาระงานของฉัน' }
            : { href: '/manage/rounds', label: 'รอบประเมิน' }
        }
      />

      <Section title="ค่ารวมของเกณฑ์">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="คะแนนฐาน" value={formatNumber(form.base_points)} />
          <Stat label="เพดานรวม" value={formatNumber(form.overall_cap)} />
          <Stat label="คะแนนขั้นต่ำ" value={formatNumber(form.min_required)} />
          <Stat label="หน่วยกิตสอนขั้นต่ำ" value={formatNumber(form.min_teaching_credits)} />
        </div>
      </Section>

      {form.categories.length === 0 ? <EmptyNote>เกณฑ์ฉบับนี้ยังไม่มีหมวด</EmptyNote> : null}
      {form.categories.map((category) => (
        <Section
          key={category.id}
          title={`หมวด ${category.code} ${category.name_th}`}
          description={`เพดานหมวด ${formatNumber(category.cap)} คะแนน`}
        >
          <div className="space-y-3">
            {category.sections.length === 0 ? <EmptyNote>ยังไม่มีข้อในหมวดนี้</EmptyNote> : null}
            {category.sections.map((section) => (
              <SectionView key={section.id} section={section} />
            ))}
          </div>
        </Section>
      ))}

      {isAdmin(me) ? (
        <p className="text-sm">
          <Link href={`/manage/rubrics/${form.id}`} className={linkClass}>
            แก้ไขเกณฑ์ฉบับนี้
          </Link>
        </p>
      ) : null}
    </div>
  );
}
