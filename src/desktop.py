"""
Desktop application launcher for Cards 4 Sale.

Starts the Flask backend in a background thread and opens a native OS
window using PyWebView so the app runs as a standalone desktop application
without requiring a separate browser.

Usage:
    python -m src.desktop          # run directly
    python src/desktop.py          # alternative

PyInstaller entry point:
    pyinstaller build_desktop.py   # see build_desktop.py in repo root
"""

import logging
import threading

import webview

from src.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_PORT = 5000


def _start_server(app, port: int) -> None:
    """Run Flask in a daemon thread — exits automatically when the window closes."""
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def main() -> None:
    """Create the Flask app, start the server, then open the native window."""
    app = create_app()

    server = threading.Thread(target=_start_server, args=(app, _PORT), daemon=True)
    server.start()
    logger.info("Flask server started on http://127.0.0.1:%d", _PORT)

    webview.create_window(
        "Cards 4 Sale — eBay Listing Generator",
        f"http://127.0.0.1:{_PORT}",
        width=1200,
        height=800,
        min_size=(800, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
