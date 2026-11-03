BEGIN;

-- V4 #293: an executive assigns which reviewer reviews which lecturer. A lecturer may
-- have several reviewers, and a reviewer may be assigned several lecturers.
CREATE TABLE "reviewer_assignment" (
  "id" uuid PRIMARY KEY DEFAULT (gen_random_uuid()),
  "reviewer_id" uuid NOT NULL,
  "reviewee_id" uuid NOT NULL,
  "assigned_by" uuid NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT (now()),
  CONSTRAINT "chk_reviewer_assignment_not_self" CHECK ("reviewer_id" != "reviewee_id"),
  CONSTRAINT "uq_reviewer_assignment" UNIQUE ("reviewer_id", "reviewee_id")
);

ALTER TABLE "reviewer_assignment"
  ADD CONSTRAINT "fk_reviewer_assignment_reviewer"
  FOREIGN KEY ("reviewer_id") REFERENCES "lecturer" ("lecturer_id");

ALTER TABLE "reviewer_assignment"
  ADD CONSTRAINT "fk_reviewer_assignment_reviewee"
  FOREIGN KEY ("reviewee_id") REFERENCES "lecturer" ("lecturer_id");

ALTER TABLE "reviewer_assignment"
  ADD CONSTRAINT "fk_reviewer_assignment_assigned_by"
  FOREIGN KEY ("assigned_by") REFERENCES "lecturer" ("lecturer_id");

CREATE INDEX ON "reviewer_assignment" ("reviewer_id");
CREATE INDEX ON "reviewer_assignment" ("reviewee_id");

COMMIT;
