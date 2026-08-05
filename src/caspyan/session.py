from typing import Protocol


class TicketProtocol(Protocol):
    def __str__(self) -> str: ...


class TicketState(Protocol):
    @property
    def username(self) -> str: ...


SESSION_USERNAME_KEY = "_cas_username"


def get_authenticated_username(session: dict) -> str | None:
    """Get the currently authenticated username from the session."""
    return session.get(SESSION_USERNAME_KEY)


def set_authenticated_username(session: dict, username: str) -> None:
    """Store the authenticated username in the session."""
    session[SESSION_USERNAME_KEY] = username


def clear_authentication(session: dict) -> None:
    """Remove authentication state from the session."""
    session.pop(SESSION_USERNAME_KEY, None)


def is_authenticated(session: dict) -> bool:
    """Check if the session has an authenticated user."""
    return bool(get_authenticated_username(session))
