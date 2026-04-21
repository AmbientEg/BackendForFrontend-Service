import os

from fastapi import Header, HTTPException


async def require_admin(authorization: str | None = Header(default=None)) -> None:
	"""Validate admin access using a bearer token header."""
	expected_token = os.getenv("ADMIN_BEARER_TOKEN", "")
	if not expected_token:
		raise HTTPException(status_code=503, detail="Admin authentication is not configured")

	if not authorization or not authorization.startswith("Bearer "):
		raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

	token = authorization.removeprefix("Bearer ").strip()
	if token != expected_token:
		raise HTTPException(status_code=403, detail="Insufficient privileges")
