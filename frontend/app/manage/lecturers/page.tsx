import type { Metadata } from 'next';
import Link from 'next/link';

import {
  Badge,
  EmptyNote,
  PageHeader,
  Pager,
  Table,
  Td,
  buttonClass,
  inputClass,
  intParam,
  linkClass,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { leaveToOwnProfile } from '@/lib/auth/guards';
import { canManage } from '@/lib/auth/permissions';
import { PAGE_SIZE, listDepartments, listLecturers } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'อาจารย์' };

export default async function LecturersPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  await leaveToOwnProfile();
  const params = await searchParams;
  const q = param(params.q);
  const departmentId = intParam(params.department_id);
  const active = param(params.is_active);
  const offset = intParam(params.offset) ?? 0;

  const [lecturers, departments, me] = await Promise.all([
    listLecturers({
      q,
      department_id: departmentId,
      is_active: active === undefined || active === '' ? undefined : active === 'true',
      limit: PAGE_SIZE,
      offset,
    }),
    listDepartments(),
    getCurrentUser(),
  ]);
  const departmentName = new Map(departments.items.map((d) => [d.id, d.name_th]));

  return (
    <div className="space-y-6">
      <PageHeader
        title="อาจารย์"
        description="ข้อมูลอาจารย์ สาขา ตำแหน่งบริหาร และข้อมูลวิชาการ"
        actions={
          canManage(me) ? (
            <Link href="/manage/lecturers/new" className={buttonClass}>
              + เพิ่มอาจารย์
            </Link>
          ) : null
        }
      />

      <form role="search" className="grid gap-2 sm:grid-cols-[1fr_12rem_10rem_auto]">
        <input name="q" defaultValue={q} placeholder="ค้นหาชื่อหรืออีเมล" className={inputClass} />
        <select name="department_id" defaultValue={departmentId ?? ''} className={inputClass} aria-label="สาขาวิชา">
          <option value="">ทุกสาขา</option>
          {departments.items.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name_th}
            </option>
          ))}
        </select>
        <select name="is_active" defaultValue={active ?? ''} className={inputClass} aria-label="สถานะ">
          <option value="">ทุกสถานะ</option>
          <option value="true">เปิดใช้งาน</option>
          <option value="false">ปิดใช้งาน</option>
        </select>
        <button type="submit" className={secondaryButtonClass}>
          ค้นหา
        </button>
      </form>

      {lecturers.items.length === 0 ? (
        <EmptyNote>ไม่พบอาจารย์</EmptyNote>
      ) : (
        <Table head={['ชื่อ', 'ตำแหน่งทางวิชาการ', 'สาขา', 'อีเมล', 'สถานะ', '']}>
          {lecturers.items.map((lecturer) => (
            <tr key={lecturer.lecturer_id}>
              <Td className="font-medium text-ink">{lecturer.name_th}</Td>
              <Td>{lecturer.rank ?? '–'}</Td>
              <Td>{departmentName.get(lecturer.department_id ?? -1) ?? '–'}</Td>
              <Td>{lecturer.email}</Td>
              <Td>
                {lecturer.is_active ? (
                  <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">เปิดใช้งาน</Badge>
                ) : (
                  <Badge>ปิดใช้งาน</Badge>
                )}
              </Td>
              <Td>
                <Link href={`/manage/lecturers/${lecturer.lecturer_id}`} className={linkClass}>
                  จัดการ
                </Link>
              </Td>
            </tr>
          ))}
        </Table>
      )}
      <Pager
        total={lecturers.meta.total}
        limit={PAGE_SIZE}
        offset={offset}
        hrefFor={(next) =>
          withQuery('/manage/lecturers', { q, department_id: departmentId, is_active: active, offset: next })
        }
      />
    </div>
  );
}
