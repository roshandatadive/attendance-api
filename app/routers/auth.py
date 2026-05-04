from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserRead
from app.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    # Accept JSON body (preferred)
    payload: LoginRequest | None = None,
    # Optionally accept form-data (email/password) for backward compatibility
    email: str = Form(None),
    password: str = Form(None),
    db: Annotated[Session, Depends(get_db)] = Depends(get_db),
) -> TokenResponse:
    """
    Login endpoint supporting both JSON and form-data.
    Defensive approach: handles invalid input gracefully without 500 errors.
    """
    # Extract credentials from JSON or form-data
    login_email = None
    login_password = None

    if payload:
        # JSON input (preferred)
        login_email = payload.email
        login_password = payload.password
    elif email and password:
        # Form-data fallback
        login_email = email
        login_password = password
    else:
        # Invalid input: return 422 instead of 500
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required fields: email and password",
        )

    # Validate credentials
    user = db.scalar(select(User).where(User.email == login_email))
    if user is None or not verify_password(login_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user))
