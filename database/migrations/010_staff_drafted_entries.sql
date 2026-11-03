BEGIN;

-- V4 #292: staff may draft a workload entry for a lecturer in their own department;
-- the lecturer must explicitly confirm it before it counts as real data.
-- entered_by: who actually created the row (the lecturer themselves, or staff on their
-- behalf). Backfilled to the submission's own lecturer_id: every existing entry was
-- self-entered.
ALTER TABLE "submission_entry" ADD COLUMN "entered_by" uuid;

UPDATE "submission_entry" AS "entry"
SET "entered_by" = "submission"."lecturer_id"
FROM "submission"
WHERE "submission"."id" = "entry"."submission_id";

ALTER TABLE "submission_entry" ALTER COLUMN "entered_by" SET NOT NULL;

ALTER TABLE "submission_entry"
  ADD CONSTRAINT "fk_submission_entry_entered_by"
  FOREIGN KEY ("entered_by") REFERENCES "lecturer" ("lecturer_id");

-- true for every existing row (self-entered, so there is nothing to confirm); a
-- staff-drafted entry is inserted with this false until the lecturer confirms it.
ALTER TABLE "submission_entry" ADD COLUMN "confirmed_by_owner" boolean NOT NULL DEFAULT true;

COMMIT;
