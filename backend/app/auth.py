from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import User
from app.services.auth_service import get_or_create_user_from_headers, get_user_by_session_token


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    session_token = request.cookies.get("yakamy_session")
    user = get_user_by_session_token(db, session_token)
    if user:
        return user
    return get_or_create_user_from_headers(db, request)


def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user
