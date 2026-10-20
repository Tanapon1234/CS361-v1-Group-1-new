import { ActionForm, type FormAction } from '@/components/manage/action-form';
import { inputClass } from '@/components/manage/ui';

/** Verify / reject with a note (a rejection needs one: the backend says so) */
export function VerdictForm({ action }: { action: FormAction }) {
  return (
    <ActionForm action={action} submitLabel="บันทึกผล" variant="secondary" className="flex flex-wrap items-end gap-2">
      <select name="status" defaultValue="verified" className={`${inputClass} w-36`} aria-label="ผลการตรวจ">
        <option value="verified">รับรอง</option>
        <option value="rejected">ตีกลับ</option>
        <option value="pending">กลับไปรอตรวจ</option>
      </select>
      <input name="note" maxLength={2000} placeholder="หมายเหตุ (ต้องใส่ถ้าตีกลับ)" className={`${inputClass} min-w-56 flex-1`} aria-label="หมายเหตุ" />
    </ActionForm>
  );
}
