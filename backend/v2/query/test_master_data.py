import json
import unittest

from backend.v2.query.master_data import (
    MasterDataRepository,
    _records_to_rows,
    handle_request,
)


class FakeRepository(MasterDataRepository):
    def __init__(self):
        self.academic_periods = [
            {
                "id": "ap-2568-1",
                "academic_year": 2568,
                "semester": "1",
                "label": "1/2568",
                "start_date": "2025-08-01",
                "end_date": "2025-12-31",
            },
            {
                "id": "ap-2567-2",
                "academic_year": 2567,
                "semester": "2",
                "label": "2/2567",
                "start_date": "2025-01-01",
                "end_date": "2025-05-31",
            },
        ]
        self.work_categories = [
            {
                "code": "TEACHING",
                "label_th": "งานสอน",
                "label_en": "Teaching",
                "description": None,
                "display_order": 10,
                "is_active": True,
            },
            {
                "code": "RESEARCH",
                "label_th": "งานวิจัย",
                "label_en": "Research",
                "description": None,
                "display_order": 20,
                "is_active": True,
            },
        ]
        self.faculties = [
            {
                "id": "fac_prapaporn-rattanatamrong",
                "public_slug": "prapaporn-rattanatamrong",
                "name_th": "ผศ.ดร.ประภาพร รัตนธำรง",
                "name_en": "Asst.Prof.Dr. Prapaporn Rattanatamrong",
                "academic_position": "ผู้ช่วยศาสตราจารย์",
                "department": "Computer Science",
                "profile_image_url": "https://example.test/prapaporn.jpg",
                "profile_image_alt": "ผศ.ดร.ประภาพร รัตนธำรง",
                "email_public": "must-not-leak@example.test",
            }
        ]

    def list_academic_periods(self, year, semester):
        return [
            row
            for row in self.academic_periods
            if (year is None or row["academic_year"] == year)
            and (semester is None or row["semester"] == semester)
        ]

    def list_evaluation_periods(self, academic_period_id):
        return [
            {
                "id": "ep-2567-2",
                "code": "PPR-2567-2",
                "label": "รอบประเมิน 2/2567",
                "start_date": "2025-01-01",
                "end_date": "2025-05-31",
                "academic_period_id": "ap-2567-2",
            }
        ]

    def list_work_categories(self, active):
        return [row for row in self.work_categories if row["is_active"] == active]

    def work_category_exists(self, category_code):
        return any(row["code"] == category_code for row in self.work_categories)

    def list_work_types(self, active, category_code):
        rows = [
            {
                "code": "PUBLICATION",
                "category_code": "RESEARCH",
                "label_th": "ผลงานตีพิมพ์",
                "label_en": "Publication",
                "description": None,
                "default_visibility": "PUBLIC",
                "display_order": 210,
                "is_active": True,
            }
        ]
        return [
            row
            for row in rows
            if row["is_active"] == active
            and (category_code is None or row["category_code"] == category_code)
        ]

    def list_faculties(self, query, status, visibility):
        return [
            row
            for row in self.faculties
            if query is None or query.lower() in row["public_slug"].lower()
        ]


def api_event(path, query=None, method="GET"):
    return {
        "rawPath": path,
        "queryStringParameters": query or {},
        "requestContext": {"http": {"method": method, "path": path}},
    }


def response_body(response):
    return json.loads(response["body"])


class MasterDataApiTest(unittest.TestCase):
    def setUp(self):
        self.repository = FakeRepository()

    def test_academic_periods_filter_uses_uniform_envelope(self):
        response = handle_request(
            api_event(
                "/api/v2/academic-periods",
                {"year": "2567", "semester": "2"},
            ),
            self.repository,
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response_body(response)["items"][0]["id"], "ap-2567-2")
        self.assertEqual(response_body(response)["meta"], {"count": 1})

    def test_invalid_semester_returns_public_error_shape(self):
        response = handle_request(
            api_event("/api/v2/academic-periods", {"semester": "4"}),
            self.repository,
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body(response)["error"]["code"], "INVALID_QUERY")
        self.assertEqual(response_body(response)["error"]["details"], {"field": "semester"})

    def test_work_types_validate_known_category(self):
        response = handle_request(
            api_event("/api/v2/work-types", {"category": "UNKNOWN"}),
            self.repository,
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body(response)["error"]["details"], {"field": "category"})

    def test_work_types_filter_by_category(self):
        response = handle_request(
            api_event("/api/v2/work-types", {"category": "RESEARCH"}),
            self.repository,
        )

        body = response_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["items"][0]["code"], "PUBLICATION")
        self.assertEqual(body["meta"], {"count": 1})

    def test_faculties_return_only_public_safe_fields(self):
        response = handle_request(
            api_event("/api/v2/faculties", {"q": "prapaporn"}),
            self.repository,
        )

        item = response_body(response)["items"][0]
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(item["public_slug"], "prapaporn-rattanatamrong")
        self.assertNotIn("email_public", item)
        self.assertEqual(
            sorted(item.keys()),
            [
                "academic_position",
                "department",
                "id",
                "name_en",
                "name_th",
                "profile_image_alt",
                "profile_image_url",
                "public_slug",
            ],
        )

    def test_public_endpoint_rejects_internal_visibility(self):
        response = handle_request(
            api_event("/api/v2/faculties", {"visibility": "INTERNAL"}),
            self.repository,
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body(response)["error"]["details"], {"field": "visibility"})

    def test_method_not_allowed_does_not_leak_stack_trace(self):
        response = handle_request(api_event("/api/v2/faculties", method="POST"), self.repository)

        body = response_body(response)
        self.assertEqual(response["statusCode"], 405)
        self.assertEqual(body["error"]["code"], "METHOD_NOT_ALLOWED")
        self.assertNotIn("Traceback", response["body"])

    def test_data_api_record_conversion(self):
        rows = _records_to_rows(
            [
                {"name": "code"},
                {"label": "is_active"},
                {"name": "description"},
            ],
            [
                [
                    {"stringValue": "TEACHING"},
                    {"booleanValue": True},
                    {"isNull": True},
                ]
            ],
        )

        self.assertEqual(
            rows,
            [{"code": "TEACHING", "is_active": True, "description": None}],
        )


if __name__ == "__main__":
    unittest.main()
