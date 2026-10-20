import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import {
  createCategory,
  createItem,
  createSection,
  deleteItem,
  deleteSection,
  setItemActive,
  updateItem,
  updateRubricVersion,
  updateSection,
} from '@/app/manage/actions/rubric';
import { ActionForm } from '@/components/manage/action-form';
import { RubricItemFields } from '@/components/manage/rubric-item-fields';
import {
  Badge,
  Checkbox,
  EmptyNote,
  Field,
  Notice,
  PageHeader,
  Section,
  inputClass,
} from '@/components/manage/ui';
import { getRubricForm, listRounds } from '@/lib/backend/api';
import {
  POSITION_LABEL,
  UNIT_LABEL,
  formatNumber,
} from '@/lib/backend/labels';
import type { RubricFormSection, RubricItem, RubricSection } from '@/types/backend';

export const metadata: Metadata = { title: 'แก้ไขเกณฑ์' };

function flatten(sections: RubricFormSection[]): RubricFormSection[] {
  return sections.flatMap((section) => [section, ...flatten(section.children)]);
}

function itemSummary(item: RubricItem): string {
  const weight =
    item.weight_mode === 'fixed'
      ? `น้ำหนัก ${formatNumber(item.weight)}`
      : `${item.assessor_position ? POSITION_LABEL[item.assessor_position] : ''} ให้ค่า ${formatNumber(item.weight_min)}–${formatNumber(item.weight_max)}${item.range_basis === 'points' ? ' คะแนน' : ''}`;
  const divisor = item.unit_divisor !== 1 ? ` ÷ ${formatNumber(item.unit_divisor)}` : '';
  const tier =
    item.tier_min !== null || item.tier_max !== null
      ? ` · นศ. ${item.tier_min ?? 0}–${item.tier_max ?? '∞'}`
      : '';
  return `${weight} · ต่อ${UNIT_LABEL[item.unit]}${divisor}${tier}`;
}

function SectionFields({
  section,
  parents,
}: {
  section?: RubricSection;
  parents: RubricSection[];
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-6">
      <Field label="รหัสข้อ *">
        <input name="code" required maxLength={10} defaultValue={section?.code} placeholder="2.3.1" className={inputClass} />
      </Field>
      <Field label="ชื่อข้อ *" className="sm:col-span-2">
        <input name="name_th" required maxLength={255} defaultValue={section?.name_th} className={inputClass} />
      </Field>
      <Field label="อยู่ใต้ข้อ">
        <select name="parent_id" defaultValue={section?.parent_id ?? ''} className={inputClass}>
          <option value="">— ระดับบนสุด —</option>
          {parents
            .filter((parent) => parent.id !== section?.id)
            .map((parent) => (
              <option key={parent.id} value={parent.id}>
                {parent.code} {parent.name_th}
              </option>
            ))}
        </select>
      </Field>
      <Field label="เพดานคะแนน">
        <input name="cap" type="number" step="0.01" min={0} defaultValue={section?.cap ?? ''} className={inputClass} />
      </Field>
      <Field label="แถวสูงสุด">
        <input name="max_entries" type="number" min={1} defaultValue={section?.max_entries ?? ''} className={inputClass} />
      </Field>
      <Field label="ลำดับ">
        <input name="sort_order" type="number" min={0} defaultValue={section?.sort_order ?? 0} className={inputClass} />
      </Field>
    </div>
  );
}

