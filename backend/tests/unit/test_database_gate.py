"""The optional SQL runner must never inherit a route to a real/remote database."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def load_gate() -> ModuleType:
    path = Path(__file__).parents[1] / "integration" / "check_processing_database.py"
    spec = importlib.util.spec_from_file_location("database_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_disposable_gate_cannot_inherit_pg_host_or_service_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = load_gate()
    monkeypatch.setattr(gate.shutil, "which", lambda name: "/test/psql")
    monkeypatch.setenv("LINKSIFTY_TEST_DATABASE_URL", "postgresql://localhost/linksifty_test")
    monkeypatch.setenv("PGHOSTADDR", "203.0.113.20")
    monkeypatch.setenv("PGSERVICE", "production")
    result = gate.local_environment()
    assert result["PGHOST"] == "127.0.0.1"
    assert "PGHOSTADDR" not in result
    assert "PGSERVICE" not in result
    assert "LINKSIFTY_TEST_DATABASE_URL" not in result


@pytest.mark.parametrize(
    "url", ["postgresql://db.example/linksifty_test", "postgresql://127.0.0.1/production"]
)
def test_disposable_gate_rejects_nonlocal_or_nontest_destinations(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    gate = load_gate()
    monkeypatch.setattr(gate.shutil, "which", lambda name: "/test/psql")
    monkeypatch.setenv("LINKSIFTY_TEST_DATABASE_URL", url)
    with pytest.raises(ValueError, match="loopback disposable"):
        gate.local_environment()
