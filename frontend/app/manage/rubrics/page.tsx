import type { Metadata } from 'next';
import Link from 'next/link';

import { createRubricVersion } from '@/app/manage/actions/rubric';
import { ActionForm } from '@/components/manage/action-form';
import { Badge, EmptyNote, Field, PageHeader, Section, Table, Td, inputClass, linkClass } from '@/components/manage/ui';
import { canManage } from '@/lib/auth/permissions';
import { listRounds, listRubricVersions } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDate, formatNumber } from '@/lib/backend/labels';

export const metadata: Metadata = { title: 'เกณฑ์ภาระงาน' };

export default async function RubricsPage() {
  const [versions, rounds, me] = await Promise.all([
    listRubricVersions(),
    listRounds(),
    getCurrentUser(),
  ]);
  const usedVersions = new Set(rounds.items.map((round) => round.rubric_version_id));

  return (
    <div className="space-y-6">
      <PageHeader
        title="เกณฑ์ภาระงาน"
        description="เกณฑ์มีหลายฉบับ ฉบับที่รอบประเมินใช้แล้วจะถูกล็อก ถ้าจะแก้ให้สร้างฉบับใหม่โดยคัดลอกจากฉบับเดิม"
      />

      <Section title="ฉบับทั้งหมด">
        {versions.items.length === 0 ? (
          <EmptyNote>ยังไม่มีเกณฑ์</EmptyNote>
        ) : (
          <Table head={['รหัสฉบับ', 'อนุมัติในการประชุม', 'คะแนนฐาน', 'เพดานรวม', 'ขั้นต่ำ', 'สถานะ', '']}>
            {versions.items.map((version) => (
              <tr key={version.id}>
                <Td className="font-medium text-ink">{version.code}</Td>
                <Td>
                  {version.approved_meeting ?? '–'}
                  {version.approved_on ? ` (${formatDate(version.approved_on)})` : ''}
                </Td>
                <Td>{formatNumber(version.base_points)}</Td>
                <Td>{formatNumber(version.overall_cap)}</Td>
                <Td>{formatNumber(version.min_required)}</Td>
                <Td className="space-x-1">
                  {version.is_active ? <Badge>ใช้งาน</Badge> : <Badge>ปิด</Badge>}
                  {usedVersions.has(version.id) ? (
                    <Badge className="border-amber-200 bg-amber-50 text-amber-800">ล็อก</Badge>
                  ) : null}
                </Td>
                <Td>
                  <Link href={`/manage/rubrics/${version.id}`} className={linkClass}>
                    เปิด
                  </Link>
                </Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>

      {canManage(me) ? (
        <Section title="สร้างฉบับใหม่">
          <ActionForm action={createRubricVersion} submitLabel="สร้างฉบับ">
            <div className="grid gap-4 sm:grid-cols-4">
              <Field label="รหัสฉบับ *">
                <input name="code" required maxLength={30} placeholder="2568-r1" className={inputClass} />
              </Field>
              <Field label="อนุมัติในการประชุมครั้งที่">
                <input name="approved_meeting" maxLength={50} placeholder="6/2567" className={inputClass} />
              </Field>
              <Field label="วันที่อนุมัติ">
                <input name="approved_on" type="date" className={inputClass} />
              </Field>
              <Field label="คัดลอกโครงจากฉบับ">
                <select name="source_version_id" className={inputClass}>
                  <option value="">— เริ่มจากว่าง —</option>
                  {versions.items.map((version) => (
                    <option key={version.id} value={version.id}>{version.code}</option>
                  ))}
                </select>
              </Field>
              <Field label="คะแนนฐาน" hint="ค่าเริ่มต้น 200">
                <input name="base_points" type="number" step="0.01" placeholder="200" className={inputClass} />
              </Field>
              <Field label="เพดานรวม" hint="ค่าเริ่มต้น 2000">
                <input name="overall_cap" type="number" step="0.01" placeholder="2000" className={inputClass} />
              </Field>
              <Field label="คะแนนขั้นต่ำ" hint="ค่าเริ่มต้น 650">
                <input name="min_required" type="number" step="0.01" placeholder="650" className={inputClass} />
              </Field>
              <Field label="หน่วยกิตสอนขั้นต่ำ" hint="ค่าเริ่มต้น 6">
                <input name="min_teaching_credits" type="number" step="0.01" placeholder="6" className={inputClass} />
              </Field>
            </div>
          </ActionForm>
        </Section>
      ) : null}
    </div>
  );
}
