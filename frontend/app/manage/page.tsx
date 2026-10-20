import type { Metadata } from 'next';
import Link from 'next/link';

import { createSubmission } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import {
  Badge,
  EmptyNote,
  Field,
  Notice,
  PageHeader,
  Section,
  StatusBadge,
  Table,
  Td,
  buttonClass,
  inputClass,
  linkClass,
} from '@/components/manage/ui';
import { getMe, listRounds, listSubmissions } from '@/lib/backend/api';
import { currentLecturerId } from '@/lib/backend/client';
import {
  POSITION_LABEL,
  SIGNER_ROLE_LABEL,
  formatDate,
  formatScore,
} from '@/lib/backend/labels';

export const metadata: Metadata = { title: 'ภาพรวมของฉัน' };

export default async function ManageHomePage() {
  const lecturerId = await currentLecturerId();
  if (!lecturerId) {
    return (
      <div className="space-y-6">
        <PageHeader title="ระบบจัดการ" description="ภาระงานประจำภาคและข้อมูลอาจารย์" />
        <Notice>เริ่มจากเลือกว่าจะใช้งานในนามอาจารย์ท่านไหน</Notice>
        <Link href="/manage/switch-user" className={buttonClass}>
          เลือกผู้ใช้งาน
        </Link>
      </div>
    );
  }

  const [me, mine, rounds] = await Promise.all([
    getMe(),
    listSubmissions({ lecturer_id: lecturerId }),
    listRounds(),
  ]);
  const roundName = new Map(rounds.items.map((round) => [round.id, round.name_th]));
  const roundsWithoutSubmission = me.open_rounds.filter(
    (round) => !mine.items.some((submission) => submission.round_id === round.id)
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title={`สวัสดี ${me.lecturer.name_th}`}
        description={[me.lecturer.rank, me.lecturer.email].filter(Boolean).join(' · ')}
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="ตำแหน่งที่ดำรงอยู่" description="มาจากเมนู อาจารย์ → ตำแหน่งบริหาร">
          {me.positions.length === 0 ? (
            <EmptyNote>ไม่มีตำแหน่งบริหาร</EmptyNote>
          ) : (
            <ul className="space-y-2 text-sm">
              {me.positions.map((position) => (
                <li key={position.id} className="flex justify-between gap-3">
                  <span className="font-medium text-ink">{POSITION_LABEL[position.position]}</span>
                  <span className="text-ink-muted">ตั้งแต่ {formatDate(position.start_date)}</span>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-4 text-xs text-ink-muted">ลงนามในใบภาระงานได้ในฐานะ</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {me.signer_roles.map((role) => (
              <Badge key={role}>{SIGNER_ROLE_LABEL[role]}</Badge>
            ))}
          </div>
        </Section>

        <Section title="รอบประเมินที่เปิดอยู่">
          {me.open_rounds.length === 0 ? (
            <EmptyNote>ยังไม่มีรอบที่เปิดให้กรอก</EmptyNote>
          ) : (
            <ul className="space-y-2 text-sm">
              {me.open_rounds.map((round) => (
                <li key={round.id} className="flex justify-between gap-3">
                  <span className="font-medium text-ink">{round.name_th}</span>
                  <span className="text-ink-muted">
                    ส่งภายใน {round.submit_due_at ? formatDate(round.submit_due_at) : '–'}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {roundsWithoutSubmission.length > 0 ? (
            <ActionForm action={createSubmission} submitLabel="สร้างใบภาระงาน" className="mt-4 space-y-3">
              <Field label="สร้างใบภาระงานของฉันสำหรับรอบ">
                <select name="round_id" className={inputClass} required>
                  {roundsWithoutSubmission.map((round) => (
                    <option key={round.id} value={round.id}>
                      {round.name_th}
                    </option>
                  ))}
                </select>
              </Field>
            </ActionForm>
          ) : null}
        </Section>
      </div>

      <Section title="ใบภาระงานของฉัน">
        {mine.items.length === 0 ? (
          <EmptyNote>ยังไม่มีใบภาระงาน</EmptyNote>
        ) : (
          <Table head={['รอบ', 'สถานะ', 'คะแนนหลังตัดเพดาน', 'หน่วยกิตสอน', '']}>
            {mine.items.map((submission) => (
              <tr key={submission.id}>
                <Td>{roundName.get(submission.round_id) ?? `รอบ #${submission.round_id}`}</Td>
                <Td>
                  <StatusBadge status={submission.status} />
                </Td>
                <Td>{formatScore(submission.capped_total)}</Td>
                <Td>{formatScore(submission.teaching_credits)}</Td>
                <Td>
                  <Link href={`/manage/submissions/${submission.id}`} className={linkClass}>
                    เปิด
                  </Link>
                </Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>
    </div>
  );
}
