-- V4 department/academic-year reporting: these columns are filtered on every report
-- query but have no index today (only the existing (round_id, lecturer_id) unique index
-- and the partial `draft` index on submission).

CREATE INDEX ON "submission" ("department_snapshot");
CREATE INDEX ON "submission" ("lecturer_id");
CREATE INDEX ON "publication" ("publication_year");
CREATE INDEX ON "faculty_publication" ("publication_id");
CREATE INDEX ON "evaluation_round" ("academic_year");
