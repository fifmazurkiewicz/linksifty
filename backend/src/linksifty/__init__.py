"""Linksifty package entrypoint."""

from linksifty.main import app


def main() -> None:
    """Run the local API server."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
