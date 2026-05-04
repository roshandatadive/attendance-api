from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.models import Attendance, Batch, BatchStudent, Session, User
from app.security import require_roles


router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/{institution_id}/summary")
def get_institution_summary(
    institution_id: int,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("programme_manager"))],
) -> dict[str, int]:
    total_batches = db.scalar(
        select(func.count(Batch.id)).where(Batch.institution_id == institution_id)
    )
    total_students = db.scalar(
        select(func.count(BatchStudent.student_id))
        .join(Batch, BatchStudent.batch_id == Batch.id)
        .where(Batch.institution_id == institution_id)
    )
    total_sessions = db.scalar(
        select(func.count(Session.id))
        .join(Batch, Session.batch_id == Batch.id)
        .where(Batch.institution_id == institution_id)
    )
    total_attendance = db.scalar(
        select(func.count(Attendance.id))
        .join(Session, Attendance.session_id == Session.id)
        .join(Batch, Session.batch_id == Batch.id)
        .where(Batch.institution_id == institution_id)
    )

    return {
        "total_batches": total_batches or 0,
        "total_students": total_students or 0,
        "total_sessions": total_sessions or 0,
        "total_attendance": total_attendance or 0,
    }
