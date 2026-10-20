import type { Metadata } from 'next';

import { switchUser } from '@/app/manage/actions/session';
import { EmptyNote, Notice, PageHeader, Pager, inputClass, intParam, param, secondaryButtonClass, withQuery } from '@/components/manage/ui';
import { PAGE_SIZE, listDepartments, listLecturers } from '@/lib/backend/api';
import { currentLecturerId } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'เลือกผู้ใช้งาน' };

export default async function SwitchUserPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const q = param(params.q);
  const offset = intParam(params.offset) ?? 0;
  const [lecturers, departments, current] = await Promise.all([
    listLecturers({ q, is_active: true, limit: PAGE_SIZE, offset }),
    listDepartments(),
    currentLecturerId(),
  ]);
  const departmentName = new Map(departments.items.map((d) => [d.id, d.name_th]));

  return (
    <div className="space-y-6">
      <PageHeader
        title="เลือกผู้ใช้งาน"
        description="ใช้ชั่วคราวจนกว่าจะต่อ Cognito: เลือกว่าจะทำงานในนามอาจารย์ท่านไหน (ระบบส่งเป็น header X-Lecturer-Id ไปที่ backend)"
      />
      <Notice>
        สิทธิ์การใช้งานจริงยังไม่ได้เช็คใน backend (TODO(auth)) ยกเว้นการประเมินที่เช็คตำแหน่งบริหารแล้ว
      </Notice>

      <form className="flex gap-2" role="search">
        <input name="q" defaultValue={q} placeholder="ค้นหาชื่อหรืออีเมล" className={inputClass} />
        <button type="submit" className={secondaryButtonClass}>
          ค้นหา
        </button>
      </form>

      {lecturers.items.length === 0 ? (
        <EmptyNote>ไม่พบอาจารย์ที่เปิดใช้งาน เพิ่มได้ที่เมนู &quot;อาจารย์&quot;</EmptyNote>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {lecturers.items.map((lecturer) => (
            <li key={lecturer.lecturer_id}>
              <form
                action={switchUser}
                className={`flex items-center justify-between gap-3 rounded-xl border p-4 ${
                  lecturer.lecturer_id === current ? 'border-brand bg-brand-soft' : 'border-line'
                }`}
              >
                <input type="hidden" name="lecturer_id" value={lecturer.lecturer_id} />
                <div className="min-w-0">
                  <p className="truncate font-semibold text-ink">{lecturer.name_th}</p>
                  <p className="truncate text-xs text-ink-muted">
                    {[lecturer.rank, departmentName.get(lecturer.department_id ?? -1), lecturer.email]
                      .filter(Boolean)
                      .join(' · ')}
                  </p>
                </div>
                <button type="submit" className={secondaryButtonClass}>
                  {lecturer.lecturer_id === current ? 'กำลังใช้งาน' : 'ใช้ชื่อนี้'}
                </button>
              </form>
            </li>
          ))}
        </ul>
      )}
      <Pager
        total={lecturers.meta.total}
        limit={PAGE_SIZE}
        offset={offset}
        hrefFor={(next) => withQuery('/manage/switch-user', { q, offset: next })}
      />
    </div>
  );
}
