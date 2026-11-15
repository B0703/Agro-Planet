"""Resultados de referencia del Anexo B (CA-04), con los datos guardados en data/cache/ y sin red.

Si un lugar no está en la caché, su prueba se salta (se descarga con scripts/prefetch.py, T13).
T06 cubre la parte de clima del B.1: altitud SRTM, temperatura media anual y días de helada al año.
"""

import pytest

from rotasat import agro, cache
from rotasat.sources import power, srtm

# Lugar: (lat, lon, altitud SRTM, T media anual °C, días de helada/año) del Anexo B.1.
B1 = {
    "Ica — Valle (Pueblo Nuevo)": (-14.13, -75.7, 405, 21.8, 0),
    "Junín — Valle del Mantaro (Chupaca)": (-12.06, -75.29, 3272, 12.1, 4),
    "Huancavelica — zona altoandina": (-12.79, -74.97, 3788, 9.1, 48),
    "Ayacucho — Huamanga": (-13.16, -74.22, 2733, 14.9, 0),
    "Apurímac — Andahuaylas": (-13.66, -73.39, 2894, 14.2, 0),
    "Puno — Altiplano (Juliaca)": (-15.5, -70.13, 3832, 9.9, 101),
    "Junín — Selva central (Satipo)": (-11.25, -74.64, 623, 26.7, 0),
}


@pytest.fixture(autouse=True)
def project_cache(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)   # usa data/cache/ del proyecto


def _cached(lat, lon) -> bool:
    p = {"lat": lat, "lon": lon}
    return cache.has("srtm", p) and cache.has(
        "power_daily", {**p, "start": "20050101", "end": "20241231", "p": sorted(power.DAILY_PARAMS)})


@pytest.mark.parametrize("site", list(B1))
def test_b1_climate(site, monkeypatch):
    lat, lon, elev, t_mean, frost = B1[site]
    if not _cached(lat, lon):
        pytest.skip("lugar no descargado en data/cache/")
    # Sin red: cualquier intento de consultar un servicio es un error.
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: pytest.fail("consultó la red"))
    d = power.daily(lat, lon)
    e = srtm.elevation(lat, lon)
    assert round(e) == elev
    corrected, _ = agro.correct_temperatures(power.daily_frame(d), d["elev_area"], e)
    clim, _ = agro.monthly_climate(corrected)
    assert round(clim["t_media"].mean(), 1) == pytest.approx(t_mean, abs=1)
    assert round(clim["dias_helada"].sum()) == pytest.approx(frost, abs=1)
    # Con los mismos datos guardados la coincidencia es exacta (Spec D3).
    assert round(clim["t_media"].mean(), 1) == t_mean
    assert round(clim["dias_helada"].sum()) == frost
