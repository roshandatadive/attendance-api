from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.models import Attendance, Batch, BatchTrainer, Session, User
from app.schemas import SessionCreate, SessionRead
from app.security import require_roles


router = APIRouter(prefix="/sessions", tags=["sessions"])


def trainer_has_batch(db: DbSession, trainer_id: int, batch_id: int) -> bool:
    return db.get(
        BatchTrainer,
        {"batch_id": batch_id, "trainer_id": trainer_id},
    ) is not None


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("trainer"))],
) -> Session:
    batch = db.get(Batch, payload.batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )
    if not trainer_has_batch(db, current_user.id, batch.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trainer cannot manage this batch",
        )

    session = Session(
        batch_id=payload.batch_id,
        session_date=payload.session_date,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/attendance")
def get_session_attendance(
    session_id: int,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("trainer"))],
) -> dict:
    session = db.get(Session, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if not trainer_has_batch(db, current_user.id, session.batch_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trainer cannot access this session",
        )

    rows = db.execute(
        select(Attendance.status, func.count(Attendance.id))
        .where(Attendance.session_id == session_id)
        .group_by(Attendance.status)
    ).all()
    status_counts = {status: count for status, count in rows}

    return {
        "total_attendance": sum(status_counts.values()),
        "status_counts": status_counts,
    }
