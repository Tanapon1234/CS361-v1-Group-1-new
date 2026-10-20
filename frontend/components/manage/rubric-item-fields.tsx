import { Checkbox, Field, inputClass } from '@/components/manage/ui';
import {
  AGG_LABEL,
  POSITION_LABEL,
  RANGE_BASIS_LABEL,
  UNIT_LABEL,
  WEIGHT_MODE_LABEL,
} from '@/lib/backend/labels';
import type { RubricItem } from '@/types/backend';

/** Inputs of a rubric item (choice). Ranged-only inputs are ignored for fixed items. */
export function RubricItemFields({ item }: { item?: RubricItem }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-4">
        <Field label="ข้อความตัวเลือก *" className="sm:col-span-2">
          <input name="label_th" required maxLength={255} defaultValue={item?.label_th} className={inputClass} />
        </Field>
        <Field label="วิธีให้น้ำหนัก">
          <select name="weight_mode" defaultValue={item?.weight_mode ?? 'fixed'} className={inputClass}>
            {Object.entries(WEIGHT_MODE_LABEL).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </Field>
        <Field label="น้ำหนัก (แบบตายตัว)" hint="เช่น 0.075">
          <input name="weight" type="number" step="0.0001" min={0} defaultValue={item?.weight ?? ''} className={inputClass} />
        </Field>
      </div>

      <fieldset className="rounded-lg border border-line-soft p-3">
        <legend className="px-1 text-xs font-semibold text-ink-muted">ใช้เมื่อผู้บริหารเป็นผู้ให้ค่า</legend>
        <div className="grid gap-3 sm:grid-cols-5">
          <Field label="ค่าต่ำสุด">
            <input name="weight_min" type="number" step="0.0001" min={0} defaultValue={item?.weight_min ?? ''} className={inputClass} />
          </Field>
          <Field label="ค่าสูงสุด">
            <input name="weight_max" type="number" step="0.0001" min={0} defaultValue={item?.weight_max ?? ''} className={inputClass} />
          </Field>
          <Field label="ความหมายของค่า">
            <select name="range_basis" defaultValue={item?.range_basis ?? 'weight'} className={inputClass}>
              {Object.entries(RANGE_BASIS_LABEL).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </Field>
          <Field label="ผู้ประเมิน">
            <select name="assessor_position" defaultValue={item?.assessor_position ?? 'exec_committee'} className={inputClass}>
              {Object.entries(POSITION_LABEL).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </Field>
          <Field label="รวมค่าแบบ">
            <select name="assessment_agg" defaultValue={item?.assessment_agg === 'average' ? 'average' : 'single'} className={inputClass}>
              <option value="single">{AGG_LABEL.single}</option>
              <option value="average">{AGG_LABEL.average}</option>
            </select>
          </Field>
        </div>
      </fieldset>

      <div className="grid gap-3 sm:grid-cols-4">
        <Field label="หน่วย">
          <select name="unit" defaultValue={item?.unit ?? 'topic'} className={inputClass}>
            {Object.entries(UNIT_LABEL).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </Field>
        <Field label="ตัวหาร" hint="เช่น 3 สำหรับวิชา 3 หน่วยกิต">
          <input name="unit_divisor" type="number" step="0.01" min={0.01} defaultValue={item?.unit_divisor ?? 1} className={inputClass} />
        </Field>
        <Field label="จำนวน นศ. ตั้งแต่">
          <input name="tier_min" type="number" min={0} defaultValue={item?.tier_min ?? ''} className={inputClass} />
        </Field>
        <Field label="ถึง">
          <input name="tier_max" type="number" min={0} defaultValue={item?.tier_max ?? ''} className={inputClass} />
        </Field>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-2">
        <Checkbox name="uses_participation" label="คิดตามสัดส่วนการมีส่วนร่วม (%)" defaultChecked={item?.uses_participation} />
        <Checkbox name="counts_teaching_credit" label="นับเป็นหน่วยกิตสอน" defaultChecked={item?.counts_teaching_credit} />
        <Checkbox name="once_per_round" label="ใช้ได้ครั้งเดียวต่อรอบ" defaultChecked={item?.once_per_round} />
        <Checkbox name="is_active" label="เปิดใช้" defaultChecked={item?.is_active ?? true} />
      </div>

      <Field
        label="ฟิลด์เพิ่มเติม (field_schema, JSON)"
        hint='เช่น {"hours": {"type": "int", "required": true}, "quartile": {"type": "enum", "values": ["Q1","Q2"]}} · type: int, number, money, string, enum, date, bool'
      >
        <textarea
          name="field_schema"
          rows={2}
          defaultValue={item?.field_schema ? JSON.stringify(item.field_schema) : ''}
          className={`${inputClass} font-mono text-xs`}
        />
      </Field>
    </div>
  );
}
