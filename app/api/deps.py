"""Request-scoped dependencies: a DB session per request, and real Clerk auth.

require_clerk_user_id does RS256 JWT verification via clerk_backend_api.
If CLERK_JWT_KEY is set it's a local math operation (no network call); if
not, it falls back to fetching Clerk's public keys over the network,
cached for 5 minutes. Either way, unlike the earlier header-based sketch
this replaced, nothing here trusts a client-supplied identity - the token
signature is actually verified.

get_current_user just-in-time provisions a local User row on first sight
of a new clerk_user_id, rather than depending on a webhook (no webhook
secret configured yet - see docs/DECISIONS.md if that changes).
"""

import os
from typing import Annotated

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def _authorized_parties() -> list[str] | None:
    raw = os.environ.get("CLERK_AUTHORIZED_PARTIES")
    return raw.split(",") if raw else None


def require_clerk_user_id(request: Request) -> str:
    state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=os.environ["CLERK_SECRET_KEY"],
            jwt_key=os.environ.get("CLERK_JWT_KEY"),
            authorized_parties=_authorized_parties(),
            accepts_token=["session_token"],
        ),
    )
    if not state.is_signed_in:
        reason = state.reason.value if state.reason else "unauthorized"
        raise HTTPException(status_code=401, detail=reason)
    return state.payload["sub"]


def get_current_user(clerk_user_id: Annotated[str, Depends(require_clerk_user_id)], db: DbSession) -> User:
    user = db.query(User).filter_by(clerk_user_id=clerk_user_id).one_or_none()
    if user is None:
        user = User(clerk_user_id=clerk_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
