import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database.models import User, WebSession

SESSION_COOKIE_NAME = "yakamy_session"
SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "30"))
TELEGRAM_AUTH_MAX_AGE = int(os.getenv("TELEGRAM_AUTH_MAX_AGE", "86400"))


def telegram_bot_username() -> str:
    return os.getenv("TELEGRAM_BOT_USERNAME", "")


def telegram_auth_enabled() -> bool:
    return bool(os.getenv("TELEGRAM_TOKEN", "") and telegram_bot_username())


def verify_telegram_login(payload: dict[str, Any]) -> None:
    bot_token = os.getenv("TELEGRAM_TOKEN", "")
    if not bot_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram auth is not configured")

    received_hash = payload.get("hash")
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Telegram hash")

    auth_date = int(payload.get("auth_date", 0))
    now = int(datetime.now(UTC).timestamp())
    if now - auth_date > TELEGRAM_AUTH_MAX_AGE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram login data is expired")

    filtered = {
        key: value
        for key, value in payload.items()
        if key != "hash" and value is not None and value != ""
    }
    data_check_string = "\n".join(f"{key}={filtered[key]}" for key in sorted(filtered))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram auth signature")


def upsert_user_from_telegram(db: Session, payload: dict[str, Any]) -> User:
    telegram_id = str(payload["id"])
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db.add(user)

    user.username = payload.get("username")
    user.first_name = payload.get("first_name")
    user.last_name = payload.get("last_name")
    user.photo_url = payload.get("photo_url")

    db.commit()
    db.refresh(user)
    return user


def get_or_create_user_from_headers(db: Session, request: Request) -> User | None:
    telegram_id = request.headers.get("X-Telegram-Id")
    if not telegram_id:
        return None

    payload = {
        "id": telegram_id,
        "username": request.headers.get("X-Telegram-Username"),
        "first_name": request.headers.get("X-Telegram-First-Name"),
        "last_name": request.headers.get("X-Telegram-Last-Name"),
        "photo_url": request.headers.get("X-Telegram-Photo-Url"),
    }
    return upsert_user_from_telegram(db, payload)


def create_web_session(db: Session, user: User) -> WebSession:
    session = WebSession(
        token=secrets.token_urlsafe(48),
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=SESSION_TTL_DAYS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def attach_session_cookie(response: Response, session: WebSession) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME)


def get_user_by_session_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None

    session = db.query(WebSession).filter(WebSession.token == token).first()
    if not session:
        return None

    if session.expires_at < datetime.now(UTC).replace(tzinfo=None):
        db.delete(session)
        db.commit()
        return None

    return session.user


def delete_session(db: Session, token: str | None) -> None:
    if not token:
        return
    session = db.query(WebSession).filter(WebSession.token == token).first()
    if session:
        db.delete(session)
        db.commit()
