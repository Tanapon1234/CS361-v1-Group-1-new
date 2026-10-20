/**
 * Shapes of the FastAPI backend (`backend/app/v2/dtos`). Numbers that are `numeric` in
 * the database arrive as JSON numbers; ids of workload rows are UUID strings.
 */

// --- envelopes ---------------------------------------------------------------------

export interface PageResponse<T> {
  items: T[];
  meta: { total: number; limit: number; offset: number };
}

export interface ListResponse<T> {
  items: T[];
  meta: { count: number };
}

export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  errors?: { field: string; message: string }[];
}

// --- enums -------------------------------------------------------------------------

export type AcademicRank = 'lecturer' | 'asst_prof' | 'assoc_prof' | 'prof';
export type PositionCode =
  | 'dean'
  | 'vice_dean'
  | 'asst_dean'
  | 'exec_committee'
  | 'dept_chair'
  | 'dept_deputy'
  | 'dept_secretary'
  | 'dept_committee';
export type SubmissionStatus =
  | 'draft'
  | 'submitted'
  | 'assessing'
  | 'dept_review'
  | 'returned'
  | 'dept_approved'
  | 'sent_to_faculty';
export type SignerRole = 'performer' | 'receiver' | 'dept_chair' | 'dept_committee';
export type ApprovalDecision = 'approved' | 'returned';
export type WeightMode = 'fixed' | 'ranged';
export type RangeBasis = 'weight' | 'points';
export type AssessmentAgg = 'none' | 'single' | 'average';
export type QuantityUnit = 'credit' | 'topic' | 'course' | 'hour' | 'person' | 'term';
export type DataSource = 'manual' | 'registrar' | 'registrar_edited';
export type EvidenceStatus = 'pending' | 'uploaded';

// --- lecturer profile --------------------------------------------------------------

