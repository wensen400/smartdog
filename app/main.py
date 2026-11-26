from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (register models on Base.metadata)
from .config import STATIC_DIR, UPLOAD_DIR
from .database import Base, engine
from .routers import auth, posts, users

Base.metadata.create_all(bind=engine)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="smartdog 智能狗", version="0.1.0")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(users.router)
