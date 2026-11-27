"""Command-line chat with the RubroRota support agent.

Usage:
    python -m support_agent
Type "sair" (or press Ctrl+C) to quit.
"""

import sys

from google import genai
from google.genai import errors

from support_agent.agent import SupportAgent
from support_agent.config import ConfigError, load_settings
from support_agent.faq import load_faq
from support_agent.tickets import TicketService

EXIT_COMMANDS = {"sair", "exit", "quit"}


def main() -> int:
    """Run the interactive chat and return a process exit code (0 = success)."""
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    agent = SupportAgent(
        client=genai.Client(api_key=settings.gemini_api_key),
        model=settings.gemini_model,
        faq=load_faq(),
        tickets=TicketService(),
    )

    print("Assistente RubroRota. Digite 'sair' para encerrar.\n")
    while True:
        try:
            message = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):  # Ctrl+C / Ctrl+Z (end of input)
            print()
            return 0

        if not message:
            continue
        if message.lower() in EXIT_COMMANDS:
            return 0

        try:
            reply = agent.ask(message)
        except errors.APIError as exc:
            # One failed request should not end the whole conversation.
            print(f"Gemini API error ({exc.code}): {exc.message}", file=sys.stderr)
            continue

        print(f"Assistente: {reply}\n")


if __name__ == "__main__":
    raise SystemExit(main())
