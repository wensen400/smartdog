from datetime import date, datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    """返回无时区信息的 UTC 时间，兼容 SQLite DateTime 存储。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    followers = relationship(
        "Follow",
        foreign_keys="Follow.followed_id",
        back_populates="followed",
        cascade="all, delete-orphan",
    )


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    breed = Column(String(100), nullable=False)
    birthday = Column(Date, nullable=True)
    avatar = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    owner = relationship("User", back_populates="pets")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    image = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),)

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "followed_id", name="uq_follow_pair"),)

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")
