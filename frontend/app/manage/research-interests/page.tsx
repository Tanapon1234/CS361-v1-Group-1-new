import type { Metadata } from 'next';

import {
  createResearchInterest,
  deleteResearchInterest,
  renameResearchInterest,
} from '@/app/manage/actions/academic';
import { ActionForm } from '@/components/manage/action-form';
import {
  EmptyNote,
  Field,
  PageHeader,
  Pager,
  Section,
  inputClass,
  intParam,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { canManage } from '@/lib/auth/permissions';
import { PAGE_SIZE, listResearchInterests } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'หัวข้อวิจัย' };

export default async function ResearchInterestsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const q = param(params.q);
  const offset = intParam(params.offset) ?? 0;
  const [interests, me] = await Promise.all([
    listResearchInterests({ q, limit: PAGE_SIZE, offset }),
    getCurrentUser(),
  ]);
  // Anyone adds a topic; renaming / deleting the shared list is for staff
  const manage = canManage(me);

  return (
    <div className="space-y-6">
      <PageHeader title="หัวข้อวิจัย" description="รายการกลางที่อาจารย์ทุกคนเลือกใช้ร่วมกัน (ลบแล้วจะหลุดจากอาจารย์ทุกคน)" />

      <Section title="เพิ่มหัวข้อวิจัย">
        <ActionForm action={createResearchInterest} submitLabel="เพิ่ม" resetOnSuccess className="flex flex-wrap items-end gap-3">
          <Field label="ชื่อหัวข้อ" className="min-w-60 flex-1">
            <input name="name" required maxLength={255} placeholder="Machine Learning" className={inputClass} />
          </Field>
        </ActionForm>
      </Section>

      <Section title={`ทั้งหมด (${interests.meta.total})`}>
        <form role="search" className="mb-4 flex gap-2">
          <input name="q" defaultValue={q} placeholder="ค้นหา" className={inputClass} />
          <button type="submit" className={secondaryButtonClass}>ค้นหา</button>
        </form>
        {interests.items.length === 0 ? (
          <EmptyNote>ไม่พบหัวข้อวิจัย</EmptyNote>
        ) : (
          <ul className="divide-y divide-line-soft">
            {interests.items.map((interest) => (
              <li key={interest.research_interest_id} className="flex flex-wrap items-start gap-2 py-3">
                {manage ? (
                  <>
                    <ActionForm
                      action={renameResearchInterest.bind(null, interest.research_interest_id)}
                      variant="secondary"
                      className="flex flex-1 flex-wrap items-center gap-2"
                    >
                      <input name="name" required maxLength={255} defaultValue={interest.name} className={`${inputClass} min-w-60 flex-1`} aria-label="ชื่อหัวข้อ" />
                    </ActionForm>
                    <ActionForm
                      inline
                      variant="danger"
                      submitLabel="ลบ"
                      confirmText={`ลบ "${interest.name}"? อาจารย์ที่เลือกหัวข้อนี้จะหลุดด้วย`}
                      action={deleteResearchInterest.bind(null, interest.research_interest_id)}
                    />
                  </>
                ) : (
                  <span className="py-2 text-sm text-ink">{interest.name}</span>
                )}
              </li>
            ))}
          </ul>
        )}
        <Pager
          total={interests.meta.total}
          limit={PAGE_SIZE}
          offset={offset}
          hrefFor={(next) => withQuery('/manage/research-interests', { q, offset: next })}
        />
      </Section>
    </div>
  );
}
