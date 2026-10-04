#!/usr/bin/env python3
"""Generate secrets for production deployment."""

import secrets
import sys
from argon2 import PasswordHasher

def generate_jwt_secret():
    """Generate a secure JWT secret key."""
    return secrets.token_urlsafe(48)

def generate_admin_password_hash(password: str):
    """Generate Argon2id hash for admin password."""
    ph = PasswordHasher()
    return ph.hash(password)

def main():
    print("=" * 60)
    print("Sahayak Backend - Secret Generator")
    print("=" * 60)
    print()
    
    # Generate JWT secret
    jwt_secret = generate_jwt_secret()
    print("✓ JWT Secret Key (use as JWT_SECRET_KEY):")
    print(f"  {jwt_secret}")
    print()
    
    # Generate admin password hash
    if len(sys.argv) > 1:
        admin_password = sys.argv[1]
    else:
        admin_password = input("Enter admin password (or press Enter to skip): ").strip()
    
    if admin_password:
        admin_hash = generate_admin_password_hash(admin_password)
        print()
        print("✓ Admin Password Hash (use as ADMIN_PASSWORD_HASH):")
        print(f"  {admin_hash}")
        print()
        print("⚠️  Save these values in Render environment variables!")
        print("   Never commit them to source control.")
    else:
        print("⚠️  Admin password hash generation skipped.")
    
    print()
    print("=" * 60)
    print("Next steps:")
    print("1. Copy these values to Render environment variables")
    print("2. Set OTP_DEMO_MODE=false in production")
    print("3. Configure DATABASE_URL with your PostgreSQL connection string")
    print("=" * 60)

if __name__ == "__main__":
    main()
