"""T08: pendiente y región (RC-06), valores por defecto y respuestas del usuario (RC-07). Sin red."""
import math

import pytest

from rotasat import agro
from rotasat.agro import Detected, resolve_inputs


def grid(n, s, w, e, c=100.0):
    return [[c, n, c], [w, c, e], [c, s, c]]


def test_slope_formula():
    lat = -12.0
    g = grid(n=110.0, s=90.0, w=100.0, e=100.0)          # solo norte–sur
    assert agro.slope_pct(g, lat) == pytest.approx(100 * 20 / (2 * 0.001 * 110540))
    g = grid(n=100.0, s=100.0, w=95.0, e=105.0)          # solo este–oeste, corregido por cos(latitud)
    expected = 100 * 10 / (2 * 0.001 * 111320 * math.cos(math.radians(lat)))
    assert agro.slope_pct(g, lat) == pytest.approx(expected)
    assert agro.slope_pct(grid(100, 100, 100, 100), lat) == 0
    assert agro.slope_pct(grid(None, 100, 100, 100), lat) is None


@pytest.mark.parametrize("pct,cls", [(0, "plano"), (2.99, "plano"), (3, "suave"), (11.99, "suave"), (12, "ladera"),
                                     (64, "ladera"), (None, "suave")])
def test_slope_class(pct, cls):
    assert agro.slope_class(pct) == cls


@pytest.mark.parametrize("elev_real,elev_area,rain,region", [
    (3700, None, 900, "altoandina"), (3699, None, 900, "sierra"), (2000, None, 100, "sierra"),
    (1999, None, 299, "costa"), (405, None, 300, "selva"), (623, None, 1582, "selva"),
    (None, 3800, 500, "altoandina"),                   # sin altitud real se usa la del área
    (None, None, 100, "costa"),
])
def test_detect_region(elev_real, elev_area, rain, region):
    assert agro.detect_region(elev_real, elev_area, rain) == region


def test_defaults_by_region():
    costa = resolve_inputs(Detected("costa", 0.4, "plano"))
    assert (costa.irrigation, costa.salt, costa.salt_level) == ("limitada", "media", 0.5)
    assert costa.rotation == (("algodon", 9), ("maiz", 4), ("algodon", 9))
    assert costa.priorities == {"aptitud": 3, "agua": 3, "suelo": 3, "plagas": 2, "clima": 3, "ingresos": 3,
                                "erosion": 2}
    assert costa.texture is None and costa.ph is None and not costa.soil_from_satellite
    for region in ("sierra", "altoandina"):
        r = resolve_inputs(Detected(region, 15, "ladera"))
        assert (r.irrigation, r.salt) == ("no", "baja")
        assert r.rotation == (("papa", 10), ("papa", 10), ("cebada", 12))
    selva = resolve_inputs(Detected("selva", 2, "plano"))
    assert selva.rotation == (("maiz", 10), ("maiz", 3), ("yuca", 10))
    assert selva.slope_class == "plano"


def test_changing_region_changes_defaults_unless_user_set_them():
    det = Detected("costa", 0.4, "plano")
    r = resolve_inputs(det, {"region": "sierra"})
    assert (r.region, r.irrigation, r.salt) == ("sierra", "no", "baja")
    r = resolve_inputs(det, {"region": "sierra", "irrigation": "suficiente"})
    assert (r.irrigation, r.salt) == ("suficiente", "baja")
    # Lo que el usuario cambió no se pisa.
    r = resolve_inputs(det, {"irrigation": "suficiente", "slope_class": "ladera", "priorities": {"agua": 5}})
    assert r.irrigation == "suficiente" and r.slope_class == "ladera"
    assert r.priorities["agua"] == 5 and r.priorities["plagas"] == 2


def test_user_soil_beats_satellite():
    det = Detected("sierra", 15, "ladera")
    sat = {"texture": "franco", "ph": 6.4}
    r = resolve_inputs(det, None, sat)
    assert (r.texture, r.ph, r.soil_from_satellite) == ("franco", 6.4, True)
    r = resolve_inputs(det, {"texture": "arenoso", "ph": 8.0}, sat)
    assert (r.texture, r.ph, r.soil_from_satellite) == ("arenoso", 8.0, False)
    r = resolve_inputs(det, {"texture": "arenoso"}, sat)
    assert (r.texture, r.ph, r.soil_from_satellite) == ("arenoso", 6.4, True)


def test_rotation_override():
    r = resolve_inputs(Detected("sierra", 15, "ladera"), {"rotation": [["quinua", 11], ["haba", 11], ["descanso", 1]]})
    assert r.rotation == (("quinua", 11), ("haba", 11), ("descanso", 1))
