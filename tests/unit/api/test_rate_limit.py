"""Tests for rate limiting middleware helpers."""

from app.api import rate_limit


class TestRateLimitPolicy:
    """Tests for endpoint-to-policy mapping."""

    def test_login_policy(self) -> None:
        policy = rate_limit.get_rate_limit_policy("/auth/login")
        assert policy.name == "auth_login"
        assert policy.limit == 5
        assert policy.window_seconds == 60

    def test_register_policy(self) -> None:
        policy = rate_limit.get_rate_limit_policy("/auth/register")
        assert policy.name == "auth_register"
        assert policy.limit == 3
        assert policy.window_seconds == 60

    def test_ingest_policy(self) -> None:
        policy = rate_limit.get_rate_limit_policy("/vaults/my-vault/ingest")
        assert policy.name == "vault_ingest"
        assert policy.limit == 2
        assert policy.window_seconds == 3600

    def test_search_policy(self) -> None:
        policy = rate_limit.get_rate_limit_policy("/vaults/my-vault/search/fulltext")
        assert policy.name == "search"
        assert policy.limit == 30
        assert policy.window_seconds == 60

    def test_default_policy(self) -> None:
        policy = rate_limit.get_rate_limit_policy("/vaults/my-vault/documents")
        assert policy.name == "default"
        assert policy.limit == 100
        assert policy.window_seconds == 60


class TestInMemoryRateLimiter:
    """Tests for sliding-window limiter behavior."""

    def test_enforces_limit_and_recovers_after_window(self, monkeypatch) -> None:
        timeline = iter([0.0, 1.0, 2.0, 65.0])
        monkeypatch.setattr(rate_limit, "monotonic", lambda: next(timeline))

        limiter = rate_limit.InMemoryRateLimiter()
        policy = rate_limit.RateLimitPolicy(name="test", limit=2, window_seconds=60)

        allowed_1, remaining_1, retry_after_1 = limiter.check("client", policy)
        assert allowed_1 is True
        assert remaining_1 == 1
        assert retry_after_1 == 0

        allowed_2, remaining_2, retry_after_2 = limiter.check("client", policy)
        assert allowed_2 is True
        assert remaining_2 == 0
        assert retry_after_2 == 0

        allowed_3, remaining_3, retry_after_3 = limiter.check("client", policy)
        assert allowed_3 is False
        assert remaining_3 == 0
        assert retry_after_3 > 0

        allowed_4, remaining_4, retry_after_4 = limiter.check("client", policy)
        assert allowed_4 is True
        assert remaining_4 == 1
        assert retry_after_4 == 0
