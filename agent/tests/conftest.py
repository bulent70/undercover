import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from agent import main
from backend.main import app


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies in place of a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture(autouse=True)
def backend(tmp_path, monkeypatch):
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "undercover.db"))
    monkeypatch.setattr(main, "backend", lambda: TestClient(app))
    return TestClient(app)


@pytest.fixture
def stub_model():
    def make(replies):
        return StubModel(messages=iter(replies))

    return make