function SectionBlock({
  section,
  parents,
  locked,
}: {
  section: RubricFormSection;
  parents: RubricSection[];
  locked: boolean;
}) {
  return (
    <div className="rounded-lg border border-line p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="font-semibold text-ink">
          {section.code} {section.name_th}
        </h4>
        <span className="flex flex-wrap gap-1">
          {section.cap !== null ? <Badge>เพดาน {formatNumber(section.cap)}</Badge> : null}
          {section.max_entries !== null ? <Badge>ไม่เกิน {section.max_entries} แถว</Badge> : null}
        </span>
      </div>

      {section.items.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {section.items.map((item) => (
            <li key={item.id} className="rounded-lg bg-surface-alt px-3 py-2">
              <details>
                <summary className="flex cursor-pointer flex-wrap items-center justify-between gap-2 text-sm">
                  <span>
                    <span className={item.is_active ? 'font-medium text-ink' : 'text-ink-muted line-through'}>
                      {item.label_th}
                    </span>
                    <span className="ml-2 text-xs text-ink-muted">{itemSummary(item)}</span>
                  </span>
                  <span className="text-xs text-brand">{locked ? 'ดูรายละเอียด' : 'แก้ไข'}</span>
                </summary>
                <div className="mt-3 space-y-3">
                  {locked ? (
                    <ActionForm
                      inline
                      variant="secondary"
                      submitLabel={item.is_active ? 'ปิดใช้ตัวเลือกนี้' : 'เปิดใช้ตัวเลือกนี้'}
                      action={setItemActive.bind(null, item.id, !item.is_active)}
                    />
                  ) : (
                    <>
                      <ActionForm action={updateItem.bind(null, item.id)} variant="secondary">
                        <RubricItemFields item={item} />
                      </ActionForm>
                      <ActionForm
                        inline
                        variant="danger"
                        submitLabel="ลบตัวเลือก"
                        confirmText="ลบตัวเลือกนี้?"
                        action={deleteItem.bind(null, item.id)}
                      />
                    </>
                  )}
                </div>
              </details>
            </li>
          ))}
        </ul>
      ) : null}

      {section.children.length > 0 ? (
        <div className="mt-3 space-y-3 border-l-2 border-line-soft pl-4">
          {section.children.map((child) => (
            <SectionBlock key={child.id} section={child} parents={parents} locked={locked} />
          ))}
        </div>
      ) : null}

      {!locked ? (
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <details className="w-full">
            <summary className="cursor-pointer font-semibold text-brand">+ เพิ่มตัวเลือกในข้อ {section.code}</summary>
            <div className="mt-3">
              <ActionForm action={createItem.bind(null, section.id)} submitLabel="เพิ่มตัวเลือก" resetOnSuccess>
                <RubricItemFields />
              </ActionForm>
            </div>
          </details>
          <details className="w-full">
            <summary className="cursor-pointer font-medium text-ink-muted">แก้ไข / ลบข้อ {section.code}</summary>
            <div className="mt-3 space-y-3">
              <ActionForm action={updateSection.bind(null, section.id)} variant="secondary">
                <SectionFields section={section} parents={parents} />
              </ActionForm>
              <ActionForm
                inline
                variant="danger"
                submitLabel="ลบข้อนี้"
                confirmText="ลบข้อนี้? (ต้องไม่มีตัวเลือกและข้อย่อยเหลืออยู่)"
                action={deleteSection.bind(null, section.id)}
              />
            </div>
          </details>
        </div>
      ) : null}
    </div>
  );
}

