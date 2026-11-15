"""T01: la app arranca sin errores."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / "app_simple.py"


def test_app_starts():
    at = AppTest.from_file(str(APP)).run(timeout=30)
    assert not at.exception
    assert at.title[0].value == "🌱 RotaSat"
