"""Support tickets: the data model and an in-memory ticket service.

This module knows nothing about the LLM. The agent (and later the HTTP API) only
call TicketService, so the storage can be swapped for a real database without
touching them.
"""

import itertools
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime

# Deliberately simple check: "something@something.something", no spaces.
# Real validation would send a confirmation e-mail; this only catches obvious typos.
_EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@dataclass(frozen=True)
class Ticket:
    """A support request that a human agent will handle."""

    id: str
    subject: str
    description: str
    customer_email: str
    created_at: datetime
    status: str = "open"


class TicketService:
    """Creates and looks up tickets, keeping them in memory (lost on restart)."""

    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}
        # Yields 1, 2, 3, ... on each next() call; used to build sequential ids.
        self._counter = itertools.count(1)
        # The web server may handle two requests at once; the lock stops them from
        # getting the same id or writing to the dict at the same time.
        self._lock = threading.Lock()

    def create(self, subject: str, description: str, customer_email: str) -> Ticket:
        """Validate the input, store a new open ticket and return it.

        Raises:
            ValueError: if a field is empty or the e-mail looks invalid.
        """
        subject = subject.strip()
        description = description.strip()
        customer_email = customer_email.strip().lower()

        if not subject:
            raise ValueError("subject must not be empty")
        if not description:
            raise ValueError("description must not be empty")
        if not _EMAIL_PATTERN.fullmatch(customer_email):
            raise ValueError(f"invalid e-mail address: {customer_email!r}")

        with self._lock:
            ticket = Ticket(
                id=f"TCK-{next(self._counter):04d}",  # TCK-0001, TCK-0002, ...
                subject=subject,
                description=description,
                customer_email=customer_email,
                created_at=datetime.now(UTC),
            )
            self._tickets[ticket.id] = ticket
        return ticket

    def get(self, ticket_id: str) -> Ticket | None:
        """Return the ticket with this id, or None if it does not exist."""
        return self._tickets.get(ticket_id)
