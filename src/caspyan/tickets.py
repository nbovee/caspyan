import secrets
from base64 import urlsafe_b64encode
from threading import Lock

from .session import TicketProtocol, TicketState


class TicketValue(TicketProtocol, TicketState):
    def __init__(self, id: str, username: str) -> None:
        self._id = id
        self._username = username

    @property
    def username(self) -> str:
        return self._username

    def __str__(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return f"TicketValue(id={self._id!r}, username={self._username!r})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TicketValue):
            return NotImplemented
        return self._id == other._id


class TicketService:
    """Thread-safe in-memory ticket store.

    Issues single-use tickets. Once validated, a ticket is consumed
    and cannot be used again.
    """

    def __init__(self) -> None:
        self._store: dict[str, TicketValue] = {}
        self._lock = Lock()

    def issue(self, username: str) -> TicketProtocol:
        """Issue a new service ticket for the given username."""
        ticket: TicketValue | None = None
        while ticket is None:
            raw = secrets.token_bytes(18)
            id = f"ST-{urlsafe_b64encode(raw).decode('ascii')}"
            value = TicketValue(id, username)
            with self._lock:
                if id not in self._store:
                    self._store[id] = value
                    ticket = value
        return ticket

    def validate(self, ticket_id: str) -> TicketState | None:
        """Validate and consume a ticket. Returns the ticket state or None."""
        with self._lock:
            return self._store.pop(ticket_id, None)