export interface Lecturer {
  lecturer_id: string;
  name_th: string;
  name_en: string | null;
  rank: string | null;
  department_id: number | null;
  profile_image_url: string | null;
  office: string | null;
  phone: string | null;
  phone_extension: string | null;
  email: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface Education {
  education_id: number;
  lecturer_id: string;
  degree: string | null;
  field: string | null;
  institution: string | null;
  country: string | null;
  graduation_year: string | null;
}

export interface ResearchInterest {
  research_interest_id: number;
  name: string;
}

export interface Expertise {
  expertise_id: number;
  description: string;
}

export interface Publication {
  publication_id: number;
  title: string;
  publication_year: number | null;
  venue: string | null;
  volume: string | null;
  pages: string | null;
  doi: string | null;
  citation_text: string | null;
  created_at: string | null;
}

export interface LecturerPublication extends Publication {
  author_order: number | null;
}

export interface PublicationProfile {
  publication_profile_id: number;
  lecturer_id: string;
  provider: string;
  url: string;
}

export interface UploadPresign {
  upload_url: string;
  fields: Record<string, string>;
  object_key: string;
  expires_at: string;
}

export interface FileDownload {
  download_url: string;
  expires_at: string;
}

// --- workload ----------------------------------------------------------------------

export interface Department {
  id: number;
  code: string;
  name_th: string;
  is_active: boolean;
}

export interface Position {
  id: string;
  lecturer_id: string;
  position: PositionCode;
  department_id: number | null;
  start_date: string;
  end_date: string | null;
}

export interface FieldSpec {
  type: 'int' | 'number' | 'money' | 'string' | 'enum' | 'date' | 'bool';
  required?: boolean;
  values?: string[];
}

export interface RubricVersion {
  id: number;
  code: string;
  approved_meeting: string | null;
  approved_on: string | null;
  base_points: number;
  overall_cap: number;
  min_required: number;
  min_teaching_credits: number;
  is_active: boolean;
}

export interface RubricCategory {
  id: number;
  version_id: number;
  code: string;
  name_th: string;
  cap: number;
  sort_order: number;
}

export interface RubricSection {
  id: number;
  category_id: number;
  parent_id: number | null;
  code: string;
  name_th: string;
  cap: number | null;
  max_entries: number | null;
  sort_order: number;
}

export interface RubricItem {
  id: number;
  section_id: number;
  label_th: string;
  weight_mode: WeightMode;
  weight: number | null;
  weight_min: number | null;
  weight_max: number | null;
  range_basis: RangeBasis | null;
  assessor_position: PositionCode | null;
  assessment_agg: AssessmentAgg;
  unit: QuantityUnit;
  unit_divisor: number;
  uses_participation: boolean;
  counts_teaching_credit: boolean;
  once_per_round: boolean;
  tier_min: number | null;
  tier_max: number | null;
  field_schema: Record<string, FieldSpec> | null;
  is_active: boolean;
}

export interface RubricFormSection extends RubricSection {
  items: RubricItem[];
  children: RubricFormSection[];
}

export interface RubricFormCategory extends RubricCategory {
  sections: RubricFormSection[];
}

export interface RubricForm extends RubricVersion {
  categories: RubricFormCategory[];
}

export interface EvaluationRound {
  id: number;
  rubric_version_id: number;
  name_th: string;
  period_start: string;
  period_end: string;
  salary_effective_on: string;
  academic_year: number;
  semester: number | null;
  submit_due_at: string | null;
  is_open: boolean;
}

export interface RoundReportRow {
  submission_id: string;
  lecturer_id: string;
  name_th: string;
  department_id: number;
  status: SubmissionStatus;
  teaching_credits: number;
  raw_total: number;
  capped_total: number;
  meets_min_teaching_credits: boolean;
  meets_min_required: boolean;
}

export interface RoundReport {
  round: EvaluationRound;
  min_required: number;
  min_teaching_credits: number;
  summary: {
    submissions: number;
    by_status: Partial<Record<SubmissionStatus, number>>;
    meeting_min_required: number;
    average_capped_total: number;
  };
  rows: RoundReportRow[];
}

export interface Submission {
  id: string;
  round_id: number;
  lecturer_id: string;
  status: SubmissionStatus;
  rank_snapshot: AcademicRank;
  department_snapshot: number;
  teaching_credits: number;
  raw_total: number;
  capped_total: number;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Entry {
  id: string;
  submission_id: string;
  item_id: number;
  title: string | null;
  course_code: string | null;
  section_no: string | null;
  student_count: number | null;
  data_source: DataSource;
  synced_at: string | null;
  quantity: number;
  participation_pct: number;
  weight_applied: number | null;
  credits: number | null;
  score: number;
  details: Record<string, unknown> | null;
  note: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface SubmissionDetail extends Submission {
  entries: Entry[];
}

export interface CategoryScore {
  category_id: number;
  code: string;
  name_th: string;
  cap: number;
  raw_score: number;
  capped_score: number;
}

export interface SubmissionSummary {
  submission_id: string;
  status: SubmissionStatus;
  categories: CategoryScore[];
  raw_total: number;
  capped_total: number;
  overall_cap: number;
  teaching_credits: number;
  min_teaching_credits: number;
  min_required: number;
  meets_min_teaching_credits: boolean;
  meets_min_required: boolean;
  pending_assessments: number;
}

export interface SubmissionTotals {
  submission_id: string;
  status: SubmissionStatus;
  submitted_at: string | null;
  categories: CategoryScore[];
  raw_total: number;
  capped_total: number;
}

export interface Approval {
  id: string;
  submission_id: string;
  signer_id: string;
  role: SignerRole;
  decision: ApprovalDecision;
  comment: string | null;
  signed_at: string;
}

export interface Assessment {
  id: string;
  entry_id: string;
  assessor_id: string;
  position_used: PositionCode;
  value_given: number;
  comment: string | null;
  assessed_at: string;
}

export interface AssessmentQueueItem {
  entry: Entry;
  lecturer_id: string;
  lecturer_name_th: string;
  department_id: number;
  item_label_th: string;
  assessor_position: PositionCode;
  range_basis: RangeBasis | null;
  weight_min: number | null;
  weight_max: number | null;
  my_assessment: Assessment | null;
}

export interface Evidence {
  id: string;
  entry_id: string;
  ref_code: string | null;
  label: string | null;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  checksum: string | null;
  status: EvidenceStatus;
  uploaded_by: string;
  created_at: string;
}

export interface EvidenceUpload {
  evidence: Evidence;
  upload_url: string;
  fields: Record<string, string>;
  expires_at: string;
}

export interface Me {
  lecturer: Lecturer;
  positions: Position[];
  signer_roles: SignerRole[];
  open_rounds: EvaluationRound[];
}

// --- lecturer work (GET /lecturers/{id}/work) ---------------------------------------

export interface WorkEntry {
  entry_id: string;
  submission_id: string;
  submission_status: SubmissionStatus;
  round_id: number;
  round_name_th: string;
  academic_year: number;
  semester: number | null;
  section_code: string;
  section_name_th: string;
  item_label_th: string;
  title: string | null;
  course_code: string | null;
  quantity: number;
  score: number;
}

export interface WorkCategoryGroup {
  code: string;
  name_th: string;
  entries: WorkEntry[];
}

export interface WorkPublication {
  publication_id: number;
  title: string;
  publication_year: number | null;
  /** publication_year in B.E. */
  academic_year: number | null;
  venue: string | null;
  doi: string | null;
  author_order: number | null;
}

export interface LecturerWork {
  lecturer_id: string;
  lecturer_name_th: string;
  filters: { academic_year: number | null; category: string | null; category_name_th: string | null };
  categories: WorkCategoryGroup[];
  publications: WorkPublication[];
  total: number;
  /** Every B.E. year with any work, newest first */
  available_years: number[];
}
