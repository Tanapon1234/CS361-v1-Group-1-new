"""API Gateway (HTTP API, payload 2.0) events reach the FastAPI app through Mangum."""

from app.lambda_handler import handler


def http_event(method: str, path: str) -> dict:
    return {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"host": "api.example"},
        "requestContext": {
            "http": {"method": method, "path": path, "sourceIp": "1.1.1.1", "protocol": "HTTP/1.1"},
            "stage": "$default",
        },
        "isBase64Encoded": False,
    }


def test_health_through_the_lambda_handler() -> None:
    response = handler(http_event("GET", "/health"), {})

    assert response["statusCode"] == 200
    assert response["body"] == '{"status":"ok"}'


def test_unknown_route_is_a_problem_json_404() -> None:
    response = handler(http_event("GET", "/api/v2/nope"), {})

    assert response["statusCode"] == 404
    assert response["headers"]["content-type"].startswith("application/problem+json")
