import base64
import hashlib
import hmac
import os
import time

from .config import SECRET_KEY, SESSION_MAX_AGE

_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, digest_b64 = stored.split("$", 1)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except (ValueError, base64.binascii.Error):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest, expected)


def _sign(payload: str) -> str:
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_token(user_id: int) -> str:
    expiry = int(time.time()) + SESSION_MAX_AGE
    payload_b64 = base64.urlsafe_b64encode(f"{user_id}:{expiry}".encode()).decode()
    return f"{payload_b64}.{_sign(payload_b64)}"


def parse_session_token(token: str | None) -> int | None:
    if not token:
        return None
    try:
        payload_b64, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(payload_b64)):
            return None
        payload = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        user_id, expiry = payload.split(":", 1)
        if int(time.time()) > int(expiry):
            return None
        return int(user_id)
    except (ValueError, base64.binascii.Error):
        return None
