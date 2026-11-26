from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import clear_session_cookie, get_optional_user, set_session_cookie
from ..models import User
from ..security import hash_password, verify_password
from ..templating import render

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/register")
def register_form(request: Request, current_user: User | None = Depends(get_optional_user)):
    if current_user:
        return RedirectResponse("/", status_code=302)
    return render(request, "register.html")


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    email = email.strip().lower()
    errors = []

    if not username or len(username) < 2:
        errors.append("用户名至少 2 个字符")
    if not email or "@" not in email:
        errors.append("邮箱格式不正确")
    if len(password) < 6:
        errors.append("密码至少 6 位")
    if password != confirm_password:
        errors.append("两次密码不一致")
    if db.query(User).filter(User.username == username).first():
        errors.append("用户名已被使用")
    if db.query(User).filter(User.email == email).first():
        errors.append("邮箱已被注册")

    if errors:
        return render(
            request, "register.html", errors=errors, username=username, email=email, status_code=400
        )

    user = User(username=username, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    response = RedirectResponse("/", status_code=302)
    set_session_cookie(response, user.id)
    return response


@router.get("/login")
def login_form(
    request: Request,
    next: str | None = None,
    current_user: User | None = Depends(get_optional_user),
):
    if current_user:
        return RedirectResponse("/", status_code=302)
    return render(request, "login.html", next=next)


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(None),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.password_hash):
        return render(
            request, "login.html", errors=["邮箱或密码错误"], email=email, next=next, status_code=400
        )

    target = next if next and next.startswith("/") else "/"
    response = RedirectResponse(target, status_code=302)
    set_session_cookie(response, user.id)
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    clear_session_cookie(response)
    return response
