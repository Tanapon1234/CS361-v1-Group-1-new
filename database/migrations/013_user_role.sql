BEGIN;

-- Roles an admin grants from the app (staff, executive, admin). `reviewer` is not stored:
-- it is derived from an active reviewer_assignment (012). Cognito groups still count too.
CREATE TABLE "user_role" (
  "lecturer_id" uuid NOT NULL,
  "role" varchar(20) NOT NULL,
  "granted_by" uuid NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT (now()),
  PRIMARY KEY ("lecturer_id", "role"),
  CONSTRAINT "chk_user_role_role" CHECK ("role" IN ('staff', 'executive', 'admin'))
);

ALTER TABLE "user_role"
  ADD CONSTRAINT "fk_user_role_lecturer"
  FOREIGN KEY ("lecturer_id") REFERENCES "lecturer" ("lecturer_id") ON DELETE CASCADE;

ALTER TABLE "user_role"
  ADD CONSTRAINT "fk_user_role_granted_by"
  FOREIGN KEY ("granted_by") REFERENCES "lecturer" ("lecturer_id");

COMMIT;
