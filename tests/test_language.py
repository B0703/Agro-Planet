"""T21: cambio de idioma de punta a punta (CA-09, RF-60 a RF-62). AppTest sin red, con Ica desde data/cache/.

Se recorre todo lo que llega al navegador (los protos de cada elemento, con el JSON de los gráficos y los enlaces ya
decodificados) y se buscan tildes, «ñ», «¿» y «¡»: en inglés solo puede quedar el botón «Español» (con su ayuda,
«Cambiar la página a español», que es parte del mismo botón). «Pueblo Nuevo, Ica» no lleva tildes.
"""
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import unquote

import pytest
from google.protobuf.json_format import MessageToDict
from streamlit.testing.v1 import AppTest

from rotasat.cache import SourceError
from rotasat.ui import climate_sections

APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
ICA = {"lat": -14.13, "lon": -75.7, "kind": "coords", "name": "Pueblo Nuevo, Ica"}
SPANISH = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
LANG_BUTTON = ("🌐 Español", "Cambiar la página a español")
VIEWS = {
    "terreno": ("terreno_place", [None, "clima", "sembrar", "rotaciones", "satelite", "whatsapp", "datos", "ayuda"]),
    "clima": ("clima_place", [None, "calendario", "lluvia", "temperatura", "humedad", "tendencia", "rio", "datos"]),
}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: (_ for _ in ()).throw(
        SourceError("red", "sin conexión en las pruebas")))
    monkeypatch.setattr(climate_sections, "_today", lambda: date(2026, 11, 15))


def _strings(o):
    if isinstance(o, str):
        s = o.strip()
        if s[:1] in "{[":
            try:
                yield from _strings(json.loads(s))
                return
            except ValueError:
                pass
        yield unquote(o) if "%" in o else o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def page_strings(at) -> list[str]:
    out = []

    def walk(node):
        proto = getattr(node, "proto", None)
        if proto is not None and hasattr(proto, "DESCRIPTOR"):
            out.extend(_strings(MessageToDict(proto)))
        children = getattr(node, "children", None)
        if isinstance(children, dict):
            for c in children.values():
                walk(c)
    walk(at._tree)
    return out


def spanish_left(at) -> set[str]:
    return {line.strip() for s in page_strings(at) for line in s.splitlines()
            if SPANISH.search(line) and line.strip() not in LANG_BUTTON}


def start(view: str, lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.lang = lang
    if view != "home":
        slot, _ = VIEWS[view]
        at.session_state.view = view
        at.session_state[slot] = dict(ICA)
    at.run(timeout=60)
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_scan_sees_charts_and_options():
    """El recorrido llega al texto de los gráficos y a las opciones de los selectores."""
    at = start("clima", "en")
    next(b for b in at.button if b.key == "bar_clima_rio").click().run(timeout=120)
    assert "mm (September to April)" in page_strings(at)
    at = start("terreno", "en")
    next(b for b in at.button if b.key == "bar_terreno_datos").click().run(timeout=120)
    assert "sandy loam" in page_strings(at)


def test_ca09_home_in_english():
    at = start("home")
    next(b for b in at.button if b.key == "lang_btn").click().run(timeout=60)
    assert spanish_left(at) == set()
    assert next(b for b in at.button if b.key == "lang_btn").label == "🌐 Español"


@pytest.mark.parametrize("view,panel", [(v, p) for v, (_, panels) in VIEWS.items() for p in panels])
def test_ca09_only_the_espanol_button_keeps_spanish_letters(view, panel):
    at = start(view)
    next(b for b in at.button if b.key == "lang_btn").click().run(timeout=60)     # 🌐 English
    assert at.session_state.lang == "en"
    if panel:
        next(b for b in at.button if b.key == f"bar_{view}_{panel}").click().run(timeout=120)
        assert not at.exception, [e.value for e in at.exception]
    assert spanish_left(at) == set()


def test_ca09_rf62_switching_keeps_view_place_and_answers():
    at = start("terreno")
    next(b for b in at.button if b.key == "bar_terreno_datos").click().run(timeout=120)
    at.session_state.overrides[(ICA["lat"], ICA["lon"])]["irrigation"] = "suficiente"
    at.session_state.panel = None
    at.run(timeout=60)
    for lang in ("en", "es"):
        next(b for b in at.button if b.key == "lang_btn").click().run(timeout=60)
        assert not at.exception, [e.value for e in at.exception]
        assert at.session_state.lang == lang
        assert at.session_state.view == "terreno"
        assert at.session_state.terreno_place == ICA                   # el terreno sigue marcado
        assert at.session_state.overrides[(ICA["lat"], ICA["lon"])] == {"irrigation": "suficiente"}
    assert "**Pueblo Nuevo, Ica**" in [m.value for m in at.markdown]
    assert not any(b.disabled for b in at.button if b.key and b.key.startswith("bar_terreno_"))
