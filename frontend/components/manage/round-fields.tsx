import { Checkbox, Field, inputClass } from '@/components/manage/ui';
import type { EvaluationRound, RubricVersion } from '@/types/backend';

/** `submit_due_at` as the value of <input type="datetime-local"> (local time) */
function localDateTime(value: string | null | undefined): string {
  if (!value) return '';
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

export function RoundFields({
  round,
  versions,
}: {
  round?: EvaluationRound;
  versions: RubricVersion[];
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-4">
      <Field label="ชื่อรอบ *" className="sm:col-span-2">
        <input name="name_th" required maxLength={100} placeholder="รอบ 1/2568" defaultValue={round?.name_th} className={inputClass} />
      </Field>
      <Field label="เกณฑ์ที่ใช้ *" hint="เปลี่ยนไม่ได้เมื่อมีใบภาระงานในรอบแล้ว">
        <select name="rubric_version_id" required defaultValue={round?.rubric_version_id} className={inputClass}>
          {versions.map((version) => (
            <option key={version.id} value={version.id} disabled={!version.is_active && version.id !== round?.rubric_version_id}>
              {version.code}
              {version.is_active ? '' : ' (ปิดใช้)'}
            </option>
          ))}
        </select>
      </Field>
      <div className="flex items-end pb-2">
        <Checkbox name="is_open" label="เปิดให้กรอก" defaultChecked={round?.is_open} />
      </div>
      <Field label="ช่วงผลงาน: ตั้งแต่ *">
        <input name="period_start" type="date" required defaultValue={round?.period_start} className={inputClass} />
      </Field>
      <Field label="ถึง *">
        <input name="period_end" type="date" required defaultValue={round?.period_end} className={inputClass} />
      </Field>
      <Field label="วันที่มีผลต่อเงินเดือน *">
        <input name="salary_effective_on" type="date" required defaultValue={round?.salary_effective_on} className={inputClass} />
      </Field>
      <Field label="กำหนดส่ง">
        <input name="submit_due_at" type="datetime-local" defaultValue={localDateTime(round?.submit_due_at)} className={inputClass} />
      </Field>
      <Field label="ปีการศึกษา (พ.ศ.) *">
        <input name="academic_year" type="number" required min={2400} max={2800} placeholder="2568" defaultValue={round?.academic_year} className={inputClass} />
      </Field>
      <Field label="ภาคการศึกษา">
        <select name="semester" defaultValue={round?.semester ?? ''} className={inputClass}>
          <option value="">—</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3 (ฤดูร้อน)</option>
        </select>
      </Field>
    </div>
  );
}
