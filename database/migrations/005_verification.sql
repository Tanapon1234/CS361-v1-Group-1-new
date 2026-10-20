-- Verification of publications and evidence files by a reviewer (V3, issue #221)
-- Target: Aurora PostgreSQL compatible SQL (PostgreSQL 15+), on top of 002-004.
--
-- New rows start as `pending`. A reviewer sets `verified` or `rejected` (with a note);
-- a verified publication can then only be changed by staff (docs/v2/permissions.md).

BEGIN;

CREATE TYPE "verification_status" AS ENUM ('pending', 'verified', 'rejected');

ALTER TABLE "publication" ADD COLUMN "verification_status" verification_status NOT NULL DEFAULT 'pending';
ALTER TABLE "publication" ADD COLUMN "verified_by" uuid;
ALTER TABLE "publication" ADD COLUMN "verified_at" timestamptz;
ALTER TABLE "publication" ADD COLUMN "verification_note" text;

ALTER TABLE "entry_evidence" ADD COLUMN "verification_status" verification_status NOT NULL DEFAULT 'pending';
ALTER TABLE "entry_evidence" ADD COLUMN "verified_by" uuid;
ALTER TABLE "entry_evidence" ADD COLUMN "verified_at" timestamptz;
ALTER TABLE "entry_evidence" ADD COLUMN "verification_note" text;

ALTER TABLE "publication" ADD FOREIGN KEY ("verified_by") REFERENCES "lecturer" ("lecturer_id") ON DELETE SET NULL DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "entry_evidence" ADD FOREIGN KEY ("verified_by") REFERENCES "lecturer" ("lecturer_id") ON DELETE SET NULL DEFERRABLE INITIALLY IMMEDIATE;

CREATE INDEX ON "publication" ("verification_status");
CREATE INDEX ON "entry_evidence" ("verification_status");

COMMIT;
