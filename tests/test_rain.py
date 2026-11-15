"""T07: lluvia satelital CHIRPS / IMERG (RC-04, RC-05) y su uso en la tabla de clima. Sin red."""
import threading

import pandas as pd
import pytest

from rotasat import cache, climate
from rotasat.cache import SourceError
from rotasat.sources import chirps, climateserv, http, imerg, power, srtm

SITE = (-12.06, -75.29)


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(climateserv, "POLL_SECONDS", 0.0)
    chirps._jobs.clear()
    chirps._errors.clear()
    yield
    for job in list(chirps._jobs.values()):
        job.join(timeout=5)


def _series(start, end, mm_per_day=1.0):
    days = pd.date_range(start, end, freq="D")
    return {"dates": [d.strftime("%Y%m%d") for d in days], "rain": [mm_per_day] * len(days)}


# --- Cliente ClimateSERV ------------------------------------------------------------------------------------------

def test_climateserv_flow_and_negative_values(monkeypatch):
    calls = []

    def fake(service, url, params=None, **kw):
        calls.append(url.rsplit("/", 2)[-2])
        if url.endswith("submitDataRequest/"):
            assert params["datatype"] == 0 and params["operationtype"] == 5
            return ["job-1"]
        if url.endswith("getDataRequestProgress/"):
            return [50.0] if calls.count("getDataRequestProgress") == 1 else [100.0]
        return {"data": [
            {"date": "01/02/2005", "value": {"avg": 3.5}},
            {"date": "01/01/2005", "value": {"avg": -9999.0}},     # negativo = sin dato
        ]}

    monkeypatch.setattr(http, "get_json", fake)
    from datetime import date
    d = climateserv.fetch_daily("chirps", 0, *SITE, date(2005, 1, 1), date(2005, 1, 2), half=0.025)
    assert d == {"dates": ["20050101", "20050102"], "rain": [None, 3.5]}
    assert calls == ["submitDataRequest", "getDataRequestProgress", "getDataRequestProgress", "getDataFromRequest"]


def test_climateserv_error_and_timeout(monkeypatch):
    from datetime import date
    monkeypatch.setattr(http, "get_json", lambda s, url, *a, **k: ["j"] if "submit" in url else [-1.0])
    with pytest.raises(SourceError):
        climateserv.fetch_daily("chirps", 0, *SITE, date(2005, 1, 1), date(2005, 1, 2), half=0.025)
    monkeypatch.setattr(http, "get_json", lambda s, url, *a, **k: ["j"] if "submit" in url else [10.0])
    with pytest.raises(SourceError, match="no terminó"):
        climateserv.fetch_daily("chirps", 0, *SITE, date(2005, 1, 1), date(2005, 1, 2), half=0.025, max_seconds=0)


def test_square_is_one_native_pixel():
    ring = climateserv.square(-12.06, -75.29, climateserv.HALF_CHIRPS)["coordinates"][0]
    assert ring[0] == [-75.315, -12.085] and ring[2] == [-75.265, -12.035] and ring[0] == ring[-1]
    ring = climateserv.square(-14.13, -75.7, climateserv.HALF_IMERG)["coordinates"][0]
    assert ring[0] == [-75.75, -14.18] and ring[2] == [-75.65, -14.08]


def test_each_source_uses_its_pixel(monkeypatch):
    seen = []
    monkeypatch.setattr(climateserv, "fetch_daily",
                        lambda service, dt, *a, half, **k: (seen.append((service, dt, half)), _series("2015-01-01", "2015-01-02"))[1])
    chirps.download(*SITE)
    imerg.download(-14.13, -75.7)
    assert seen == [("chirps", 0, 0.025), ("imerg", 26, 0.05)]


# --- Descarga en segundo plano (RC-05) ----------------------------------------------------------------------------

def test_background_download_lifecycle(monkeypatch):
    release = threading.Event()

    def slow_fetch(*a, **k):
        release.wait(5)
        return _series("2005-01-01", "2005-01-05")

    monkeypatch.setattr(climateserv, "fetch_daily", slow_fetch)
    assert chirps.status(*SITE) == chirps.MISSING
    assert chirps.ensure_background(*SITE) == chirps.RUNNING
    assert chirps.ensure_background(*SITE) == chirps.RUNNING     # no lanza un segundo hilo
    assert len(chirps._jobs) == 1
    release.set()
    chirps._jobs[(-12.06, -75.29)].join(5)
    assert chirps.status(*SITE) == chirps.READY
    assert chirps.cached(*SITE)["rain"] == [1.0] * 5


