from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from .config import get_settings

PBKDF2_ITERATIONS = 100_000


@dataclass(frozen=True)
class AccessTokenPayload:
    user_id: str
    workspace_id: str
    exp: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        iterations_text, salt_hex, digest_hex = password_hash.split("$", maxsplit=2)
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
    except (TypeError, ValueError):
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate.hex(), digest_hex)


def create_access_token(user_id: str, workspace_id: str) -> str:
    settings = get_settings()
    expiry = int((_now() + timedelta(seconds=settings.auth_token_ttl_seconds)).timestamp())
    payload = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "exp": expiry,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_token = _urlsafe_b64encode(payload_bytes)
    signature = hmac.new(
        settings.app_secret_key.encode("utf-8"),
        payload_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{payload_token}.{_urlsafe_b64encode(signature)}"


def decode_access_token(token: str) -> AccessTokenPayload:
    settings = get_settings()

    try:
        payload_token, signature_token = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

    expected_signature = hmac.new(
        settings.app_secret_key.encode("utf-8"),
        payload_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(_urlsafe_b64encode(expected_signature), signature_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    try:
        payload = json.loads(_urlsafe_b64decode(payload_token))
        token_payload = AccessTokenPayload(
            user_id=payload["user_id"],
            workspace_id=payload["workspace_id"],
            exp=int(payload["exp"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

    if token_payload.exp < int(_now().timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token expired")

    return token_payload
