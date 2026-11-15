"""T18: NDVI (RC-16, RF-33) y SoilGrids (RC-19), con servicios simulados. Sin red. CA-12."""
import math
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rotasat import agro
from rotasat.cache import SourceError
from rotasat.sources import ndvi, soilgrids

APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
ICA = {"lat": -14.13, "lon": -75.7, "kind": "coords", "name": "Pueblo Nuevo, Ica"}


# --- RC-16 en el motor -------------------------------------------------------------------------------------------

def test_ndvi_series_drops_no_data_and_filters_with_centered_median():
    dates = ["2023-01-01", "2023-01-17", "2023-02-02", "2023-02-18", "2023-03-06", "2023-03-22"]
    raw = [5000, -3000, 1000, 1500, None, 9000]                  # −3000 y None: sin dato
    s = agro.ndvi_series(dates, raw)
    assert list(s["ndvi"]) == pytest.approx([0.5, 0.1, 0.15, 0.9])
    assert math.isnan(s["filtrado"].iloc[0]) and math.isnan(s["filtrado"].iloc[-1])   # extremos sin valor
    assert list(s["filtrado"].iloc[1:3]) == pytest.approx([0.15, 0.15])


def test_bare_months_are_those_with_filtered_ndvi_below_0_2():
    dates = ["2023-06-01", "2023-06-17", "2023-07-03", "2023-07-19", "2024-06-01", "2024-08-01"]
    s = agro.ndvi_series(dates, [3000, 1000, 1500, 1800, 5000, 6000])
    assert agro.bare_months(s) == [6, 7]


# --- RC-19 en el motor -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("clay,sand,texture", [
    (40, 10, "arcilloso"), (39.9, 10, "franco-arcilloso"), (27, 80, "franco-arcilloso"), (26.9, 70, "arenoso"),
    (10, 69.9, "franco-arenoso"), (10, 50, "franco-arenoso"), (10, 49.9, "franco"),
])
def test_soil_texture(clay, sand, texture):
    assert agro.soil_texture(clay, sand) == texture


@pytest.mark.parametrize("ph,cls", [(5.49, "acido"), (5.5, "lig"), (6.49, "lig"), (6.5, "neutro"), (7.5, "neutro"),
                                    (7.51, "alcalino")])
def test_ph_class(ph, cls):
    assert agro.ph_class(ph) == cls


# --- Fuentes con servicios simulados -----------------------------------------------------------------------------

@pytest.fixture
def tmp_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))


def test_ndvi_downloads_in_chunks_of_ten(tmp_cache, monkeypatch):
    dates = [{"modis_date": f"A2023{d:03d}", "calendar_date": f"2023-{1 + d // 32:02d}-01"} for d in range(1, 300, 12)]
    dates += [{"modis_date": "A2022365", "calendar_date": "2022-12-31"}]          # fuera de 2023–2024
    calls = []

    def fake(service, url, params=None, **kw):
        calls.append(url.rsplit("/", 1)[-1])
        if url.endswith("/dates"):
            return {"dates": dates}
        return {"subset": [{"calendar_date": "x", "data": [100]} for _ in range(10)]}
    monkeypatch.setattr("rotasat.sources.http.get_json", fake)
    out = ndvi.series(-14.13, -75.7)
    wanted = len(dates) - 1
    assert calls == ["dates"] + ["subset"] * math.ceil(wanted / 10)
    assert ndvi.cached(-14.13, -75.7) == out and ndvi.cached(-14.13, -75.7, "viirs") is None


def _soil(clay, sand, ph):
    def layer(name, v):
        return {"name": name, "unit_measure": {"d_factor": 10},
                "depths": [{"label": "0-5cm", "values": {"mean": v}}, {"label": "5-15cm", "values": {"mean": v}}]}
    return {"properties": {"layers": [layer("clay", clay), layer("sand", sand), layer("phh2o", ph)]}}


def test_soilgrids_tries_neighbours_north_south_east_west(tmp_cache, monkeypatch):
    asked = []

    def fake(service, url, params=None, **kw):
        p = dict(params)
        asked.append((p["lat"], p["lon"]))
        if (p["lat"], p["lon"]) == (-14.13, -75.69):                            # este: el primero con dato
            return _soil(82, 754, 79)
        return _soil(None, None, None)
    monkeypatch.setattr("rotasat.sources.http.get_json", fake)
    est = soilgrids.estimate(-14.13, -75.70)
    assert asked == [(-14.13, -75.7), (-14.12, -75.7), (-14.14, -75.7), (-14.13, -75.69)]
    assert est == {"texture": "arenoso", "ph": pytest.approx(7.9), "ph_class": "alcalino", "clay": pytest.approx(8.2),
                   "sand": pytest.approx(75.4), "nearby": True}


def test_soilgrids_without_data_anywhere_fails(tmp_cache, monkeypatch):
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: _soil(None, None, None))
    with pytest.raises(SourceError):
        soilgrids.estimate(-14.13, -75.70)


# --- Interfaz ----------------------------------------------------------------------------------------------------

@pytest.fixture
def offline(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: (_ for _ in ()).throw(
        SourceError("red", "sin conexión en las pruebas")))


