import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User


@pytest.fixture()
def db_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_factory):
    def override_get_db():
        db = db_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register(client, username, email, password="secret123"):
    return client.post(
        "/auth/register",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )


def login(client, email, password="secret123"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_register_login_logout(client):
    r = register(client, "alice", "alice@example.com")
    assert r.status_code == 200
    assert "alice" in r.text

    r = client.post("/auth/logout", follow_redirects=True)
    assert "登录" in r.text

    r = login(client, "alice@example.com", "wrongpass")
    assert "邮箱或密码错误" in r.text

    r = login(client, "alice@example.com")
    assert "退出" in r.text


def test_register_validation(client):
    r = client.post(
        "/auth/register",
        data={"username": "a", "email": "bad", "password": "123", "confirm_password": "456"},
    )
    assert r.status_code == 400
    assert "用户名至少 2 个字符" in r.text
    assert "邮箱格式不正确" in r.text
    assert "密码至少 6 位" in r.text
    assert "两次密码不一致" in r.text


def test_password_is_hashed(client, db_factory):
    register(client, "alice", "alice@example.com")
    db = db_factory()
    user = db.query(User).filter(User.username == "alice").first()
    db.close()
    assert user.password_hash != "secret123"
    assert "$" in user.password_hash


def test_create_post_requires_login(client):
    r = client.get("/posts/new", follow_redirects=False)
    assert r.status_code == 302
    assert "/auth/login" in r.headers["location"]


def test_create_post_and_comment(client):
    register(client, "alice", "alice@example.com")
    r = client.post(
        "/posts",
        data={"title": "我的金毛", "content": "今天出去散步了"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    post_url = r.headers["location"]
    assert post_url.startswith("/posts/")

    r = client.get(post_url)
    assert "我的金毛" in r.text
    assert "今天出去散步了" in r.text

    r = client.post(post_url + "/comments", data={"content": "好可爱！"}, follow_redirects=True)
    assert r.status_code == 200
    assert "好可爱！" in r.text


def test_like_toggle(client):
    register(client, "alice", "alice@example.com")
    r = client.post("/posts", data={"title": "t", "content": "c"}, follow_redirects=False)
    post_id = r.headers["location"].rsplit("/", 1)[-1]

    r = client.post(f"/posts/{post_id}/like")
    assert r.json() == {"liked": True, "count": 1}

    r = client.post(f"/posts/{post_id}/like")
    assert r.json() == {"liked": False, "count": 0}


def test_hot_sort(client):
    register(client, "alice", "alice@example.com")
    first = client.post("/posts", data={"title": "first", "content": "a"}, follow_redirects=False)
    second = client.post("/posts", data={"title": "second", "content": "b"}, follow_redirects=False)
    first_id = first.headers["location"].rsplit("/", 1)[-1]
    second_id = second.headers["location"].rsplit("/", 1)[-1]

    client.post(f"/posts/{first_id}/like")

    r = client.get("/?sort=hot")
    assert r.text.index("first") < r.text.index("second")


def test_follow_and_following_feed(client):
    register(client, "alice", "alice@example.com")
    client.post("/auth/logout")
    register(client, "bob", "bob@example.com")

    r = client.post("/users/alice/follow")
    assert r.json()["following"] is True

    # alice 发帖后，bob 的关注动态里应能看到
    client.post("/auth/logout")
    login(client, "alice@example.com")
    client.post("/posts", data={"title": "alice 的帖子", "content": "x"}, follow_redirects=False)
    client.post("/auth/logout")
    login(client, "bob@example.com")

    r = client.get("/following")
    assert "alice 的帖子" in r.text


def test_add_pet_and_profile(client):
    register(client, "alice", "alice@example.com")
    r = client.post(
        "/users/alice/pets",
        data={"name": "旺财", "breed": "金毛", "birthday": "2020-01-01", "bio": "很乖"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert "旺财" in r.text
    assert "金毛" in r.text
