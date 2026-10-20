'use client';

import { useMemo, useState } from 'react';

import { Field, inputClass } from '@/components/manage/ui';
import { POSITION_LABEL, UNIT_LABEL, formatNumber } from '@/lib/backend/labels';
import type { Entry, FieldSpec, RubricForm, RubricFormSection, RubricItem } from '@/types/backend';

/** Columns of submission_entry that a field_schema may name (checked on the column) */
const ENTRY_COLUMNS = new Set(['title', 'course_code', 'section_no', 'student_count', 'credits']);

interface Choice {
  item: RubricItem;
  group: string;
}

function choicesOf(form: RubricForm): Choice[] {
  const walk = (sections: RubricFormSection[], category: string): Choice[] =>
    sections.flatMap((section) => [
      ...section.items
        .filter((item) => item.is_active)
        .map((item) => ({ item, group: `${category} › ${section.code} ${section.name_th}` })),
      ...walk(section.children, category),
    ]);
  return form.categories.flatMap((category) =>
    walk(category.sections, `หมวด ${category.code}`)
  );
}

function toDetailValue(spec: FieldSpec, raw: string | boolean): unknown {
  if (spec.type === 'bool') return raw === true;
  if (raw === '') return undefined;
  if (spec.type === 'int') return Number.parseInt(String(raw), 10);
  if (spec.type === 'number' || spec.type === 'money') return Number(raw);
  return raw;
}

/**
 * Inputs of one entry. Which inputs show depends on the chosen rubric item; the extra
 * `field_schema` fields are sent as one JSON `details_json` hidden input.
 * The score is never entered: the backend computes it.
 */
