"""
Admin endpoints — triage analytics and session management.
Protected by role-based access (role == 'admin').
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.triage_session import TriageSession
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that checks the current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


@router.get("/stats")
def admin_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Dashboard summary statistics:
    - Total triage sessions
    - Severity breakdown
    - Appointment conversion rate
    """
    total_triages = db.query(func.count(TriageSession.id)).scalar() or 0

    severity_counts = (
        db.query(TriageSession.severity, func.count(TriageSession.id))
        .group_by(TriageSession.severity)
        .all()
    )
    severity_breakdown = {sev or "unassessed": count for sev, count in severity_counts}

    total_appointments = db.query(func.count(Appointment.id)).scalar() or 0
    conversion_rate = (
        round((total_appointments / total_triages) * 100, 1)
        if total_triages > 0
        else 0.0
    )

    high_severity = sum(
        count for sev, count in severity_counts
        if sev in ("high", "emergency")
    )

    return {
        "total_triages": total_triages,
        "high_severity_cases": high_severity,
        "total_appointments": total_appointments,
        "conversion_rate": conversion_rate,
        "severity_breakdown": severity_breakdown,
    }


@router.get("/sessions")
def admin_triage_sessions(
    severity: Optional[str] = Query(default=None, description="Filter by severity level"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List recent triage sessions with optional severity filter, paginated."""
    query = db.query(TriageSession, User).join(User, TriageSession.patient_id == User.id)

    if severity:
        query = query.filter(TriageSession.severity == severity.lower())

    total = query.count()
    sessions = (
        query.order_by(TriageSession.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "sessions": [
            {
                "id": ts.id,
                "patient_name": user.full_name,
                "patient_email": user.email,
                "chief_complaint": ts.chief_complaint,
                "severity": ts.severity,
                "ai_recommendation": ts.ai_recommendation,
                "created_at": ts.created_at.isoformat() if ts.created_at else None,
            }
            for ts, user in sessions
        ],
    }
