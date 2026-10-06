"""RDS Data API persistence for lecturer education records."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from .dto import CreateEducationDTO, PatchEducationDTO

LOGGER = logging.getLogger(__name__)
PATCHABLE_EDUCATION_COLUMNS = {
    "country": "country",
    "degree": "degree",
    "display_order": "display_order",
    "field_of_study": "field_of_study",
    "graduation_year": "graduation_year",
    "institution": "institution",
}


class LecturerNotFoundError(Exception):
    """The lecturer does not exist or is not active."""


class EducationNotFoundError(Exception):
    """The education record does not exist for the lecturer."""


class EducationDao:
    def create(self, lecturer_id: str, education: CreateEducationDTO) -> dict[str, Any]:
        raise NotImplementedError

    def list_for_lecturer(self, lecturer_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_for_lecturer(
        self,
        lecturer_id: str,
        education_id: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def update_for_lecturer(
        self,
        lecturer_id: str,
        education_id: str,
        education: PatchEducationDTO,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def delete_for_lecturer(self, lecturer_id: str, education_id: str) -> None:
        raise NotImplementedError


@dataclass
class DataApiEducationDao(EducationDao):
    resource_arn: str
    secret_arn: str
    database: str
    client: Any | None = None

    def __post_init__(self) -> None:
        if self.client is None:
            import boto3

            self.client = boto3.client("rds-data")

    def _execute(
        self,
        sql: str,
        params: dict[str, Any],
        transaction_id: str | None = None,
    ) -> list[dict[str, Any]]:
        request = {
            "resourceArn": self.resource_arn,
            "secretArn": self.secret_arn,
            "database": self.database,
            "sql": sql,
            "parameters": [_data_api_param(name, value) for name, value in params.items()],
            "includeResultMetadata": True,
        }
        if transaction_id is not None:
            request["transactionId"] = transaction_id
        response = self.client.execute_statement(
            **request,
        )
        columns = [
            column.get("label") or column.get("name")
            for column in response.get("columnMetadata", [])
        ]
        return [
            {str(column): _field_value(value) for column, value in zip(columns, record)}
            for record in response.get("records", [])
        ]

    def create(self, lecturer_id: str, education: CreateEducationDTO) -> dict[str, Any]:
        transaction_id = self.client.begin_transaction(
            resourceArn=self.resource_arn,
            secretArn=self.secret_arn,
            database=self.database,
        )["transactionId"]
        try:
            lecturer_rows = self._execute(
                """
                SELECT id
                FROM faculty
                WHERE id = :lecturer_id AND status = 'ACTIVE'
                FOR UPDATE
                """,
                {"lecturer_id": lecturer_id},
                transaction_id,
            )
            if not lecturer_rows:
                raise LecturerNotFoundError(lecturer_id)

            display_order = education.display_order
            if display_order is None:
                order_rows = self._execute(
                    """
                    SELECT COALESCE(MAX(display_order) + 1, 0) AS display_order
                    FROM faculty_education
                    WHERE faculty_id = :lecturer_id
                    """,
                    {"lecturer_id": lecturer_id},
                    transaction_id,
                )
                display_order = order_rows[0]["display_order"]

            education_id = f"edu_{uuid.uuid4().hex}"
            rows = self._execute(
                """
                INSERT INTO faculty_education (
                    id, faculty_id, degree, field_of_study, institution, country,
                    graduation_year, display_order
                )
                VALUES (
                    :id, :lecturer_id, :degree, :field_of_study, :institution, :country,
                    :graduation_year, :display_order
                )
                RETURNING id, faculty_id, degree, field_of_study, institution, country,
                          graduation_year, display_order,
                          created_at::text AS created_at, updated_at::text AS updated_at
                """,
                {
                    "id": education_id,
                    "lecturer_id": lecturer_id,
                    "degree": education.degree,
                    "field_of_study": education.field_of_study,
                    "institution": education.institution,
                    "country": education.country,
                    "graduation_year": education.graduation_year,
                    "display_order": display_order,
                },
                transaction_id,
            )
            if not rows:
                raise RuntimeError("Education insert returned no record")

            self.client.commit_transaction(
                resourceArn=self.resource_arn,
                secretArn=self.secret_arn,
                transactionId=transaction_id,
            )
            return rows[0]
        except Exception:
            try:
                self.client.rollback_transaction(
                    resourceArn=self.resource_arn,
                    secretArn=self.secret_arn,
                    transactionId=transaction_id,
                )
            except Exception:
                LOGGER.exception("Failed to roll back lecturer education transaction")
            raise

    def list_for_lecturer(self, lecturer_id: str) -> list[dict[str, Any]]:
        lecturer_rows = self._execute(
            """
            SELECT id
            FROM faculty
            WHERE id = :lecturer_id AND status = 'ACTIVE'
            """,
            {"lecturer_id": lecturer_id},
        )
        if not lecturer_rows:
            raise LecturerNotFoundError(lecturer_id)

        return self._execute(
            """
            SELECT id, faculty_id, degree, field_of_study, institution, country,
                   graduation_year, display_order,
                   created_at::text AS created_at, updated_at::text AS updated_at
            FROM faculty_education
            WHERE faculty_id = :lecturer_id
            ORDER BY display_order ASC, created_at ASC, id ASC
            """,
            {"lecturer_id": lecturer_id},
        )

    def get_for_lecturer(
        self,
        lecturer_id: str,
        education_id: str,
    ) -> dict[str, Any]:
        lecturer_rows = self._execute(
            """
            SELECT id
            FROM faculty
            WHERE id = :lecturer_id AND status = 'ACTIVE'
            """,
            {"lecturer_id": lecturer_id},
        )
        if not lecturer_rows:
            raise LecturerNotFoundError(lecturer_id)

        education_rows = self._execute(
            """
            SELECT id, faculty_id, degree, field_of_study, institution, country,
                   graduation_year, display_order,
                   created_at::text AS created_at, updated_at::text AS updated_at
            FROM faculty_education
            WHERE faculty_id = :lecturer_id AND id = :education_id
            """,
            {
                "lecturer_id": lecturer_id,
                "education_id": education_id,
            },
        )
        if not education_rows:
            raise EducationNotFoundError(education_id)
        return education_rows[0]

    def update_for_lecturer(
        self,
        lecturer_id: str,
        education_id: str,
        education: PatchEducationDTO,
    ) -> dict[str, Any]:
        transaction_id = self.client.begin_transaction(
            resourceArn=self.resource_arn,
            secretArn=self.secret_arn,
            database=self.database,
        )["transactionId"]
        try:
            lecturer_rows = self._execute(
                """
                SELECT id
                FROM faculty
                WHERE id = :lecturer_id AND status = 'ACTIVE'
                FOR UPDATE
                """,
                {"lecturer_id": lecturer_id},
                transaction_id,
            )
            if not lecturer_rows:
                raise LecturerNotFoundError(lecturer_id)

            values = {
                "degree": education.degree,
                "field_of_study": education.field_of_study,
                "institution": education.institution,
                "country": education.country,
                "graduation_year": education.graduation_year,
                "display_order": education.display_order,
            }
            fields = sorted(education.provided_fields)
            assignments = ", ".join(
                f"{PATCHABLE_EDUCATION_COLUMNS[field]} = :{field}" for field in fields
            )
            params = {
                "lecturer_id": lecturer_id,
                "education_id": education_id,
                **{field: values[field] for field in fields},
            }
            rows = self._execute(
                f"""
                UPDATE faculty_education
                SET {assignments}, updated_at = now()
                WHERE faculty_id = :lecturer_id AND id = :education_id
                RETURNING id, faculty_id, degree, field_of_study, institution, country,
                          graduation_year, display_order,
                          created_at::text AS created_at, updated_at::text AS updated_at
                """,
                params,
                transaction_id,
            )
            if not rows:
                raise EducationNotFoundError(education_id)

            self.client.commit_transaction(
                resourceArn=self.resource_arn,
                secretArn=self.secret_arn,
                transactionId=transaction_id,
            )
            return rows[0]
        except Exception:
            try:
                self.client.rollback_transaction(
                    resourceArn=self.resource_arn,
                    secretArn=self.secret_arn,
                    transactionId=transaction_id,
                )
            except Exception:
                LOGGER.exception("Failed to roll back lecturer education update transaction")
            raise

    def delete_for_lecturer(self, lecturer_id: str, education_id: str) -> None:
        transaction_id = self.client.begin_transaction(
            resourceArn=self.resource_arn,
            secretArn=self.secret_arn,
            database=self.database,
        )["transactionId"]
        try:
            lecturer_rows = self._execute(
                """
                SELECT id
                FROM faculty
                WHERE id = :lecturer_id AND status = 'ACTIVE'
                FOR UPDATE
                """,
                {"lecturer_id": lecturer_id},
                transaction_id,
            )
            if not lecturer_rows:
                raise LecturerNotFoundError(lecturer_id)

            education_rows = self._execute(
                """
                DELETE FROM faculty_education
                WHERE faculty_id = :lecturer_id AND id = :education_id
                RETURNING id, faculty_id, degree, field_of_study, institution, country,
                          graduation_year, display_order,
                          created_at::text AS created_at, updated_at::text AS updated_at
                """,
                {
                    "lecturer_id": lecturer_id,
                    "education_id": education_id,
                },
                transaction_id,
            )
            if not education_rows:
                raise EducationNotFoundError(education_id)

            self._execute(
                """
                INSERT INTO audit_event (
                    id, action, entity_type, entity_id, before_json
                )
                VALUES (
                    :id, 'DELETE', 'FACULTY_EDUCATION', :entity_id,
                    CAST(:before_json AS jsonb)
                )
                """,
                {
                    "id": f"audit_{uuid.uuid4().hex}",
                    "entity_id": education_id,
                    "before_json": json.dumps(education_rows[0], ensure_ascii=False),
                },
                transaction_id,
            )

            self.client.commit_transaction(
                resourceArn=self.resource_arn,
                secretArn=self.secret_arn,
                transactionId=transaction_id,
            )
        except Exception:
            try:
                self.client.rollback_transaction(
                    resourceArn=self.resource_arn,
                    secretArn=self.secret_arn,
                    transactionId=transaction_id,
                )
            except Exception:
                LOGGER.exception("Failed to roll back lecturer education deletion transaction")
            raise


def _data_api_param(name: str, value: Any) -> dict[str, Any]:
    if value is None:
        data_value = {"isNull": True}
    elif isinstance(value, bool):
        data_value = {"booleanValue": value}
    elif isinstance(value, int):
        data_value = {"longValue": value}
    elif isinstance(value, float):
        data_value = {"doubleValue": value}
    else:
        data_value = {"stringValue": str(value)}
    return {"name": name, "value": data_value}


def _field_value(field: dict[str, Any]) -> Any:
    if field.get("isNull"):
        return None
    for key in ("stringValue", "longValue", "doubleValue", "booleanValue"):
        if key in field:
            return field[key]
    return None