export function EntryFields({
  form,
  entry,
  publications = [],
}: {
  form: RubricForm;
  entry?: Entry;
  /** The owner's own publications, to link a line to one */
  publications?: { publication_id: number; title: string; publication_year: number | null }[];
}) {
  const choices = useMemo(() => choicesOf(form), [form]);
  const [itemId, setItemId] = useState<number>(entry?.item_id ?? choices[0]?.item.id ?? 0);
  const [details, setDetails] = useState<Record<string, string | boolean>>(() =>
    Object.fromEntries(
      Object.entries(entry?.details ?? {}).map(([key, value]) => [
        key,
        typeof value === 'boolean' ? value : String(value ?? ''),
      ])
    )
  );

  const item =
    choices.find((choice) => choice.item.id === itemId)?.item ??
    // an entry whose item was turned off later still has to be editable
    form.categories
      .flatMap((c) => c.sections)
      .flatMap(function all(s: RubricFormSection): RubricItem[] {
        return [...s.items, ...s.children.flatMap(all)];
      })
      .find((candidate) => candidate.id === itemId);

  const schema = Object.entries(item?.field_schema ?? {}).filter(([name]) => !ENTRY_COLUMNS.has(name));
  const schemaNames = new Set(Object.keys(item?.field_schema ?? {}));
  const needsStudents = item?.tier_min !== null || item?.tier_max !== null || schemaNames.has('student_count');
  const groups = [...new Set(choices.map((choice) => choice.group))];

  const detailsJson = JSON.stringify(
    Object.fromEntries(
      schema
        .map(([name, spec]) => [name, toDetailValue(spec, details[name] ?? (spec.type === 'bool' ? false : ''))])
        .filter(([, value]) => value !== undefined)
    )
  );

  if (choices.length === 0 && !entry) {
    return <p className="text-sm text-ink-muted">เกณฑ์ของรอบนี้ยังไม่มีตัวเลือกที่เปิดใช้</p>;
  }

  return (
    <div className="space-y-4">
      <Field label="รายการภาระงาน *">
        <select
          name="item_id"
          value={itemId}
          onChange={(event) => setItemId(Number(event.target.value))}
          className={inputClass}
          required
        >
          {groups.map((group) => (
            <optgroup key={group} label={group}>
              {choices
                .filter((choice) => choice.group === group)
                .map(({ item: option }) => (
                  <option key={option.id} value={option.id}>
                    {option.label_th}
                  </option>
                ))}
            </optgroup>
          ))}
          {entry && !choices.some((choice) => choice.item.id === entry.item_id) && item ? (
            <option value={item.id}>{item.label_th} (ปิดใช้แล้ว)</option>
          ) : null}
        </select>
      </Field>

      {item ? (
        <p className="rounded-lg bg-surface-alt px-3 py-2 text-xs text-ink-muted">
          {item.weight_mode === 'fixed'
            ? `น้ำหนัก ${formatNumber(item.weight)} × คะแนนฐาน ${formatNumber(form.base_points)} ต่อ ${formatNumber(item.unit_divisor)} ${UNIT_LABEL[item.unit]}`
            : `${item.assessor_position ? POSITION_LABEL[item.assessor_position] : 'ผู้บริหาร'} เป็นผู้ให้ค่า ${formatNumber(item.weight_min)}–${formatNumber(item.weight_max)} หลังส่งใบ (ระหว่างนี้คะแนนเป็น 0)`}
          {item.tier_min !== null || item.tier_max !== null
            ? ` · ใช้กับจำนวนนักศึกษา ${item.tier_min ?? 0}–${item.tier_max ?? 'ขึ้นไป'} คน`
            : ''}
          {item.once_per_round ? ' · ใช้ได้ครั้งเดียวต่อรอบ' : ''}
        </p>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-4">
        <Field label="ชื่อเรื่อง / โครงการ / นักศึกษา" className="sm:col-span-2">
          <input name="title" maxLength={500} defaultValue={entry?.title ?? ''} className={inputClass} />
        </Field>
        <Field label="รหัสวิชา">
          <input name="course_code" maxLength={15} placeholder="CS222" defaultValue={entry?.course_code ?? ''} className={inputClass} />
        </Field>
        <Field label="ตอนเรียน (section)">
          <input name="section_no" maxLength={10} defaultValue={entry?.section_no ?? ''} className={inputClass} />
        </Field>
        <Field label={`จำนวน (${item ? UNIT_LABEL[item.unit] : 'หน่วย'}) *`}>
          <input name="quantity" type="number" step="0.01" min={0.01} required defaultValue={entry?.quantity ?? 1} className={inputClass} />
        </Field>
        {needsStudents ? (
          <Field label="จำนวนนักศึกษา *">
            <input name="student_count" type="number" min={0} required defaultValue={entry?.student_count ?? ''} className={inputClass} />
          </Field>
        ) : null}
        {item?.uses_participation ? (
          <Field label="สัดส่วนการมีส่วนร่วม (%) *">
            <input name="participation_pct" type="number" step="0.01" min={0.01} max={100} required defaultValue={entry?.participation_pct ?? 100} className={inputClass} />
          </Field>
        ) : (
          <input type="hidden" name="participation_pct" value="100" />
        )}
        {item?.counts_teaching_credit || schemaNames.has('credits') ? (
          <Field label="หน่วยกิตสอน">
            <input name="credits" type="number" step="0.01" min={0} defaultValue={entry?.credits ?? ''} className={inputClass} />
          </Field>
        ) : null}
        {schema.map(([name, spec]) => (
          <Field key={name} label={`${name}${spec.required ? ' *' : ''}`}>
            {spec.type === 'enum' ? (
              <select
                value={String(details[name] ?? '')}
                onChange={(event) => setDetails({ ...details, [name]: event.target.value })}
                required={spec.required}
                className={inputClass}
              >
                <option value="">—</option>
                {spec.values?.map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            ) : spec.type === 'bool' ? (
              <input
                type="checkbox"
                checked={details[name] === true}
                onChange={(event) => setDetails({ ...details, [name]: event.target.checked })}
                className="h-4 w-4 accent-brand"
              />
            ) : (
              <input
                type={spec.type === 'date' ? 'date' : spec.type === 'string' ? 'text' : 'number'}
                step={spec.type === 'int' ? 1 : 'any'}
                value={String(details[name] ?? '')}
                onChange={(event) => setDetails({ ...details, [name]: event.target.value })}
                required={spec.required}
                className={inputClass}
              />
            )}
          </Field>
        ))}
      </div>
      <input type="hidden" name="details_json" value={schema.length ? detailsJson : ''} />

      <Field
        label="ผูกกับผลงานตีพิมพ์ของฉัน (ถ้ามี)"
        hint="ใช้กับรายการงานวิชาการ เลือกได้เฉพาะผลงานที่คุณเป็นผู้แต่ง เพิ่มผลงานใหม่ได้ที่หน้านี้ด้านบน"
      >
        {entry?.publication_id ? <input type="hidden" name="publication_was" value="1" /> : null}
        <select name="publication_id" defaultValue={entry?.publication_id ?? ''} className={inputClass}>
          <option value="">ไม่ผูกกับผลงาน</option>
          {publications.map((publication) => (
            <option key={publication.publication_id} value={publication.publication_id}>
              {publication.publication_year ? `${publication.publication_year} · ` : ''}
              {publication.title}
            </option>
          ))}
        </select>
      </Field>

      <Field label="หมายเหตุ">
        <textarea name="note" rows={2} maxLength={5000} defaultValue={entry?.note ?? ''} className={inputClass} />
      </Field>
    </div>
  );
}
