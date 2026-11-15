"""T20: paneles de la vista Clima (RF-51 a RF-57, RC-18) y CA-03 (parte del clima). AppTest sin red, con los datos
guardados en data/cache/."""
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rotasat.cache import SourceError
from rotasat.ui import climate_sections

APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
SITES = {
    "ica": {"lat": -14.13, "lon": -75.7, "kind": "coords", "name": "Pueblo Nuevo, Ica"},
    "chupaca": {"lat": -12.06, "lon": -75.29, "kind": "coords", "name": "Chupaca, Junín"},
    "satipo": {"lat": -11.25, "lon": -74.64, "kind": "coords", "name": "Satipo, Junín"},
}
PANELS = ["calendario", "lluvia", "temperatura", "humedad", "tendencia", "rio", "datos"]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: (_ for _ in ()).throw(
        SourceError("red", "sin conexión en las pruebas")))
    monkeypatch.setattr(climate_sections, "_today", lambda: date(2026, 11, 15))   # última temporada: 2025–26


def show(site: str, lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.view = "clima"
    at.session_state.lang = lang
    at.session_state.clima_place = dict(SITES[site])
    at.run(timeout=60)
    assert not at.exception, [e.value for e in at.exception]
    return at


def bar_keys(at) -> list[str]:
    return [b.key.removeprefix("bar_clima_") for b in at.button if b.key and b.key.startswith("bar_clima_")]


def open_panel(site: str, panel: str, lang: str = "es") -> AppTest:
    at = show(site, lang)
    next(b for b in at.button if b.key == f"bar_clima_{panel}").click().run(timeout=120)
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state.panel == panel
    return at


def text(at) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption] + [i.value for i in at.info]
    parts += [w.value for w in at.warning] + [e.value for e in at.error] + [s.value for s in at.success]
    return "\n".join(parts)


def html(at) -> str:
    return "\n".join(h.proto.body for h in at.get("html"))


# --- CA-03 (clima): cada panel se abre sin errores, en los 3 lugares y en los 2 idiomas --------------------------

CASES = [(site, panel) for site in SITES for panel in PANELS if panel != "rio" or site == "ica"]


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("site,panel", CASES)
def test_ca03_panels_open_without_errors(site, panel, lang):
    open_panel(site, panel, lang)


def test_river_icon_only_in_the_ica_basin():
    assert bar_keys(show("ica")) == PANELS
    for site in ("chupaca", "satipo"):
        assert bar_keys(show(site)) == [p for p in PANELS if p != "rio"]


def test_closing_a_panel():
    at = open_panel("chupaca", "calendario")
    at.session_state.panel = None                       # lo que hace on_dismiss (Esc, ✕ o tocar fuera)
    at.run(timeout=60)
    assert not at.exception and at.session_state.panel is None


# --- Contenido ---------------------------------------------------------------------------------------------------

def test_rf51_calendar():
    at = open_panel("chupaca", "calendario")
    cal = html(at)
    assert cal.count('<th class="rs-cal-row">') == 6
    assert "rgb(" in cal


def test_rf52_rain_source_and_comparison():
    t = text(open_panel("chupaca", "lluvia"))
    assert "**Fuente de la lluvia:** CHIRPS → **792 mm al año**." in t
    assert "CHIRPS 792" in t


def test_rf53_frost_bars_in_the_highlands_and_no_frost_on_the_coast():
    assert "**❄️ Días con riesgo de helada por mes**" in text(open_panel("chupaca", "temperatura"))
    assert "En este lugar prácticamente no hay heladas." in text(open_panel("ica", "temperatura"))


def test_rf54_moisture_coast_warning():
    assert "En la costa el modelo **no ve el riego**" in text(open_panel("ica", "humedad"))


def test_rf55_trend_sentence():
    assert "Entre 2005–2009 y 2020–2024 la temperatura máxima media **" in text(open_panel("satipo", "tendencia"))


def test_rf56_river_in_spanish():
    at = open_panel("ica", "rio")
    t = text(at)
    assert ("El agua del río Ica nace como lluvia en la cuenca alta de Huancavelica (Choclococha). Si allá llueve "
            "poco, el río trae poco y se depende más de los pozos de un acuífero ya sobreexplotado.") in t
    m = at.metric[-1]                                   # las 3 cifras de la vista van antes
    assert (m.label, m.value, m.delta) == ("Temporada 2025–26", "975 mm", "+8% frente al promedio")
    assert [s.value for s in at.success] == ["**Año normal o húmedo**."]
    assert at.success[0].icon == "🟢"


def test_rf56_river_in_english():
    at = open_panel("ica", "rio", "en")
    assert "upper Huancavelica basin (Choclococha)" in text(at)
    m = at.metric[-1]                                   # las 3 cifras de la vista van antes
    assert (m.label, m.value, m.delta) == ("Season 2025–26", "975 mm", "+8% vs. average")
    assert [s.value for s in at.success] == ["**Normal or wet year**."]


def test_rf56_river_failure_is_a_plain_message(monkeypatch):
    monkeypatch.setattr(climate_sections, "_today", lambda: date(2031, 6, 1))   # temporada no guardada y sin red
    at = open_panel("ica", "rio")
    assert "No se pudo calcular la lluvia de la cuenca alta en este momento." in [w.value for w in at.warning]


def test_rf57_about_the_data():
    t = text(open_panel("chupaca", "datos"))
    assert "**Temperatura corregida por altitud**" in t and "- Lluvia: CHIRPS" in t


def test_terreno_clima_panel_has_the_river_section_only_in_ica():
    def sections(site):
        at = AppTest.from_file(APP).run(timeout=60)
        at.session_state.view = "terreno"
        at.session_state.terreno_place = dict(SITES[site])
        at.run(timeout=60)
        next(b for b in at.button if b.key == "bar_terreno_clima").click().run(timeout=120)
        assert not at.exception, [e.value for e in at.exception]
        return [e.label for e in at.expander]
    assert "💧 ¿Traerá agua el río?" in sections("ica")
    assert "💧 ¿Traerá agua el río?" not in sections("chupaca")
