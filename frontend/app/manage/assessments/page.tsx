import type { Metadata } from 'next';
import Link from 'next/link';

import { deleteMyAssessment, putMyAssessment } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import {
  Badge,
  EmptyNote,
  Field,
  PageHeader,
  Pager,
  inputClass,
  intParam,
  linkClass,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { PAGE_SIZE, listAssessmentQueue, listDepartments, listRounds } from '@/lib/backend/api';
import { currentLecturerId } from '@/lib/backend/client';
import { POSITION_LABEL, RANGE_BASIS_LABEL, formatNumber, formatScore } from '@/lib/backend/labels';

export const metadata: Metadata = { title: 'งานประเมินของฉัน' };

export default async function AssessmentsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const me = await currentLecturerId();
  const roundId = intParam(params.round_id);
  const rawStatus = param(params.status);
  const status = rawStatus === 'done' ? 'done' : rawStatus === 'all' ? undefined : 'pending';
  const offset = intParam(params.offset) ?? 0;

  if (!me) {
    return (
      <div className="space-y-6">
        <PageHeader title="งานประเมินของฉัน" />
        <EmptyNote>
          ต้อง <Link href="/manage/switch-user" className={linkClass}>เลือกผู้ใช้งาน</Link> ก่อน
        </EmptyNote>
      </div>
    );
  }

  const [queue, rounds, departments] = await Promise.all([
    listAssessmentQueue({ round_id: roundId, status, offset }),
    listRounds(),
    listDepartments(),
  ]);
  const departmentName = new Map(departments.items.map((d) => [d.id, d.name_th]));

  return (
    <div className="space-y-6">
      <PageHeader
        title="งานประเมินของฉัน"
        description="รายการที่ตำแหน่งบริหารปัจจุบันของคุณต้องให้ค่า (เฉพาะใบที่อยู่ในสถานะ รอผู้บริหารประเมิน)"
      />

      <form role="search" className="flex flex-wrap gap-2">
        <select name="status" defaultValue={rawStatus ?? 'pending'} className={`${inputClass} sm:w-48`} aria-label="สถานะ">
          <option value="pending">ยังไม่ได้ประเมิน</option>
          <option value="done">ประเมินแล้ว</option>
          <option value="all">ทั้งหมด</option>
        </select>
        <select name="round_id" defaultValue={roundId ?? ''} className={`${inputClass} sm:w-56`} aria-label="รอบ">
          <option value="">ทุกรอบ</option>
          {rounds.items.map((round) => (
            <option key={round.id} value={round.id}>{round.name_th}</option>
          ))}
        </select>
        <button type="submit" className={secondaryButtonClass}>กรอง</button>
      </form>

      {queue.items.length === 0 ? (
        <EmptyNote>ไม่มีรายการ (ถ้าคิดว่าควรมี ตรวจตำแหน่งบริหารของคุณที่เมนูอาจารย์)</EmptyNote>
      ) : (
        <ul className="space-y-3">
          {queue.items.map((row) => (
            <li key={row.entry.id} className="rounded-xl border border-line p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-ink">
                    {row.lecturer_name_th}{' '}
                    <span className="text-sm font-normal text-ink-muted">
                      · {departmentName.get(row.department_id) ?? ''}
                    </span>
                  </p>
                  <p className="text-sm text-ink">{row.item_label_th}</p>
                  <p className="text-xs text-ink-muted">
                    {[row.entry.title, `จำนวน ${formatNumber(row.entry.quantity)}`, row.entry.note]
                      .filter(Boolean)
                      .join(' · ')}
                  </p>
                  <p className="mt-1 text-xs text-ink-muted">
                    ประเมินในฐานะ {POSITION_LABEL[row.assessor_position]} · ช่วง {formatNumber(row.weight_min)}–{formatNumber(row.weight_max)} ·{' '}
                    {row.range_basis ? RANGE_BASIS_LABEL[row.range_basis] : ''}
                  </p>
                </div>
                <div className="text-right">
                  {row.my_assessment ? (
                    <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">
                      ให้ไว้ {formatNumber(row.my_assessment.value_given)}
                    </Badge>
                  ) : (
                    <Badge>ยังไม่ประเมิน</Badge>
                  )}
                  <p className="mt-1 text-xs text-ink-muted">คะแนนรายการตอนนี้ {formatScore(row.entry.score)}</p>
                  <Link href={`/manage/submissions/${row.entry.submission_id}`} className={`text-xs ${linkClass}`}>
                    เปิดใบภาระงาน
                  </Link>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-end gap-3 border-t border-line-soft pt-3">
                <ActionForm
                  action={putMyAssessment.bind(null, row.entry.id)}
                  submitLabel={row.my_assessment ? 'แก้ค่าประเมิน' : 'ให้ค่าประเมิน'}
                  className="flex flex-wrap items-end gap-3"
                >
                  <Field label="ค่า" className="w-32">
                    <input
                      name="value_given"
                      type="number"
                      step="0.0001"
                      required
                      min={row.weight_min ?? undefined}
                      max={row.weight_max ?? undefined}
                      defaultValue={row.my_assessment?.value_given ?? ''}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="ความเห็น" className="min-w-60 flex-1">
                    <input name="comment" maxLength={2000} defaultValue={row.my_assessment?.comment ?? ''} className={inputClass} />
                  </Field>
                </ActionForm>
                {row.my_assessment ? (
                  <ActionForm
                    inline
                    variant="danger"
                    submitLabel="ถอนค่า"
                    confirmText="ถอนค่าประเมินของคุณ?"
                    action={deleteMyAssessment.bind(null, row.entry.id)}
                  />
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
      <Pager
        total={queue.meta.total}
        limit={PAGE_SIZE}
        offset={offset}
        hrefFor={(next) => withQuery('/manage/assessments', { round_id: roundId, status: rawStatus, offset: next })}
      />
    </div>
  );
}
