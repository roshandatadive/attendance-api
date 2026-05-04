from datetime import date, datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonitoringTokenRequest(BaseModel):
    api_key: str


class BatchCreate(BaseModel):
    name: str
    institution_id: int | None = None
    programme_id: int | None = None


class BatchRead(BaseModel):
    id: int
    name: str
    institution_id: int | None
    programme_id: int | None

    model_config = {"from_attributes": True}


class BatchInviteRead(BaseModel):
    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}


class BatchJoinRequest(BaseModel):
    token: str


class BatchJoinRead(BaseModel):
    batch_id: int
    student_id: int


class SessionCreate(BaseModel):
    batch_id: int
    session_date: date


class SessionRead(BaseModel):
    id: int
    batch_id: int
    session_date: date

    model_config = {"from_attributes": True}


class AttendanceCreate(BaseModel):
    session_id: int
    status: str = "present"


class AttendanceRead(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: str
    marked_at: datetime

    model_config = {"from_attributes": True}
