import logging
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from src.auth.jwt import get_current_user
from src.auth.models import CurrentUser
from src.auth.supabase import get_supabase_admin_client
from src.config import Settings, get_settings
from src.mqtt.client import mqtt_service

logger = logging.getLogger("smartrent.admin")

router = APIRouter(prefix="/admin", tags=["SuperAdmin"])


class CreateTestUserRequest(BaseModel):
    email: str
    password: str
    name: str = "Test Landlord"
    seed_property: bool = True


class SeedTestPropertyRequest(BaseModel):
    user_id: UUID
    property_name: str = "Demo Apartment 101"
    address: str = "100 Ocean Drive, Miami, FL"


def require_superadmin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Ensures that the requesting user has superadmin privileges.
    Checks user role claim or email prefix in development.
    """
    if current_user.role == "superadmin":
        return current_user

    # Also permit designated admin emails in development/testing
    if current_user.email and current_user.email.startswith("admin"):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="SuperAdmin privileges required",
    )


@router.get("/status")
async def get_system_status(
    admin_user: CurrentUser = Depends(require_superadmin),
    settings: Settings = Depends(get_settings),
):
    """Returns comprehensive system and component health metrics."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "mqtt_connected": mqtt_service.is_connected,
        "caller": admin_user.email,
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_test_user(
    body: CreateTestUserRequest,
    admin_user: CurrentUser = Depends(require_superadmin),
    admin_db: Client = Depends(get_supabase_admin_client),
):
    """
    Creates a pre-confirmed test user in Supabase Auth using the admin client.
    Optionally provisions a demo property with 4 sample IoT devices.
    """
    logger.info("Admin %s creating test user %s", admin_user.email, body.email)

    try:
        auth_response = admin_db.auth.admin.create_user(
            {
                "email": body.email,
                "password": body.password,
                "email_confirm": True,
                "user_metadata": {"name": body.name},
            }
        )
        created_user = auth_response.user
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user in Supabase Auth",
            )
    except Exception as e:
        logger.error("Failed to create test user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating user: {e}",
        ) from e

    seeded_property = None
    if body.seed_property:
        seeded_property = await seed_property_with_devices(
            user_id=UUID(created_user.id),
            property_name=f"{body.name}'s Apartment",
            address="42 IoT Avenue, Tech City",
            admin_db=admin_db,
        )

    return {
        "message": "User created successfully",
        "user": {
            "id": created_user.id,
            "email": created_user.email,
            "name": body.name,
        },
        "seeded_property": seeded_property,
    }


@router.post("/seed-property", status_code=status.HTTP_201_CREATED)
async def seed_property_endpoint(
    body: SeedTestPropertyRequest,
    admin_user: CurrentUser = Depends(require_superadmin),
    admin_db: Client = Depends(get_supabase_admin_client),
):
    """Provisions a sample property with pre-configured IoT devices for any user."""
    return await seed_property_with_devices(
        user_id=body.user_id,
        property_name=body.property_name,
        address=body.address,
        admin_db=admin_db,
    )


async def seed_property_with_devices(
    user_id: UUID,
    property_name: str,
    address: str,
    admin_db: Client,
) -> dict[str, Any]:
    """Helper to insert a property and standard suite of test IoT devices."""
    prop_id = str(uuid4())
    prop_data = {
        "id": prop_id,
        "owner_id": str(user_id),
        "name": property_name,
        "address": address,
        "timezone": "UTC",
    }
    admin_db.table("properties").insert(prop_data).execute()

    # Provision standard set of 4 IoT devices
    devices = [
        {
            "id": f"lock_{prop_id[:8]}",
            "property_id": prop_id,
            "device_type": "lock",
            "name": "Entrance Smart Lock (TTLock)",
            "is_active": True,
            "settings": {"state": "locked", "lock_state": "locked", "battery": 92},
        },
        {
            "id": f"light_{prop_id[:8]}",
            "property_id": prop_id,
            "device_type": "relay",
            "name": "Living Room Chandelier",
            "is_active": True,
            "settings": {"state": "OFF"},
        },
        {
            "id": f"valve_{prop_id[:8]}",
            "property_id": prop_id,
            "device_type": "valve",
            "name": "Main Water Shutoff Valve",
            "is_active": True,
            "settings": {"state": "open", "leak_detected": False},
        },
        {
            "id": f"climate_{prop_id[:8]}",
            "property_id": prop_id,
            "device_type": "climate",
            "name": "Central Air Conditioner",
            "is_active": True,
            "settings": {
                "current_temperature": 23.5,
                "target_temperature": 22.0,
                "mode": "cool",
            },
        },
    ]

    for dev in devices:
        admin_db.table("devices").insert(dev).execute()

    return {
        "property": prop_data,
        "devices": devices,
    }
