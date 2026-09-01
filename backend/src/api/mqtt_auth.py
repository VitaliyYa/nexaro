from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from src.auth.supabase import get_supabase_admin_client
from src.config import Settings, get_settings
from src.schemas.generated.api.mqtt_auth import (
    AclCheckRequest,
    SuperuserAuthRequest,
    UserAuthRequest,
)
from src.services.mqtt_auth_service import is_topic_allowed_for_edge, verify_password_hash

router = APIRouter(prefix="/auth/mqtt", tags=["MQTT Mosquitto Auth Webhooks"])


@router.post("/user", status_code=status.HTTP_200_OK)
async def authenticate_mqtt_user(
    body: UserAuthRequest,
    settings: Settings = Depends(get_settings),
    admin_db: Client = Depends(get_supabase_admin_client),
):
    """
    Mosquitto /user webhook for checking MQTT credentials.
    Returns 200 if credentials are valid, 401/403 otherwise.
    """
    # 1. Check system backend worker credentials
    if body.username == settings.MQTT_WORKER_USERNAME:
        if body.password == settings.MQTT_WORKER_PASSWORD:
            return {"status": "ok", "user": body.username}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid backend worker credentials",
        )

    # 2. Check Edge Node credentials from Supabase mqtt_credentials table
    response = (
        admin_db.table("mqtt_credentials")
        .select("id, property_id, password_hash, is_active")
        .eq("username", body.username)
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

    if not verify_password_hash(body.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MQTT password",
        )

    return {"status": "ok", "user": body.username, "property_id": record.get("property_id")}


@router.post("/superuser", status_code=status.HTTP_200_OK)
async def authenticate_mqtt_superuser(
    body: SuperuserAuthRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Mosquitto /superuser webhook.
    Only the backend worker has superuser status across all tenant topics.
    """
    if body.username == settings.MQTT_WORKER_USERNAME:
        return {"status": "ok", "superuser": True}

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User is not an MQTT superuser",
    )


@router.post("/acl", status_code=status.HTTP_200_OK)
async def check_mqtt_acl(
    body: AclCheckRequest,
    settings: Settings = Depends(get_settings),
    admin_db: Client = Depends(get_supabase_admin_client),
):
    """
    Mosquitto /acl webhook.
    Enforces multi-tenant isolation so Edge nodes only access their property namespace.
    """
    # 1. Superuser backend worker can access any topic in properties/
    if body.username == settings.MQTT_WORKER_USERNAME:
        if body.topic.startswith("properties/") or body.topic == "$SYS/#":
            return {"status": "ok", "allowed": True}
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Backend worker attempted out-of-scope topic",
        )

    # 2. Lookup Edge node property_id from DB
    response = (
        admin_db.table("mqtt_credentials")
        .select("property_id, is_active")
        .eq("username", body.username)
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
    if not is_topic_allowed_for_edge(property_id, body.topic, body.acc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Topic access denied for property {property_id}",
        )

    return {"status": "ok", "allowed": True}
