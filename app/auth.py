"""Protects the admin endpoints with an API key."""

import secrets

from fastapi import Header, HTTPException, status

from app import config


def require_admin(x_admin_key: str | None = Header(default=None)):
    """
    Allow the request only if the X-Admin-Key header matches ADMIN_API_KEY.

    compare_digest takes the same time whether the first character or the
    last one is wrong, so an attacker can't guess the key one character at
    a time by timing the responses.
    """
    if not config.ADMIN_API_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Reviewing is switched off: ADMIN_API_KEY is not set")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, config.ADMIN_API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or wrong admin key")
