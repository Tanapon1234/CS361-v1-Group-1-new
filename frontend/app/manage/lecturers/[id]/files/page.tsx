import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import {
  deleteLecturerFile,
  finishLecturerFileUpload,
  startLecturerFileUpload,
} from '@/app/manage/actions/academic';
import { ActionForm } from '@/components/manage/action-form';
import { FileUpload } from '@/components/manage/file-upload';
import { LecturerHeader } from '@/components/manage/lecturer-tabs';
import { Notice, Section, linkClass } from '@/components/manage/ui';
import { canEditLecturer } from '@/lib/auth/permissions';
import { getLecturer } from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';

export const metadata: Metadata = { title: 'รูปและ CV' };

export default async function LecturerFilesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [lecturer, me] = await Promise.all([getLecturer(id), getCurrentUser()]);
  if (!lecturer) notFound();
  const editable = canEditLecturer(me, id);

  return (
    <div className="space-y-6">
      <LecturerHeader lecturer={lecturer} current={`/manage/lecturers/${id}/files`} />
      {!editable ? (
        <Notice>ดูได้อย่างเดียว: แก้ไขได้เฉพาะเจ้าของข้อมูลหรือเจ้าหน้าที่</Notice>
      ) : null}
      {/* Disabled for viewers: every input and button inside is off (the backend checks too) */}
      <fieldset disabled={!editable} className="m-0 min-w-0 space-y-6 border-0 p-0">
        <Notice>
          ไฟล์อัปโหลดตรงจาก browser ไป S3 ด้วย presigned URL (ต้องตั้ง DATA_BUCKET_NAME และ CORS ของ bucket
          ฝั่ง backend) รูปรับ JPEG / PNG / WebP ไม่เกิน 5 MB ส่วน CV รับ PDF ไม่เกิน 10 MB
        </Notice>

        <Section title="รูปประจำตัว">
          {lecturer.profile_image_url ? (
            // The column holds an S3 key; this route redirects to a short-lived URL
            // eslint-disable-next-line @next/next/no-img-element -- signed S3 URL, not worth the image optimizer
            <img
              src={`/manage/lecturers/${id}/profile-image?v=${encodeURIComponent(lecturer.profile_image_url)}`}
              alt={`รูปประจำตัวของ ${lecturer.name_th}`}
              className="mb-4 h-32 w-32 rounded-xl border border-line object-cover"
            />
          ) : (
            <p className="mb-4 text-sm text-ink-muted">ยังไม่มีรูป</p>
          )}
          <FileUpload
            accept="image/jpeg,image/png,image/webp"
            start={startLecturerFileUpload.bind(null, id, 'profile-image')}
            finish={finishLecturerFileUpload.bind(null, id, 'profile-image')}
            submitLabel="อัปโหลดรูป"
          />
          {lecturer.profile_image_url ? (
            <div className="mt-3">
              <ActionForm
                inline
                variant="danger"
                submitLabel="ลบรูป"
                confirmText="ลบรูปประจำตัว?"
                action={deleteLecturerFile.bind(null, id, 'profile-image')}
              />
            </div>
          ) : null}
        </Section>

        <Section title="CV">
          <p className="mb-4 text-sm">
            <a href={`/manage/lecturers/${id}/cv`} className={linkClass}>
              ดาวน์โหลด CV ปัจจุบัน
            </a>{' '}
            <span className="text-ink-muted">(ถ้ายังไม่มี จะขึ้นข้อความแจ้ง)</span>
          </p>
          <FileUpload
            accept="application/pdf"
            start={startLecturerFileUpload.bind(null, id, 'cv')}
            finish={finishLecturerFileUpload.bind(null, id, 'cv')}
            submitLabel="อัปโหลด CV"
          />
          <div className="mt-3">
            <ActionForm
              inline
              variant="danger"
              submitLabel="ลบ CV"
              confirmText="ลบ CV?"
              action={deleteLecturerFile.bind(null, id, 'cv')}
            />
          </div>
        </Section>
      </fieldset>
    </div>
  );
}
