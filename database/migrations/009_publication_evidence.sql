-- V4 FR4: evidence for a publication that is not tied to any workload entry.
-- Same presigned-S3 shape as entry_evidence (003); no per-file verification here —
-- the publication's own verification_status (005) covers the whole publication.

CREATE TABLE "publication_evidence" (
  "id" uuid PRIMARY KEY DEFAULT (gen_random_uuid()),
  "publication_id" int NOT NULL,
  "label" varchar(255),
  "s3_key" varchar(512) UNIQUE NOT NULL,
  "file_name" varchar(255) NOT NULL,
  "mime_type" varchar(100) NOT NULL,
  "size_bytes" bigint NOT NULL,
  "checksum" char(64),
  "status" evidence_status NOT NULL DEFAULT 'pending',
  "uploaded_by" uuid NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT (now())
);

ALTER TABLE "publication_evidence" ADD FOREIGN KEY ("publication_id") REFERENCES "publication" ("publication_id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "publication_evidence" ADD FOREIGN KEY ("uploaded_by") REFERENCES "lecturer" ("lecturer_id") DEFERRABLE INITIALLY IMMEDIATE;

CREATE INDEX ON "publication_evidence" ("publication_id");
