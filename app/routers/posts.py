from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_optional_user
from ..models import Comment, Like, Post, User
from ..templating import render
from ..uploads import save_image

router = APIRouter(tags=["posts"])


def _liked_post_ids(db: Session, user_id: int) -> set[int]:
    return {like.post_id for like in db.query(Like).filter(Like.user_id == user_id).all()}


@router.get("/")
def feed(
    request: Request,
    sort: str = "latest",
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    query = db.query(Post).options(
        selectinload(Post.author),
        selectinload(Post.likes),
        selectinload(Post.comments),
    )
    if sort == "hot":
        posts = sorted(query.all(), key=lambda p: len(p.likes), reverse=True)
    else:
        posts = query.order_by(Post.created_at.desc()).all()

    liked_ids = _liked_post_ids(db, current_user.id) if current_user else set()
    return render(request, "index.html", posts=posts, sort=sort, liked_post_ids=liked_ids)


@router.get("/posts/new")
def new_post_form(request: Request, current_user: User | None = Depends(get_optional_user)):
    if not current_user:
        return RedirectResponse("/auth/login?next=/posts/new", status_code=302)
    return render(request, "new_post.html")


@router.post("/posts")
async def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    image: UploadFile | None = File(None),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse("/auth/login?next=/posts/new", status_code=302)

    title = title.strip()
    content = content.strip()
    errors = []
    if not title:
        errors.append("标题不能为空")
    if not content:
        errors.append("正文不能为空")

    image_path = None
    if image and image.filename:
        try:
            image_path = await save_image(image)
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        return render(
            request, "new_post.html", errors=errors, title=title, content=content, status_code=400
        )

    post = Post(author_id=current_user.id, title=title, content=content, image=image_path)
    db.add(post)
    db.commit()
    db.refresh(post)
    return RedirectResponse(f"/posts/{post.id}", status_code=302)


@router.get("/posts/{post_id}")
def post_detail(
    request: Request,
    post_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .options(
            selectinload(Post.author),
            selectinload(Post.likes),
            selectinload(Post.comments).selectinload(Comment.author),
        )
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    liked = current_user is not None and any(l.user_id == current_user.id for l in post.likes)
    return render(request, "post_detail.html", post=post, liked=liked)


@router.post("/posts/{post_id}/comments")
def add_comment(
    request: Request,
    post_id: int,
    content: str = Form(...),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse(f"/auth/login?next=/posts/{post_id}", status_code=302)
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    content = content.strip()
    if content:
        db.add(Comment(post_id=post_id, author_id=current_user.id, content=content))
        db.commit()
    return RedirectResponse(f"/posts/{post_id}", status_code=302)


@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return JSONResponse({"redirect": "/auth/login"}, status_code=401)
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    existing = (
        db.query(Like)
        .filter(Like.post_id == post_id, Like.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        liked = False
    else:
        db.add(Like(post_id=post_id, user_id=current_user.id))
        db.commit()
        liked = True

    count = db.query(Like).filter(Like.post_id == post_id).count()
    return {"liked": liked, "count": count}
