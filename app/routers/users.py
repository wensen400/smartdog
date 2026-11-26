from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_optional_user
from ..models import Follow, Like, Pet, Post, User
from ..templating import render
from ..uploads import save_image

router = APIRouter(tags=["users"])


@router.get("/following")
def following_feed(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse("/auth/login?next=/following", status_code=302)

    followed_ids = [follow.followed_id for follow in current_user.following]
    posts = []
    if followed_ids:
        posts = (
            db.query(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.likes),
                selectinload(Post.comments),
            )
            .filter(Post.author_id.in_(followed_ids))
            .order_by(Post.created_at.desc())
            .all()
        )
    liked_ids = {like.post_id for like in db.query(Like).filter(Like.user_id == current_user.id).all()}
    return render(request, "following.html", posts=posts, liked_post_ids=liked_ids)


@router.get("/users/{username}")
def profile(
    request: Request,
    username: str,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .options(
            selectinload(User.pets),
            selectinload(User.following),
            selectinload(User.followers),
        )
        .filter(User.username == username)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    posts = (
        db.query(Post)
        .options(selectinload(Post.likes), selectinload(Post.comments))
        .filter(Post.author_id == user.id)
        .order_by(Post.created_at.desc())
        .all()
    )

    is_following = current_user is not None and any(
        follow.follower_id == current_user.id for follow in user.followers
    )
    liked_ids = (
        {like.post_id for like in db.query(Like).filter(Like.user_id == current_user.id).all()}
        if current_user
        else set()
    )
    return render(
        request,
        "user_profile.html",
        profile_user=user,
        posts=posts,
        is_following=is_following,
        follower_count=len(user.followers),
        following_count=len(user.following),
        liked_post_ids=liked_ids,
    )


@router.post("/users/{username}/follow")
def toggle_follow(
    username: str,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return JSONResponse({"redirect": "/auth/login"}, status_code=401)
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == current_user.id:
        return JSONResponse({"error": "不能关注自己"}, status_code=400)

    existing = (
        db.query(Follow)
        .filter(Follow.follower_id == current_user.id, Follow.followed_id == target.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        following = False
    else:
        db.add(Follow(follower_id=current_user.id, followed_id=target.id))
        db.commit()
        following = True

    count = db.query(Follow).filter(Follow.followed_id == target.id).count()
    return {"following": following, "count": count}


@router.get("/users/{username}/edit")
def edit_profile_form(
    request: Request,
    username: str,
    current_user: User | None = Depends(get_optional_user),
):
    if not current_user or current_user.username != username:
        return RedirectResponse("/auth/login?next=/users/" + username + "/edit", status_code=302)
    return render(request, "edit_profile.html", profile_user=current_user)


@router.post("/users/{username}/edit")
async def edit_profile(
    request: Request,
    username: str,
    bio: str = Form(""),
    avatar: UploadFile | None = File(None),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user or current_user.username != username:
        return RedirectResponse("/auth/login", status_code=302)

    errors = []
    current_user.bio = bio.strip()
    if avatar and avatar.filename:
        try:
            current_user.avatar = await save_image(avatar)
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        return render(request, "edit_profile.html", profile_user=current_user, errors=errors, status_code=400)
    db.commit()
    return RedirectResponse(f"/users/{username}", status_code=302)


@router.post("/users/{username}/pets")
async def add_pet(
    request: Request,
    username: str,
    name: str = Form(...),
    breed: str = Form(...),
    birthday: str = Form(""),
    bio: str = Form(""),
    avatar: UploadFile | None = File(None),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user or current_user.username != username:
        return RedirectResponse("/auth/login", status_code=302)

    errors = []
    name = name.strip()
    breed = breed.strip()
    if not name:
        errors.append("宠物名字不能为空")
    if not breed:
        errors.append("品种不能为空")

    birthday_date = None
    if birthday:
        try:
            birthday_date = date.fromisoformat(birthday)
        except ValueError:
            errors.append("生日格式不正确")

    avatar_path = None
    if avatar and avatar.filename:
        try:
            avatar_path = await save_image(avatar)
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        return render(request, "edit_profile.html", profile_user=current_user, errors=errors, status_code=400)

    pet = Pet(
        owner_id=current_user.id,
        name=name,
        breed=breed,
        birthday=birthday_date,
        bio=bio.strip(),
        avatar=avatar_path,
    )
    db.add(pet)
    db.commit()
    return RedirectResponse(f"/users/{username}", status_code=302)


@router.post("/pets/{pet_id}/delete")
def delete_pet(
    pet_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse("/auth/login", status_code=302)
    pet = db.get(Pet, pet_id)
    if not pet or pet.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="宠物档案不存在")
    db.delete(pet)
    db.commit()
    return RedirectResponse(f"/users/{current_user.username}/edit", status_code=302)
