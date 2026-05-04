from datetime import date, datetime, timedelta, timezone

from app.db import Base, SessionLocal, engine
from app.models import Attendance, Batch, BatchStudent, BatchTrainer, Session, User
from app.security import hash_password


PASSWORD = "password123"


def get_or_create_user(db, name: str, email: str, role: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_batch(
    db,
    name: str,
    institution_id: int,
    programme_id: int,
) -> Batch:
    batch = db.query(Batch).filter(Batch.name == name).first()
    if batch:
        return batch

    batch = Batch(
        name=name,
        institution_id=institution_id,
        programme_id=programme_id,
    )
    db.add(batch)
    db.flush()
    return batch


def assign_trainer(db, batch: Batch, trainer: User) -> None:
    key = {"batch_id": batch.id, "trainer_id": trainer.id}
    if db.get(BatchTrainer, key) is None:
        db.add(BatchTrainer(**key))


def assign_student(db, batch: Batch, student: User) -> None:
    key = {"batch_id": batch.id, "student_id": student.id}
    if db.get(BatchStudent, key) is None:
        db.add(BatchStudent(**key))


def get_or_create_session(db, batch: Batch, session_date: date) -> Session:
    session = (
        db.query(Session)
        .filter(Session.batch_id == batch.id, Session.session_date == session_date)
        .first()
    )
    if session:
        return session

    session = Session(batch_id=batch.id, session_date=session_date)
    db.add(session)
    db.flush()
    return session


def mark_attendance(db, session: Session, student: User, status: str) -> None:
    existing = (
        db.query(Attendance)
        .filter(
            Attendance.session_id == session.id,
            Attendance.student_id == student.id,
        )
        .first()
    )
    if existing:
        return

    db.add(
        Attendance(
            session_id=session.id,
            student_id=student.id,
            status=status,
            marked_at=datetime.now(timezone.utc),
        )
    )


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        institutions = [
            get_or_create_user(db, "Institution One", "institution@example.com", "institution"),
            get_or_create_user(db, "Institution Two", "institution2@example.com", "institution"),
        ]
        trainers = [
            get_or_create_user(db, "Trainer One", "trainer@example.com", "trainer"),
            get_or_create_user(db, "Trainer Two", "trainer2@example.com", "trainer"),
            get_or_create_user(db, "Trainer Three", "trainer3@example.com", "trainer"),
            get_or_create_user(db, "Trainer Four", "trainer4@example.com", "trainer"),
        ]
        students = [
            get_or_create_user(
                db,
                f"Student {index}",
                "student@example.com" if index == 1 else f"student{index}@example.com",
                "student",
            )
            for index in range(1, 16)
        ]
        get_or_create_user(
            db,
            "Programme Manager",
            "programme_manager@example.com",
            "programme_manager",
        )
        get_or_create_user(
            db,
            "Monitoring Officer",
            "monitoring_officer@example.com",
            "monitoring_officer",
        )

        batches = [
            get_or_create_batch(db, "Backend Batch", institutions[0].id, 1),
            get_or_create_batch(db, "Frontend Batch", institutions[0].id, 1),
            get_or_create_batch(db, "Data Batch", institutions[1].id, 2),
        ]

        assign_trainer(db, batches[0], trainers[0])
        assign_trainer(db, batches[0], trainers[1])
        assign_trainer(db, batches[1], trainers[2])
        assign_trainer(db, batches[2], trainers[3])

        for student in students[:6]:
            assign_student(db, batches[0], student)
        for student in students[6:11]:
            assign_student(db, batches[1], student)
        for student in students[11:]:
            assign_student(db, batches[2], student)

        today = date.today()
        session_plan = [
            (batches[0], today - timedelta(days=7)),
            (batches[0], today - timedelta(days=6)),
            (batches[0], today - timedelta(days=5)),
            (batches[1], today - timedelta(days=4)),
            (batches[1], today - timedelta(days=3)),
            (batches[1], today - timedelta(days=2)),
            (batches[2], today - timedelta(days=1)),
            (batches[2], today),
        ]
        sessions = [get_or_create_session(db, batch, session_date) for batch, session_date in session_plan]

        batch_students = {
            batches[0].id: students[:6],
            batches[1].id: students[6:11],
            batches[2].id: students[11:],
        }
        for session in sessions:
            for index, student in enumerate(batch_students[session.batch_id]):
                status = "present" if index % 4 != 0 else "absent"
                mark_attendance(db, session, student, status)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
