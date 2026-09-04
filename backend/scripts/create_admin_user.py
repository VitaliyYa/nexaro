#!/usr/bin/env python3
"""
Creates or resets a SuperAdmin user in Supabase Auth.
Usage:
    uv run --directory backend python scripts/create_admin_user.py
"""

import os

from supabase import create_client

from src.config import get_settings


def main():
    settings = get_settings()
    admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)

    email = os.getenv("ADMIN_USER_EMAIL", "admin@smartrent.io")
    password = os.getenv("ADMIN_USER_PASSWORD", "AdminPassword123!")

    print(f"Connecting to Supabase at: {settings.SUPABASE_URL}")

    # Check if user already exists
    users_resp = admin_client.auth.admin.list_users()
    existing_user = next((u for u in users_resp if u.email == email), None)

    if not existing_user:
        print(f"Creating new SuperAdmin user: {email}...")
        admin_client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
                "app_metadata": {"role": "superadmin"},
                "user_metadata": {"name": "SmartRent SuperAdmin", "role": "superadmin"},
            }
        )
        print("SuperAdmin created successfully!")
    else:
        print(f"User {email} already exists. Updating role and password...")
        admin_client.auth.admin.update_user_by_id(
            existing_user.id,
            {
                "password": password,
                "email_confirm": True,
                "app_metadata": {"role": "superadmin"},
                "user_metadata": {"name": "SmartRent SuperAdmin", "role": "superadmin"},
            },
        )
        print("User updated to SuperAdmin successfully!")

    print("\n" + "=" * 60)
    print("  УЧЕТНЫЕ ДАННЫЕ СУПЕР-АДМИНИСТРАТОРА SMARTRENT:")
    print("=" * 60)
    print(f"  Email:    {email}")
    print(f"  Password: {password}")
    print("  URL:      http://localhost:3000/login")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
