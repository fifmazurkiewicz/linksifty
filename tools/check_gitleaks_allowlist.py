"""Exercise the real CI scanner with synthetic data only; requires Docker."""

import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    """Reject credentials in the lock while allowing only its hash entries."""
    config = Path(__file__).resolve().parents[1] / ".gitleaks.toml"
    digest = "31d82cafe9476b025fa8d4c193be7602d5a9138ecb047f69d2c85170fa4be639"
    # Construct a nonfunctional provider-shaped canary, never a real credential.
    canary = "ghp_" + "0123456789abcdefghijklmnopqrstuvwxyz"
    cases = [
        ("hash in lock", ".agent/lock.yaml", f"    api-key.md: {digest}\n", 0),
        ("hash outside lock", "other.yaml", f"    api-key.md: {digest}\n", 1),
        ("credential in lock", ".agent/lock.yaml", f"token: {canary}\n", 1),
        (
            "credential beside hash",
            ".agent/lock.yaml",
            f"    api-key.md: {digest} # {canary}\n",
            1,
        ),
    ]
    for label, filename, content, expected in cases:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            (root / "gitleaks.toml").write_text(config.read_text())
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-w",
                    "/src",
                    "-v",
                    f"{root}:/src:ro",
                    "ghcr.io/gitleaks/gitleaks:v8.28.0",
                    "dir",
                    ".",
                    "--config=/src/gitleaks.toml",
                    "--redact",
                    "--no-banner",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != expected:
                raise SystemExit(
                    f"FAIL {label}: expected {expected}, got {result.returncode}\n{result.stderr}"
                )
            print(f"PASS {label}")


if __name__ == "__main__":
    main()
