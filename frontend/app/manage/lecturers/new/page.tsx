import type { Metadata } from 'next';

import { createLecturer } from '@/app/manage/actions/people';
import { ActionForm } from '@/components/manage/action-form';
import { LecturerFields } from '@/components/manage/lecturer-fields';
import { Notice, PageHeader, Section } from '@/components/manage/ui';
import { leaveIfLecturerOnly } from '@/lib/auth/guards';
import { canManage } from '@/lib/auth/permissions';
import { listDepartments } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'เพิ่มอาจารย์' };

export default async function NewLecturerPage() {
  await leaveIfLecturerOnly();
  const [departments, me] = await Promise.all([listDepartments(true), getCurrentUser()]);
  return (
    <div className="space-y-6">
      <PageHeader title="เพิ่มอาจารย์" back={{ href: '/manage/lecturers', label: 'รายชื่ออาจารย์' }} />
      {canManage(me) ? (
        <Section title="ข้อมูลทั่วไป">
          <ActionForm action={createLecturer} submitLabel="เพิ่มอาจารย์">
            <LecturerFields departments={departments.items} />
          </ActionForm>
        </Section>
      ) : (
        <Notice tone="error">เพิ่มอาจารย์ได้เฉพาะเจ้าหน้าที่</Notice>
      )}
    </div>
  );
}
