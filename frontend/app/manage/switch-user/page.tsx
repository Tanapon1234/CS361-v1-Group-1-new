import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { switchUser } from '@/app/manage/actions/session';
import { EmptyNote, Notice, PageHeader, Pager, inputClass, intParam, param, secondaryButtonClass, withQuery } from '@/components/manage/ui';
import { PAGE_SIZE, listDepartments, listLecturers } from '@/lib/backend/api';
import { cognitoEnabled } from '@/lib/auth/cognito';
import { currentLecturerId } from '@/lib/backend/client';

const ROLE_CHOICES = [
  ['staff', 'เจ้าหน้าที่'],
  ['reviewer', 'ผู้ตรวจสอบ'],
  ['executive', 'ผู้บริหาร'],
  ['admin', 'ผู้ดูแลระบบ'],
] as const;

export const metadata: Metadata = { title: 'เลือกผู้ใช้งาน' };

export default async function SwitchUserPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  // With Cognito, people sign in for real
  if (cognitoEnabled()) redirect('/login');
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
        description="โหมดพัฒนา (ยังไม่ได้ตั้ง COGNITO_CLIENT_ID): เลือกว่าจะทำงานในนามอาจารย์ท่านไหน และมีบทบาทอะไรเพิ่ม"
      />
      <Notice>
        ระบบส่งเป็น header X-Lecturer-Id และ X-Dev-Roles ซึ่ง backend เช็คสิทธิ์ตามบทบาทจริง
        (docs/v2/permissions.md) และไม่รับ header นี้ใน production
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
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
                    {ROLE_CHOICES.map(([value, label]) => (
                      <label key={value} className="flex items-center gap-1 text-xs text-ink-muted">
                        <input type="checkbox" name="roles" value={value} className="h-3.5 w-3.5 accent-brand" />
                        {label}
                      </label>
                    ))}
                  </div>
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
