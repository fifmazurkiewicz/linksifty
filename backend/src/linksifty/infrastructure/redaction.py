"""Shared bounded redaction for explicitly enabled diagnostics."""

import re


def redact(value: object, secrets: tuple[str, ...] = ()) -> object:
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
            else redact(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item, secrets) for item in value]
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
