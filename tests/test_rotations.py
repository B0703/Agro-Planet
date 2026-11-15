"""T10: evaluación de una rotación en la línea de 36 meses (RC-10) y sus puntajes (RC-11). Climas sintéticos, sin red."""
import pytest

from rotasat import agro
from rotasat.crops import get
from tests.test_suitability import clim, inputs

SIERRA = (("papa", 10), ("papa", 10), ("cebada", 12))


# --- RC-10: colocación en la línea ---------------------------------------------------------------------------------

def test_place_sierra_default_truncates_third_crop():
    # Papa (6 meses) en oct. del año 1 → meses 10–15; la siguiente en oct. del año 2 → 22–27;
    # la cebada en dic. del año 3 → mes 36 en adelante: solo cuenta el mes 36 (§10.1).
    assert agro.place_rotation(SIERRA) == [("papa", 10, 16), ("papa", 22, 28), ("cebada", 36, 41)]


def test_place_starts_when_previous_ends_if_month_matches():
    # Algodón (7) en set. → 9–15; termina en abril del año 2 y el maíz se siembra en abril: empieza en el 16.
    costa = (("algodon", 9), ("maiz", 4), ("algodon", 9))
    assert agro.place_rotation(costa) == [("algodon", 9, 16), ("maiz", 16, 21), ("algodon", 21, 28)]


def test_place_third_crop_entirely_outside_timeline():
    rot = (("descanso", 12), ("descanso", 12), ("papa", 1))
    assert agro.place_rotation(rot) == [("descanso", 12, 24), ("descanso", 24, 36), ("papa", 37, 43)]
    ev = agro.evaluate_rotation(rot, clim(), inputs())
    assert ev["meses_desnudo"] == 1          # solo el mes 36 queda sin cultivo; la papa no entra


@pytest.mark.parametrize("rot,rep", [
    (SIERRA, 1),                                                        # papa → papa seguidas
    ((("papa", 10), ("cebada", 12), ("papa", 10)), 0.5),                # papa … papa separadas por uno
    ((("quinua", 5), ("avena", 5), ("frijol", 1)), 0),
    ((("maiz", 10), ("cebada", 3), ("avena", 10)), 2.5),               # tres gramíneas: 2 seguidas + 0.5
])
def test_family_repetition(rot, rep):
    assert agro.family_repetition(rot) == rep


# --- RC-10: datos de la rotación -----------------------------------------------------------------------------------

def test_evaluate_sierra_by_hand():
    calor = {m: 2.0 for m in range(1, 13)}
    c = clim(rain=100, et0=100, frost=1.0, dias_calor=calor)
    inp = inputs()                                         # pendiente suave (0.7), sal baja
    ev = agro.evaluate_rotation(SIERRA, c, inp)
    # Tramo analizado: meses 10–36 (27). Con cultivo: 6 + 6 de papa y 1 de cebada; desnudos: 14.
    assert ev["meses_desnudo"] == 14
    # Lluvia aprovechable de 100 mm = 56. Papa: 85 − 56 = 29 × 12; cebada: 75 − 56 = 19.
    assert ev["agua_m3ha"] == pytest.approx((29 * 12 + 19) * 10)
    # Helada: 1 día × sensibilidad (papa 0.9, cebada 0.3). Calor: 2 días × sensibilidad (0.5 y 0.5).
    assert ev["helada"] == pytest.approx(0.9 * 12 + 0.3)
    assert ev["calor"] == pytest.approx(2 * 0.5 * 12 + 2 * 0.5)
    assert ev["clima"] == pytest.approx(ev["helada"] + ev["calor"])
    # Erosión: desnudo 1 × 0.7 + 0.15; papa 1 × 0.7 × (1 − 0.6); cebada 1 × 0.7 × (1 − 0.7).
    assert ev["erosion"] == pytest.approx(14 * 0.85 + 12 * 0.7 * 0.4 + 0.7 * 0.3)
    assert ev["nitrogeno"] == -8
    assert ev["ingreso"] == 4 + 4 + 2 + 0.5                # la cebada es forrajera
    assert ev["sal"] == 0
    apts = [agro.crop_suitability(get(cid), m, c, inp)["aptitud"] for cid, m in SIERRA]
    assert ev["aptitud"] == pytest.approx(sum(apts) / 3)
    assert ev["aptitud_min"] == pytest.approx(min(apts))


def test_slope_and_salt_and_fallow():
    rot = (("descanso", 1), ("algodon", 1), ("quinua", 1))
    c = clim(rain=50)
    ev = agro.evaluate_rotation(rot, c, inputs(slope_class="ladera", salt="alta"))
    # Descanso 1–12, algodón ene. año 2 → 13–19, quinua ene. año 3 → 25–29; desnudos: 20–24 y 30–36.
    assert ev["meses_desnudo"] == 12
    assert ev["erosion"] == pytest.approx(12 * (0.5 + 0.15) + 12 * 0.5 * 0.5 + 7 * 0.5 * 0.4 + 5 * 0.5 * 0.5)
    assert ev["sal"] == pytest.approx((1 - 1.0) + (1 - 0.9) + (1 - 0.9))
    apts = [70] + [agro.crop_suitability(get(cid), 1, c, inputs(slope_class="ladera", salt="alta"))["aptitud"]
                   for cid in ("algodon", "quinua")]
    assert ev["aptitud"] == pytest.approx(sum(apts) / 3)


