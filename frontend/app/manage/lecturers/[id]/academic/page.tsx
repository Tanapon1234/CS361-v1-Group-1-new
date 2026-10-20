import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import {
  createEducation,
  createPublicationProfile,
  deleteEducation,
  deletePublicationProfile,
  replaceLecturerExpertise,
  replaceLecturerResearchInterests,
  updateEducation,
  updatePublicationProfile,
} from '@/app/manage/actions/academic';
import { ActionForm } from '@/components/manage/action-form';
import { LecturerHeader } from '@/components/manage/lecturer-tabs';
import { EmptyNote, Field, Notice, Section, Table, Td, inputClass, linkClass } from '@/components/manage/ui';
import { keepToSelf } from '@/lib/auth/guards';
import { canEditLecturer } from '@/lib/auth/permissions';
import {
  MAX_PAGE,
  getLecturer,
  listEducations,
  listExpertise,
  listLecturerExpertise,
  listLecturerPublications,
  listLecturerResearchInterests,
  listPublicationProfiles,
  listResearchInterests,
  settle,
} from '@/lib/backend/api';
import { getCurrentUser } from '@/lib/backend/client';
import type { Education } from '@/types/backend';

export const metadata: Metadata = { title: 'ข้อมูลวิชาการ' };

function EducationInputs({ education }: { education?: Education }) {
  return (
    <div className="grid gap-3 sm:grid-cols-5">
      <input name="degree" placeholder="วุฒิ เช่น Ph.D." defaultValue={education?.degree ?? ''} maxLength={100} className={inputClass} aria-label="วุฒิ" />
      <input name="field" placeholder="สาขา" defaultValue={education?.field ?? ''} maxLength={255} className={inputClass} aria-label="สาขา" />
      <input name="institution" placeholder="สถาบัน" defaultValue={education?.institution ?? ''} maxLength={500} className={inputClass} aria-label="สถาบัน" />
      <input name="country" placeholder="ประเทศ" defaultValue={education?.country ?? ''} maxLength={100} className={inputClass} aria-label="ประเทศ" />
      <input name="graduation_year" placeholder="ปีที่จบ" defaultValue={education?.graduation_year ?? ''} maxLength={10} className={inputClass} aria-label="ปีที่จบ" />
    </div>
  );
}

