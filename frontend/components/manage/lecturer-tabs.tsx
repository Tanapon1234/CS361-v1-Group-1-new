import { Badge, PageHeader, Tabs } from '@/components/manage/ui';
import type { Lecturer } from '@/types/backend';

/** Header + tabs shared by the three /manage/lecturers/[id] pages */
export function LecturerHeader({ lecturer, current }: { lecturer: Lecturer; current: string }) {
  const base = `/manage/lecturers/${lecturer.lecturer_id}`;
  return (
    <>
      <PageHeader
        title={lecturer.name_th}
        description={[lecturer.name_en, lecturer.rank, lecturer.email].filter(Boolean).join(' · ')}
        back={{ href: '/manage/lecturers', label: 'รายชื่ออาจารย์' }}
        actions={
          lecturer.is_active ? (
            <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">เปิดใช้งาน</Badge>
          ) : (
            <Badge>ปิดใช้งาน</Badge>
          )
        }
      />
      <Tabs
        current={current}
        items={[
          { href: base, label: 'ข้อมูลทั่วไปและตำแหน่ง' },
          { href: `${base}/academic`, label: 'ข้อมูลวิชาการ' },
          { href: `${base}/files`, label: 'รูปและ CV' },
        ]}
      />
    </>
  );
}
