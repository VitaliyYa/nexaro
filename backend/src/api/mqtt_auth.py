import urllib.parse
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from supabase import Client

from src.auth.supabase import get_supabase_admin_client
from src.config import Settings, get_settings
from src.schemas.generated.api.mqtt_auth import (
    Acc,
    AclCheckRequest,
    SuperuserAuthRequest,
    UserAuthRequest,
)
from src.services.mqtt_auth_service import is_topic_allowed_for_edge, verify_password_hash

router = APIRouter(prefix="/auth/mqtt", tags=["MQTT Mosquitto Auth Webhooks"])


async def _parse_request_data(request: Request) -> dict[str, Any]:
    """Extracts payload regardless of whether it was sent as JSON or form-urlencoded."""
    body_bytes = await request.body()
    if not body_bytes:
        return {}

    # 1. Try JSON
    try:
        import json

        data = json.loads(body_bytes.decode("utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Try URL-encoded query string
    try:
        qs_data = urllib.parse.parse_qs(body_bytes.decode("utf-8"))
        if qs_data:
            return {k: v[0] if len(v) == 1 else v for k, v in qs_data.items()}
    except Exception:
        pass

    # 3. Try request.form() if available
    try:
        form = await request.form()
        if form:
            return dict(form)
    except Exception:
        pass

    return {}


@router.post("/user", status_code=status.HTTP_200_OK)
async def authenticate_mqtt_user(
    request: Request,
    body: UserAuthRequest | None = Body(None),
    settings: Settings = Depends(get_settings),
    admin_db: Client = Depends(get_supabase_admin_client),
):
    """
    Mosquitto /user webhook for checking MQTT credentials.
    Returns 200 if credentials are valid, 401/403 otherwise.
    """
    if body:
        username = body.username
        password = body.password
    else:
        data = await _parse_request_data(request)
        username = data.get("username") or data.get("user") or ""
        password = data.get("password") or data.get("pw") or ""

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing username or password in MQTT auth request",
        )

    # 1. Check system backend worker credentials
    if username == settings.MQTT_WORKER_USERNAME:
        if password == settings.MQTT_WORKER_PASSWORD:
            return {"status": "ok", "user": username}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid backend worker credentials",
        )

    # 2. Check Edge Node credentials from Supabase mqtt_credentials table
    response = (
        admin_db.table("mqtt_credentials")
        .select("id, property_id, password_hash, is_active")
        .eq("username", username)
        .eq("is_active", True)
        .execute()
    )

    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MQTT user not found or inactive",
        )

    record = response.data[0]
    stored_hash = record.get("password_hash", "")

    if not verify_password_hash(password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MQTT password",
        )

    return {"status": "ok", "user": username, "property_id": record.get("property_id")}


@router.post("/superuser", status_code=status.HTTP_200_OK)
async def authenticate_mqtt_superuser(
    request: Request,
    body: SuperuserAuthRequest | None = Body(None),
    settings: Settings = Depends(get_settings),
):
    """
    Mosquitto /superuser webhook.
    Only the backend worker has superuser status across all tenant topics.
    """
    if body:
        username = body.username
    else:
        data = await _parse_request_data(request)
        username = data.get("username") or data.get("user") or ""

    if username == settings.MQTT_WORKER_USERNAME:
        return {"status": "ok", "superuser": True}

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User is not an MQTT superuser",
    )


@router.post("/acl", status_code=status.HTTP_200_OK)
async def check_mqtt_acl(
    request: Request,
    body: AclCheckRequest | None = Body(None),
    settings: Settings = Depends(get_settings),
    admin_db: Client = Depends(get_supabase_admin_client),
):
    """
    Mosquitto /acl webhook.
    Enforces multi-tenant isolation so Edge nodes only access their property namespace.
    """
    if body:
        username = body.username
        topic = body.topic
        acc = body.acc
    else:
        data = await _parse_request_data(request)
        username = data.get("username") or data.get("user") or ""
        topic = data.get("topic") or ""
        raw_acc = data.get("acc", 1)
        try:
            acc = Acc(int(raw_acc))
        except Exception:
            acc = Acc.integer_1

    # 1. Superuser backend worker can access any topic in properties/
    if username == settings.MQTT_WORKER_USERNAME:
        if topic.startswith("properties/") or topic == "$SYS/#":
            return {"status": "ok", "allowed": True}
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Backend worker attempted out-of-scope topic",
        )

    # 2. Lookup Edge node property_id from DB
    response = (
        admin_db.table("mqtt_credentials")
        .select("property_id, is_active")
        .eq("username", username)
        .eq("is_active", True)
        .execute()
    )

    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unknown or inactive MQTT edge user",
        )

    property_id = response.data[0]["property_id"]

    # 3. Check topic permission
    if not is_topic_allowed_for_edge(property_id, topic, acc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Topic access denied for property {property_id}",
        )

    return {"status": "ok", "allowed": True}