export default async function RubricPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const versionId = Number.parseInt(id, 10);
  const [form, rounds] = await Promise.all([
    Number.isFinite(versionId) ? getRubricForm(versionId) : Promise.resolve(null),
    listRounds(),
  ]);
  if (!form) notFound();
  const usedBy = rounds.items.filter((round) => round.rubric_version_id === form.id);
  const locked = usedBy.length > 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`เกณฑ์ฉบับ ${form.code}`}
        back={{ href: '/manage/rubrics', label: 'เกณฑ์ภาระงาน' }}
        actions={locked ? <Badge className="border-amber-200 bg-amber-50 text-amber-800">ล็อก</Badge> : null}
      />

      {locked ? (
        <Notice>
          ฉบับนี้ถูกใช้ในรอบ {usedBy.map((round) => round.name_th).join(', ')} จึงแก้โครงไม่ได้แล้ว
          (ทำได้แค่เปิด/ปิดตัวเลือก) ถ้าต้องแก้ ให้สร้างฉบับใหม่โดยคัดลอกจากฉบับนี้
        </Notice>
      ) : null}

      <Section title="ค่าของฉบับ">
        <fieldset disabled={locked} className="space-y-4">
          <ActionForm action={updateRubricVersion.bind(null, form.id)}>
            <div className="grid gap-4 sm:grid-cols-4">
              <Field label="รหัสฉบับ">
                <input name="code" required maxLength={30} defaultValue={form.code} className={inputClass} />
              </Field>
              <Field label="อนุมัติในการประชุม">
                <input name="approved_meeting" maxLength={50} defaultValue={form.approved_meeting ?? ''} className={inputClass} />
              </Field>
              <Field label="วันที่อนุมัติ">
                <input name="approved_on" type="date" defaultValue={form.approved_on ?? ''} className={inputClass} />
              </Field>
              <div className="flex items-end pb-2">
                <Checkbox name="is_active" label="ใช้งานอยู่" defaultChecked={form.is_active} />
              </div>
              <Field label="คะแนนฐาน">
                <input name="base_points" type="number" step="0.01" defaultValue={form.base_points} className={inputClass} />
              </Field>
              <Field label="เพดานรวม">
                <input name="overall_cap" type="number" step="0.01" defaultValue={form.overall_cap} className={inputClass} />
              </Field>
              <Field label="คะแนนขั้นต่ำ">
                <input name="min_required" type="number" step="0.01" defaultValue={form.min_required} className={inputClass} />
              </Field>
              <Field label="หน่วยกิตสอนขั้นต่ำ">
                <input name="min_teaching_credits" type="number" step="0.01" defaultValue={form.min_teaching_credits} className={inputClass} />
              </Field>
            </div>
          </ActionForm>
        </fieldset>
      </Section>

      {form.categories.length === 0 ? <EmptyNote>ยังไม่มีหมวด เริ่มจากเพิ่มหมวดด้านล่าง</EmptyNote> : null}

      {form.categories.map((category) => {
        const parents = flatten(category.sections);
        return (
          <Section
            key={category.id}
            title={`หมวด ${category.code} ${category.name_th}`}
            description={`เพดานหมวด ${formatNumber(category.cap)} คะแนน`}
          >
            <div className="space-y-3">
              {category.sections.length === 0 ? <EmptyNote>ยังไม่มีข้อในหมวดนี้</EmptyNote> : null}
              {category.sections.map((section) => (
                <SectionBlock key={section.id} section={section} parents={parents} locked={locked} />
              ))}
            </div>
            {!locked ? (
              <details className="mt-4 border-t border-line-soft pt-4 text-sm">
                <summary className="cursor-pointer font-semibold text-brand">+ เพิ่มข้อในหมวด {category.code}</summary>
                <div className="mt-3">
                  <ActionForm action={createSection.bind(null, category.id)} submitLabel="เพิ่มข้อ" resetOnSuccess>
                    <SectionFields parents={parents} />
                  </ActionForm>
                </div>
              </details>
            ) : null}
          </Section>
        );
      })}

      {!locked ? (
        <Section title="เพิ่มหมวด">
          <ActionForm action={createCategory.bind(null, form.id)} submitLabel="เพิ่มหมวด" resetOnSuccess className="flex flex-wrap items-end gap-3">
            <Field label="รหัส" className="w-24">
              <input name="code" required maxLength={5} placeholder="1" className={inputClass} />
            </Field>
            <Field label="ชื่อหมวด" className="min-w-56 flex-1">
              <input name="name_th" required maxLength={100} placeholder="งานสอน" className={inputClass} />
            </Field>
            <Field label="เพดาน" className="w-32">
              <input name="cap" type="number" step="0.01" min={0} required placeholder="900" className={inputClass} />
            </Field>
            <Field label="ลำดับ" className="w-24">
              <input name="sort_order" type="number" min={0} defaultValue={(form.categories.length + 1) * 10} className={inputClass} />
            </Field>
          </ActionForm>
        </Section>
      ) : null}
    </div>
  );
}
