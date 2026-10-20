import type { Metadata } from 'next';
import Link from 'next/link';

import { createPublication } from '@/app/manage/actions/academic';
import { ActionForm } from '@/components/manage/action-form';
import { PublicationFields } from '@/components/manage/publication-fields';
import {
  EmptyNote,
  PageHeader,
  Pager,
  Section,
  Table,
  Td,
  inputClass,
  intParam,
  linkClass,
  param,
  secondaryButtonClass,
  withQuery,
} from '@/components/manage/ui';
import { PAGE_SIZE, listPublications } from '@/lib/backend/api';

export const metadata: Metadata = { title: 'ผลงานตีพิมพ์' };

export default async function PublicationsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const q = param(params.q);
  const year = intParam(params.publication_year);
  const offset = intParam(params.offset) ?? 0;
  const publications = await listPublications({ q, publication_year: year, limit: PAGE_SIZE, offset });

  return (
    <div className="space-y-6">
      <PageHeader title="ผลงานตีพิมพ์" description="รายการผลงานกลาง (DOI ห้ามซ้ำ)" />

      <Section title={`ผลงานทั้งหมด (${publications.meta.total})`}>
        <form role="search" className="mb-4 grid gap-2 sm:grid-cols-[1fr_8rem_auto]">
          <input name="q" defaultValue={q} placeholder="ค้นหาชื่อ แหล่งตีพิมพ์ หรือ DOI" className={inputClass} />
          <input name="publication_year" type="number" defaultValue={year} placeholder="ปี" className={inputClass} aria-label="ปี" />
          <button type="submit" className={secondaryButtonClass}>ค้นหา</button>
        </form>
        {publications.items.length === 0 ? (
          <EmptyNote>ไม่พบผลงาน</EmptyNote>
        ) : (
          <Table head={['ชื่อผลงาน', 'ปี', 'แหล่งตีพิมพ์', 'DOI']}>
            {publications.items.map((publication) => (
              <tr key={publication.publication_id}>
                <Td>
                  <Link href={`/manage/publications/${publication.publication_id}`} className={linkClass}>
                    {publication.title}
                  </Link>
                </Td>
                <Td>{publication.publication_year ?? '–'}</Td>
                <Td>{publication.venue ?? '–'}</Td>
                <Td className="break-all">{publication.doi ?? '–'}</Td>
              </tr>
            ))}
          </Table>
        )}
        <Pager
          total={publications.meta.total}
          limit={PAGE_SIZE}
          offset={offset}
          hrefFor={(next) => withQuery('/manage/publications', { q, publication_year: year, offset: next })}
        />
      </Section>

      <Section title="เพิ่มผลงาน">
        <ActionForm action={createPublication} submitLabel="เพิ่มผลงาน">
          <PublicationFields />
        </ActionForm>
      </Section>
    </div>
  );
}
