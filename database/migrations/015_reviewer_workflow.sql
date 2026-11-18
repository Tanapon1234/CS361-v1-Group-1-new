-- The approval flow starts with the assigned reviewer instead of the staff "receive" step.
-- A reviewer signs as the new signer role `reviewer`; old `receiver` and `dept_committee`
-- rows stay valid as history. The sheet verdict table from 014 is replaced by this flow.
-- (ALTER TYPE ... ADD VALUE cannot run inside a transaction block on every PostgreSQL
-- version, so this file has no BEGIN / COMMIT.)
ALTER TYPE "signer_role" ADD VALUE IF NOT EXISTS 'reviewer';

DROP TABLE IF EXISTS "submission_review";
