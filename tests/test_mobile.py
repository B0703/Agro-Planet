"""T21: CA-11 y RNF-06 en un navegador real (Chrome o Edge sin ventana), con scripts/check_mobile.py.

Se deselecciona por defecto porque arranca la app y un navegador (unos minutos): `pytest -m browser`.
"""
import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location("check_mobile",
                                               Path(__file__).parent.parent / "scripts" / "check_mobile.py")
check_mobile = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check_mobile)

pytestmark = pytest.mark.browser


@pytest.mark.parametrize("lang", ["es", "en"])
def test_ca11_390_px_no_horizontal_scroll_and_every_button_can_be_tapped(lang):
    assert check_mobile.main(["--lang", lang]) == 0


def test_rnf06_desktop_1280x800():
    assert check_mobile.main(["--width", "1280", "--height", "800", "--no-mobile"]) == 0
