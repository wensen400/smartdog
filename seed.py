"""演示数据种子脚本：创建两个用户、各自宠物与若干帖子。

用法：
    .venv/bin/python seed.py
"""
from app.database import Base, SessionLocal, engine
from app.models import Pet, Post, User
from app.security import hash_password


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(User).count() > 0:
        print("已有用户数据，跳过种子。")
        db.close()
        return

    alice = User(username="alice", email="alice@example.com", password_hash=hash_password("secret123"), bio="两只毛孩子的铲屎官")
    bob = User(username="bob", email="bob@example.com", password_hash=hash_password("secret123"), bio="爱遛狗的程序员")
    db.add_all([alice, bob])
    db.flush()

    db.add_all([
        Pet(owner_id=alice.id, name="旺财", breed="金毛", birthday=None, bio="温柔的大暖男"),
        Pet(owner_id=alice.id, name="咪咪", breed="英短", birthday=None, bio="高冷小公主"),
        Pet(owner_id=bob.id, name="豆豆", breed="柯基", birthday=None, bio="短腿跑得飞快"),
    ])
    db.add_all([
        Post(author_id=alice.id, title="第一次带旺财去海边", content="看到大海直接冲进去了，开心得不行！"),
        Post(author_id=bob.id, title="豆豆的日常拆家", content="今天又把我拖鞋咬坏了，但看它那无辜的眼神就原谅了。"),
    ])
    db.commit()
    db.close()
    print("种子数据创建完成：alice / bob（密码均为 secret123）")


if __name__ == "__main__":
    main()
