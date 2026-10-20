import { Field, inputClass } from '@/components/manage/ui';
import type { Publication } from '@/types/backend';

export function PublicationFields({ publication }: { publication?: Publication }) {
  return (
    <div className="grid gap-4 sm:grid-cols-6">
      <Field label="ชื่อผลงาน *" className="sm:col-span-6">
        <input name="title" required defaultValue={publication?.title} className={inputClass} />
      </Field>
      <Field label="ปี (ค.ศ.)" className="sm:col-span-1">
        <input name="publication_year" type="number" min={1900} max={2200} defaultValue={publication?.publication_year ?? ''} className={inputClass} />
      </Field>
      <Field label="แหล่งตีพิมพ์" className="sm:col-span-3">
        <input name="venue" defaultValue={publication?.venue ?? ''} className={inputClass} />
      </Field>
      <Field label="Volume" className="sm:col-span-1">
        <input name="volume" maxLength={50} defaultValue={publication?.volume ?? ''} className={inputClass} />
      </Field>
      <Field label="หน้า" className="sm:col-span-1">
        <input name="pages" maxLength={50} defaultValue={publication?.pages ?? ''} className={inputClass} />
      </Field>
      <Field label="DOI" className="sm:col-span-6">
        <input name="doi" maxLength={255} placeholder="10.xxxx/xxxx" defaultValue={publication?.doi ?? ''} className={inputClass} />
      </Field>
      <Field label="Citation" className="sm:col-span-6">
        <textarea name="citation_text" rows={3} defaultValue={publication?.citation_text ?? ''} className={inputClass} />
      </Field>
    </div>
  );
}
