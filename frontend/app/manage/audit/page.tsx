import type { Metadata } from 'next';

import {
  Badge,
  EmptyNote,
  Notice,
  PageHeader,
  Pager,
  Section,
  Table,
  Td,
  inputClass,
  intParam,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { isAdmin } from '@/lib/auth/permissions';
import { PAGE_SIZE, listAuditLog, listLecturers, MAX_PAGE, settle } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import { formatDateTime } from '@/lib/backend/labels';

export const metadata: Metadata = { title: 'ประวัติการแก้ไข' };

const ACTION_LABEL = { insert: 'เพิ่ม', update: 'แก้ไข', delete: 'ลบ' } as const;

export default async function AuditPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  if (!isAdmin(await getCurrentUser())) {
    return (
      <div className="space-y-6">
        <PageHeader title="ประวัติการแก้ไข" />
        <Notice tone="error">หน้านี้สำหรับผู้ดูแลระบบเท่านั้น</Notice>
      </div>
    );
  }
  const params = await searchParams;
  const entity = param(params.entity) || undefined;
  const entityId = param(params.entity_id) || undefined;
  const actorId = param(params.actor_id) || undefined;
  const offset = intParam(params.offset) ?? 0;
  const [log, lecturers] = await Promise.all([
    settle(listAuditLog({ entity, entity_id: entityId, actor_id: actorId, offset })),
    listLecturers({ limit: MAX_PAGE }),
  ]);
  const names = new Map(lecturers.items.map((l) => [l.lecturer_id, l.name_th]));

  return (
    <div className="space-y-6">
      <PageHeader title="ประวัติการแก้ไข" description="ใครแก้อะไรเมื่อไร (ใหม่สุดก่อน) บันทึกอัตโนมัติทุกครั้งที่ข้อมูลเปลี่ยน" />
      <form role="search" className="grid gap-2 sm:grid-cols-[1fr_1fr_1fr_auto]">
        <input name="entity" defaultValue={entity} placeholder="ตาราง เช่น publication" className={inputClass} aria-label="ตาราง" />
        <input name="entity_id" defaultValue={entityId} placeholder="รหัสแถว" className={inputClass} aria-label="รหัสแถว" />
        <select name="actor_id" defaultValue={actorId ?? ''} className={inputClass} aria-label="ผู้แก้ไข">
          <option value="">ทุกคน</option>
          {lecturers.items.map((l) => (
            <option key={l.lecturer_id} value={l.lecturer_id}>{l.name_th}</option>
          ))}
        </select>
        <button type="submit" className={secondaryButtonClass}>ค้นหา</button>
      </form>
      <Section title={`รายการ (${log.data?.meta.total ?? 0})`}>
        {log.error ? (
          <Notice tone="error">{log.error}</Notice>
        ) : log.data?.items.length === 0 ? (
          <EmptyNote>ไม่พบรายการ</EmptyNote>
        ) : (
          <Table head={['เวลา', 'ผู้แก้ไข', 'การกระทำ', 'ข้อมูล', 'รายละเอียด']}>
            {log.data?.items.map((row) => (
              <tr key={row.id}>
                <Td className="whitespace-nowrap">{formatDateTime(row.occurred_at)}</Td>
                <Td>
                  {row.actor_id ? names.get(row.actor_id) ?? row.actor_id : 'script'}
                  <p className="text-xs text-ink-muted">{row.actor_roles}</p>
                </Td>
                <Td><Badge>{ACTION_LABEL[row.action]}</Badge></Td>
                <Td>
                  {row.entity}
                  <p className="text-xs break-all text-ink-muted">{row.entity_id}</p>
                </Td>
                <Td>
                  <details>
                    <summary className="cursor-pointer text-xs text-brand">{row.request ?? 'ดู'}</summary>
                    <pre className="mt-2 max-h-60 overflow-auto rounded bg-surface-alt p-2 text-xs">
                      {JSON.stringify(row.changes, null, 2)}
                    </pre>
                  </details>
                </Td>
              </tr>
            ))}
          </Table>
        )}
        {log.data ? (
          <Pager
            total={log.data.meta.total}
            limit={PAGE_SIZE}
            offset={offset}
            hrefFor={(next) => withQuery('/manage/audit', { entity, entity_id: entityId, actor_id: actorId, offset: next })}
          />
        ) : null}
      </Section>
    </div>
  );
}
