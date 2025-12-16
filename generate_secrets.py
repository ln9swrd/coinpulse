#!/usr/bin/env python3
"""
CoinPulse Deployment Secret Generator
Generates secure random secrets for production deployment
"""

import secrets
import string
from datetime import datetime

def generate_secret_key(length=32):
    """Generate a secure SECRET_KEY for Flask"""
    return secrets.token_urlsafe(length)

def generate_api_key(length=32):
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret(length=64):
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(length)

def main():
    print("=" * 60)
    print("CoinPulse Production Secrets Generator")
    print("=" * 60)
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Generate Flask SECRET_KEY
    secret_key = generate_secret_key(32)
    print("🔐 Flask SECRET_KEY:")
    print(f"SECRET_KEY={secret_key}")
    print()

    # Generate JWT Secret (if needed in future)
    jwt_secret = generate_jwt_secret(64)
    print("🔑 JWT Secret (Optional - for future use):")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()

    # Generate sample API key
    api_key = generate_api_key(32)
    print("🔓 Sample Admin API Key (Optional):")
    print(f"ADMIN_API_KEY={api_key}")
    print()

    print("=" * 60)
    print("⚠️  SECURITY WARNING:")
    print("=" * 60)
    print("1. NEVER commit these secrets to Git!")
    print("2. Add them to DigitalOcean Environment Variables")
    print("3. Store a backup copy in a secure password manager")
    print("4. Delete this output after copying the secrets")
    print()
    print("📋 Next Steps:")
    print("1. Copy SECRET_KEY above")
    print("2. Go to DigitalOcean → App → Settings → Environment Variables")
    print("3. Add: SECRET_KEY=<paste-value-here>")
    print("4. Save and redeploy")
    print("=" * 60)

if __name__ == "__main__":
    main()
