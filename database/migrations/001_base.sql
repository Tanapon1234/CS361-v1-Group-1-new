-- V2 Faculty Output Repository baseline schema
-- Target: Aurora PostgreSQL compatible SQL

BEGIN;

CREATE TABLE faculty (
  id text PRIMARY KEY,
  public_slug text NOT NULL,
  name_th text,
  name_en text,
  academic_position text,
  department text,
  office_public text,
  phone_public text,
  email_public text,
  profile_image_url text,
  profile_image_alt text,
  visibility text NOT NULL DEFAULT 'PUBLIC',
  status text NOT NULL DEFAULT 'ACTIVE',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CONSTRAINT uq_faculty_public_slug UNIQUE (public_slug),
  CONSTRAINT chk_faculty_name_present CHECK (
    COALESCE(NULLIF(trim(name_th), ''), NULLIF(trim(name_en), '')) IS NOT NULL
  ),
  CONSTRAINT chk_faculty_visibility CHECK (visibility IN ('PUBLIC', 'INTERNAL', 'RESTRICTED')),
  CONSTRAINT chk_faculty_status CHECK (status IN ('ACTIVE', 'DELETED'))
);

CREATE TABLE faculty_education (
  id text PRIMARY KEY,
  faculty_id text NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
  degree text,
  field_of_study text,
  institution text,
  country text,
  graduation_year integer,
  display_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE faculty_interest (
  id text PRIMARY KEY,
  faculty_id text NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
  interest_type text NOT NULL,
  value text NOT NULL,
  visibility text NOT NULL DEFAULT 'PUBLIC',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_faculty_interest_value UNIQUE (faculty_id, interest_type, value),
  CONSTRAINT chk_faculty_interest_type CHECK (interest_type IN ('RESEARCH_INTEREST', 'EXPERTISE', 'KEYWORD')),
  CONSTRAINT chk_faculty_interest_visibility CHECK (visibility IN ('PUBLIC', 'INTERNAL', 'RESTRICTED'))
);

CREATE TABLE app_user (
  id text PRIMARY KEY,
  cognito_sub text NOT NULL,
  email text,
  display_name text,
  identity_provider text NOT NULL DEFAULT 'COGNITO',
  status text NOT NULL DEFAULT 'ACTIVE',
  last_login_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CONSTRAINT uq_app_user_cognito_sub UNIQUE (cognito_sub),
  CONSTRAINT chk_app_user_status CHECK (status IN ('ACTIVE', 'SUSPENDED', 'DELETED')),
  CONSTRAINT chk_app_user_identity_provider CHECK (identity_provider IN ('COGNITO', 'SYSTEM'))
);

CREATE TABLE app_role (
  code text PRIMARY KEY,
  label text NOT NULL,
  description text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app_user_role (
  id text PRIMARY KEY,
  user_id text NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  role_code text NOT NULL REFERENCES app_role(code),
  assigned_by_user_id text REFERENCES app_user(id) ON DELETE SET NULL,
  assigned_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  revoke_reason text,
  CONSTRAINT chk_app_user_role_revoked_after_assigned CHECK (revoked_at IS NULL OR revoked_at >= assigned_at)
);

CREATE TABLE auth_login_event (
  id text PRIMARY KEY,
  user_id text REFERENCES app_user(id) ON DELETE SET NULL,
  cognito_sub text,
  email text,
  login_status text NOT NULL,
  failure_reason text,
  ip_address inet,
  user_agent text,
  request_id text,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_auth_login_event_status CHECK (login_status IN ('SUCCESS', 'FAILED'))
);

CREATE TABLE academic_period (
  id text PRIMARY KEY,
  academic_year integer NOT NULL,
  semester text NOT NULL,
  label text NOT NULL,
  start_date date,
  end_date date,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_academic_period_year_semester UNIQUE (academic_year, semester),
  CONSTRAINT chk_academic_period_semester CHECK (semester IN ('1', '2', '3', 'SUMMER', 'OTHER')),
  CONSTRAINT chk_academic_period_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE TABLE evaluation_period (
  id text PRIMARY KEY,
  code text NOT NULL UNIQUE,
  label text NOT NULL,
  start_date date NOT NULL,
  end_date date NOT NULL,
  academic_period_id text REFERENCES academic_period(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_evaluation_period_dates CHECK (end_date >= start_date)
);

CREATE TABLE work_category (
  code text PRIMARY KEY,
  label_th text NOT NULL,
  label_en text NOT NULL,
  description text,
  display_order integer NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE work_type (
  code text PRIMARY KEY,
  category_code text NOT NULL REFERENCES work_category(code),
  label_th text NOT NULL,
  label_en text NOT NULL,
  description text,
  default_visibility text NOT NULL DEFAULT 'INTERNAL',
  display_order integer NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_work_type_category_code UNIQUE (category_code, code),
  CONSTRAINT chk_work_type_default_visibility CHECK (default_visibility IN ('PUBLIC', 'INTERNAL', 'RESTRICTED'))
);

CREATE TABLE import_batch (
  id text PRIMARY KEY,
  source_system text NOT NULL,
  source_name text NOT NULL,
  source_version text,
  source_type text NOT NULL,
  source_s3_key text,
  source_hash text NOT NULL,
  status text NOT NULL DEFAULT 'PENDING',
  record_count integer NOT NULL DEFAULT 0,
  valid_count integer NOT NULL DEFAULT 0,
  warning_count integer NOT NULL DEFAULT 0,
  error_count integer NOT NULL DEFAULT 0,
  started_at timestamptz,
  completed_at timestamptz,
  created_by text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_import_batch_source_hash UNIQUE (source_system, source_name, source_hash),
  CONSTRAINT chk_import_batch_status CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'WARNING')),
  CONSTRAINT chk_import_batch_counts CHECK (
    record_count >= 0 AND valid_count >= 0 AND warning_count >= 0 AND error_count >= 0
  )
);

CREATE TABLE source_record (
  id text PRIMARY KEY,
  import_batch_id text NOT NULL REFERENCES import_batch(id) ON DELETE CASCADE,
  source_system text NOT NULL,
  source_record_key text NOT NULL,
  source_section_code text,
  source_hash text NOT NULL,
  row_number integer,
  raw_record jsonb NOT NULL DEFAULT '{}'::jsonb,
  target_entity_type text,
  target_entity_id text,
  status text NOT NULL DEFAULT 'PENDING',
  error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_source_record_idempotency UNIQUE (source_system, source_record_key, source_hash),
  CONSTRAINT chk_source_record_status CHECK (status IN ('PENDING', 'IMPORTED', 'SKIPPED', 'WARNING', 'ERROR'))
);

CREATE TABLE work_item (
  id text PRIMARY KEY,
  category_code text NOT NULL,
  work_type_code text NOT NULL,
  title text NOT NULL,
  description text,
  start_date date,
  end_date date,
  visibility text NOT NULL DEFAULT 'INTERNAL',
  status text NOT NULL DEFAULT 'ACTIVE',
  source_score numeric(12,2),
  source_weight numeric(12,4),
  source_section_code text,
  import_batch_id text REFERENCES import_batch(id) ON DELETE SET NULL,
  source_record_id text REFERENCES source_record(id) ON DELETE SET NULL,
  created_by text,
  updated_by text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CONSTRAINT fk_work_item_category_type FOREIGN KEY (category_code, work_type_code)
    REFERENCES work_type(category_code, code),
  CONSTRAINT chk_work_item_visibility CHECK (visibility IN ('PUBLIC', 'INTERNAL', 'RESTRICTED')),
  CONSTRAINT chk_work_item_status CHECK (status IN ('ACTIVE', 'DELETED')),
  CONSTRAINT chk_work_item_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
  CONSTRAINT chk_work_item_source_score CHECK (source_score IS NULL OR source_score >= 0),
  CONSTRAINT chk_work_item_source_weight CHECK (source_weight IS NULL OR source_weight >= 0)
);

CREATE TABLE faculty_work_item (
  id text PRIMARY KEY,
  faculty_id text NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
  work_item_id text NOT NULL REFERENCES work_item(id) ON DELETE CASCADE,
  academic_period_id text REFERENCES academic_period(id) ON DELETE SET NULL,
  evaluation_period_id text REFERENCES evaluation_period(id) ON DELETE SET NULL,
  role text,
  contribution_order integer,
  contribution_percent numeric(5,2),
  contribution_note text,
  quantity numeric(12,2),
  credits numeric(12,2),
  hours numeric(12,2),
  source_section_code text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_faculty_work_item_role UNIQUE (faculty_id, work_item_id, role),
  CONSTRAINT chk_fwi_contribution_percent CHECK (
    contribution_percent IS NULL OR (contribution_percent >= 0 AND contribution_percent <= 100)
  ),
  CONSTRAINT chk_fwi_non_negative_values CHECK (
    (quantity IS NULL OR quantity >= 0)
    AND (credits IS NULL OR credits >= 0)
    AND (hours IS NULL OR hours >= 0)
  )
);

CREATE TABLE teaching_detail (
  work_item_id text PRIMARY KEY REFERENCES work_item(id) ON DELETE CASCADE,
  course_code text,
  course_title text,
  degree_level text,
  teaching_mode text,
  section_count integer,
  student_count integer,
  credits numeric(12,2),
  lecture_hours numeric(12,2),
  lab_hours numeric(12,2),
  workload_hours numeric(12,2),
  reference_label text,
  CONSTRAINT chk_teaching_non_negative CHECK (
    (section_count IS NULL OR section_count >= 0)
    AND (student_count IS NULL OR student_count >= 0)
    AND (credits IS NULL OR credits >= 0)
    AND (lecture_hours IS NULL OR lecture_hours >= 0)
    AND (lab_hours IS NULL OR lab_hours >= 0)
    AND (workload_hours IS NULL OR workload_hours >= 0)
  )
);

CREATE TABLE publication_detail (
  work_item_id text PRIMARY KEY REFERENCES work_item(id) ON DELETE CASCADE,
  publication_title text NOT NULL,
  venue text,
  publisher text,
  publication_year integer,
  publication_date date,
  doi text,
  isbn text,
  issn text,
  quartile text,
  indexing_database text,
  publication_kind text,
  external_url text,
  CONSTRAINT chk_publication_year CHECK (
    publication_year IS NULL OR (publication_year >= 1900 AND publication_year <= 3000)
  ),
  CONSTRAINT chk_publication_quartile CHECK (
    quartile IS NULL OR quartile IN ('TIER1', 'Q1', 'Q2', 'Q3', 'Q4', 'NO_Q', 'TCI1', 'TCI2', 'OTHER')
  )
);

CREATE TABLE research_project_detail (
  work_item_id text PRIMARY KEY REFERENCES work_item(id) ON DELETE CASCADE,
  project_title text,
  funding_source text,
  funding_type text,
  budget_amount numeric(14,2),
  currency text DEFAULT 'THB',
  project_status text,
  contract_number text,
  principal_investigator text,
  project_start_date date,
  project_end_date date,
  CONSTRAINT chk_research_budget CHECK (budget_amount IS NULL OR budget_amount >= 0),
  CONSTRAINT chk_research_dates CHECK (
    project_end_date IS NULL OR project_start_date IS NULL OR project_end_date >= project_start_date
  )
);

CREATE TABLE supervision_detail (
  work_item_id text PRIMARY KEY REFERENCES work_item(id) ON DELETE CASCADE,
  supervision_type text,
  supervision_role text,
  degree_level text,
  program_name text,
  course_code text,
  student_count integer,
  credits numeric(12,2),
  student_identifier_policy text NOT NULL DEFAULT 'REDACTED',
  CONSTRAINT chk_supervision_student_count CHECK (student_count IS NULL OR student_count >= 0),
  CONSTRAINT chk_supervision_credits CHECK (credits IS NULL OR credits >= 0),
  CONSTRAINT chk_supervision_identifier_policy CHECK (student_identifier_policy IN ('REDACTED', 'INTERNAL_ONLY', 'NOT_STORED'))
);

CREATE TABLE service_detail (
  work_item_id text PRIMARY KEY REFERENCES work_item(id) ON DELETE CASCADE,
  service_scope text,
  organization_name text,
  service_role text,
  committee_name text,
  order_reference text,
  service_date date,
  service_end_date date,
  CONSTRAINT chk_service_dates CHECK (
    service_end_date IS NULL OR service_date IS NULL OR service_end_date >= service_date
  )
);

CREATE TABLE administration_detail (
  work_item_id text PRIMARY KEY REFERENCES work_item(id) ON DELETE CASCADE,
  position_title text,
  organization_unit text,
  appointment_type text,
  appointed_from date,
  appointed_to date,
  appointment_reference text,
  CONSTRAINT chk_administration_dates CHECK (
    appointed_to IS NULL OR appointed_from IS NULL OR appointed_to >= appointed_from
  )
);

CREATE TABLE evidence_reference (
  id text PRIMARY KEY,
  work_item_id text NOT NULL REFERENCES work_item(id) ON DELETE CASCADE,
  reference_type text NOT NULL,
  label text NOT NULL,
  external_url text,
  s3_key text,
  mime_type text,
  checksum_sha256 text,
  visibility text NOT NULL DEFAULT 'INTERNAL',
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_evidence_reference_type CHECK (reference_type IN ('URL', 'S3_OBJECT', 'DOCUMENT_ID', 'TEXT_NOTE', 'OTHER')),
  CONSTRAINT chk_evidence_visibility CHECK (visibility IN ('PUBLIC', 'INTERNAL', 'RESTRICTED')),
  CONSTRAINT chk_evidence_location CHECK (external_url IS NOT NULL OR s3_key IS NOT NULL OR reference_type IN ('TEXT_NOTE', 'OTHER'))
);

CREATE TABLE audit_event (
  id text PRIMARY KEY,
  actor_user_id text REFERENCES app_user(id) ON DELETE SET NULL,
  actor_subject text,
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id text NOT NULL,
  before_json jsonb,
  after_json jsonb,
  request_id text,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_faculty_status_visibility ON faculty(status, visibility);
CREATE INDEX idx_faculty_public_slug ON faculty(public_slug);

CREATE INDEX idx_faculty_education_faculty ON faculty_education(faculty_id);
CREATE INDEX idx_faculty_interest_faculty ON faculty_interest(faculty_id);
CREATE INDEX idx_faculty_interest_value ON faculty_interest(value);

CREATE UNIQUE INDEX uq_app_user_email_lower
  ON app_user (lower(email))
  WHERE email IS NOT NULL AND trim(email) <> '';
CREATE INDEX idx_app_user_status ON app_user(status);
CREATE INDEX idx_app_user_role_user ON app_user_role(user_id);
CREATE INDEX idx_app_user_role_role ON app_user_role(role_code);
CREATE UNIQUE INDEX uq_app_user_active_role
  ON app_user_role (user_id, role_code)
  WHERE revoked_at IS NULL;
CREATE INDEX idx_auth_login_event_user ON auth_login_event(user_id);
CREATE INDEX idx_auth_login_event_occurred_at ON auth_login_event(occurred_at);
CREATE INDEX idx_auth_login_event_status ON auth_login_event(login_status);

CREATE INDEX idx_evaluation_period_dates ON evaluation_period(start_date, end_date);

CREATE INDEX idx_work_type_category ON work_type(category_code);

CREATE INDEX idx_import_batch_source ON import_batch(source_system, source_name, source_hash);
CREATE INDEX idx_source_record_lookup ON source_record(source_system, source_record_key, source_hash);
CREATE INDEX idx_source_record_target ON source_record(target_entity_type, target_entity_id);

CREATE INDEX idx_work_item_category ON work_item(category_code);
CREATE INDEX idx_work_item_type ON work_item(work_type_code);
CREATE INDEX idx_work_item_visibility ON work_item(visibility);
CREATE INDEX idx_work_item_status ON work_item(status);
CREATE INDEX idx_work_item_status_visibility ON work_item(status, visibility);
CREATE INDEX idx_work_item_dates ON work_item(start_date, end_date);
CREATE INDEX idx_work_item_source_record ON work_item(source_record_id);
CREATE INDEX idx_work_item_title ON work_item(title);

CREATE INDEX idx_fwi_faculty ON faculty_work_item(faculty_id);
CREATE INDEX idx_fwi_work_item ON faculty_work_item(work_item_id);
CREATE INDEX idx_fwi_academic_period ON faculty_work_item(academic_period_id);
CREATE INDEX idx_fwi_evaluation_period ON faculty_work_item(evaluation_period_id);
CREATE INDEX idx_fwi_faculty_period ON faculty_work_item(faculty_id, academic_period_id);

CREATE INDEX idx_teaching_course_code ON teaching_detail(course_code);

CREATE INDEX idx_publication_year ON publication_detail(publication_year);
CREATE INDEX idx_publication_title ON publication_detail(publication_title);
CREATE UNIQUE INDEX uq_publication_doi
  ON publication_detail (lower(doi))
  WHERE doi IS NOT NULL AND trim(doi) <> '';

CREATE INDEX idx_research_funding_source ON research_project_detail(funding_source);
CREATE INDEX idx_supervision_degree_level ON supervision_detail(degree_level);
CREATE INDEX idx_service_scope ON service_detail(service_scope);
CREATE INDEX idx_administration_position ON administration_detail(position_title);

CREATE INDEX idx_evidence_work_item ON evidence_reference(work_item_id);
CREATE INDEX idx_evidence_visibility ON evidence_reference(visibility);

CREATE INDEX idx_audit_entity ON audit_event(entity_type, entity_id);
CREATE INDEX idx_audit_actor_user ON audit_event(actor_user_id);
CREATE INDEX idx_audit_occurred_at ON audit_event(occurred_at);

COMMIT;
