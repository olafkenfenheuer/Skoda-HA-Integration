"""Tests for the wait time derived from a 429 response."""

from __future__ import annotations

from datetime import timedelta

from custom_components.skoda_connect.api import _rate_limit_wait

DETAIL = "Rate limit exceeded. Retry after 2740 seconds."


def test_retry_after_header_wins() -> None:
    headers = {"Retry-After": "30", "RateLimit-Reset": "2742"}
    assert _rate_limit_wait(headers, DETAIL) == timedelta(seconds=30)


def test_rate_limit_reset_header() -> None:
    assert _rate_limit_wait({"RateLimit-Reset": "2742"}, DETAIL) == timedelta(seconds=2742)


def test_detail_fallback() -> None:
    assert _rate_limit_wait({}, DETAIL) == timedelta(seconds=2740)


def test_unknown() -> None:
    assert _rate_limit_wait({}, "Too Many Requests") is None
