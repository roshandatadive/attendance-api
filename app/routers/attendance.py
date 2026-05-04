from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.models import Attendance, BatchStudent, Session, User
from app.schemas import AttendanceCreate, AttendanceRead
from app.security import require_roles


router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def mark_attendance(
    payload: AttendanceCreate,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("student"))],
) -> Attendance:
    session = db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    batch_student = db.get(
        BatchStudent,
        {"batch_id": session.batch_id, "student_id": current_user.id},
    )
    if batch_student is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student does not belong to this session batch",
        )

    existing_attendance = db.scalar(
        select(Attendance).where(
            Attendance.session_id == payload.session_id,
            Attendance.student_id == current_user.id,
        )
    )
    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already marked",
        )

    attendance = Attendance(
        session_id=payload.session_id,
        student_id=current_user.id,
        status=payload.status,
        marked_at=datetime.now(timezone.utc),
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance
