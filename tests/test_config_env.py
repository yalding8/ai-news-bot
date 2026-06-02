"""
Regression tests for config env loading precedence.

Incident (2026-06-02): a long-lived interactive shell on the shared host had
stale `WECOM_WEBHOOK_URL` / `LLM_*` values exported into the environment. Because
`config.py` called `load_dotenv()` with its default behaviour (do NOT override
already-present env vars), those stale exports shadowed the correct values in
`.env`, so manual runs sent news to the wrong WeCom group.

The fix is `load_dotenv(override=True)`: `.env` becomes the single source of truth
for any key it defines, while keys absent from `.env` (e.g. CI secrets) still come
from the environment.
"""

import importlib

import dotenv

import config


def _reload_config_clean():
    """Re-execute config.py against the real environment (test teardown)."""
    importlib.reload(config)


def test_dotenv_overrides_preexisting_env(monkeypatch, tmp_path):
    """A value in .env must win over a stale value already in os.environ."""
    env_file = tmp_path / ".env"
    env_file.write_text("WECOM_WEBHOOK_URL=https://correct.example/news\n")
    monkeypatch.setenv("WECOM_WEBHOOK_URL", "https://injected.example/stale")

    real_load = dotenv.load_dotenv

    def fake_load(*args, **kwargs):
        # Pin discovery to our temp .env, but PRESERVE the override flag that
        # config.py chose — that flag is exactly what this test pins down.
        return real_load(dotenv_path=str(env_file),
                         override=kwargs.get("override", False))

    monkeypatch.setattr(dotenv, "load_dotenv", fake_load)

    try:
        importlib.reload(config)
        assert config.WECOM_WEBHOOK_URLS == ["https://correct.example/news"]
    finally:
        monkeypatch.undo()
        _reload_config_clean()


def test_env_used_when_no_dotenv_file(monkeypatch):
    """With no .env (CI / GitHub Actions), env vars (secrets) must still be read."""
    monkeypatch.setenv("WECOM_WEBHOOK_URL", "https://ci-secret.example/news")

    def fake_load_no_file(*args, **kwargs):
        return False  # simulate "no .env found" — load nothing

    monkeypatch.setattr(dotenv, "load_dotenv", fake_load_no_file)

    try:
        importlib.reload(config)
        assert config.WECOM_WEBHOOK_URLS == ["https://ci-secret.example/news"]
    finally:
        monkeypatch.undo()
        _reload_config_clean()
