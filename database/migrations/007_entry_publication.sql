BEGIN;

-- A line of a submission can point at the publication it claims (academic-work items).
-- No ON DELETE action: a publication used on a sheet cannot be deleted from under it,
-- and the entry lock trigger (004) would reject a SET NULL on a submitted sheet anyway.
ALTER TABLE "submission_entry" ADD COLUMN "publication_id" integer;

ALTER TABLE "submission_entry"
  ADD CONSTRAINT "fk_submission_entry_publication"
  FOREIGN KEY ("publication_id") REFERENCES "publication" ("publication_id");

CREATE INDEX ON "submission_entry" ("publication_id");

COMMIT;
