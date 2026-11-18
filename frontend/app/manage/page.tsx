import type { Metadata } from 'next';
import Link from 'next/link';

import { createSubmission } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { RoundStatusMark, roundStatusRail } from '@/components/manage/round-status';
import {
  Badge,
  EmptyNote,
  Notice,
  PageHeader,
  Section,
  StatusBadge,
  buttonClass,
  secondaryButtonClass,
} from '@/components/manage/ui';
import { canCreateSubmission } from '@/lib/auth/permissions';
import { getMe, listRoundsWithState, listSubmissions } from '@/lib/backend/api';
import { currentLecturerId } from '@/lib/backend/client';
import {
  POSITION_LABEL,
  SIGNER_ROLE_LABEL,
  formatDate,
  formatDateTime,
  formatNumber,
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
    listRoundsWithState(),
  ]);
  // One card per round: every round still taking work, plus any closed round where I have a submission
  const mineByRound = new Map(mine.items.map((submission) => [submission.round_id, submission]));
  const myRounds = rounds.filter(({ round, state }) => state !== 'closed' || mineByRound.has(round.id));
  const mayCreate = canCreateSubmission(me);
  // Nothing to say for an ordinary lecturer: no position and only their own signing role
  const showPositions = me.positions.length > 0;
  const signsBeyondOwn = me.signer_roles.some((role) => role !== 'performer');

  return (
    <div className="space-y-6">
      <PageHeader
        title={`สวัสดี ${me.lecturer.name_th}`}
        description={[me.lecturer.rank, me.lecturer.email].filter(Boolean).join(' · ')}
      />

      {showPositions || signsBeyondOwn ? (
        <Section
          title={showPositions ? 'ตำแหน่งที่ดำรงอยู่' : 'สิทธิ์ลงนามของฉัน'}
          description={showPositions ? 'มาจากเมนู อาจารย์ → ตำแหน่งบริหาร' : undefined}
        >
          {showPositions ? (
            <ul className="space-y-2 text-sm">
              {me.positions.map((position) => (
                <li key={position.id} className="flex justify-between gap-3">
                  <span className="font-medium text-ink">{POSITION_LABEL[position.position]}</span>
                  <span className="text-ink-muted">ตั้งแต่ {formatDate(position.start_date)}</span>
                </li>
              ))}
            </ul>
          ) : null}
          <p className={`text-xs text-ink-muted ${showPositions ? 'mt-4' : ''}`}>
            ลงนามในใบภาระงานได้ในฐานะ
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {me.signer_roles.map((role) => (
              <Badge key={role}>{SIGNER_ROLE_LABEL[role]}</Badge>
            ))}
          </div>
        </Section>
      ) : null}

      <Section
        title="รอบประเมินของฉัน"
        description="รอบที่เปิดรับอยู่ และรอบที่ฉันมีใบภาระงานแล้ว"
      >
        {myRounds.length === 0 ? (
          <EmptyNote>ยังไม่มีรอบที่เปิดให้กรอก</EmptyNote>
        ) : (
          <ul className="space-y-4">
            {myRounds.map(({ round, state }) => {
              const submission = mineByRound.get(round.id);
              return (
                <li key={round.id} className={`rounded-xl border border-line ${roundStatusRail(state)}`}>
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 px-4 pt-4">
                    <p className="font-semibold text-ink">{round.name_th}</p>
                    <RoundStatusMark status={state} />
                  </div>
                  <p className="px-4 text-[13px] text-ink-muted">
                    {round.submit_due_at ? `ส่งภายใน ${formatDateTime(round.submit_due_at)}` : 'ไม่กำหนดวันส่ง'}
                  </p>

                  <div className="mt-3 border-t border-line-soft bg-surface-alt px-4 py-3">
                    <p className="text-xs font-medium text-ink-muted">ใบภาระงานของฉัน</p>
                    {submission ? (
                      <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                        <div className="min-w-0 space-y-1">
                          <StatusBadge status={submission.status} />
                          <p className="text-[13px] text-ink-muted">
                            คะแนน {formatScore(submission.capped_total)} · หน่วยกิตสอน{' '}
                            {formatNumber(submission.teaching_credits)}
                          </p>
                        </div>
                        <Link href={`/manage/submissions/${submission.id}`} className={`${secondaryButtonClass} min-h-11 px-4`}>
                          เปิดใบภาระงาน
                        </Link>
                      </div>
                    ) : (
                      <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                        <p className="text-sm text-ink">ยังไม่มีใบภาระงาน</p>
                        {mayCreate && state !== 'closed' ? (
                          <ActionForm inline large action={createSubmission} submitLabel="สร้างใบภาระงาน">
                            <input type="hidden" name="round_id" value={round.id} />
                          </ActionForm>
                        ) : null}
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Section>
    </div>
  );
}
