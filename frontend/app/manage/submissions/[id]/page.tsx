import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import {
  createEntry,
  deleteEntry,
  deleteEvidence,
  deleteSubmission,
  finishEvidenceUpload,
  signSubmission,
  startEvidenceUpload,
  updateEntry,
} from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { EntryFields } from '@/components/manage/entry-fields';
import { FileUpload } from '@/components/manage/file-upload';
import {
  Badge,
  EmptyNote,
  Field,
  Notice,
  PageHeader,
  Section,
  Stat,
  StatusBadge,
  Table,
  Td,
  inputClass,
  linkClass,
} from '@/components/manage/ui';
import { canSign } from '@/lib/auth/permissions';
import {
  MAX_PAGE,
  getLecturer,
  getRound,
  getRubricForm,
  getSubmission,
  getSubmissionSummary,
  getSubmissionTotals,
  listApprovals,
  listEntryAssessments,
  listEvidence,
  listLecturers,
  settle,
} from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import {
  DATA_SOURCE_LABEL,
  EDITABLE_STATUSES,
  POSITION_LABEL,
  RANK_LABEL,
  SIGNER_ROLE_LABEL,
  UNIT_LABEL,
  WORKFLOW_STEP,
  formatBytes,
  formatDateTime,
  formatNumber,
  formatScore,
} from '@/lib/backend/labels';
import type { Entry, RubricFormSection, RubricItem } from '@/types/backend';

export const metadata: Metadata = { title: 'ใบภาระงาน' };

function allSections(sections: RubricFormSection[]): RubricFormSection[] {
  return sections.flatMap((section) => [section, ...allSections(section.children)]);
}

function detailsText(entry: Entry): string {
  return Object.entries(entry.details ?? {})
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(' · ');
}

