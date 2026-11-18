import type { Metadata } from 'next';
import Link from 'next/link';

import {
  Badge,
  Notice,
  PageHeader,
  Section,
  buttonClass,
  secondaryButtonClass,
} from '@/components/manage/ui';
import { CategoryLegend, YearStackedChart } from '@/components/manage/work-charts';
import { RoundSheetList } from '@/components/manage/round-sheet-list';
import { canCreateSubmission } from '@/lib/auth/permissions';
import { getLecturerWork, getMe, listRoundsWithState, listSubmissions, settle } from '@/lib/backend/api';
import { currentLecturerId } from '@/lib/backend/client';
import {
  POSITION_LABEL,
  SIGNER_ROLE_LABEL,
  formatDate,
} from '@/lib/backend/labels';
import { summarizeWork } from '@/lib/work-summary';

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

  const [me, mine, rounds, work] = await Promise.all([
    getMe(),
    listSubmissions({ lecturer_id: lecturerId }),
    listRoundsWithState(),
    settle(getLecturerWork(lecturerId, {})),
  ]);
  const summary = work.data ? summarizeWork(work.data) : null;
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

      {summary && summary.years.length > 0 ? (
        <Section
          title="สรุปผลงานของฉัน"
          description="คะแนนรายปีการศึกษา แบ่งตามหมวด นับเฉพาะใบที่ส่งแล้ว"
          actions={
            <Link href="/manage/summary" className={secondaryButtonClass}>
              ดูสรุปเชิงลึก
            </Link>
          }
        >
          <div className="space-y-4 rounded-2xl border border-line bg-surface p-5">
            <YearStackedChart summary={summary} />
            <CategoryLegend summary={summary} years={summary.years.slice(-8)} />
          </div>
        </Section>
      ) : null}

      <Section
        title="รอบประเมินของฉัน"
        description="รอบที่เปิดรับอยู่ และรอบที่ฉันมีใบภาระงานแล้ว"
      >
        <RoundSheetList rounds={rounds} mine={mine.items} mayCreate={mayCreate} />
      </Section>
    </div>
  );
}