def test_background_failure_needs_retry(monkeypatch):
    def boom(*a, **k):
        raise SourceError("chirps", "caído")

    monkeypatch.setattr(climateserv, "fetch_daily", boom)
    chirps.ensure_background(*SITE)
    chirps._jobs[(-12.06, -75.29)].join(5)
    assert chirps.status(*SITE) == chirps.FAILED
    assert chirps.ensure_background(*SITE) == chirps.FAILED      # no reintenta solo (RF-22: botón)
    assert chirps.last_error(*SITE).service == "chirps"
    monkeypatch.setattr(climateserv, "fetch_daily", lambda *a, **k: _series("2005-01-01", "2005-01-02"))
    assert chirps.retry(*SITE) == chirps.RUNNING
    chirps._jobs[(-12.06, -75.29)].join(5)
    assert chirps.status(*SITE) == chirps.READY


def test_imerg_never_downloads_from_page(monkeypatch):
    monkeypatch.setattr(climateserv, "fetch_daily", lambda *a, **k: pytest.fail("no debe descargar"))
    assert imerg.cached(-14.13, -75.7) is None


# --- RC-04 en la tabla de clima -----------------------------------------------------------------------------------

def test_monthly_rain_divides_by_years_and_ignores_missing():
    s = _series("2015-01-01", "2024-12-31", 2.0)
    s["rain"][0] = None
    m = climate.monthly_rain(s, 10)
    assert list(m.index) == list(range(1, 13))
    assert m[1] == pytest.approx((31 * 10 - 1) * 2 / 10)
    assert m[7] == pytest.approx(31 * 2.0)


def _fake_place(monkeypatch, *, elev, rain_per_day):
    idx = pd.date_range("2005-01-01", "2024-12-31", freq="D")
    n = len(idx)
    daily = {"elev_area": elev + 100, "dates": [d.strftime("%Y%m%d") for d in idx],
             "t_mean": [15.0] * n, "t_max": [20.0] * n, "t_min": [10.0] * n, "rain": [rain_per_day] * n,
             "ra": [30.0] * n}
    monkeypatch.setattr(power, "daily", lambda lat, lon: daily)
    monkeypatch.setattr(srtm, "terrain", lambda lat, lon: {"elev": elev, "grid": [[elev] * 3] * 3})


def test_build_sierra_preliminary_then_chirps(monkeypatch):
    _fake_place(monkeypatch, elev=3272.0, rain_per_day=1.0)
    started = []
    monkeypatch.setattr(chirps, "ensure_background", lambda lat, lon: (started.append(1), chirps.RUNNING)[1])
    pc = climate.build(*SITE)
    assert pc.rain_source == climate.POWER_RAIN and pc.preliminary and started == [1]
    assert pc.clim.loc[1, "lluvia"] == pytest.approx(31.0)

    cache.save(chirps.SERVICE, chirps._params(*SITE), _series("2005-01-01", "2024-12-31", 3.0))
    pc = climate.build(*SITE)
    assert pc.rain_source == climate.CHIRPS_RAIN and not pc.preliminary
    assert pc.clim.loc[1, "lluvia"] == pytest.approx(93.0)
    assert pc.rain_power[1] == pytest.approx(31.0)              # la original se conserva (RF-52)


def test_build_coast_uses_imerg_only_if_cached(monkeypatch):
    _fake_place(monkeypatch, elev=405.0, rain_per_day=0.1)
    monkeypatch.setattr(chirps, "ensure_background", lambda *a: pytest.fail("en costa no se descarga lluvia"))
    pc = climate.build(-14.13, -75.7)
    assert pc.correction.coast and pc.rain_source == climate.POWER_RAIN and not pc.preliminary
    cache.save(imerg.SERVICE, imerg._params(-14.13, -75.7), _series("2015-01-01", "2024-12-31", 0.5))
    pc = climate.build(-14.13, -75.7)
    assert pc.rain_source == climate.IMERG_RAIN
    assert pc.clim.loc[1, "lluvia"] == pytest.approx(15.5)
