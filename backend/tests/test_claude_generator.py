"""Claude report generator: API wiring + no-PHI payload (mocked client)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.services import report_generation as rg
from app.services.report_generation import (
    ClaudeReportGenerator,
    OrganVolumeCtx,
    ReportContext,
)


class _FakeBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeResponse:
    stop_reason = "end_turn"

    def __init__(self, text: str) -> None:
        self.content = [_FakeBlock(text)]


class _FakeMessages:
    def __init__(self, captured: dict[str, Any]) -> None:
        self._captured = captured

    def create(self, **kwargs: Any) -> _FakeResponse:
        self._captured.update(kwargs)
        return _FakeResponse("INDICATION\nScintigraphie osseuse.\n\nCONCLUSION\nÀ valider.")


class _FakeClient:
    def __init__(self, captured: dict[str, Any]) -> None:
        self.messages = _FakeMessages(captured)


def test_claude_generator_reformulates_and_sends_no_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(rg, "_build_client", lambda api_key: _FakeClient(captured))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        context = ReportContext(
            exam_type="bone",
            pseudonym="SC-abc123",
            organs=[OrganVolumeCtx("vertebrae_L3", 40.0, False)],
            score_value="40.0",
            score_type="bsi_proxy",
            score_details={"needs_clinical_validation": True},
            foci=[],
        )
        result = ClaudeReportGenerator().generate(context)
        assert "INDICATION" in result

        assert captured["model"] == "claude-opus-4-8"
        assert captured["thinking"] == {"type": "adaptive"}

        sent = json.dumps(captured, default=str)
        assert "SC-abc123" in sent  # pseudonym is fine
        for forbidden in ("PatientName", "PatientID", "PatientBirthDate"):
            assert forbidden not in sent
    finally:
        get_settings.cache_clear()


def test_claude_generator_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError):
            ClaudeReportGenerator().generate(
                ReportContext(exam_type="bone", pseudonym="P", organs=[], score_value=None)
            )
    finally:
        get_settings.cache_clear()
