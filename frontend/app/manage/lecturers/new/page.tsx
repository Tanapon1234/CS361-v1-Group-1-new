import type { Metadata } from 'next';

import { createLecturer } from '@/app/manage/actions/people';
import { ActionForm } from '@/components/manage/action-form';
import { LecturerFields } from '@/components/manage/lecturer-fields';
import { PageHeader, Section } from '@/components/manage/ui';
import { listDepartments } from '@/lib/backend/api';

export const metadata: Metadata = { title: 'เพิ่มอาจารย์' };

export default async function NewLecturerPage() {
  const departments = await listDepartments(true);
  return (
    <div className="space-y-6">
      <PageHeader title="เพิ่มอาจารย์" back={{ href: '/manage/lecturers', label: 'รายชื่ออาจารย์' }} />
      <Section title="ข้อมูลทั่วไป">
        <ActionForm action={createLecturer} submitLabel="เพิ่มอาจารย์">
          <LecturerFields departments={departments.items} />
        </ActionForm>
      </Section>
    </div>
  );
}