def test_plano_slope_factor():
    ev = agro.evaluate_rotation((("descanso", 1), ("descanso", 1), ("descanso", 1)), clim(rain=100),
                                inputs(slope_class="plano"))
    assert ev["meses_desnudo"] == 0
    assert ev["erosion"] == pytest.approx(36 * 1 * 0.3 * 0.5)


# --- RC-11: normalización dentro del grupo -------------------------------------------------------------------------

def _ev(**kw):
    base = {"aptitud": 80, "aptitud_min": 80, "agua_m3ha": 0, "clima": 0, "erosion": 0, "sal": 0,
            "nitrogeno": 0, "ingreso": 10, "repeticion": 0}
    return {**base, **kw}


GROUP = [
    _ev(aptitud=50, aptitud_min=30, agua_m3ha=0, clima=50, nitrogeno=-8, repeticion=1),
    _ev(aptitud=80, aptitud_min=60, agua_m3ha=100, clima=100, nitrogeno=0, repeticion=0),
    _ev(aptitud=90, aptitud_min=80, agua_m3ha=200, clima=100, nitrogeno=4, repeticion=0.5),
]


def test_scores_by_hand():
    s = agro.score_rotations(GROUP, inputs())
    # Agua (relativo al máximo 200): 100, 100 − 60×100/200, 100 − 60×200/200.
    assert [r["scores"]["agua"] for r in s] == pytest.approx([100, 70, 40])
    # Clima (mín 50, máx 100): 100, 100 − 60×50/100 = 70, 70.
    assert [r["scores"]["clima"] for r in s] == pytest.approx([100, 70, 70])
    # Erosión: todo 0 → máximo 0 → 100.  Ingresos: todo igual → 100.
    assert [r["scores"]["erosion"] for r in s] == [100, 100, 100]
    assert [r["scores"]["ingresos"] for r in s] == [100, 100, 100]
    # Suelo (más es mejor, rango 12): 40, 40 + 60×8/12, 100.
    assert [r["scores"]["suelo"] for r in s] == pytest.approx([40, 80, 100])
    # Plagas (menos es mejor, rango 1): 40, 100, 70.
    assert [r["scores"]["plagas"] for r in s] == pytest.approx([40, 100, 70])
    assert [r["scores"]["aptitud"] for r in s] == [50, 80, 90]
    assert "sal" not in s[0]["scores"]                       # sal «baja»: no entra
    # Pesos por defecto: aptitud 3, agua 3, suelo 3, plagas 2, clima 3, ingresos 3, erosión 2 (suma 19).
    t0 = (3 * 50 + 3 * 100 + 3 * 40 + 2 * 40 + 3 * 100 + 3 * 100 + 2 * 100) / 19 * 0.85   # aptitud mín 30 < 40
    t1 = (3 * 80 + 3 * 70 + 3 * 80 + 2 * 100 + 3 * 70 + 3 * 100 + 2 * 100) / 19
    t2 = (3 * 90 + 3 * 40 + 3 * 100 + 2 * 70 + 3 * 70 + 3 * 100 + 2 * 100) / 19
    assert [r["total"] for r in s] == pytest.approx([t0, t1, t2])


def test_salt_counts_with_weight_two_unless_low():
    group = [_ev(sal=0.2), _ev(sal=1.0)]
    s = agro.score_rotations(group, inputs(salt="media"))
    assert [r["scores"]["sal"] for r in s] == pytest.approx([100, 100 - 60 * 0.8 / 1.0])
    # Todo lo demás es igual (100 o aptitud 80): total = (3×80 + 16×100 + 2×sal) / 21.
    assert s[1]["total"] == pytest.approx((3 * 80 + 16 * 100 + 2 * 52) / 21)


def test_priorities_weight_the_total():
    pr = {k: 0 for k in agro.DEFAULT_PRIORITIES} | {"agua": 5}
    s = agro.score_rotations(GROUP, inputs(priorities=pr))
    assert [r["total"] for r in s] == pytest.approx([100 * 0.85, 70, 40])


def test_scores_depend_on_the_group():
    """RC-11: el mismo resultado puntúa distinto según con qué rotaciones se compara."""
    alone = agro.score_rotations(GROUP[1:2], inputs())[0]
    in_group = agro.score_rotations(GROUP, inputs())[1]
    assert alone["scores"]["agua"] == 100 and in_group["scores"]["agua"] == pytest.approx(70)
    assert alone["total"] != pytest.approx(in_group["total"])
