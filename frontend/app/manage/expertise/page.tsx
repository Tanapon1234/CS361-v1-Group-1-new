import type { Metadata } from 'next';

import { createExpertise, deleteExpertise, updateExpertise } from '@/app/manage/actions/academic';
import { ActionForm } from '@/components/manage/action-form';
import {
  EmptyNote,
  Field,
  Notice,
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
import { PAGE_SIZE, listExpertise, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'ความเชี่ยวชาญ' };

export default async function ExpertisePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const q = param(params.q);
  const offset = intParam(params.offset) ?? 0;
  const [expertise, me] = await Promise.all([
    settle(listExpertise({ q, limit: PAGE_SIZE, offset })),
    getCurrentUser(),
  ]);
  // Anyone adds an item; editing / deleting the shared list is for staff
  const manage = canManage(me);

  return (
    <div className="space-y-6">
      <PageHeader title="ความเชี่ยวชาญ" description="รายการกลางที่อาจารย์ทุกคนเลือกใช้ร่วมกัน" />

      <Section title="เพิ่มความเชี่ยวชาญ">
        <ActionForm action={createExpertise} submitLabel="เพิ่ม" resetOnSuccess className="flex flex-wrap items-end gap-3">
          <Field label="คำอธิบาย" className="min-w-60 flex-1">
            <input name="description" required placeholder="Cloud Computing" className={inputClass} />
          </Field>
        </ActionForm>
      </Section>

      <Section title="ทั้งหมด">
        {expertise.error ? (
          <Notice tone="error">{expertise.error}</Notice>
        ) : (
          <>
              <form role="search" className="mb-4 flex gap-2">
                <input name="q" defaultValue={q} placeholder="ค้นหา" className={inputClass} />
                <button type="submit" className={secondaryButtonClass}>ค้นหา</button>
              </form>
              {expertise.data?.items.length === 0 ? (
                <EmptyNote>ไม่พบรายการ</EmptyNote>
              ) : (
                <ul className="divide-y divide-line-soft">
                  {expertise.data?.items.map((item) => (
                    <li key={item.expertise_id} className="flex flex-wrap items-start gap-2 py-3">
                      {manage ? (
                        <>
                        <ActionForm
                          action={updateExpertise.bind(null, item.expertise_id)}
                          variant="secondary"
                          className="flex flex-1 flex-wrap items-center gap-2"
                        >
                          <input name="description" required defaultValue={item.description} className={`${inputClass} min-w-60 flex-1`} aria-label="คำอธิบาย" />
                        </ActionForm>
                        <ActionForm
                          inline
                          variant="danger"
                          submitLabel="ลบ"
                          confirmText={`ลบ "${item.description}"?`}
                          action={deleteExpertise.bind(null, item.expertise_id)}
                        />
                      </>
                    ) : (
                      <span className="py-2 text-sm text-ink">{item.description}</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
            <Pager
              total={expertise.data?.meta.total ?? 0}
              limit={PAGE_SIZE}
              offset={offset}
              hrefFor={(next) => withQuery('/manage/expertise', { q, offset: next })}
            />
          </>
        )}
      </Section>
    </div>
  );
}
