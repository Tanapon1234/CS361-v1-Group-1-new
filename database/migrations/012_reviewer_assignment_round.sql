BEGIN;

-- V4: a reviewer assignment belongs to one evaluation round. It is only in effect while
-- that round is open and before its submit_due_at (see SqlReviewerAssignmentDAO).
ALTER TABLE "reviewer_assignment" ADD COLUMN "round_id" smallint;

-- Existing assignments had no round: carry each one into every round that is open now.
-- Assignments with no open round to attach to would be inactive anyway, so they are dropped.
INSERT INTO "reviewer_assignment" ("reviewer_id", "reviewee_id", "assigned_by", "created_at", "round_id")
SELECT ra."reviewer_id", ra."reviewee_id", ra."assigned_by", ra."created_at", er."id"
FROM "reviewer_assignment" ra
CROSS JOIN "evaluation_round" er
WHERE ra."round_id" IS NULL AND er."is_open";

DELETE FROM "reviewer_assignment" WHERE "round_id" IS NULL;

ALTER TABLE "reviewer_assignment" ALTER COLUMN "round_id" SET NOT NULL;

ALTER TABLE "reviewer_assignment"
  ADD CONSTRAINT "fk_reviewer_assignment_round"
  FOREIGN KEY ("round_id") REFERENCES "evaluation_round" ("id");

ALTER TABLE "reviewer_assignment" DROP CONSTRAINT "uq_reviewer_assignment";
ALTER TABLE "reviewer_assignment"
  ADD CONSTRAINT "uq_reviewer_assignment" UNIQUE ("round_id", "reviewer_id", "reviewee_id");

CREATE INDEX ON "reviewer_assignment" ("round_id");

COMMIT;