export default async function LecturerAcademicPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await keepToSelf(id);
  const [lecturer, me] = await Promise.all([getLecturer(id), getCurrentUser()]);
  if (!lecturer) notFound();
  const editable = canEditLecturer(me, id);

  // Each section loads on its own, so one failing call shows a note instead of breaking the page
  const [interests, allInterests, expertise, allExpertise, educations, profiles, publications] =
    await Promise.all([
      settle(listLecturerResearchInterests(id)),
      settle(listResearchInterests({ limit: MAX_PAGE })),
      settle(listLecturerExpertise(id)),
      settle(listExpertise({ limit: MAX_PAGE })),
      settle(listEducations(id)),
      settle(listPublicationProfiles(id)),
      settle(listLecturerPublications(id)),
    ]);
  const chosenInterests = new Set(interests.data?.items.map((i) => i.research_interest_id));
  const chosenExpertise = new Set(expertise.data?.items.map((e) => e.expertise_id));

  return (
    <div className="space-y-6">
      <LecturerHeader lecturer={lecturer} current={`/manage/lecturers/${id}/academic`} />
      {!editable ? (
        <Notice>ดูได้อย่างเดียว: แก้ไขได้เฉพาะเจ้าของข้อมูลหรือเจ้าหน้าที่</Notice>
      ) : null}
      {/* Disabled for viewers: every input and button inside is off (the backend checks too) */}
      <fieldset disabled={!editable} className="m-0 min-w-0 space-y-6 border-0 p-0">

        <Section
          title="หัวข้อวิจัยที่สนใจ"
          description={
            <>
              เลือกจากรายการกลาง (เพิ่มรายการได้ที่{' '}
              <Link href="/manage/research-interests" className={linkClass}>หัวข้อวิจัย</Link>)
            </>
          }
        >
          {interests.error || allInterests.error ? (
            <Notice tone="error">{interests.error ?? allInterests.error}</Notice>
          ) : allInterests.data?.items.length === 0 ? (
            <EmptyNote>ยังไม่มีหัวข้อวิจัยในระบบ</EmptyNote>
          ) : (
            <ActionForm action={replaceLecturerResearchInterests.bind(null, id)}>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {allInterests.data?.items.map((interest) => (
                  <label key={interest.research_interest_id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      name="research_interest_ids"
                      value={interest.research_interest_id}
                      defaultChecked={chosenInterests.has(interest.research_interest_id)}
                      className="h-4 w-4 accent-brand"
                    />
                    {interest.name}
                  </label>
                ))}
              </div>
            </ActionForm>
          )}
        </Section>

        <Section
          title="ความเชี่ยวชาญ"
          description={
            <>
              เลือกจากรายการกลาง (เพิ่มได้ที่{' '}
              <Link href="/manage/expertise" className={linkClass}>ความเชี่ยวชาญ</Link>)
            </>
          }
        >
          {expertise.error || allExpertise.error ? (
            <Notice tone="error">{expertise.error ?? allExpertise.error}</Notice>
          ) : allExpertise.data?.items.length === 0 ? (
            <EmptyNote>ยังไม่มีรายการความเชี่ยวชาญในระบบ</EmptyNote>
          ) : (
            <ActionForm action={replaceLecturerExpertise.bind(null, id)}>
              <div className="grid gap-2 sm:grid-cols-2">
                {allExpertise.data?.items.map((item) => (
                  <label key={item.expertise_id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      name="expertise_ids"
                      value={item.expertise_id}
                      defaultChecked={chosenExpertise.has(item.expertise_id)}
                      className="h-4 w-4 accent-brand"
                    />
                    {item.description}
                  </label>
                ))}
              </div>
            </ActionForm>
          )}
        </Section>

        <Section title="ประวัติการศึกษา">
          {educations.error ? (
            <Notice tone="error">{educations.error}</Notice>
          ) : (
            <div className="space-y-3">
              {educations.data?.items.length === 0 ? <EmptyNote>ยังไม่มีข้อมูล</EmptyNote> : null}
              {educations.data?.items.map((education) => (
                <div key={education.education_id} className="rounded-lg border border-line p-3">
                  <ActionForm
                    action={updateEducation.bind(null, id, education.education_id)}
                    variant="secondary"
                    className="space-y-3"
                  >
                    <EducationInputs education={education} />
                  </ActionForm>
                  <div className="mt-2">
                    <ActionForm
                      inline
                      variant="danger"
                      submitLabel="ลบ"
                      confirmText="ลบประวัติการศึกษานี้?"
                      action={deleteEducation.bind(null, id, education.education_id)}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
          <ActionForm
            action={createEducation.bind(null, id)}
            submitLabel="เพิ่มประวัติการศึกษา"
            resetOnSuccess
            className="mt-4 space-y-3 border-t border-line-soft pt-4"
          >
            <EducationInputs />
          </ActionForm>
        </Section>

        <Section title="โปรไฟล์ทางวิชาการภายนอก" description="เช่น Google Scholar, Scopus, ORCID">
          {profiles.error ? (
            <Notice tone="error">{profiles.error}</Notice>
          ) : (
            <div className="space-y-3">
              {profiles.data?.items.length === 0 ? <EmptyNote>ยังไม่มีโปรไฟล์</EmptyNote> : null}
              {profiles.data?.items.map((profile) => (
                <div key={profile.publication_profile_id} className="flex flex-wrap items-start gap-2">
                  <ActionForm
                    action={updatePublicationProfile.bind(null, id, profile.publication_profile_id)}
                    variant="secondary"
                    className="flex flex-1 flex-wrap items-center gap-2"
                  >
                    <input name="provider" required defaultValue={profile.provider} maxLength={100} className={`${inputClass} sm:w-44`} aria-label="ผู้ให้บริการ" />
                    <input name="url" type="url" required defaultValue={profile.url} className={`${inputClass} sm:flex-1`} aria-label="URL" />
                  </ActionForm>
                  <ActionForm
                    inline
                    variant="danger"
                    submitLabel="ลบ"
                    confirmText="ลบโปรไฟล์นี้?"
                    action={deletePublicationProfile.bind(null, id, profile.publication_profile_id)}
                  />
                </div>
              ))}
            </div>
          )}
          <ActionForm
            action={createPublicationProfile.bind(null, id)}
            submitLabel="เพิ่มโปรไฟล์"
            resetOnSuccess
            className="mt-4 flex flex-wrap items-end gap-2 border-t border-line-soft pt-4"
          >
            <Field label="ผู้ให้บริการ" className="sm:w-44">
              <input name="provider" required maxLength={100} placeholder="Google Scholar" className={inputClass} />
            </Field>
            <Field label="URL" className="flex-1">
              <input name="url" type="url" required placeholder="https://" className={inputClass} />
            </Field>
          </ActionForm>
        </Section>

        <Section
          title="ผลงานตีพิมพ์"
          description={
            <>
              ผลงานที่ผูกกับอาจารย์ท่านนี้ (แก้ไขผลงานได้ที่{' '}
              <Link href="/manage/publications" className={linkClass}>ผลงานตีพิมพ์</Link>; API ยังไม่มีเส้นผูกผู้แต่ง)
            </>
          }
        >
          {publications.error ? (
            <Notice tone="error">{publications.error}</Notice>
          ) : publications.data?.items.length === 0 ? (
            <EmptyNote>ยังไม่มีผลงาน</EmptyNote>
          ) : (
            <Table head={['ลำดับผู้แต่ง', 'ชื่อผลงาน', 'ปี', 'แหล่งตีพิมพ์']}>
              {publications.data?.items.map((publication) => (
                <tr key={publication.publication_id}>
                  <Td>{publication.author_order ?? '–'}</Td>
                  <Td>
                    <Link href={`/manage/publications/${publication.publication_id}`} className={linkClass}>
                      {publication.title}
                    </Link>
                  </Td>
                  <Td>{publication.publication_year ?? '–'}</Td>
                  <Td>{publication.venue ?? '–'}</Td>
                </tr>
              ))}
            </Table>
          )}
        </Section>
      </fieldset>
    </div>
  );
}
