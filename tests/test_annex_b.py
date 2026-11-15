"""Resultados de referencia del Anexo B (CA-04), con los datos guardados en data/cache/ y sin red.

Si un lugar no está completo en la caché, su prueba se salta (se descarga con scripts/prefetch.py, T13).
Hasta T08 se cubre la parte de clima y zona del B.1: altitud SRTM, pendiente, región, fuente de lluvia, lluvia
anual, temperatura media anual y días de helada al año. Con los mismos datos guardados la coincidencia es exacta (Spec D3).
"""
import pytest

from rotasat import cache, climate
from rotasat.sources import chirps, imerg, power

# Lugar: (lat, lon, altitud SRTM, pendiente %, clase, región, fuente de lluvia, lluvia anual mm, T media anual °C,
#         días de helada/año) — Anexo B.1.
B1 = {
    "Ica — Valle (Pueblo Nuevo)": (-14.13, -75.7, 405, 0, "plano", "costa", climate.IMERG_RAIN, 49, 21.8, 0),
    "Junín — Valle del Mantaro (Chupaca)": (-12.06, -75.29, 3272, 15, "ladera", "sierra", climate.CHIRPS_RAIN, 792,
                                            12.1, 4),
    "Huancavelica — zona altoandina": (-12.79, -74.97, 3788, 64, "ladera", "altoandina", climate.CHIRPS_RAIN, 902,
                                       9.1, 48),
    "Ayacucho — Huamanga": (-13.16, -74.22, 2733, 8, "suave", "sierra", climate.CHIRPS_RAIN, 642, 14.9, 0),
    "Apurímac — Andahuaylas": (-13.66, -73.39, 2894, 28, "ladera", "sierra", climate.CHIRPS_RAIN, 907, 14.2, 0),
    "Puno — Altiplano (Juliaca)": (-15.5, -70.13, 3832, 3, "plano", "altoandina", climate.CHIRPS_RAIN, 498, 9.9,
                                   101),
    "Junín — Selva central (Satipo)": (-11.25, -74.64, 623, 2, "plano", "selva", climate.CHIRPS_RAIN, 1582, 26.7, 0),
}


@pytest.fixture(autouse=True)
def project_cache(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)   # usa data/cache/ del proyecto
    # Sin red: cualquier intento de consultar un servicio es un error.
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: pytest.fail("consultó la red"))


def _complete(lat, lon, source) -> bool:
    p = {"lat": lat, "lon": lon}
    base = cache.has("srtm", p) and cache.has(
        "power_daily", {**p, "start": "20050101", "end": "20241231", "p": sorted(power.DAILY_PARAMS)})
    rain = imerg.cached(lat, lon) if source == climate.IMERG_RAIN else chirps.cached(lat, lon)
    return base and rain is not None


def _place(site):
    lat, lon, _, _, _, _, source, *_ = B1[site]
    if not _complete(lat, lon, source):
        pytest.skip("lugar no descargado por completo en data/cache/")
    return climate.build(lat, lon, start_download=False)


@pytest.mark.parametrize("site", list(B1))
def test_b1_climate(site):
    lat, lon, elev, slope, slope_cls, region, source, rain, t_mean, frost = B1[site]
    pc = _place(site)
    assert round(pc.elev) == elev
    det = climate.detect(pc, lat)
    assert round(det.slope_pct) == slope and det.slope_class == slope_cls
    assert det.region == region
    assert pc.rain_source == source and not pc.preliminary
    assert round(pc.clim["lluvia"].sum()) == rain
    assert round(pc.clim["t_media"].mean(), 1) == t_mean
    assert round(pc.clim["dias_helada"].sum()) == frost
