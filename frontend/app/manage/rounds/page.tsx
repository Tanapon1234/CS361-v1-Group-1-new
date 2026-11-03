import type { Metadata } from 'next';
import Link from 'next/link';

import { createRound } from '@/app/manage/actions/workload';
import { ActionForm } from '@/components/manage/action-form';
import { RoundFields } from '@/components/manage/round-fields';
import { Badge, EmptyNote, Notice, PageHeader, Section, StatusBadge, Table, Td, linkClass } from '@/components/manage/ui';
import { canManage, isLecturerOnly } from '@/lib/auth/permissions';
import { listRounds, listRubricVersions, listSubmissions } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDate, formatDateTime } from '@/lib/backend/labels';

export const metadata: Metadata = { title: 'รอบประเมิน' };

export default async function RoundsPage() {
  const [rounds, versions, me] = await Promise.all([
    listRounds(),
    listRubricVersions(),
    getCurrentUser(),
  ]);
  const versionCode = new Map(versions.items.map((v) => [v.id, v.code]));
  // A plain lecturer only looks: which rounds exist and where their own sheet stands
  const ownOnly = isLecturerOnly(me);
  const mine = ownOnly && me ? await listSubmissions({ lecturer_id: me.lecturer.lecturer_id }) : null;
  const myByRound = new Map((mine?.items ?? []).map((submission) => [submission.round_id, submission]));

  return (
    <div className="space-y-6">
      <PageHeader
        title="รอบประเมิน"
        description={
          ownOnly
            ? 'ดูว่ามีรอบไหนบ้างและใบภาระงานของคุณในแต่ละรอบ (แก้ไขรอบไม่ได้)'
            : 'เปิด/ปิดรอบ ดูใบภาระงานในรอบ และสรุปคะแนน'
        }
      />

      <Section title="รอบทั้งหมด">
        {rounds.items.length === 0 ? (
          <EmptyNote>ยังไม่มีรอบ</EmptyNote>
        ) : (
          <Table head={['รอบ', 'ช่วงผลงาน', ownOnly ? 'ใบภาระงานของฉัน' : 'เกณฑ์', 'กำหนดส่ง', 'สถานะ', '']}>
            {rounds.items.map((round) => (
              <tr key={round.id}>
                <Td className="font-medium text-ink">{round.name_th}</Td>
                <Td>
                  {formatDate(round.period_start)} – {formatDate(round.period_end)}
                </Td>
                <Td>
                  {ownOnly ? (
                    myByRound.get(round.id) ? (
                      <StatusBadge status={myByRound.get(round.id)!.status} />
                    ) : (
                      <span className="text-ink-muted">ยังไม่ได้สร้าง</span>
                    )
                  ) : (
                    (versionCode.get(round.rubric_version_id) ?? '–')
                  )}
                </Td>
                <Td>{formatDateTime(round.submit_due_at)}</Td>
                <Td>
                  {round.is_open ? (
                    <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">เปิดกรอก</Badge>
                  ) : (
                    <Badge>ปิด</Badge>
                  )}
                </Td>
                <Td>
                  <Link href={`/manage/rounds/${round.id}`} className={linkClass}>
                    เปิด
                  </Link>
                </Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>

      {canManage(me) ? (
        <Section title="เปิดรอบใหม่">
          {versions.items.length === 0 ? (
            <Notice>
              ต้องมีเกณฑ์ภาระงานก่อน สร้างได้ที่{' '}
              <Link href="/manage/rubrics" className={linkClass}>เกณฑ์ภาระงาน</Link>
            </Notice>
          ) : (
            <ActionForm action={createRound} submitLabel="สร้างรอบ">
              <RoundFields versions={versions.items} />
            </ActionForm>
          )}
        </Section>
      ) : null}
    </div>
  );
}
