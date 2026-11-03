import type { Me, Role, SignerRole, Submission } from '@/types/backend';

/**
 * docs/v2/permissions.md on the page side: hide what the user may not do. Only a
 * convenience, the backend checks every call (app/v2/permissions.py).
 */

/** Admin counts as every role */
export function hasRole(me: Me | null, ...roles: Role[]): boolean {
  return !!me && (me.roles.includes('admin') || roles.some((role) => me.roles.includes(role)));
}

export const isAdmin = (me: Me | null) => hasRole(me, 'admin');
export const isExecutive = (me: Me | null) => hasRole(me, 'executive');
/** Master data, lecturers, rubrics, rounds — admin only (V4 #291: staff lost this) */
export const canManage = (me: Me | null) => isAdmin(me);
/** Any publication, not just their own — backend kept this for staff (PublicationService) */
export const canManageAnyPublication = (me: Me | null) => hasRole(me, 'staff');
export const canReview = (me: Me | null) => hasRole(me, 'reviewer');
/**
 * Sees everyone's submissions and reports. A plain reviewer is NOT included here — they
 * are a regular lecturer except for the verification queue of lecturers assigned to them
 * (backend: app.v2.security.VIEW_ALL_ROLES).
 */
export const viewsAll = (me: Me | null) => hasRole(me, 'staff', 'executive');

/**
 * Signed in with no role beyond "lecturer" (a plain reviewer counts as this too): sees and
 * edits only their own profile, works and workload sheets, plus the verification queue
 * if they have the reviewer role. Master data, the lecturer directory and the rubric are
 * not for them.
 */
export const isLecturerOnly = (me: Me | null) => !!me && !hasRole(me, 'staff', 'executive');

/** Staff view ใบภาระงาน only; they may not create one (backend: SubmissionService.create_submission) */
export const canCreateSubmission = (me: Me | null) =>
  !!me && (isAdmin(me) || !me.roles.includes('staff'));

export const isSelf = (me: Me | null, lecturerId: string) => me?.lecturer.lecturer_id === lecturerId;

/** A lecturer's profile data: themselves or staff */
export const canEditLecturer = (me: Me | null, lecturerId: string) =>
  canManage(me) || isSelf(me, lecturerId);

/** Department chair / committee: see their department's submissions and reports */
export function signsForDepartment(me: Me | null): boolean {
  return !!me?.positions.some(
    (held) => held.position === 'dept_chair' || held.position === 'dept_committee'
  );
}

/** Holds any position that can assess items (ranged 3.1 / 3.2 in rubric version 1) */
export const mayAssess = (me: Me | null) => !!me && (me.positions.length > 0 || isAdmin(me));

/** Who signs each step of a submission (backend: can_sign in app/v2/services/access.py) */
export function canSign(me: Me | null, role: SignerRole, submission: Submission): boolean {
  if (!me) return false;
  const holds = (position: string) =>
    me.positions.some(
      (held) => held.position === position && held.department_id === submission.department_snapshot
    );
  switch (role) {
    case 'performer':
      return isSelf(me, submission.lecturer_id);
    case 'receiver':
      return hasRole(me, 'staff');
    case 'dept_chair':
      return holds('dept_chair');
    case 'dept_committee':
      return holds('dept_committee');
  }
}
