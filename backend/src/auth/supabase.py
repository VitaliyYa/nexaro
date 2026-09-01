from fastapi import Depends
from supabase import Client, ClientOptions, create_client

from src.auth.jwt import get_current_user
from src.auth.models import CurrentUser
from src.config import Settings, get_settings


def get_supabase_client(
    current_user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Client:
    """
    Returns a Supabase client configured with the caller's JWT token.
    This ensures that all PostgREST queries pass auth.uid() to PostgreSQL and strictly enforce RLS.
    """
    options = ClientOptions(
        headers={
            "Authorization": f"Bearer {current_user.token}",
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
        }
    )
    client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_PUBLISHABLE_KEY,
        options=options,
    )
    # Also set auth token in postgrest client
    client.postgrest.auth(current_user.token)
    return client


def get_supabase_admin_client(
    settings: Settings = Depends(get_settings),
) -> Client:
    """
    Returns a Supabase client configured with the service_role key.
    STRICT RULE: Only for internal background tasks (MQTT telemetry ingestion, cron, Mosquitto webhook).
    Never inject this into user-facing API routes.
    """
    options = ClientOptions(
        headers={
            "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}",
            "apikey": settings.SUPABASE_SECRET_KEY,
        }
    )
    client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SECRET_KEY,
        options=options,
    )
    client.postgrest.auth(settings.SUPABASE_SECRET_KEY)
    return client
