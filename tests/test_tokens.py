"""Tests for onepaste.tokens."""

import importlib.util

import pytest

from onepaste import tokens


@pytest.fixture
def force_estimate(monkeypatch):
    """Force the estimator path regardless of tiktoken availability."""
    monkeypatch.setattr(tokens, "_encoding", None)
    monkeypatch.setattr(tokens, "_encoding_failed", True)
    monkeypatch.setattr(tokens, "_tiktoken", None)


class TestEstimatePath:
    def test_count_divides_chars(self, force_estimate):
        assert tokens.count_tokens("12345678") == 2

    def test_minimum_is_one(self, force_estimate):
        assert tokens.count_tokens("a") == 1
        assert tokens.count_tokens("") == 1

    def test_rounds_up(self, force_estimate):
        assert tokens.count_tokens("12345") == 2

    def test_label_mentions_estimate(self, force_estimate):
        assert "estimate" in tokens.method_label()
        assert not tokens.is_exact()


class TestRealPath:
    def test_returns_positive_int(self):
        assert tokens.count_tokens("hello world, this is code.") > 0

    def test_tiktoken_optional(self):
        spec = importlib.util.find_spec("tiktoken")
        if spec is None:
            assert not tokens.is_exact()
        else:
            # Either exact (encoding cached/downloadable) or graceful fallback.
            assert tokens.count_tokens("x") >= 1
