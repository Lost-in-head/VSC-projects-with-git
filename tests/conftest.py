import importlib

import pytest


@pytest.fixture(autouse=True)
def force_mock_mode(monkeypatch):
    """Always run tests in safe mock mode and reload config-dependent clients."""
    monkeypatch.setenv("USE_OPENAI_MOCK", "True")
    monkeypatch.setenv("USE_EBAY_MOCK", "True")

    import src.config as config
    import src.api.openai_client as openai_client
    import src.api.ebay_client as ebay_client

    importlib.reload(config)
    importlib.reload(openai_client)
    importlib.reload(ebay_client)

    yield
