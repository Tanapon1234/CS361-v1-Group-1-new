"""V2 public master data API backed by Aurora PostgreSQL through RDS Data API."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Iterable

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

VALID_SEMESTERS = {"1", "2", "3", "SUMMER", "OTHER"}
PUBLIC_VISIBILITY = "PUBLIC"
ACTIVE_STATUS = "ACTIVE"

JSON_HEADERS = {
    "content-type": "application/json; charset=utf-8",
    "access-control-allow-origin": "*",
}


class MasterDataQueryError(Exception):
    """Validation error returned to public API callers."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.code = "INVALID_QUERY"
        self.status = 400
        self.details = {"field": field}


class MasterDataRouteError(Exception):
    """Route/method error returned to public API callers."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def _json_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
    }


def _error_response(error: Exception) -> dict[str, Any]:
    if isinstance(error, MasterDataQueryError):
        return _json_response(
            error.status,
            {
                "error": {
                    "code": error.code,
                    "message": str(error),
                    "details": error.details,
                }
            },
        )

    if isinstance(error, MasterDataRouteError):
        return _json_response(
            error.status,
            {
                "error": {
                    "code": error.code,
                    "message": str(error),
                }
            },
        )

    LOGGER.exception("Unhandled V2 master data API error")
    return _json_response(
        500,
        {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Unable to load V2 master data",
            }
        },
    )


def _envelope(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"items": items, "meta": {"count": len(items)}}


def _query_params(event: dict[str, Any]) -> dict[str, str]:
    params = event.get("queryStringParameters") or {}
    return {str(key): str(value) for key, value in params.items() if value is not None}


def _optional_param(params: dict[str, str], key: str) -> str | None:
    value = params.get(key)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _method(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    return str(http.get("method") or event.get("httpMethod") or "GET").upper()


def _path(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    raw_path = event.get("rawPath") or http.get("path") or event.get("path") or "/"
    path = str(raw_path).rstrip("/")
    return path or "/"


def _parse_year(params: dict[str, str]) -> int | None:
    year = _optional_param(params, "year")
    if year is None:
        return None
    if not year.isdigit() or len(year) != 4:
        raise MasterDataQueryError("year", "year must be a 4-digit academic year")
    return int(year)


def _parse_semester(params: dict[str, str]) -> str | None:
    semester = _optional_param(params, "semester")
    if semester is None:
        return None
    if semester not in VALID_SEMESTERS:
        raise MasterDataQueryError("semester", "semester must be one of 1, 2, 3, SUMMER, OTHER")
    return semester


def _parse_active(params: dict[str, str]) -> bool:
    active = _optional_param(params, "active")
    if active is None:
        return True
    if active == "true":
        return True
    if active == "false":
        return False
    raise MasterDataQueryError("active", "active must be true or false")


def _parse_public_status(params: dict[str, str]) -> str:
    status = _optional_param(params, "status") or ACTIVE_STATUS
    if status != ACTIVE_STATUS:
        raise MasterDataQueryError("status", "status must be ACTIVE for public master data endpoints")
    return status


def _parse_public_visibility(params: dict[str, str]) -> str:
    visibility = _optional_param(params, "visibility") or PUBLIC_VISIBILITY
    if visibility != PUBLIC_VISIBILITY:
        raise MasterDataQueryError(
            "visibility", "visibility must be PUBLIC for public master data endpoints"
        )
    return visibility


def _public_faculty(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "public_slug": row.get("public_slug"),
        "name_th": row.get("name_th"),
        "name_en": row.get("name_en"),
        "academic_position": row.get("academic_position"),
        "department": row.get("department"),
        "profile_image_url": row.get("profile_image_url"),
        "profile_image_alt": row.get("profile_image_alt"),
    }


class MasterDataRepository:
    """Storage boundary used by the Lambda handler."""

    def list_academic_periods(self, year: int | None, semester: str | None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_evaluation_periods(self, academic_period_id: str | None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_work_categories(self, active: bool) -> list[dict[str, Any]]:
        raise NotImplementedError

    def work_category_exists(self, category_code: str) -> bool:
        raise NotImplementedError

    def list_work_types(self, active: bool, category_code: str | None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_faculties(self, query: str | None, status: str, visibility: str) -> list[dict[str, Any]]:
        raise NotImplementedError


@dataclass
class DataApiMasterDataRepository(MasterDataRepository):
    resource_arn: str
    secret_arn: str
    database: str
    client: Any | None = None

    def __post_init__(self) -> None:
        if self.client is None:
            import boto3

            self.client = boto3.client("rds-data")

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        request: dict[str, Any] = {
            "resourceArn": self.resource_arn,
            "secretArn": self.secret_arn,
            "database": self.database,
            "sql": sql,
        }
        if params:
            request["parameters"] = [_data_api_param(name, value) for name, value in params.items()]

        response = self.client.execute_statement(**request)
        return _records_to_rows(response.get("columnMetadata", []), response.get("records", []))

    def list_academic_periods(self, year: int | None, semester: str | None) -> list[dict[str, Any]]:
        where: list[str] = []
        params: dict[str, Any] = {}
        if year is not None:
            where.append("academic_year = :year")
            params["year"] = year
        if semester is not None:
            where.append("semester = :semester")
            params["semester"] = semester

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        return self.execute(
            f"""
            SELECT id, academic_year, semester, label,
                   start_date::text AS start_date,
                   end_date::text AS end_date
            FROM academic_period
            {where_clause}
            ORDER BY academic_year DESC,
              CASE semester
                WHEN '3' THEN 5
                WHEN '2' THEN 4
                WHEN '1' THEN 3
                WHEN 'SUMMER' THEN 2
                WHEN 'OTHER' THEN 1
                ELSE 0
              END DESC
            """,
            params,
        )

    def list_evaluation_periods(self, academic_period_id: str | None) -> list[dict[str, Any]]:
        where = ""
        params: dict[str, Any] = {}
        if academic_period_id:
            where = "WHERE academic_period_id = :academic_period_id"
            params["academic_period_id"] = academic_period_id

        return self.execute(
            f"""
            SELECT id, code, label,
                   start_date::text AS start_date,
                   end_date::text AS end_date,
                   academic_period_id
            FROM evaluation_period
            {where}
            ORDER BY start_date DESC, code ASC
            """,
            params,
        )

    def list_work_categories(self, active: bool) -> list[dict[str, Any]]:
        return self.execute(
            """
            SELECT code, label_th, label_en, description, display_order, is_active
            FROM work_category
            WHERE is_active = :active
            ORDER BY display_order ASC, code ASC
            """,
            {"active": active},
        )

    def work_category_exists(self, category_code: str) -> bool:
        rows = self.execute(
            """
            SELECT code
            FROM work_category
            WHERE code = :category_code
            LIMIT 1
            """,
            {"category_code": category_code},
        )
        return bool(rows)

    def list_work_types(self, active: bool, category_code: str | None) -> list[dict[str, Any]]:
        where = ["wt.is_active = :active"]
        params: dict[str, Any] = {"active": active}
        if category_code:
            where.append("wt.category_code = :category_code")
            params["category_code"] = category_code

        return self.execute(
            f"""
            SELECT wt.code, wt.category_code, wt.label_th, wt.label_en,
                   wt.description, wt.default_visibility, wt.display_order, wt.is_active
            FROM work_type wt
            JOIN work_category wc ON wc.code = wt.category_code
            WHERE {' AND '.join(where)}
            ORDER BY wc.display_order ASC, wt.display_order ASC, wt.code ASC
            """,
            params,
        )

    def list_faculties(self, query: str | None, status: str, visibility: str) -> list[dict[str, Any]]:
        where = ["status = :status", "visibility = :visibility"]
        params: dict[str, Any] = {"status": status, "visibility": visibility}

        if query:
            where.append(
                """(
                    public_slug ILIKE :query
                    OR name_th ILIKE :query
                    OR name_en ILIKE :query
                    OR academic_position ILIKE :query
                    OR department ILIKE :query
                )"""
            )
            params["query"] = f"%{query}%"

        return self.execute(
            f"""
            SELECT id, public_slug, name_th, name_en, academic_position, department,
                   profile_image_url, profile_image_alt
            FROM faculty
            WHERE {' AND '.join(where)}
            ORDER BY COALESCE(NULLIF(name_th, ''), NULLIF(name_en, ''), public_slug) ASC
            """,
            params,
        )


def _data_api_param(name: str, value: Any) -> dict[str, Any]:
    field: dict[str, Any]
    if value is None:
        field = {"isNull": True}
    elif isinstance(value, bool):
        field = {"booleanValue": value}
    elif isinstance(value, int):
        field = {"longValue": value}
    elif isinstance(value, float):
        field = {"doubleValue": value}
    else:
        field = {"stringValue": str(value)}
    return {"name": name, "value": field}


def _field_value(field: dict[str, Any]) -> Any:
    if field.get("isNull"):
        return None
    for key in ("stringValue", "longValue", "doubleValue", "booleanValue"):
        if key in field:
            return field[key]
    if "blobValue" in field:
        return field["blobValue"]
    return None


def _records_to_rows(
    column_metadata: Iterable[dict[str, Any]], records: Iterable[list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    columns = [column.get("label") or column.get("name") for column in column_metadata]
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.append({str(column): _field_value(field) for column, field in zip(columns, record)})
    return rows


class MasterDataService:
    def __init__(self, repository: MasterDataRepository) -> None:
        self.repository = repository

    def list_academic_periods(self, params: dict[str, str]) -> dict[str, Any]:
        items = self.repository.list_academic_periods(_parse_year(params), _parse_semester(params))
        return _envelope(items)

    def list_evaluation_periods(self, params: dict[str, str]) -> dict[str, Any]:
        academic_period_id = _optional_param(params, "academic_period_id")
        return _envelope(self.repository.list_evaluation_periods(academic_period_id))

    def list_work_categories(self, params: dict[str, str]) -> dict[str, Any]:
        return _envelope(self.repository.list_work_categories(_parse_active(params)))

    def list_work_types(self, params: dict[str, str]) -> dict[str, Any]:
        active = _parse_active(params)
        category = _optional_param(params, "category")
        if category and not self.repository.work_category_exists(category):
            raise MasterDataQueryError("category", "category must be a known work category code")
        return _envelope(self.repository.list_work_types(active, category))

    def list_faculties(self, params: dict[str, str]) -> dict[str, Any]:
        query = _optional_param(params, "q")
        status = _parse_public_status(params)
        visibility = _parse_public_visibility(params)
        items = [_public_faculty(row) for row in self.repository.list_faculties(query, status, visibility)]
        return _envelope(items)


_DEFAULT_REPOSITORY: DataApiMasterDataRepository | None = None


def _default_repository() -> DataApiMasterDataRepository:
    global _DEFAULT_REPOSITORY
    if _DEFAULT_REPOSITORY is None:
        resource_arn = os.environ["DB_CLUSTER_ARN"]
        secret_arn = os.environ["DB_SECRET_ARN"]
        database = os.environ["DB_NAME"]
        _DEFAULT_REPOSITORY = DataApiMasterDataRepository(resource_arn, secret_arn, database)
    return _DEFAULT_REPOSITORY


def handle_request(event: dict[str, Any], repository: MasterDataRepository | None = None) -> dict[str, Any]:
    try:
        if _method(event) != "GET":
            raise MasterDataRouteError(405, "METHOD_NOT_ALLOWED", "Only GET is supported")

        params = _query_params(event)
        service = MasterDataService(repository or _default_repository())
        path = _path(event)

        routes = {
            "/api/v2/academic-periods": service.list_academic_periods,
            "/api/v2/evaluation-periods": service.list_evaluation_periods,
            "/api/v2/work-categories": service.list_work_categories,
            "/api/v2/work-types": service.list_work_types,
            "/api/v2/faculties": service.list_faculties,
        }
        route = routes.get(path)
        if route is None:
            raise MasterDataRouteError(404, "NOT_FOUND", "V2 master data route not found")

        body = route(params)
        LOGGER.info(
            "v2_master_data_request path=%s status=200 count=%s",
            path,
            body.get("meta", {}).get("count"),
        )
        return _json_response(200, body)
    except Exception as error:
        return _error_response(error)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return handle_request(event)
