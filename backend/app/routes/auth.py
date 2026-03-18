from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database.db import get_db
from app.database.models import User
from app.schemas.user import UserResponse
from app.services.auth_service import (
    attach_session_cookie,
    clear_session_cookie,
    create_web_session,
    delete_session,
    telegram_auth_enabled,
    telegram_bot_username,
    upsert_user_from_telegram,
    verify_telegram_login,
)

router = APIRouter()


class TelegramLoginPayload(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


@router.get("/config")
def auth_config() -> dict[str, Any]:
    return {
        "telegram_auth_enabled": telegram_auth_enabled(),
        "bot_username": telegram_bot_username(),
    }


@router.post("/telegram/login", response_model=UserResponse)
def telegram_login(payload: TelegramLoginPayload, response: Response, db: Session = Depends(get_db)):
    data = payload.model_dump()
    verify_telegram_login(data)
    user = upsert_user_from_telegram(db, data)
    session = create_web_session(db, user)
    attach_session_cookie(response, session)
    return user


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    delete_session(db, request.cookies.get("yakamy_session"))
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
