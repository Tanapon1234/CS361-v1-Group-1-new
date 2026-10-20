"""AWS Lambda entry point: API Gateway (HTTP API, payload 2.0) -> the FastAPI app."""

from mangum import Mangum

from app.main import app

# lifespan "off": Lambda freezes between requests, so shutdown hooks would not run anyway
handler = Mangum(app, lifespan="off")