def open_panel(panel: str, lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.view = "terreno"
    at.session_state.lang = lang
    at.session_state.terreno_place = dict(ICA)
    at.run(timeout=60)
    next(b for b in at.button if b.key == f"bar_terreno_{panel}").click().run(timeout=120)
    assert not at.exception, [e.value for e in at.exception]
    return at


FAKE_NDVI = {"dates": ["2023-06-01", "2023-06-17", "2023-07-03", "2023-07-19", "2024-01-01"],
             "values": [3000, 1000, 1500, 1800, 6000]}


def test_satellite_panel_with_saved_series(offline, monkeypatch):
    monkeypatch.setattr(ndvi, "cached", lambda lat, lon, product="modis": FAKE_NDVI if product == "modis" else None)
    at = open_panel("satelite")
    assert len(at.get("plotly_chart")) == 1
    assert "**Meses con el campo pelado:** junio, julio · NDVI promedio 0.27" in [m.value for m in at.markdown]


def test_satellite_button_asks_the_service_when_not_saved(offline, monkeypatch):
    monkeypatch.setattr(ndvi, "cached", lambda *a, **k: None)
    monkeypatch.setattr(ndvi, "series", lambda lat, lon, product="modis": FAKE_NDVI)
    at = open_panel("satelite", "en")
    assert not at.get("plotly_chart")
    next(b for b in at.button if b.label == "Query the satellite (2023–2024)").click().run(timeout=120)
    assert len(at.get("plotly_chart")) == 1
    assert "**Months with a bare field:** June, July · mean NDVI 0.27" in [m.value for m in at.markdown]


def test_ca12_ndvi_service_down_shows_plain_error_and_page_keeps_working(offline, monkeypatch):
    monkeypatch.setattr(ndvi, "cached", lambda *a, **k: None)
    monkeypatch.setattr(ndvi, "series", lambda *a, **k: (_ for _ in ()).throw(SourceError("ndvi", "timeout")))
    at = open_panel("satelite")
    next(b for b in at.button if b.label == "Consultar el satélite (2023–2024)").click().run(timeout=120)
    assert not at.exception
    assert [e.value for e in at.error] == ["El servidor de imágenes de la NASA (ORNL) no respondió. Inténtelo más tarde."]
    next(b for b in at.button if b.key == "bar_terreno_sembrar").click().run(timeout=120)   # lo demás sigue
    assert not at.exception and [m.value for m in at.metric] == ["3", "11", "3"]


def test_viirs_failure_keeps_modis(offline, monkeypatch):
    monkeypatch.setattr(ndvi, "cached", lambda lat, lon, product="modis": FAKE_NDVI if product == "modis" else None)
    monkeypatch.setattr(ndvi, "series", lambda *a, **k: (_ for _ in ()).throw(SourceError("ndvi", "timeout")))
    at = open_panel("satelite")
    next(b for b in at.button if b.label == "Agregar VIIRS").click().run(timeout=120)
    assert any(w.value == "VIIRS no está disponible ahora. La app sigue funcionando con MODIS." for w in at.warning)
    assert len(at.get("plotly_chart")) == 1


ESTIMATE = {"texture": "arenoso", "ph": 7.85, "ph_class": "alcalino", "clay": 8.2, "sand": 75.4, "nearby": True}


def test_soilgrids_button_fills_soil_and_user_answer_wins(offline, monkeypatch):
    monkeypatch.setattr(soilgrids, "estimate", lambda lat, lon: ESTIMATE)
    at = open_panel("datos")
    next(b for b in at.button if b.label == "Estimar mi suelo con satélite (SoilGrids)").click().run(timeout=120)
    assert not at.exception
    assert [s.value for s in at.success] == ["Estimación satelital: **arenoso**, pH 7.8 (alcalino) · punto cercano "
                                             "(en pueblos no hay dato). Si usted conoce su suelo, su respuesta manda."]
    assert next(s for s in at.selectbox if s.label == "Tipo de suelo").value == "arenoso"
    assert next(s for s in at.selectbox if s.label.startswith("pH")).value == "alcalino"
    # Lo que escribe el usuario manda (RC-07).
    next(s for s in at.selectbox if s.label == "Tipo de suelo").set_value("franco").run(timeout=120)
    assert next(s for s in at.selectbox if s.label == "Tipo de suelo").value == "franco"
    # «Volver a los valores detectados» borra también la estimación.
    next(b for b in at.button if b.label == "Volver a los valores detectados").click().run(timeout=120)
    assert next(s for s in at.selectbox if s.label == "Tipo de suelo").value is None and not at.success


def test_soilgrids_failure_message(offline, monkeypatch):
    monkeypatch.setattr(soilgrids, "estimate", lambda lat, lon: (_ for _ in ()).throw(SourceError("soilgrids")))
    at = open_panel("datos", "en")
    next(b for b in at.button if b.label == "Estimate my soil by satellite (SoilGrids)").click().run(timeout=120)
    assert [w.value for w in at.warning] == ["SoilGrids did not respond or has no data here. Enter your soil by hand "
                                             "above."]
