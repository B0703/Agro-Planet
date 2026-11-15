"""T05: clientes de NASA POWER y SRTM.

Las pruebas normales simulan la red. Las marcadas `network` consultan los servicios reales:
    pytest -m network
"""
import math

import pytest

from rotasat import cache
from rotasat.cache import SourceError
from rotasat.sources import http, power, srtm

ICA = (-14.13, -75.70)


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(srtm, "MIN_INTERVAL", 0.0)


def _fake_daily(url, params=None, **kw):
    assert url.endswith("/daily/point")
    days = ["20050101", "20050102", "20050103"]
    def s(vals):
        return dict(zip(days, vals))
    return {
        "geometry": {"coordinates": [params["longitude"], params["latitude"], 1319.63]},
        "properties": {"parameter": {
            "T2M": s([19.39, -999.0, 20.0]), "T2M_MAX": s([24.3, 26.05, 25.0]), "T2M_MIN": s([15.18, 15.44, -999]),
            "PRECTOTCORR": s([0.0, 0.0, 1.2]), "TOA_SW_DWN": s([40.67, 40.67, 40.6]),
        }},
    }


def test_power_daily_parses_and_caches(monkeypatch):
    calls = []
    monkeypatch.setattr(http, "get_json", lambda service, url, params=None, **kw: (calls.append(1), _fake_daily(url, params))[1])
    d = power.daily(*ICA)
    assert d["elev_area"] == 1319.63
    assert d["dates"] == ["20050101", "20050102", "20050103"]
    assert d["t_mean"] == [19.39, None, 20.0]       # -999 → faltante
    assert d["t_min"][2] is None
    power.daily(-14.130000001, -75.70)               # mismo punto redondeado: sale de la caché
    assert len(calls) == 1
    df = power.daily_frame(d)
    assert list(df.columns) == ["t_mean", "t_max", "t_min", "rain", "ra"]
    assert math.isnan(df["t_mean"].iloc[1]) and str(df.index[0].date()) == "2005-01-01"


def test_power_soil_drops_annual_month(monkeypatch):
    def fake(service, url, params=None, **kw):
        m = {"200501": 0.21, "200502": 0.18, "200513": 0.17, "200601": -999}
        return {"properties": {"parameter": {"GWETTOP": m, "GWETROOT": {k: 0.38 for k in m}}}}
    monkeypatch.setattr(http, "get_json", fake)
    s = power.soil_moisture(*ICA)
    assert s["months"] == ["200501", "200502", "200601"]
    assert s["surface"] == [0.21, 0.18, None]


def test_power_unexpected_response(monkeypatch):
    monkeypatch.setattr(http, "get_json", lambda *a, **k: {"messages": ["error"]})
    with pytest.raises(SourceError) as e:
        power.daily(*ICA)
    assert e.value.service == "power"
    assert not cache.has("power_daily", {"lat": -14.13})


def test_srtm_grid_order(monkeypatch):
    seen = {}

    def fake(service, url, params=None, **kw):
        seen["locations"] = params["locations"]
        return {"status": "OK", "results": [{"elevation": e} for e in [1, 2, 3, 4, 405, 6, 7, None, 9]]}

    monkeypatch.setattr(http, "get_json", fake)
    t = srtm.terrain(*ICA)
    assert t["elev"] == 405.0
    assert t["grid"] == [[1.0, 2.0, 3.0], [4.0, 405.0, 6.0], [7.0, None, 9.0]]
    pts = [tuple(map(float, p.split(","))) for p in seen["locations"].split("|")]
    assert pts[0] == (-14.129, -75.701)   # noroeste
    assert pts[4] == (-14.13, -75.7)      # centro
    assert pts[8] == (-14.131, -75.699)   # sureste


def test_srtm_error_status(monkeypatch):
    monkeypatch.setattr(http, "get_json", lambda *a, **k: {"status": "INVALID_REQUEST", "error": "bad"})
    with pytest.raises(SourceError):
        srtm.elevation(*ICA)


@pytest.mark.network
def test_network_ica():
    """Criterio de T05: Ica se descarga y guarda; la altitud SRTM es 405 m."""
    assert srtm.elevation(*ICA) == 405.0
    d = power.daily(*ICA)
    assert len(d["dates"]) == 7305 and d["dates"][0] == "20050101" and d["dates"][-1] == "20241231"
    assert d["elev_area"] is not None and d["elev_area"] > 405
    s = power.soil_moisture(*ICA)
    assert len(s["months"]) == 240
    assert cache.has("srtm", {"lat": -14.13, "lon": -75.7})
