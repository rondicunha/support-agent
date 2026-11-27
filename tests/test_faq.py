"""Tests for the FAQ loader."""

from support_agent.faq import load_faq


def test_load_faq_returns_markdown_with_questions():
    faq = load_faq()

    # A missing or empty file would mean the FAQ was not packaged correctly.
    assert faq.strip()
    # Each question is a level-2 Markdown heading.
    assert faq.count("\n## ") >= 10


def test_load_faq_includes_fictional_disclaimer():
    # The service is fictional; the disclaimer must never be dropped by accident.
    assert "Projeto fictício" in load_faq()
