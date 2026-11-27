"""Loads the FAQ that grounds the assistant's answers.

The FAQ ships inside the package (support_agent/data/faq.md), so it is found the same
way no matter where the code is run from or how the package was installed.
"""

from importlib.resources import files

# Location of the FAQ relative to the package root.
FAQ_RESOURCE = "data/faq.md"


def load_faq() -> str:
    """Return the full FAQ as Markdown text.

    Raises:
        FileNotFoundError: if the FAQ was not packaged (a build/packaging bug).
    """
    # files("support_agent") points at the installed package folder, not at the
    # current working directory, so this works from any terminal location.
    return files("support_agent").joinpath(FAQ_RESOURCE).read_text(encoding="utf-8")
