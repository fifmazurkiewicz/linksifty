"""Explicit metadata-only tracing; telemetry failures must not repeat or stop work."""

import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from langfuse import Langfuse, LangfuseGeneration

from linksifty.application.processing_contracts import ModelResult

_logger = logging.getLogger(__name__)


class LangfuseTelemetry:
    def __init__(self, client: Langfuse | None = None) -> None:
        self._client = client

    @contextmanager
    def scope(self, name: str, identifier: str) -> Iterator[None]:
        if self._client is None:
            yield
            return
        try:
            context = self._client.start_as_current_observation(
                name=name, metadata={"job_id": identifier}
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
    def generation(self, model: str) -> Iterator[Callable[[ModelResult], None]]:
        observation = None
        try:
            if self._client is not None:
                observation = self._client.start_observation(
                    name="openrouter.assessment", as_type="generation", model=model
                )
        except Exception:
            _logger.warning("telemetry_unavailable")

        def finish(result: ModelResult) -> None:
            if observation is None:
                return
            try:
                observation.update(
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
