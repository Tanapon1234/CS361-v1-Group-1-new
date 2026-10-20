import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import {
  BackToFacultyDirectory,
  FacultyContactSection,
  FacultyCvSection,
  FacultyEducationSection,
  FacultyExpertiseSection,
  FacultyExternalProfilesSection,
  FacultyProfileHeader,
  FacultyPublicationsSection,
  FacultyResearchInterestsSection,
  facultyDisplayName,
} from '@/components/faculty/faculty-profile-sections';
import { ProfileState } from '@/components/faculty/profile-state';
import { FacultyApiError, getFacultyDetail } from '@/lib/faculty-api';
import type { FacultyDetail } from '@/types/faculty';

interface ProfilePageProps {
  params: Promise<{ id: string }>;
}

/** Section jump-menu — only shows sections that actually have data */
const SECTION_LINKS: ReadonlyArray<{
  id: string;
  label: string;
  isVisible: (faculty: FacultyDetail) => boolean;
}> = [
  {
    id: 'cv-heading',
    label: 'ประวัติย่อ',
    isVisible: (faculty) => Boolean(faculty.cv?.url),
  },
  {
    id: 'contact-heading',
    label: 'ข้อมูลติดต่อ',
    isVisible: (faculty) =>
      Boolean(faculty.contact && Object.values(faculty.contact).some(Boolean)),
  },
  {
    id: 'research-heading',
    label: 'หัวข้อวิจัยที่สนใจ',
    isVisible: (faculty) => faculty.research_interests.length > 0,
  },
  {
    id: 'education-heading',
    label: 'การศึกษา',
    isVisible: (faculty) => faculty.education.length > 0,
  },
  {
    id: 'expertise-heading',
    label: 'ความเชี่ยวชาญ',
    isVisible: (faculty) => faculty.expertise.length > 0,
  },
  {
    id: 'publications-heading',
    label: 'ผลงานตีพิมพ์',
    // Always visible — even with no publications, a status message still needs to show
    isVisible: () => true,
  },
  {
    id: 'profiles-heading',
    label: 'โปรไฟล์ทางวิชาการ',
    isVisible: (faculty) => faculty.publication_profiles.length > 0,
  },
];

type LoadResult =
  | { status: 'ok'; faculty: FacultyDetail }
  | { status: 'not-found' }
  | { status: 'invalid-id' };

/**
 * Fetches once — both generateMetadata and the page itself call this
 * function without duplicating the API call, since Next's fetch cache
 * dedupes it within the same render pass.
 */
async function loadFaculty(id: string): Promise<LoadResult> {
  try {
    return { status: 'ok', faculty: await getFacultyDetail(id) };
  } catch (error) {
    if (error instanceof FacultyApiError && error.kind === 'not-found') {
      return { status: 'not-found' };
    }

    if (error instanceof FacultyApiError && error.kind === 'invalid-id') {
      return { status: 'invalid-id' };
    }

    // network / http / parse / config → let the segment's error.tsx handle it
    throw error;
  }
}

export async function generateMetadata({ params }: ProfilePageProps): Promise<Metadata> {
  const { id } = await params;
  const result = await loadFaculty(id);

  // Call notFound() here in generateMetadata too, since metadata is awaited
  // before the shell streams out — this is the last point where an HTTP 404
  // can actually still be set. (Waiting until the page alone calls it is too
  // late — loading.tsx would have already flushed a 200.)
  if (result.status === 'not-found') {
    notFound();
  }

  if (result.status === 'invalid-id') {
    return { title: 'รหัสอาจารย์ไม่ถูกต้อง' };
  }

  const name = facultyDisplayName(result.faculty);

  return {
    title: name,
    description: [name, result.faculty.academic_position, 'ภาควิชาวิทยาการคอมพิวเตอร์']
      .filter(Boolean)
      .join(' · '),
  };
}

/**
 * Server Component — fetches `GET /public/v3/faculties/{id}` on the server.
 * 404 → not-found.tsx, 400 → "invalid id" state, anything else → error.tsx.
 * loading.tsx shows while rendering waits, per Next.js file convention.
 */
export default async function FacultyProfilePage({ params }: ProfilePageProps) {
  const { id } = await params;
  const result = await loadFaculty(id);

  if (result.status === 'not-found') {
    notFound();
  }

  if (result.status === 'invalid-id') {
    return (
      <ProfileState
        title="รูปแบบรหัสอาจารย์ไม่ถูกต้อง"
        description="ลิงก์ที่เปิดอาจไม่สมบูรณ์ กรุณาเลือกรายชื่ออาจารย์จากหน้ารายชื่ออีกครั้ง"
      />
    );
  }

  const { faculty } = result;
  const visibleLinks = SECTION_LINKS.filter((link) => link.isVisible(faculty));

  return (
    /* No nested <main> here — layout.tsx already provides the site's single <main> */
    <div>
      <FacultyProfileHeader faculty={faculty} />

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12">
        <BackToFacultyDirectory />

        <div className="mt-8 lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:gap-10">
          <aside className="mb-8 lg:mb-0">
            <nav
              aria-label="หัวข้อข้อมูลอาจารย์"
              className="overflow-x-auto rounded-xl border border-line bg-surface-alt p-2 lg:sticky lg:top-28 lg:overflow-visible"
            >
              <ul className="flex min-w-max gap-1 lg:block lg:min-w-0 lg:space-y-1">
                {visibleLinks.map((link) => (
                  <li key={link.id}>
                    <a
                      href={`#${link.id}`}
                      className="block rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap text-ink-muted transition-colors hover:bg-brand-soft hover:text-brand"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>

          <article className="min-w-0 space-y-12">
            <FacultyCvSection faculty={faculty} />
            <FacultyContactSection faculty={faculty} />
            <FacultyResearchInterestsSection faculty={faculty} />
            <FacultyEducationSection faculty={faculty} />
            <FacultyExpertiseSection faculty={faculty} />
            <FacultyPublicationsSection faculty={faculty} />
            <FacultyExternalProfilesSection faculty={faculty} />
          </article>
        </div>
      </div>
    </div>
  );
}
