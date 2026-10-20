import 'server-only';

import { backend, backendOrNull } from '@/lib/backend/client';
import type {
  Approval,
  Assessment,
  AssessmentQueueItem,
  Department,
  Education,
  EvaluationRound,
  Evidence,
  Expertise,
  Lecturer,
  LecturerPublication,
  ListResponse,
  Me,
  PageResponse,
  Position,
  Publication,
  PublicationProfile,
  ResearchInterest,
  RoundReport,
  RubricCategory,
  RubricForm,
  RubricVersion,
  Submission,
  SubmissionDetail,
  SubmissionStatus,
  SubmissionSummary,
  SubmissionTotals,
} from '@/types/backend';

/** Reads (GET) used by the /manage pages. Changes live in app/manage/actions/. */

export const PAGE_SIZE = 20;
/** The backend's largest page; enough for dropdowns of master data */
export const MAX_PAGE = 100;

// --- people -------------------------------------------------------------------------

export const getMe = () => backend<Me>('GET', '/me');

export const listLecturers = (query: {
  q?: string;
  department_id?: number;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}) => backend<PageResponse<Lecturer>>('GET', '/lecturers', { query });

export const getLecturer = (id: string) => backendOrNull<Lecturer>(`/lecturers/${id}`);

export const listPositions = (lecturerId: string) =>
  backend<ListResponse<Position>>('GET', `/lecturers/${lecturerId}/positions`);

export const listDepartments = (isActive?: boolean) =>
  backend<PageResponse<Department>>('GET', '/departments', {
    query: { limit: MAX_PAGE, is_active: isActive },
  });

// --- lecturer academic profile ------------------------------------------------------

export const listEducations = (lecturerId: string) =>
  backend<ListResponse<Education>>('GET', `/lecturers/${lecturerId}/educations`);

export const listLecturerResearchInterests = (lecturerId: string) =>
  backend<ListResponse<ResearchInterest>>('GET', `/lecturers/${lecturerId}/research-interests`);

export const listLecturerExpertise = (lecturerId: string) =>
  backend<ListResponse<Expertise>>('GET', `/lecturers/${lecturerId}/expertise`);

export const listPublicationProfiles = (lecturerId: string) =>
  backend<ListResponse<PublicationProfile>>(
    'GET',
    `/lecturers/${lecturerId}/publication-profiles`
  );

export const listLecturerPublications = (lecturerId: string) =>
  backend<PageResponse<LecturerPublication>>('GET', `/lecturers/${lecturerId}/publications`, {
    query: { limit: MAX_PAGE },
  });

export const listResearchInterests = (query: { q?: string; limit?: number; offset?: number }) =>
  backend<PageResponse<ResearchInterest>>('GET', '/research-interests', { query });

export const listExpertise = (query: { q?: string; limit?: number; offset?: number }) =>
  backend<PageResponse<Expertise>>('GET', '/expertise', { query });

export const listPublications = (query: {
  q?: string;
  publication_year?: number;
  limit?: number;
  offset?: number;
}) => backend<PageResponse<Publication>>('GET', '/publications', { query });

export const getPublication = (id: number) => backendOrNull<Publication>(`/publications/${id}`);

// --- rubric -------------------------------------------------------------------------

export const listRubricVersions = () =>
  backend<PageResponse<RubricVersion>>('GET', '/rubric-versions', {
    query: { limit: MAX_PAGE },
  });

export const getRubricForm = (versionId: number) =>
  backendOrNull<RubricForm>(`/rubric-versions/${versionId}/form`);

export const listRubricCategories = (versionId: number) =>
  backend<ListResponse<RubricCategory>>('GET', `/rubric-versions/${versionId}/categories`);

// --- rounds -------------------------------------------------------------------------

export const listRounds = (isOpen?: boolean) =>
  backend<PageResponse<EvaluationRound>>('GET', '/rounds', {
    query: { limit: MAX_PAGE, is_open: isOpen },
  });

export const getRound = (id: number) => backendOrNull<EvaluationRound>(`/rounds/${id}`);

export const listRoundSubmissions = (
  roundId: number,
  query: { department_id?: number; status?: SubmissionStatus; offset?: number }
) =>
  backend<PageResponse<Submission>>('GET', `/rounds/${roundId}/submissions`, {
    query: { ...query, limit: PAGE_SIZE },
  });

export const getRoundReport = (roundId: number, departmentId?: number) =>
  backend<RoundReport>('GET', `/rounds/${roundId}/report`, {
    query: { department_id: departmentId },
  });

// --- submissions --------------------------------------------------------------------

export const listSubmissions = (query: {
  round_id?: number;
  lecturer_id?: string;
  status?: SubmissionStatus;
  offset?: number;
}) =>
  backend<PageResponse<Submission>>('GET', '/submissions', {
    query: { ...query, limit: PAGE_SIZE },
  });

export const getSubmission = (id: string) =>
  backendOrNull<SubmissionDetail>(`/submissions/${id}`);

export const getSubmissionSummary = (id: string) =>
  backend<SubmissionSummary>('GET', `/submissions/${id}/summary`);

/** Frozen totals exist only after the submission was sent (409 before) */
export async function getSubmissionTotals(id: string): Promise<SubmissionTotals | null> {
  try {
    return await backend<SubmissionTotals>('GET', `/submissions/${id}/totals`);
  } catch {
    return null;
  }
}

export const listApprovals = (id: string) =>
  backend<ListResponse<Approval>>('GET', `/submissions/${id}/approvals`);

export const listEvidence = (entryId: string) =>
  backend<ListResponse<Evidence>>('GET', `/entries/${entryId}/evidence`);

export const listEntryAssessments = (entryId: string) =>
  backend<ListResponse<Assessment>>('GET', `/entries/${entryId}/assessments`);

export const listAssessmentQueue = (query: {
  round_id?: number;
  status?: 'pending' | 'done';
  offset?: number;
}) =>
  backend<PageResponse<AssessmentQueueItem>>('GET', '/assessments', {
    query: { ...query, limit: PAGE_SIZE },
  });

/** Run reads in parallel, but keep one failing section from breaking the whole page */
export async function settle<T>(promise: Promise<T>): Promise<{ data: T | null; error: string | null }> {
  try {
    return { data: await promise, error: null };
  } catch (error) {
    return { data: null, error: error instanceof Error ? error.message : String(error) };
  }
}
