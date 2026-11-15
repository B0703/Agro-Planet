"""T13: scripts/prefetch.py (RNF-03), con caché temporal y fuentes simuladas. Sin red."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from rotasat import cache

_SPEC = importlib.util.spec_from_file_location("prefetch", Path(__file__).parent.parent / "scripts" / "prefetch.py")
prefetch = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prefetch)


@pytest.fixture
def no_network(monkeypatch, tmp_path):
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: pytest.fail("consultó la red"))


@pytest.fixture
def fake_sources(monkeypatch, no_network):
    """Fuentes simuladas que anotan qué se pidió. Ica es costa; el resto no."""
    calls = []

    def rec(name):
        return lambda lat, lon: calls.append((name, lat)) or {"ok": True}

    for mod, fn in [(prefetch.power, "daily"), (prefetch.srtm, "terrain"), (prefetch.power, "soil_moisture"),
                    (prefetch.chirps, "download"), (prefetch.imerg, "download"), (prefetch.geocode, "point_name")]:
        monkeypatch.setattr(mod, fn, rec(f"{mod.__name__.rsplit('.', 1)[-1]}.{fn}"))
    monkeypatch.setattr(prefetch.climate, "build", lambda lat, lon, start_download: SimpleNamespace(
        correction=SimpleNamespace(coast=lat == -14.13)))
    return calls


def test_sites_are_annex_b():
    assert len(prefetch.SITES) == 7
    assert prefetch.SITES["Ica — Valle (Pueblo Nuevo)"] == (-14.13, -75.7)


def test_check_on_empty_cache_reports_everything_missing_without_network(no_network):
    lines = []
    missing = prefetch.run({"Ica": (-14.13, -75.7)}, check=True, out=lines.append)
    assert missing == 5                                  # POWER diario, SRTM, humedad, lluvia y nombre
    assert all("falta en la caché" in x for x in lines[1:])
    assert prefetch.http.get_json is not prefetch._offline   # la red queda como estaba


def test_coast_downloads_imerg_and_others_chirps(fake_sources):
    assert prefetch.run({"Ica": (-14.13, -75.7), "Puno": (-15.5, -70.13)}, out=lambda _: None) == 0
    names = [n for n, _ in fake_sources]
    assert names == ["power.daily", "srtm.terrain", "power.soil_moisture", "imerg.download", "geocode.point_name",
                     "power.daily", "srtm.terrain", "power.soil_moisture", "chirps.download", "geocode.point_name"]


def test_searches_are_prefetched(fake_sources, monkeypatch):
    monkeypatch.setattr(prefetch.geocode, "search", lambda q: fake_sources.append(("geocode.search", q)) or [])
    lines = []
    assert prefetch.run({}, out=lines.append, searches=prefetch.SEARCHES) == 0
    assert fake_sources == [("geocode.search", "Tarma, Junin")]
    assert lines == ["Búsquedas de ejemplo (OpenStreetMap)", "  ✓ «Tarma, Junin» (0 s)"]


def test_a_failure_does_not_stop_the_rest(fake_sources, monkeypatch):
    def boom(lat, lon):
        raise cache.SourceError("power", cause=TimeoutError())
    monkeypatch.setattr(prefetch.power, "soil_moisture", boom)
    lines = []
    assert prefetch.run({"Puno": (-15.5, -70.13)}, out=lines.append) == 1
    assert "  ✗ NASA POWER (humedad del suelo): power: TimeoutError" in lines
    assert ("chirps.download", -15.5) in fake_sources


def test_main_site_filter_and_exit_codes(fake_sources):
    assert prefetch.main(["--site", "puno"]) == 0
    assert {lat for _, lat in fake_sources} == {-15.5}
    assert prefetch.main(["--site", "Lima"]) == 2
