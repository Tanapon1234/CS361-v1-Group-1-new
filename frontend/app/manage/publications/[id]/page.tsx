import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { deletePublication, updatePublication } from '@/app/manage/actions/academic';
import { ActionForm } from '@/components/manage/action-form';
import { PublicationFields } from '@/components/manage/publication-fields';
import { PageHeader, Section } from '@/components/manage/ui';
import { getPublication } from '@/lib/backend/api';

export const metadata: Metadata = { title: 'แก้ไขผลงาน' };

export default async function PublicationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const publicationId = Number.parseInt(id, 10);
  const publication = Number.isFinite(publicationId) ? await getPublication(publicationId) : null;
  if (!publication) notFound();

  return (
    <div className="space-y-6">
      <PageHeader
        title={publication.title}
        back={{ href: '/manage/publications', label: 'ผลงานตีพิมพ์' }}
        actions={
          <ActionForm
            inline
            variant="danger"
            submitLabel="ลบผลงาน"
            confirmText="ลบผลงานนี้? การผูกกับอาจารย์ทุกคนจะหายไปด้วย"
            action={deletePublication.bind(null, publicationId)}
          />
        }
      />
      <Section title="ข้อมูลผลงาน">
        <ActionForm action={updatePublication.bind(null, publicationId)}>
          <PublicationFields publication={publication} />
        </ActionForm>
      </Section>
    </div>
  );
}
