"""Shared test helpers for mocking Clerk's verification result."""

from clerk_backend_api.security.types import AuthStatus, RequestState


def signed_in(clerk_user_id: str) -> RequestState:
    return RequestState(status=AuthStatus.SIGNED_IN, payload={"sub": clerk_user_id})


def signed_out() -> RequestState:
    return RequestState(status=AuthStatus.SIGNED_OUT, reason=None)
