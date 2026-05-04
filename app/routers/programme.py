from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.models import Attendance, Batch, BatchStudent, Session, User
from app.security import require_roles


router = APIRouter(prefix="/programme", tags=["programme"])


@router.get("/summary")
def get_programme_summary(
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("programme_manager"))],
    programme_id: int | None = None,
) -> dict[str, int]:
    batch_filters = []
    if programme_id is not None:
        batch_filters.append(Batch.programme_id == programme_id)

    total_batches = db.scalar(select(func.count(Batch.id)).where(*batch_filters))
    total_students = db.scalar(
        select(func.count(BatchStudent.student_id))
        .join(Batch, BatchStudent.batch_id == Batch.id)
        .where(*batch_filters)
    )
    total_sessions = db.scalar(
        select(func.count(Session.id))
        .join(Batch, Session.batch_id == Batch.id)
        .where(*batch_filters)
    )
    total_attendance = db.scalar(
        select(func.count(Attendance.id))
        .join(Session, Attendance.session_id == Session.id)
        .join(Batch, Session.batch_id == Batch.id)
        .where(*batch_filters)
    )

    return {
        "total_batches": total_batches or 0,
        "total_students": total_students or 0,
        "total_sessions": total_sessions or 0,
        "total_attendance": total_attendance or 0,
    }
