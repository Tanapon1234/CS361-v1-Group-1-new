import type {
  AcademicRank,
  AssessmentAgg,
  DataSource,
  PositionCode,
  QuantityUnit,
  RangeBasis,
  SignerRole,
  SubmissionStatus,
  WeightMode,
} from '@/types/backend';

/** Thai labels for the backend's enum values (shared by Server and Client Components). */

export const SUBMISSION_STATUS_LABEL: Record<SubmissionStatus, string> = {
  draft: 'ร่าง',
  submitted: 'ส่งแล้ว รอรับเรื่อง',
  assessing: 'รอผู้บริหารประเมิน',
  dept_review: 'รอกรรมการสาขาพิจารณา',
  returned: 'ถูกตีกลับ',
  dept_approved: 'สาขาอนุมัติแล้ว',
  sent_to_faculty: 'ส่งคณะแล้ว',
};

export const POSITION_LABEL: Record<PositionCode, string> = {
  dean: 'คณบดี',
  vice_dean: 'รองคณบดี',
  asst_dean: 'ผู้ช่วยคณบดี',
  exec_committee: 'กรรมการบริหารคณะ',
  dept_chair: 'หัวหน้าสาขาวิชา',
  dept_deputy: 'ผู้ช่วย/รองหัวหน้าสาขา',
  dept_secretary: 'เลขา/ผู้ช่วยเลขาสาขา',
  dept_committee: 'กรรมการประจำสาขาวิชา',
};

/** Positions held inside one department (the others are faculty-level) */
export const DEPARTMENT_POSITIONS: readonly PositionCode[] = [
  'dept_chair',
  'dept_deputy',
  'dept_secretary',
  'dept_committee',
];

export const SIGNER_ROLE_LABEL: Record<SignerRole, string> = {
  performer: 'ผู้ปฏิบัติ (เจ้าของใบ)',
  receiver: 'ผู้รับเรื่อง',
  dept_chair: 'หัวหน้าสาขาวิชา',
  dept_committee: 'กรรมการประจำสาขาวิชา',
};

export const RANK_LABEL: Record<AcademicRank, string> = {
  lecturer: 'อาจารย์',
  asst_prof: 'ผู้ช่วยศาสตราจารย์',
  assoc_prof: 'รองศาสตราจารย์',
  prof: 'ศาสตราจารย์',
};

export const UNIT_LABEL: Record<QuantityUnit, string> = {
  credit: 'หน่วยกิต',
  topic: 'เรื่อง',
  course: 'วิชา',
  hour: 'ชั่วโมง',
  person: 'คน',
  term: 'วาระ',
};

export const WEIGHT_MODE_LABEL: Record<WeightMode, string> = {
  fixed: 'น้ำหนักตายตัว',
  ranged: 'ผู้บริหารเป็นผู้ให้ค่า',
};

export const RANGE_BASIS_LABEL: Record<RangeBasis, string> = {
  weight: 'ค่าเป็นน้ำหนัก (× คะแนนฐาน)',
  points: 'ค่าเป็นคะแนนตรง',
};

export const AGG_LABEL: Record<AssessmentAgg, string> = {
  none: 'ไม่ต้องประเมิน',
  single: 'ผู้ประเมินคนเดียว',
  average: 'เฉลี่ยจากผู้ประเมินหลายคน',
};

export const DATA_SOURCE_LABEL: Record<DataSource, string> = {
  manual: 'กรอกเอง',
  registrar: 'จากทะเบียน',
  registrar_edited: 'จากทะเบียน (แก้ไข)',
};

/**
 * The approval step at each status — mirrors backend/app/v2/services/workflow.py.
 * Only used to word the buttons; the backend decides what actually happens.
 */
export const WORKFLOW_STEP: Partial<
  Record<SubmissionStatus, { role: SignerRole; approve: string; canReturn: boolean }>
> = {
  draft: { role: 'performer', approve: 'ส่งใบภาระงาน', canReturn: false },
  returned: { role: 'performer', approve: 'ส่งใบภาระงานอีกครั้ง', canReturn: false },
  submitted: { role: 'receiver', approve: 'รับเรื่อง', canReturn: true },
  assessing: { role: 'dept_chair', approve: 'ยืนยันผลประเมิน ส่งต่อกรรมการสาขา', canReturn: true },
  dept_review: { role: 'dept_committee', approve: 'อนุมัติระดับสาขา', canReturn: true },
  dept_approved: { role: 'receiver', approve: 'ส่งต่อคณะ', canReturn: true },
};

export const EDITABLE_STATUSES: readonly SubmissionStatus[] = ['draft', 'returned'];

const numberFormat = new Intl.NumberFormat('th-TH', { maximumFractionDigits: 4 });
const scoreFormat = new Intl.NumberFormat('th-TH', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatNumber(value: number | null | undefined): string {
  return value === null || value === undefined ? '–' : numberFormat.format(value);
}

export function formatScore(value: number | null | undefined): string {
  return value === null || value === undefined ? '–' : scoreFormat.format(value);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '–';
  return new Date(value).toLocaleDateString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '–';
  return new Date(value).toLocaleString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
