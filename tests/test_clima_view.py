"""T19: vista Clima (RF-40 a RF-45, RNF-09, CA-07). AppTest sin red; el navegador (get_geolocation) es simulado."""
import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rotasat.cache import SourceError
from rotasat.ui import location

APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
ICA_COORDS = {"coords": {"latitude": -14.13, "longitude": -75.70}}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: (_ for _ in ()).throw(
        SourceError("red", "sin conexión en las pruebas")))


@pytest.fixture
def browser(monkeypatch):
    """Lo que responde el navegador al pedido de ubicación (None = aún no responde). Anota cada pedido."""
    state = {"answer": None, "asked": []}

    def fake(component_key=None):
        state["asked"].append(component_key)
        return state["answer"]
    monkeypatch.setattr(location, "get_geolocation", fake)
    return state


def enter_clima(lang="es") -> AppTest:
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.lang = lang
    at.run(timeout=60)
    next(b for b in at.button if b.key == "home_clima").click().run(timeout=60)
    assert not at.exception, [e.value for e in at.exception]
    return at


def bar(at):
    return [b for b in at.button if b.key and b.key.startswith("bar_clima_")]


def test_rnf09_home_does_not_ask_for_location(browser):
    AppTest.from_file(APP).run(timeout=60)
    assert browser["asked"] == []


def test_rf41_entering_asks_and_shows_search_while_waiting(browser):
    at = enter_clima()
    assert browser["asked"]                                                     # se pidió al entrar
    assert "### 🌦️ Clima de mi ubicación" in [m.value for m in at.markdown]
    assert any("Buscando su ubicación" in i.value for i in at.info)
    assert "¿No aparece el permiso o prefiere otro lugar? Escríbalo aquí:" in [m.value for m in at.markdown]
    assert at.text_input(key="clima_place_q") is not None
    assert not bar(at)


def test_ca07_with_permission_shows_my_location_and_its_climate(browser):
    browser["answer"] = ICA_COORDS
    at = enter_clima()
    assert at.session_state.clima_place == {"lat": -14.13, "lon": -75.7, "kind": "gps", "name": "Pueblo Nuevo, Ica"}
    assert "**Mi ubicación actual (Pueblo Nuevo, Ica)**" in [m.value for m in at.markdown]
    assert [(m.label, m.value) for m in at.metric] == [("🌧️ Lluvia al año", "49 mm"),
                                                      ("🌡️ Temperatura media", "21.8 °C"),
                                                      ("❄️ Días con riesgo de helada", "0 al año")]
    assert "🌧️ **Casi no llueve**: 49 mm al año. Aquí los cultivos dependen del riego." in [m.value for m in at.markdown]
    assert "Toque un icono para ver el detalle:" in [c.value for c in at.caption]
    assert len(bar(at)) == 7 and not any(b.disabled for b in bar(at))
    assert at.session_state.terreno_place is None                               # RF-45: independientes


@pytest.mark.parametrize("answer,message", [
    ({"error": {"code": 1, "message": "User denied"}}, "No se dio permiso para usar la ubicación. Escriba su ubicación."),
    ({"error": {"code": 2}}, "El dispositivo no pudo obtener la ubicación. Escriba su ubicación."),
    ({"error": {"code": 0, "message": "Browser does not support geolocation!"}},
     "Este navegador no permite obtener la ubicación. Escriba su ubicación."),
])
def test_ca07_without_permission_asks_to_type(browser, answer, message):
    browser["answer"] = answer
    at = enter_clima()
    assert [w.value for w in at.warning] == [message]
    assert "**¿De qué lugar quiere ver el clima?**" in [m.value for m in at.markdown]
    assert at.text_input(key="clima_place_q") is not None
    assert not any("Buscando su ubicación" in i.value for i in at.info)


def test_ca07_no_answer_in_15_seconds(browser):
    at = enter_clima()                                                          # el navegador no responde
    assert any("Buscando su ubicación" in i.value for i in at.info)
    at.session_state["clima_place_gps_t0"] = time.monotonic() - 16
    at.run(timeout=60)
    assert [w.value for w in at.warning] == ["La ubicación tardó demasiado en responder. Escriba su ubicación."]
    assert "**¿De qué lugar quiere ver el clima?**" in [m.value for m in at.markdown]


def test_ca07_in_english(browser):
    browser["answer"] = {"error": {"code": 1}}
    at = enter_clima("en")
    assert [w.value for w in at.warning] == ["Location permission was not granted. Please type your location."]


def test_typing_a_place_after_failure(browser):
    browser["answer"] = {"error": {"code": 1}}
    at = enter_clima()
    at.text_input(key="clima_place_q").input("-14.13, -75.70")
    next(b for b in at.button if b.label == "Buscar").click().run(timeout=60)
    assert "**Pueblo Nuevo, Ica**" in [m.value for m in at.markdown]
    assert len(bar(at)) == 7


def test_language_switch_while_waiting_does_not_ask_again(browser):
    at = enter_clima()
    n = at.session_state["clima_place_gps_n"]
    next(b for b in at.button if b.key == "lang_btn").click().run(timeout=60)
    assert at.session_state["clima_place_gps_n"] == n
    assert any("Finding your location" in i.value for i in at.info)


def test_rf45_place_is_reused_when_coming_back(browser):
    browser["answer"] = ICA_COORDS
    at = enter_clima()
    asked = len(browser["asked"])
    next(b for b in at.button if b.key == "home_back").click().run(timeout=60)
    next(b for b in at.button if b.key == "home_clima").click().run(timeout=60)
    assert len(browser["asked"]) == asked                                       # no se volvió a pedir
    assert "**Mi ubicación actual (Pueblo Nuevo, Ica)**" in [m.value for m in at.markdown]


def test_rf44_see_what_to_plant_carries_the_place_to_terreno(browser):
    browser["answer"] = ICA_COORDS
    at = enter_clima()
    next(b for b in at.button if b.key == "clima_to_terreno").click().run(timeout=60)
    assert at.session_state.view == "terreno"
    assert at.session_state.terreno_place == at.session_state.clima_place
    assert "**Mi ubicación actual (Pueblo Nuevo, Ica)**" in [m.value for m in at.markdown]
    assert not any(b.disabled for b in at.button if b.key and b.key.startswith("bar_terreno_"))


def test_rf44_change_place_goes_back_to_typing_without_asking(browser):
    browser["answer"] = ICA_COORDS
    at = enter_clima()
    asked = len(browser["asked"])
    next(b for b in at.button if b.key == "clima_change").click().run(timeout=60)
    assert at.session_state.clima_place is None
    assert "**¿De qué lugar quiere ver el clima?**" in [m.value for m in at.markdown]
    assert len(browser["asked"]) == asked and not at.warning
