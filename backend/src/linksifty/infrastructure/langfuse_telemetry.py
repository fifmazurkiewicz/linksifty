"""Explicit redacted tracing; telemetry failures must not repeat or stop work."""

import logging
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager

from langfuse import Langfuse, LangfuseGeneration, propagate_attributes

from linksifty.application.processing_contracts import ModelResult
from linksifty.infrastructure.redaction import redact

_logger = logging.getLogger(__name__)


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
                input=redact(details, self._secrets),
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
        context = ExitStack()
        try:
            observation = context.enter_context(
                self._client.start_as_current_observation(
                    name=name,
                    metadata={
                        "reservation_id"
                        if name == "orphan.reconciliation"
                        else "job_id": identifier
                    },
                )
            )
            if name == "processing":
                context.enter_context(
                    propagate_attributes(session_id=f"linksifty:job:{identifier}")
                )
        except Exception:
            _logger.warning("telemetry_unavailable")
            try:
                context.close()
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
                context.close()
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
                    input=redact(input, self._secrets),
                )
        except Exception:
            _logger.warning("telemetry_unavailable")

        def finish(result: ModelResult) -> None:
            if observation is None:
                return
            try:
                observation.update(
                    output=redact(result.assessment.model_dump(mode="json"), self._secrets)
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
