import uuid

import jwt
import pytest
from fastapi import HTTPException

from src.auth.jwt import verify_supabase_jwt
from src.config import Settings


def test_verify_supabase_jwt_valid():
    user_id = str(uuid.uuid4())
    secret = "my_jwt_super_secret_that_is_at_least_32_bytes_long"
    token = jwt.encode({"sub": user_id, "email": "test@smartrent.io"}, secret, algorithm="HS256")

    settings = Settings(
        SUPABASE_JWT_SECRET=secret,
        SUPABASE_JWT_ALGORITHM="HS256",
    )

    payload = verify_supabase_jwt(token, settings)
    assert payload["sub"] == user_id
    assert payload["email"] == "test@smartrent.io"


def test_verify_supabase_jwt_invalid_secret():
    user_id = str(uuid.uuid4())
    token = jwt.encode({"sub": user_id}, "secret_A_with_at_least_32_characters_for_hmac", algorithm="HS256")

    settings = Settings(
        SUPABASE_JWT_SECRET="secret_B_with_at_least_32_characters_for_hmac",
        SUPABASE_JWT_ALGORITHM="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_supabase_jwt(token, settings)
    assert exc_info.value.status_code == 401


def test_verify_supabase_jwt_malformed():
    settings = Settings(
        SUPABASE_JWT_SECRET="secret_B",
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_supabase_jwt("not.a.valid.jwt.token", settings)
    assert exc_info.value.status_code == 401
