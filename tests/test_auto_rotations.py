"""T11: rotaciones automáticas A y B (RC-12), con tablas y climas sintéticos. Sin red."""
import pandas as pd
import pytest

from rotasat import agro
from rotasat.crops import get
from tests.test_suitability import clim, inputs


def table(*rows):
    """Tabla RC-09 mínima, ya ordenada: (id, aptitud redondeada, mejor mes)."""
    return pd.DataFrame([{"id": i, "aptitud": a, "mes": m} for i, a, m in rows])


# --- RC-12.1 Candidatos --------------------------------------------------------------------------------------------

def test_candidates_threshold_and_max_eight():
    rows = [(c, 90 - i, 1) for i, c in enumerate(
        ["quinua", "cebada", "haba", "papa", "avena", "olluco", "tarwi", "frijol", "maiz", "sorgo"])]
    assert agro.candidates(table(*rows)) == ["quinua", "cebada", "haba", "papa", "avena", "olluco", "tarwi", "frijol"]
    t = table(("quinua", 80, 1), ("cebada", 46, 1), ("haba", 45, 1), ("papa", 44, 1))
    assert agro.candidates(t) == ["quinua", "cebada", "haba"]               # ≥ 45 entra, 44 no


def test_candidates_fall_back_to_first_three():
    t = table(("quinua", 60, 1), ("cebada", 30, 1), ("haba", 20, 1), ("papa", 10, 1))
    assert agro.candidates(t) == ["quinua", "cebada", "haba"]


# --- RC-12.2–3 Secuencias -------------------------------------------------------------------------------------------

def test_sequences_use_best_month_and_drop_consecutive_family():
    months = {"quinua": 5, "cebada": 6, "avena": 7}                        # amarantácea, gramínea, gramínea
    seqs = agro.candidate_sequences(["quinua", "cebada", "avena"], months)
    # Las 6 permutaciones menos las que ponen cebada y avena seguidas: solo quedan las que tienen la quinua al medio.
    assert seqs == [(("cebada", 6), ("quinua", 5), ("avena", 7)), (("avena", 7), ("quinua", 5), ("cebada", 6))]


def test_sequences_require_a_legume_when_there_is_one():
    months = {c: 1 for c in ("quinua", "papa", "cebada", "haba")}
    seqs = agro.candidate_sequences(["quinua", "papa", "cebada", "haba"], months)
    assert seqs and all(any(get(c).is_legume for c, _ in s) for s in seqs)
    assert len(agro.candidate_sequences(["quinua", "papa", "cebada"], months)) == 6   # sin leguminosas no se exige


def test_main_crop():
    assert agro.main_crop((("papa", 10), ("papa", 10), ("cebada", 12))) == "papa"
    assert agro.main_crop((("algodon", 9), ("maiz", 4), ("algodon", 9))) == "algodon"
    assert agro.main_crop((("quinua", 5), ("cebada", 6), ("haba", 7))) == "quinua"   # empate: el primero


# --- RC-12.4–8 Elección de A y B -------------------------------------------------------------------------------------

def _setup(rows, frost=0.0, **inp):
    c = clim(t=15, rain=100, et0=100, frost=frost)
    i = inputs(**inp)
    return table(*rows), c, i


def test_a_is_best_and_scores_are_recomputed_among_the_three():
    t, c, inp = _setup([("quinua", 90, 5), ("haba", 85, 6), ("cebada", 80, 7), ("olluco", 70, 8)])
    res = agro.auto_rotations(t, c, inp)
    assert [r.label for r in res] == ["Actual", "A", "B"]
    assert res[0].rotation == inp.rotation
    # A es la de mayor total entre todas las secuencias puntuadas junto con la actual.
    seqs = agro.candidate_sequences(agro.candidates(t), dict(zip(t["id"], t["mes"])))
    big = agro.score_rotations([agro.evaluate_rotation(r, c, inp) for r in [inp.rotation, *seqs]], inp)
    best = max(range(len(seqs)), key=lambda k: big[k + 1]["total"])
    assert res[1].rotation == seqs[best]
    # RC-12.8: lo que se muestra es el puntaje entre Actual, A y B solamente.
    shown = agro.score_rotations([r.evaluation for r in res], inp)
    assert [r.total for r in res] == pytest.approx([s["total"] for s in shown])


def test_b_contains_main_crop_when_candidate_and_missing_from_a():
    # Rotación actual de la sierra: papa → papa → cebada. Con 3 días de helada al mes la papa (sensibilidad 0.9) es
    # candidata pero la menos apta, y no entra en A.
    t, c, inp = _setup([("quinua", 95, 5), ("haba", 94, 6), ("avena", 93, 7), ("papa", 46, 10)], frost=3.0)
    a, b = agro.auto_rotations(t, c, inp)[1:]
    assert "papa" not in {x for x, _ in a.rotation}
    assert "papa" in {x for x, _ in b.rotation}


def test_b_otherwise_uses_a_different_set_of_crops():
    # Cultivo principal (papa) fuera de los candidatos: B es la siguiente con otros 3 cultivos.
    t, c, inp = _setup([("quinua", 95, 5), ("haba", 94, 6), ("avena", 93, 7), ("olluco", 90, 8)])
    a, b = agro.auto_rotations(t, c, inp)[1:]
    assert {x for x, _ in a.rotation} != {x for x, _ in b.rotation}


def test_rotation_names_es_en():
    t, c, inp = _setup([("quinua", 95, 5), ("haba", 94, 6), ("avena", 93, 7)])
    res = agro.auto_rotations(t, c, inp)
    assert agro.rotation_name(res[0], "es") == "Actual: Papa → Papa → Cebada"
    assert agro.rotation_name(res[0], "en") == "Current: Potato → Potato → Barley"
    assert agro.rotation_name(res[1], "es").startswith("A: ")
