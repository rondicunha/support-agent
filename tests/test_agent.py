"""Tests for SupportAgent that run without calling the Gemini API.

A MagicMock stands in for genai.Client: it accepts any call and records it, so we can
check what the agent sent and make it return whatever we want.
"""

import gc
import weakref
from unittest.mock import MagicMock

import pytest

from support_agent.agent import SupportAgent, build_system_prompt
from support_agent.tickets import TicketService

FAQ = "## Quanto custa uma caravana?\nR$ 45,00."


@pytest.fixture
def tickets() -> TicketService:
    return TicketService()


@pytest.fixture
def client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def agent(client, tickets) -> SupportAgent:
    return SupportAgent(client=client, model="test-model", faq=FAQ, tickets=tickets)


def test_system_prompt_embeds_faq():
    prompt = build_system_prompt(FAQ)

    assert f"<faq>\n{FAQ}\n</faq>" in prompt


def test_chat_is_configured_with_prompt_and_ticket_tool(agent, client):
    # call_args holds the arguments of the last call made on the mock.
    kwargs = client.chats.create.call_args.kwargs
    config = kwargs["config"]

    assert kwargs["model"] == "test-model"
    assert FAQ in config.system_instruction
    assert config.tools == [agent.create_ticket]


class _FakeChats:
    def create(self, **kwargs: object) -> object:
        return object()  # a chat that, like the real one, does not point back to the client


class _FakeClient:
    """Minimal client whose chat holds no reference to it (MagicMock children would)."""

    def __init__(self) -> None:
        self.chats = _FakeChats()


def test_agent_keeps_client_alive(tickets):
    # Regression test: if nothing references the client, Python frees it and the SDK
    # closes the connection, so the first ask() fails. weakref lets us watch an object
    # without keeping it alive ourselves.
    fake_client = _FakeClient()
    ref = weakref.ref(fake_client)
    agent = SupportAgent(client=fake_client, model="m", faq=FAQ, tickets=tickets)

    del fake_client
    gc.collect()

    assert ref() is not None, "the agent let the client be garbage-collected"
    assert agent is not None


def test_ask_returns_reply_text(agent, client):
    chat = client.chats.create.return_value
    chat.send_message.return_value.text = "Custa R$ 45,00."

    assert agent.ask("Quanto custa?") == "Custa R$ 45,00."
    chat.send_message.assert_called_once_with("Quanto custa?")


def test_ask_returns_empty_string_when_reply_has_no_text(agent, client):
    client.chats.create.return_value.send_message.return_value.text = None

    assert agent.ask("Oi") == ""


def test_create_ticket_tool_opens_ticket(agent, tickets):
    result = agent.create_ticket("Bus late", "Waited 40 minutes.", "fan@example.com")

    assert result == {"ticket_id": "TCK-0001", "status": "open"}
    assert tickets.get("TCK-0001") is not None


def test_create_ticket_tool_returns_error_instead_of_raising(agent, tickets):
    result = agent.create_ticket("Bus late", "Waited 40 minutes.", "not-an-email")

    assert "error" in result
    assert tickets.get("TCK-0001") is None
