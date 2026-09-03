#!/usr/bin/env python3
"""
Helper script to create a confirmed test user and print a valid Supabase JWT access token for Swagger UI.
"""

import os

from supabase import create_client

from src.config import get_settings


def main():
    settings = get_settings()
    admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
    public_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)

    email = os.getenv("TEST_USER_EMAIL", "testowner@smartrent.io")
    password = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")

    # 1. Ensure test user exists and email is confirmed
    users = admin_client.auth.admin.list_users()
    existing_user = next((u for u in users if u.email == email), None)

    if not existing_user:
        admin_client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
    elif not existing_user.email_confirmed_at:
        admin_client.auth.admin.update_user_by_id(existing_user.id, {"email_confirm": True})

    # 2. Sign in to obtain access token
    session = public_client.auth.sign_in_with_password({"email": email, "password": password})
    access_token = session.session.access_token

    print("\n" + "=" * 60)
    print("  Supabase User: " + email)
    print("=" * 60)
    print("\nВАШ JWT ACCESS TOKEN (скопируйте в Swagger Authorize):\n")
    print(access_token)
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
