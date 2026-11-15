"""Resultados de referencia del Anexo B (CA-04), con los datos guardados en data/cache/ y sin red.

Si un lugar no está completo en la caché, su prueba se salta (se descarga con scripts/prefetch.py, T13).
Hasta T09 se cubre el B.1 completo (clima, zona y contadores Aptos / Con cuidado / No), el B.2 (los 5 cultivos más
aptos con su mejor mes, en el mismo orden) y CA-05. Con los mismos datos guardados la coincidencia es exacta (Spec D3).
"""
import pytest

from rotasat import agro, cache, climate, i18n
from rotasat.crops import get
from rotasat.sources import chirps, imerg, power

# Lugar: (lat, lon, altitud SRTM, pendiente %, clase, región, fuente de lluvia, lluvia anual mm, T media anual °C,
#         días de helada/año, aptos/con cuidado/no) — Anexo B.1.
B1 = {
    "Ica — Valle (Pueblo Nuevo)": (-14.13, -75.7, 405, 0, "plano", "costa", climate.IMERG_RAIN, 49, 21.8, 0, (3, 11, 3)),
    "Junín — Valle del Mantaro (Chupaca)": (-12.06, -75.29, 3272, 15, "ladera", "sierra", climate.CHIRPS_RAIN, 792,
                                            12.1, 4, (8, 1, 8)),
    "Huancavelica — zona altoandina": (-12.79, -74.97, 3788, 64, "ladera", "altoandina", climate.CHIRPS_RAIN, 902,
                                       9.1, 48, (7, 0, 10)),
    "Ayacucho — Huamanga": (-13.16, -74.22, 2733, 8, "suave", "sierra", climate.CHIRPS_RAIN, 642, 14.9, 0, (10, 1, 6)),
    "Apurímac — Andahuaylas": (-13.66, -73.39, 2894, 28, "ladera", "sierra", climate.CHIRPS_RAIN, 907, 14.2, 0, (9, 2, 6)),
    "Puno — Altiplano (Juliaca)": (-15.5, -70.13, 3832, 3, "plano", "altoandina", climate.CHIRPS_RAIN, 498, 9.9,
                                   101, (4, 3, 10)),
    "Junín — Selva central (Satipo)": (-11.25, -74.64, 623, 2, "plano", "selva", climate.CHIRPS_RAIN, 1582, 26.7, 0, (9, 0, 8)),
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
    lat, lon, elev, slope, slope_cls, region, source, rain, t_mean, frost, counts = B1[site]
    pc = _place(site)
    assert round(pc.elev) == elev
    det = climate.detect(pc, lat)
    assert round(det.slope_pct) == slope and det.slope_class == slope_cls
    assert det.region == region
    assert pc.rain_source == source and not pc.preliminary
    assert round(pc.clim["lluvia"].sum()) == rain
    assert round(pc.clim["t_media"].mean(), 1) == t_mean
    assert round(pc.clim["dias_helada"].sum()) == frost
    table = agro.suitability_table(pc.clim, agro.resolve_inputs(det))
    assert agro.level_counts(table) == counts


# Anexo B.2: los 5 cultivos más aptos (nombre ES, aptitud, mejor mes), en orden.
B2 = {
    "Ica — Valle (Pueblo Nuevo)": "Quinua 76 (mayo) | Cebada 72 (mayo) | Sorgo 70 (enero) | Avena forrajera 64 (mayo) | Maní 60 (enero)",
    "Junín — Valle del Mantaro (Chupaca)": "Papa 100 (noviembre) | Olluco 100 (octubre) | Haba 100 (noviembre) | Quinua 100 (diciembre) | Tarwi (chocho) 100 (octubre)",
    "Huancavelica — zona altoandina": "Avena forrajera 86 (noviembre) | Cebada 85 (noviembre) | Quinua 84 (noviembre) | Olluco 78 (octubre) | Haba 76 (noviembre)",
    "Ayacucho — Huamanga": "Haba 100 (noviembre) | Avena forrajera 100 (diciembre) | Quinua 100 (diciembre) | Cebada 100 (diciembre) | Tarwi (chocho) 100 (octubre)",
    "Apurímac — Andahuaylas": "Papa 100 (noviembre) | Maíz amiláceo 100 (noviembre) | Haba 100 (noviembre) | Quinua 100 (noviembre) | Olluco 100 (noviembre)",
    "Puno — Altiplano (Juliaca)": "Cebada 93 (noviembre) | Quinua 92 (noviembre) | Avena forrajera 91 (noviembre) | Haba 66 (noviembre) | Tarwi (chocho) 63 (octubre)",
    "Junín — Selva central (Satipo)": "Algodón 100 (octubre) | Maíz amarillo duro 100 (noviembre) | Pallar 100 (diciembre) | Camote 100 (noviembre) | Sorgo 100 (diciembre)",
}


@pytest.mark.parametrize("site", list(B2))
def test_b2_top5(site):
    pc = _place(site)
    table = agro.suitability_table(pc.clim, agro.resolve_inputs(climate.detect(pc, B1[site][0])))
    got = " | ".join(f"{get(r.id).name_es} {r.aptitud} ({i18n.month(r.mes, 'es')})" for r in table.head(5).itertuples())
    assert got == B2[site]


# Anexo B.3: totales de Actual, A y B puntuadas entre las tres (RC-11, RC-12.8). A y B se toman del anexo, cada
# cultivo en su mejor mes de la tabla (RC-12.2); que el motor las elija solo se prueba en T11.
B3 = {
    "Ica — Valle (Pueblo Nuevo)": ("Quinua → Avena forrajera → Frijol", "Algodón → Quinua → Maní", (56, 90, 89)),
    "Junín — Valle del Mantaro (Chupaca)": ("Avena forrajera → Tarwi (chocho) → Quinua",
                                            "Quinua → Tarwi (chocho) → Papa", (67, 97, 96)),
    "Huancavelica — zona altoandina": ("Avena forrajera → Quinua → Tarwi (chocho)",
                                       "Quinua → Tarwi (chocho) → Papa", (65, 94, 92)),
    "Ayacucho — Huamanga": ("Avena forrajera → Tarwi (chocho) → Quinua", "Quinua → Tarwi (chocho) → Papa", (67, 97, 96)),
    "Apurímac — Andahuaylas": ("Quinua → Avena forrajera → Tarwi (chocho)", "Quinua → Papa → Tarwi (chocho)",
                               (67, 97, 96)),
    "Puno — Altiplano (Juliaca)": ("Quinua → Avena forrajera → Tarwi (chocho)", "Quinua → Tarwi (chocho) → Papa",
                                   (65, 94, 93)),
    "Junín — Selva central (Satipo)": ("Maní → Maíz amarillo duro → Pallar", "Maní → Camote → Pallar", (58, 96, 93)),
}


@pytest.mark.parametrize("site", list(B3))
def test_b3_rotation_totals(site):
    from rotasat.crops import CROPS
    by_name = {c.name_es: c.id for c in CROPS}
    a, b, totals = B3[site]
    pc = _place(site)
    inp = agro.resolve_inputs(climate.detect(pc, B1[site][0]))
    best = agro.suitability_table(pc.clim, inp).set_index("id")["mes"]
    rot = lambda s: tuple((by_name[n], int(best[by_name[n]])) for n in s.split(" → "))
    evals = [agro.evaluate_rotation(r, pc.clim, inp) for r in (inp.rotation, rot(a), rot(b))]
    assert tuple(round(s["total"]) for s in agro.score_rotations(evals, inp)) == totals


@pytest.mark.parametrize("site", list(B3))
def test_b3_auto_rotations(site):
    """T11 (RC-12): el motor elige solo A y B, y los totales mostrados (entre Actual, A y B) son los del B.3."""
    a, b, totals = B3[site]
    pc = _place(site)
    inp = agro.resolve_inputs(climate.detect(pc, B1[site][0]))
    res = agro.auto_rotations(agro.suitability_table(pc.clim, inp), pc.clim, inp)
    assert [agro.rotation_name(r, "es") for r in res[1:]] == [f"A: {a}", f"B: {b}"]
    assert tuple(round(r.total) for r in res) == totals


def test_ca05_ica_sufficient_irrigation():
    """CA-05: en Ica, con «Sí, agua suficiente», la quinua sube de 76 a 89 y queda sin limitaciones importantes."""
    pc = _place("Ica — Valle (Pueblo Nuevo)")
    det = climate.detect(pc, -14.13)
    before = agro.suitability_table(pc.clim, agro.resolve_inputs(det)).set_index("id").loc["quinua"]
    after = agro.suitability_table(pc.clim, agro.resolve_inputs(det, {"irrigation": "suficiente"})).set_index("id").loc["quinua"]
    assert (before["aptitud"], after["aptitud"]) == (76, 89)
    assert after["limitante"] == ("Sin limitaciones importantes", {})
