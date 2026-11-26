"""Command-line entry point: sends a single prompt to Gemini and prints the answer.

Usage:
    python -m support_agent "What are your support hours?"
"""

import sys

from google import genai
from google.genai import errors

from support_agent.config import ConfigError, load_settings

DEFAULT_PROMPT = "In one sentence, what can a customer support assistant help with?"


def main() -> int:
    """Run the CLI and return a process exit code (0 = success)."""
    # sys.argv[0] is the program name; everything after it is the user's prompt.
    prompt = " ".join(sys.argv[1:]) or DEFAULT_PROMPT

    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
    except errors.APIError as exc:
        print(f"Gemini API error ({exc.code}): {exc.message}", file=sys.stderr)
        return 1

    print(response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
