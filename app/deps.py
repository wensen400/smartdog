from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .config import SESSION_MAX_AGE
from .database import get_db
from .models import User
from .security import create_session_token, parse_session_token

SESSION_COOKIE = "smartdog_session"


def set_session_cookie(response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user_id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)
    user_id = parse_session_token(token)
    user = db.get(User, user_id) if user_id is not None else None
    request.state.current_user = user
    return user
