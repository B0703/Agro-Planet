"""T16: vista Mi terreno (RF-11 a RF-22, CA-02, CA-08). AppTest sin red: los datos de Ica salen de data/cache/ y los
casos de fallo o de descarga en curso usan fuentes simuladas."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rotasat import climate
from rotasat.cache import SourceError
from rotasat.sources import chirps

_real_build = climate.build
APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
BAR = "bar_terreno_"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)          # usa data/cache/ del proyecto
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: (_ for _ in ()).throw(
        SourceError("red", "sin conexión en las pruebas")))


def terreno() -> AppTest:
    at = AppTest.from_file(APP).run(timeout=60)
    next(b for b in at.button if b.key == "home_terreno").click().run(timeout=60)
    assert not at.exception
    return at


def search(at: AppTest, text: str) -> AppTest:
    at.text_input(key="terreno_place_q").input(text)
    next(b for b in at.button if b.label == "Buscar").click().run(timeout=60)
    assert not at.exception
    return at


def bar(at):
    return [b for b in at.button if b.key and b.key.startswith(BAR)]


def captions(at):
    return [c.value for c in at.caption]


def test_ca02_coordinates_enable_icons_and_show_place_line():
    at = terreno()
    assert len(bar(at)) == 7 and all(b.disabled for b in bar(at))
    assert any("**Marque su terreno**" in i.value for i in at.info)              # RF-17
    search(at, "-14.13, -75.70")
    assert at.session_state.terreno_place == {"lat": -14.13, "lon": -75.7, "kind": "coords",
                                              "name": "Pueblo Nuevo, Ica"}
    assert "**Pueblo Nuevo, Ica**" in [m.value for m in at.markdown]
    assert "🏜️ Costa desértica · 405 m de altitud · -14.1300, -75.7000" in captions(at)
    assert "Toque un icono para ver esa información:" in captions(at)
    assert not any(b.disabled for b in bar(at))
    assert not at.info                                                          # Ica (costa): nada preliminar


def test_place_line_follows_language():
    at = search(terreno(), "-14.13, -75.70")
    next(b for b in at.button if b.key == "lang_btn").click().run(timeout=60)
    assert "**Pueblo Nuevo, Ica**" in [m.value for m in at.markdown]            # el nombre no se traduce
    assert "🏜️ Desert coast · 405 m altitude · -14.1300, -75.7000" in captions(at)


def test_search_single_result_goes_directly(monkeypatch):
    monkeypatch.setattr(climate, "build", lambda *a, **k: (_ for _ in ()).throw(SourceError("power")))
    at = search(terreno(), "Tarma, Junin")                                       # CA-06, desde la caché
    assert at.session_state.terreno_place["name"] == "Tarma, Junín"
    assert at.session_state.terreno_place["kind"] == "search"


def test_search_several_results_are_listed(monkeypatch):
    found = [{"name": f"Pueblo Nuevo, {r}", "lat": -7.0 - i, "lon": -79.0} for i, r in enumerate("ABC")]
    monkeypatch.setattr("rotasat.sources.geocode.search", lambda text: found)
    monkeypatch.setattr(climate, "build", lambda *a, **k: (_ for _ in ()).throw(SourceError("power")))
    at = search(terreno(), "Pueblo Nuevo")
    assert "¿Cuál de estos lugares es?" in [m.value for m in at.markdown]
    choices = [b for b in at.button if b.key and b.key.startswith("terreno_place_choice_")]
    assert [b.label for b in choices] == ["Pueblo Nuevo, A", "Pueblo Nuevo, B", "Pueblo Nuevo, C"]
    choices[1].click().run(timeout=60)
    assert at.session_state.terreno_place == {"lat": -8.0, "lon": -79.0, "kind": "search", "name": "Pueblo Nuevo, B"}


@pytest.mark.parametrize("answer,message", [
    ([], "No encontramos ese lugar. Pruebe con el nombre del distrito o escriba coordenadas."),
    (SourceError("geocode"), "El buscador no respondió. Pruebe otra vez, escriba coordenadas o haga clic en el mapa."),
])
def test_search_without_results_or_failing(monkeypatch, answer, message):
    def fake(text):
        if isinstance(answer, Exception):
            raise answer
        return answer
    monkeypatch.setattr("rotasat.sources.geocode.search", fake)
    at = search(terreno(), "zzzz")
    assert message in [w.value for w in at.warning]
    assert at.session_state.terreno_place is None


def test_rf22_main_data_failure_shows_retry_and_keeps_icons_disabled(monkeypatch):
    calls = []

    def failing(lat, lon, **k):
        calls.append((lat, lon))
        raise SourceError("power", cause=TimeoutError())
    monkeypatch.setattr(climate, "build", failing)
    at = search(terreno(), "-12.5, -75.1")
    assert [e.value for e in at.error] == ["No se pudieron obtener los datos de la NASA (TimeoutError). Revise su "
                                           "internet."]
    assert all(b.disabled for b in bar(at))
    next(b for b in at.button if b.label == "Reintentar").click().run(timeout=60)
    assert len(calls) == 2                                                      # «Reintentar» vuelve a pedir


_REAL = {}


def _fake_pc(source, status):
    if "ica" not in _REAL:                                                      # tabla de Ica, de la caché
        _REAL["ica"] = _real_build(-14.13, -75.7, start_download=False)
    real = _REAL["ica"]
    return climate.PlaceClimate(clim=real.clim, rain_power=real.rain_power, p90=real.p90,
                                correction=real.correction, elev=3300.0, elev_area=real.elev_area,
                                terrain=real.terrain, rain_source=source, rain_status=status)


def test_ca08_preliminary_notice_goes_away_when_rain_arrives(monkeypatch):
    state = {"status": chirps.RUNNING}
    prelim, final = _fake_pc(climate.POWER_RAIN, chirps.RUNNING), _fake_pc(climate.CHIRPS_RAIN, chirps.READY)
    monkeypatch.setattr(climate, "build", lambda lat, lon, **k: prelim if state["status"] == chirps.RUNNING else final)
    monkeypatch.setattr(chirps, "status", lambda lat, lon: state["status"])
    at = search(terreno(), "-12.5, -75.1")
    assert any("**preliminares**" in i.value for i in at.info)
    at.run(timeout=60)                                                          # sigue descargando: no cambia
    assert any("**preliminares**" in i.value for i in at.info)
    state["status"] = chirps.READY                                              # lo que ve el sondeo de 6 s
    at.run(timeout=60)
    assert not any("**preliminares**" in i.value for i in at.info)


def test_rf22_rain_failure_offers_retry(monkeypatch):
    state = {"status": chirps.FAILED}
    retried = []
    monkeypatch.setattr(climate, "build", lambda lat, lon, **k: _fake_pc(climate.POWER_RAIN, state["status"]))
    monkeypatch.setattr(chirps, "status", lambda lat, lon: state["status"])
    monkeypatch.setattr(chirps, "retry", lambda lat, lon: retried.append((lat, lon)) or chirps.RUNNING)
    at = search(terreno(), "-12.5, -75.1")
    assert any("**subestima la lluvia en sierra y selva**" in w.value for w in at.warning)
    assert not any(b.disabled for b in bar(at))                                  # se sigue con lo disponible
    next(b for b in at.button if b.label == "Reintentar lluvia satelital").click().run(timeout=60)
    assert retried == [(-12.5, -75.1)]


def test_gps_button_only_asks_after_click():
    at = terreno()
    assert not at.info or all("Buscando su ubicación" not in i.value for i in at.info)
    next(b for b in at.button if b.key == "terreno_place_gps_btn").click().run(timeout=60)
    assert any("Buscando su ubicación" in i.value for i in at.info)
