"""Explicit redacted tracing; telemetry failures must not repeat or stop work."""

import logging
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from langfuse import Langfuse, LangfuseGeneration

from linksifty.application.processing_contracts import ModelResult

_logger = logging.getLogger(__name__)


def _redact(value: object, secrets: tuple[str, ...] = ()) -> object:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]"
            if str(key).lower()
            in {
                "authorization",
                "cookie",
                "password",
                "secret",
                "api_key",
                "access_token",
                "refresh_token",
                "user_id",
                "email",
                "lease_token",
            }
            else _redact(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item, secrets) for item in value]
    if not isinstance(value, str):
        return value
    for secret in secrets:
        value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"(?i)\b(Bearer|Basic)\s+[\w.\-~+/=]+", r"\1 [REDACTED]", value)
    value = re.sub(r"(?i)(https?://)[^/\s@]+@", r"\1[REDACTED]@", value)
    value = re.sub(
        r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|secret)"
        r"[\"']?\s*[:=]\s*[\"']?)[^\s&\"',}]+",
        r"\1[REDACTED]",
        value,
    )
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "[REDACTED]", value)
    value = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[REDACTED]", value)
    # ponytail: bound each text field; use explicit source IDs to locate large inputs.
    return value[:200000] + ("\n[TRUNCATED at 200000 characters]" if len(value) > 200000 else "")


class LangfuseTelemetry:
    def __init__(self, client: Langfuse | None = None, *, secrets: tuple[str, ...] = ()) -> None:
        self._client = client
        self._secrets = tuple(value for value in secrets if value)

    def event(self, name: str, details: dict[str, object]) -> None:
        if self._client is None:
            return
        try:
            self._client.create_event(
                name=name,
                input=_redact(details, self._secrets),
                level="ERROR"
                if details.get("status") == "failed" or details.get("failure")
                else "DEFAULT",
            )
        except Exception:
            _logger.warning("telemetry_unavailable")

    @contextmanager
    def scope(self, name: str, identifier: str) -> Iterator[None]:
        if self._client is None:
            yield
            return
        try:
            context = self._client.start_as_current_observation(
                name=name,
                metadata={
                    "reservation_id" if name == "orphan.reconciliation" else "job_id": identifier
                },
            )
            observation = context.__enter__()
        except Exception:
            _logger.warning("telemetry_unavailable")
            yield
            return
        try:
            yield
        except BaseException as error:
            try:
                observation.update(level="ERROR", status_message=type(error).__name__)
            except Exception:
                _logger.warning("telemetry_unavailable")
            raise
        finally:
            try:
                # Never export exception messages/stack traces containing private payloads.
                context.__exit__(None, None, None)
            except Exception:
                _logger.warning("telemetry_unavailable")

    @contextmanager
    def generation(
        self, model: str, *, input: object = None
    ) -> Iterator[Callable[[ModelResult], None]]:
        observation = None
        try:
            if self._client is not None:
                observation = self._client.start_observation(
                    name="openrouter.assessment",
                    as_type="generation",
                    model=model,
                    input=_redact(input, self._secrets),
                )
        except Exception:
            _logger.warning("telemetry_unavailable")

        def finish(result: ModelResult) -> None:
            if observation is None:
                return
            try:
                observation.update(
                    output=_redact(result.assessment.model_dump(mode="json"), self._secrets)
                    if result.assessment
                    else None,
                    metadata={
                        "failure_reason": result.failure_reason or "none",
                        "accepted": result.assessment is not None,
                    },
                    level="ERROR" if result.failure_reason else "DEFAULT",
                    status_message=result.failure_reason,
                )
                if isinstance(observation, LangfuseGeneration):
                    observation.update(
                        usage_details={
                            name: value
                            for name, value in {
                                "input": result.input_tokens,
                                "output": result.output_tokens,
                            }.items()
                            if value is not None
                        },
                        cost_details={"total": float(result.cost)}
                        if result.cost is not None
                        else None,
                    )
            except Exception:
                _logger.warning("telemetry_unavailable")

        try:
            yield finish
        except BaseException as error:
            if observation is not None:
                try:
                    observation.update(level="ERROR", status_message=type(error).__name__)
                except Exception:
                    _logger.warning("telemetry_unavailable")
            raise
        finally:
            if observation is not None:
                try:
                    observation.end()
                except Exception:
                    _logger.warning("telemetry_unavailable")

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.shutdown()
            except Exception:
                _logger.warning("telemetry_unavailable")
