"""
API v1 router — aggregates all endpoint sub-routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import admin, appointments, auth, triage

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(triage.router)
api_router.include_router(appointments.router)
api_router.include_router(admin.router)
