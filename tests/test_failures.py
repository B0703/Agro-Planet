"""T21: revisión de fallos de servicios (RNF-05, P7) y tiempos (RNF-04). AppTest sin red.

Ningún fallo de un servicio externo deja la página en blanco ni muestra un error técnico: se avisa en lenguaje sencillo
y se ofrece reintentar o seguir con lo disponible. Lo ya probado en otras partes: búsqueda caída y fallo de los datos
principales en Mi terreno (test_terreno_view), NDVI y SoilGrids (test_ndvi_soil, CA-12) y el río (test_clima_panels).
"""
import time
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rotasat.cache import SourceError
from rotasat.sources import chirps, geocode, power
from rotasat.ui import climate_sections

APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
ICA = {"lat": -14.13, "lon": -75.7, "kind": "coords", "name": "Pueblo Nuevo, Ica"}
CHUPACA = {"lat": -12.06, "lon": -75.29, "kind": "coords", "name": "Chupaca, Junín"}
PANELS = {"terreno": ["clima", "sembrar", "rotaciones", "satelite", "whatsapp", "datos", "ayuda"],
          "clima": ["calendario", "lluvia", "temperatura", "humedad", "tendencia", "datos"]}


def _down(*_a, **_k):
    raise SourceError("servicio", "sin conexión en las pruebas")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)
    monkeypatch.setattr("rotasat.sources.http.get_json", _down)
    monkeypatch.setattr(climate_sections, "_today", lambda: date(2026, 11, 15))


def show(view: str, place: dict, panel: str | None = None) -> AppTest:
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.view = view
    at.session_state[f"{view}_place"] = dict(place)
    at.run(timeout=60)
    if panel:
        next(b for b in at.button if b.key == f"bar_{view}_{panel}").click().run(timeout=120)
    assert not at.exception, [e.value for e in at.exception]
    return at


def search(at, view: str, text: str) -> None:
    at.text_input(key=f"{view}_place_q").input(text)
    next(b for b in at.button if b.label == "Buscar").click().run(timeout=60)
    assert not at.exception, [e.value for e in at.exception]


def test_clima_main_data_failure_offers_retry_and_change_place(monkeypatch, tmp_path):
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))              # lugar nuevo, sin nada guardado
    at = show("clima", {"lat": -12.5, "lon": -75.0, "kind": "coords", "name": None})
    assert [e.value for e in at.error] == ["No se pudieron obtener los datos de la NASA (SourceError). Revise su internet."]
    labels = [b.label for b in at.button]
    assert "Reintentar" in labels and "Cambiar de lugar" in labels
    assert not [b for b in at.button if b.key and b.key.startswith("bar_clima_")]


def test_place_name_service_down_falls_back_to_coordinates(monkeypatch):
    monkeypatch.setattr(geocode, "point_name", _down)
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.view = "terreno"
    at.run(timeout=60)
    search(at, "terreno", "-14.13, -75.70")
    assert "**Coordenadas -14.1300, -75.7000**" in [m.value for m in at.markdown]
    assert not any(b.disabled for b in at.button if b.key and b.key.startswith("bar_terreno_"))


@pytest.mark.parametrize("view,panel", [("terreno", "clima"), ("clima", "calendario"), ("clima", "humedad")])
def test_soil_moisture_down(monkeypatch, view, panel):
    monkeypatch.setattr(power, "soil_moisture", _down)
    at = show(view, ICA, panel)
    if panel == "calendario":                       # la fila de humedad simplemente no aparece (RF-51)
        assert "Humedad del suelo, raíces" not in "\n".join(h.proto.body for h in at.get("html"))
    else:
        assert "No se pudo obtener la humedad del suelo en este momento." in [w.value for w in at.warning]


@pytest.mark.parametrize("view,panel", [(v, p) for v, ps in PANELS.items() for p in ps])
def test_satellite_rain_failed_every_panel_still_works(monkeypatch, view, panel):
    """CHIRPS falló en un lugar de la sierra: aviso con reintento y todos los paneles con la lluvia de NASA POWER."""
    monkeypatch.setattr(chirps, "cached", lambda *a, **k: None)
    monkeypatch.setattr(chirps, "status", lambda *a, **k: chirps.FAILED)
    monkeypatch.setattr(chirps, "ensure_background", lambda *a, **k: chirps.FAILED)
    at = show(view, CHUPACA, panel)
    assert any(w.value.startswith("El servicio de lluvia satelital no respondió.") for w in at.warning)
    assert "Reintentar lluvia satelital" in [b.label for b in at.button]


# --- RNF-04 Tiempos ----------------------------------------------------------------------------------------------

def test_rnf04_saved_place_enables_icons_in_5_s_and_panels_open_in_3_s():
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.view = "terreno"
    at.run(timeout=60)
    t0 = time.perf_counter()
    search(at, "terreno", "-14.13, -75.70")
    assert time.perf_counter() - t0 < 5
    assert not any(b.disabled for b in at.button if b.key and b.key.startswith("bar_terreno_"))
    for panel in PANELS["terreno"]:
        t0 = time.perf_counter()
        next(b for b in at.button if b.key == f"bar_terreno_{panel}").click().run(timeout=60)
        assert not at.exception
        assert time.perf_counter() - t0 < 3, panel
        at.session_state.panel = None
        at.run(timeout=60)
