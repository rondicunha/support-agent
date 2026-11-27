"""The support agent: Gemini + the FAQ as context + a tool to open tickets."""

from google import genai
from google.genai import types

from support_agent.tickets import TicketService

# The FAQ is inserted between <faq> tags so the model can tell our rules apart from
# the reference material it should answer from.
SYSTEM_PROMPT_TEMPLATE = """\
You are the virtual support assistant of RubroRota, a fictional bus-trip and
membership service for Flamengo fans.

Rules:
1. Answer ONLY with information from the FAQ inside the <faq> tags. Never use outside
   knowledge, and never invent prices, deadlines, policies or contact details.
2. You only help with RubroRota services. For anything else (including Flamengo
   matches, players, results or history), politely say it is outside what you can
   help with and mention what you can do instead.
3. If the question is about RubroRota but the FAQ does not answer it, if the customer
   reports a problem that needs a person (a bus that did not show up, a double
   charge, a lost item...), or if they ask to talk to a human, offer to open a support
   ticket.
4. Before calling create_ticket you need the customer's e-mail and a clear
   description of the problem. Ask for whatever is missing; never make it up. Only
   open the ticket after the customer agrees.
5. After a ticket is created, give the customer the ticket id and say the team will
   reply by e-mail. Do not promise a response time.
6. If create_ticket returns an error, explain what is wrong in plain words and ask
   for the corrected information.
7. Reply in the customer's language, in a short and friendly tone.

<faq>
{faq}
</faq>
"""


def build_system_prompt(faq: str) -> str:
    """Return the system instructions with the FAQ embedded."""
    return SYSTEM_PROMPT_TEMPLATE.format(faq=faq)


class SupportAgent:
    """One conversation with a customer. The chat keeps the message history."""

    def __init__(self, client: genai.Client, model: str, faq: str, tickets: TicketService) -> None:
        # Keep a reference to the client: the chat does not hold one, and genai.Client
        # closes its HTTP connection when it is garbage-collected. Without this line
        # the first message fails with "the client has been closed".
        self._client = client
        self._tickets = tickets
        config = types.GenerateContentConfig(
            system_instruction=build_system_prompt(faq),
            # Passing a plain Python function turns on automatic function calling: the
            # SDK reads its name, type hints and docstring to describe the tool to the
            # model, runs it when the model asks, and sends the result back.
            tools=[self.create_ticket],
            # Safety net: at most 3 tool calls per user message, so a confused model
            # cannot loop forever (and burn API quota).
            automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=3),
        )
        self._chat = client.chats.create(model=model, config=config)

    def ask(self, message: str) -> str:
        """Send the customer's message and return the assistant's reply."""
        response = self._chat.send_message(message)
        # .text is None when the reply has no text part (e.g. it was blocked).
        return response.text or ""

    # The docstring below is sent to the model as the tool description, so it is
    # written for the model: when to use the tool and what each argument means.
    def create_ticket(self, subject: str, description: str, customer_email: str) -> dict:
        """Open a support ticket so a human agent contacts the customer by e-mail.

        Use only when the FAQ cannot solve the customer's request and the customer
        agreed to open a ticket.

        Args:
            subject: Short summary of the problem, e.g. "Bus did not show up".
            description: What happened, with the details the customer gave.
            customer_email: The e-mail address the customer provided.

        Returns:
            {"ticket_id": ..., "status": ...} on success, or {"error": ...} when the
            data is invalid.
        """
        try:
            ticket = self._tickets.create(subject, description, customer_email)
        except ValueError as exc:
            # Returned (not raised) so the model sees a clean message and can ask the
            # customer for the right information.
            return {"error": str(exc)}
        return {"ticket_id": ticket.id, "status": ticket.status}
