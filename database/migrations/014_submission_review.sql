BEGIN;

-- A reviewer's verdict on a whole sheet (V4): is it complete and does the evidence match what
-- was entered. One row per sheet, written by the reviewer assigned to the owner in that round.
-- It does not change the sheet's workflow status. Same status type as evidence verification (005).
CREATE TABLE "submission_review" (
  "submission_id" uuid PRIMARY KEY,
  "status" verification_status NOT NULL DEFAULT 'pending',
  "note" text,
  "reviewed_by" uuid,
  "reviewed_at" timestamptz,
  "updated_at" timestamptz NOT NULL DEFAULT (now())
);

ALTER TABLE "submission_review"
  ADD CONSTRAINT "fk_submission_review_submission"
  FOREIGN KEY ("submission_id") REFERENCES "submission" ("id") ON DELETE CASCADE;

ALTER TABLE "submission_review"
  ADD CONSTRAINT "fk_submission_review_reviewed_by"
  FOREIGN KEY ("reviewed_by") REFERENCES "lecturer" ("lecturer_id") ON DELETE SET NULL;

COMMIT;
