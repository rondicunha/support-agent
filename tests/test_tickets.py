"""Tests for the in-memory ticket service."""

import pytest

from support_agent.tickets import Ticket, TicketService


@pytest.fixture
def service() -> TicketService:
    # A fresh service per test, so tickets from one test never leak into another.
    return TicketService()


def create_valid(service: TicketService, **overrides: str) -> Ticket:
    """Create a ticket with valid defaults, replacing only the fields given."""
    fields = {
        "subject": "Bus did not show up",
        "description": "Waited at Praça XV for 40 minutes and the bus never came.",
        "customer_email": "fan@example.com",
    }
    fields.update(overrides)
    return service.create(**fields)


def test_create_stores_fields_and_opens_ticket(service):
    ticket = create_valid(service)

    assert ticket.subject == "Bus did not show up"
    assert ticket.customer_email == "fan@example.com"
    assert ticket.status == "open"
    assert ticket.created_at.tzinfo is not None  # timezone-aware, not a "naive" datetime


def test_create_assigns_sequential_ids(service):
    first = create_valid(service)
    second = create_valid(service)

    assert (first.id, second.id) == ("TCK-0001", "TCK-0002")


def test_create_normalizes_whitespace_and_email_case(service):
    ticket = create_valid(service, subject="  Refund  ", customer_email=" Fan@Example.COM ")

    assert ticket.subject == "Refund"
    assert ticket.customer_email == "fan@example.com"


def test_get_returns_created_ticket(service):
    ticket = create_valid(service)

    assert service.get(ticket.id) == ticket


def test_get_unknown_id_returns_none(service):
    assert service.get("TCK-9999") is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"subject": "   "},
        {"description": ""},
        {"customer_email": "not-an-email"},
        {"customer_email": "fan@example"},
        {"customer_email": "fan @example.com"},
    ],
)
def test_create_rejects_invalid_input(service, overrides):
    with pytest.raises(ValueError):
        create_valid(service, **overrides)
