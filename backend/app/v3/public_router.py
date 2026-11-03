"""`/public/v3`: read-only directory for the website, open to anyone.

Kept apart from `api_v3_router` so no endpoint there can be opened by accident: that router
checks every call against ROUTE_RULES, this one has a single controller of GETs and
exposes only the fields in app/v3/dtos/public_faculty_dto.py.
"""

from fastapi import APIRouter

from app.v3.controllers import public_faculty_controller

public_v3_router = APIRouter(prefix="/public/v3")
public_v3_router.include_router(public_faculty_controller.router)
