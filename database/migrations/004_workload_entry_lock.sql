-- Relax the submission_entry lock from 003 so the review workflow can run.
-- Target: Aurora PostgreSQL compatible SQL (PostgreSQL 15+)
--
-- 003 blocked every INSERT/UPDATE/DELETE on submission_entry unless submission.status = 'draft'.
-- Two cases need more than that:
--   1. A `returned` submission goes back to its owner to fix entries and resubmit.
--   2. During `assessing`, an assessor's value sets the entry's weight_applied and score.
--      The owner's data stays locked; only the computed columns may change.

BEGIN;

CREATE OR REPLACE FUNCTION "submission_entry_draft_only"() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  target_submission uuid := CASE WHEN TG_OP = 'DELETE' THEN OLD.submission_id ELSE NEW.submission_id END;
  current_status submission_status;
BEGIN
  SELECT status INTO current_status FROM submission WHERE id = target_submission;
  -- NOT FOUND: the parent submission is being deleted (ON DELETE CASCADE), so let it through.
  IF NOT FOUND OR current_status IN ('draft', 'returned') THEN
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
  END IF;

  -- Locked submission: allow an UPDATE that only changes the computed score columns.
  IF TG_OP = 'UPDATE' AND (
    NEW.submission_id, NEW.item_id, NEW.title, NEW.course_code, NEW.section_no,
    NEW.student_count, NEW.data_source, NEW.synced_at, NEW.quantity, NEW.participation_pct,
    NEW.credits, NEW.details, NEW.note, NEW.sort_order
  ) IS NOT DISTINCT FROM (
    OLD.submission_id, OLD.item_id, OLD.title, OLD.course_code, OLD.section_no,
    OLD.student_count, OLD.data_source, OLD.synced_at, OLD.quantity, OLD.participation_pct,
    OLD.credits, OLD.details, OLD.note, OLD.sort_order
  ) THEN
    RETURN NEW;
  END IF;

  RAISE EXCEPTION 'submission % is %, entries can only change while it is a draft or returned',
    target_submission, current_status
    USING ERRCODE = 'check_violation';
END;
$$;

COMMIT;