export default async function SubmissionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const submission = await getSubmission(id);
  if (!submission) notFound();

  const round = await getRound(submission.round_id);
  const [form, summary, totals, approvals, owner, lecturers, me] = await Promise.all([
    round ? getRubricForm(round.rubric_version_id) : Promise.resolve(null),
    getSubmissionSummary(id),
    getSubmissionTotals(id),
    listApprovals(id),
    getLecturer(submission.lecturer_id),
    listLecturers({ limit: MAX_PAGE }),
    getCurrentUser(),
  ]);
  if (!form) notFound();

  const items = new Map<number, RubricItem>();
  const sections = form.categories.flatMap((category) =>
    allSections(category.sections).map((section) => ({ category, section }))
  );
  for (const { section } of sections) for (const item of section.items) items.set(item.id, item);
  const lecturerName = new Map(lecturers.items.map((l) => [l.lecturer_id, l.name_th]));

  const isOwner = me?.lecturer.lecturer_id === submission.lecturer_id;
  // Only the owner changes entries, and only while draft / returned
  const editable = isOwner && EDITABLE_STATUSES.includes(submission.status);
  const step = WORKFLOW_STEP[submission.status];
  const signs = !!step && canSign(me, step.role, submission);

  // Evidence for every entry, assessments for the ranged ones (small numbers per form)
  const [evidence, assessments] = await Promise.all([
    Promise.all(submission.entries.map((entry) => settle(listEvidence(entry.id)))),
    Promise.all(
      submission.entries.map((entry) =>
        items.get(entry.item_id)?.weight_mode === 'ranged'
          ? settle(listEntryAssessments(entry.id))
          : Promise.resolve(null)
      )
    ),
  ]);
  const evidenceOf = new Map(submission.entries.map((entry, i) => [entry.id, evidence[i]]));
  const assessmentsOf = new Map(submission.entries.map((entry, i) => [entry.id, assessments[i]]));

  return (
    <div className="space-y-6">
      <PageHeader
        title={`ใบภาระงาน: ${owner?.name_th ?? 'อาจารย์'}`}
        description={`${round?.name_th ?? ''} · เกณฑ์ ${form.code} · ${RANK_LABEL[submission.rank_snapshot]}`}
        back={{ href: '/manage/submissions', label: 'ใบภาระงาน' }}
        actions={
          <>
            <StatusBadge status={submission.status} />
            {isOwner && submission.status === 'draft' ? (
              <ActionForm
                inline
                variant="danger"
                submitLabel="ลบใบ"
                confirmText="ลบใบภาระงานนี้ทั้งใบ รวมรายการและไฟล์แนบ?"
                action={deleteSubmission.bind(null, id)}
              />
            ) : null}
          </>
        }
      />

      {!me ? (
        <Notice tone="error">
          ยังไม่ได้เลือกผู้ใช้งาน ทำได้แค่ดู <Link href="/manage/switch-user" className={linkClass}>เลือกผู้ใช้</Link>
        </Notice>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Stat
          label="คะแนนหลังตัดเพดาน"
          value={formatScore(summary.capped_total)}
          hint={`จากคะแนนดิบ ${formatScore(summary.raw_total)} · เพดาน ${formatNumber(summary.overall_cap)}`}
        />
        <Stat
          label="เกณฑ์ขั้นต่ำ"
          value={summary.meets_min_required ? 'ผ่าน' : 'ยังไม่ผ่าน'}
          hint={`ต้องได้อย่างน้อย ${formatNumber(summary.min_required)}`}
        />
        <Stat
          label="หน่วยกิตสอน"
          value={formatNumber(summary.teaching_credits)}
          hint={summary.meets_min_teaching_credits ? 'ครบขั้นต่ำแล้ว' : `ต้องมีอย่างน้อย ${formatNumber(summary.min_teaching_credits)}`}
        />
        <Stat label="รอผู้บริหารประเมิน" value={summary.pending_assessments} hint="รายการที่ยังไม่มีค่าประเมิน" />
      </div>

      <Section title="คะแนนรายหมวด" description={totals ? 'คำนวณสดจากรายการ · ด้านขวาคือยอดที่ระบบ freeze ไว้ตอนส่ง' : 'คำนวณสดจากรายการ'}>
        <Table head={['หมวด', 'เพดาน', 'คะแนนดิบ', 'หลังตัดเพดาน', ...(totals ? ['ยอดที่ freeze'] : [])]}>
          {summary.categories.map((category) => (
            <tr key={category.category_id}>
              <Td className="font-medium text-ink">{category.code} {category.name_th}</Td>
              <Td>{formatNumber(category.cap)}</Td>
              <Td>{formatScore(category.raw_score)}</Td>
              <Td className="font-semibold">{formatScore(category.capped_score)}</Td>
              {totals ? (
                <Td>{formatScore(totals.categories.find((c) => c.category_id === category.category_id)?.capped_score)}</Td>
              ) : null}
            </tr>
          ))}
        </Table>
      </Section>

      <Section
        title="การส่งและการอนุมัติ"
        description="ขั้นถัดไปมาจากสถานะของใบ: เจ้าของส่ง, เจ้าหน้าที่รับเรื่อง, หัวหน้าและกรรมการของสาขาลงนาม"
      >
        {step && !signs ? (
          <Notice>
            ขั้นถัดไป: รอ <strong>{SIGNER_ROLE_LABEL[step.role]}</strong> ลงนาม
          </Notice>
        ) : step ? (
          <div className="mb-5 grid gap-4 rounded-lg border border-line-soft bg-surface-alt p-4 lg:grid-cols-2">
            <div>
              <p className="text-sm text-ink">
                ขั้นถัดไป: <strong>{SIGNER_ROLE_LABEL[step.role]}</strong> (คุณ)
              </p>
              <ActionForm
                action={signSubmission.bind(null, id, 'approved')}
                submitLabel={step.approve}
                className="mt-3 space-y-3"
              >
                <Field label="หมายเหตุ (ไม่บังคับ)">
                  <input name="comment" maxLength={2000} className={inputClass} />
                </Field>
              </ActionForm>
            </div>
            {step.canReturn ? (
              <div>
                <p className="text-sm text-ink">ตีกลับให้เจ้าของแก้ไข</p>
                <ActionForm
                  action={signSubmission.bind(null, id, 'returned')}
                  submitLabel="ตีกลับ"
                  variant="danger"
                  className="mt-3 space-y-3"
                >
                  <Field label="เหตุผล *">
                    <input name="comment" required maxLength={2000} className={inputClass} />
                  </Field>
                </ActionForm>
              </div>
            ) : null}
          </div>
        ) : (
          <Notice tone="success">ใบนี้ส่งถึงคณะแล้ว ไม่มีขั้นตอนต่อ</Notice>
        )}
        {approvals.items.length === 0 ? (
          <EmptyNote>ยังไม่มีประวัติ</EmptyNote>
        ) : (
          <Table head={['เวลา', 'ผู้ลงนาม', 'บทบาท', 'ผล', 'หมายเหตุ']}>
            {approvals.items.map((approval) => (
              <tr key={approval.id}>
                <Td>{formatDateTime(approval.signed_at)}</Td>
                <Td>{lecturerName.get(approval.signer_id) ?? approval.signer_id}</Td>
                <Td>{SIGNER_ROLE_LABEL[approval.role]}</Td>
                <Td>
                  {approval.decision === 'approved' ? (
                    <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">ผ่าน</Badge>
                  ) : (
                    <Badge className="border-brand/30 bg-brand-soft text-brand">ตีกลับ</Badge>
                  )}
                </Td>
                <Td>{approval.comment ?? '–'}</Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>

      {editable ? (
        <Section title="เพิ่มรายการ" description="เลือกรายการตามเกณฑ์ ระบบจะคำนวณคะแนนให้เอง">
          <ActionForm action={createEntry.bind(null, id)} submitLabel="เพิ่มรายการ" resetOnSuccess>
            <EntryFields form={form} />
          </ActionForm>
        </Section>
      ) : (
        <Notice>ใบอยู่ในสถานะที่แก้รายการไม่ได้ (แก้ได้เฉพาะตอนเป็นร่างหรือถูกตีกลับ)</Notice>
      )}

      {form.categories.map((category) => {
        const categorySections = sections.filter((s) => s.category.id === category.id);
        const entriesInCategory = submission.entries.filter((entry) =>
          categorySections.some((s) => s.section.id === items.get(entry.item_id)?.section_id)
        );
        return (
          <Section
            key={category.id}
            title={`หมวด ${category.code} ${category.name_th}`}
            description={`${entriesInCategory.length} รายการ · เพดาน ${formatNumber(category.cap)}`}
          >
            {entriesInCategory.length === 0 ? (
              <EmptyNote>ยังไม่มีรายการในหมวดนี้</EmptyNote>
            ) : (
              <ul className="space-y-3">
                {entriesInCategory.map((entry) => {
                  const item = items.get(entry.item_id);
                  const section = categorySections.find((s) => s.section.id === item?.section_id)?.section;
                  const files = evidenceOf.get(entry.id);
                  const given = assessmentsOf.get(entry.id);
                  return (
                    <li key={entry.id} className="rounded-lg border border-line p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-xs text-ink-muted">
                            {section?.code} {section?.name_th}
                          </p>
                          <p className="font-semibold text-ink">{item?.label_th ?? `item #${entry.item_id}`}</p>
                          <p className="mt-1 text-sm text-ink-muted">
                            {[
                              entry.title,
                              entry.course_code && `วิชา ${entry.course_code}${entry.section_no ? ` (${entry.section_no})` : ''}`,
                              entry.student_count !== null && `นศ. ${entry.student_count} คน`,
                              `${formatNumber(entry.quantity)} ${item ? UNIT_LABEL[item.unit] : ''}`,
                              entry.participation_pct !== 100 && `มีส่วนร่วม ${formatNumber(entry.participation_pct)}%`,
                              entry.credits !== null && `หน่วยกิตสอน ${formatNumber(entry.credits)}`,
                              detailsText(entry),
                              entry.data_source !== 'manual' && DATA_SOURCE_LABEL[entry.data_source],
                            ]
                              .filter(Boolean)
                              .join(' · ')}
                          </p>
                          {entry.note ? <p className="mt-1 text-xs text-ink-muted">หมายเหตุ: {entry.note}</p> : null}
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-ink">{formatScore(entry.score)}</p>
                          <p className="text-xs text-ink-muted">
                            {entry.weight_applied !== null
                              ? `น้ำหนัก ${formatNumber(entry.weight_applied)}`
                              : item?.weight_mode === 'ranged'
                                ? 'รอ/ตามค่าประเมิน'
                                : ''}
                          </p>
                        </div>
                      </div>

                      {given?.data && given.data.items.length > 0 ? (
                        <div className="mt-3 rounded-lg bg-surface-alt px-3 py-2 text-xs text-ink-muted">
                          ค่าประเมิน:{' '}
                          {given.data.items
                            .map((a) => `${lecturerName.get(a.assessor_id) ?? 'ผู้ประเมิน'} (${POSITION_LABEL[a.position_used]}) ${formatNumber(a.value_given)}`)
                            .join(' · ')}
                        </div>
                      ) : null}

                      <div className="mt-3 border-t border-line-soft pt-3">
                        <p className="mb-2 text-xs font-semibold text-ink-muted">ไฟล์หลักฐาน</p>
                        {files?.error ? (
                          <p className="text-xs text-brand">{files.error}</p>
                        ) : files?.data?.items.length ? (
                          <ul className="mb-2 space-y-1 text-sm">
                            {files.data.items.map((file) => (
                              <li key={file.id} className="flex flex-wrap items-center gap-2">
                                {file.status === 'uploaded' ? (
                                  <a href={`/manage/evidence/${file.id}`} className={linkClass}>{file.file_name}</a>
                                ) : (
                                  <span className="text-ink-muted">{file.file_name}</span>
                                )}
                                <span className="text-xs text-ink-muted">
                                  {[file.label, formatBytes(file.size_bytes)].filter(Boolean).join(' · ')}
                                </span>
                                {file.status === 'pending' ? <Badge>ยังอัปโหลดไม่เสร็จ</Badge> : null}
                                {editable ? (
                                  <ActionForm
                                    inline
                                    variant="danger"
                                    submitLabel="ลบ"
                                    confirmText={`ลบไฟล์ ${file.file_name}?`}
                                    action={deleteEvidence.bind(null, file.id)}
                                  />
                                ) : null}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mb-2 text-xs text-ink-muted">ยังไม่มีไฟล์</p>
                        )}
                        {editable ? (
                          <FileUpload
                            withLabel
                            accept="application/pdf,image/jpeg,image/png"
                            start={startEvidenceUpload.bind(null, entry.id)}
                            finish={finishEvidenceUpload}
                            submitLabel="แนบไฟล์"
                          />
                        ) : null}
                      </div>

                      {editable ? (
                        <details className="mt-3 border-t border-line-soft pt-3">
                          <summary className="cursor-pointer text-sm font-semibold text-brand">แก้ไข / ลบรายการ</summary>
                          <div className="mt-3 space-y-3">
                            <ActionForm action={updateEntry.bind(null, entry.id)} variant="secondary">
                              <EntryFields form={form} entry={entry} />
                            </ActionForm>
                            <ActionForm
                              inline
                              variant="danger"
                              submitLabel="ลบรายการ"
                              confirmText="ลบรายการนี้ รวมไฟล์แนบ?"
                              action={deleteEntry.bind(null, entry.id)}
                            />
                          </div>
                        </details>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </Section>
        );
      })}

      <p className="text-xs text-ink-muted">
        ยังไม่มีไฟล์ PDF ของใบ (backend ตอบ 501) · สร้างเมื่อ {formatDateTime(submission.created_at)}
        {submission.submitted_at ? ` · ส่งเมื่อ ${formatDateTime(submission.submitted_at)}` : ''}
      </p>
    </div>
  );
}
