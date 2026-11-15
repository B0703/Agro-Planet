"""T02: crops.py reproduce el Anexo A del Spec.

Compara cada valor con las tablas del Anexo A, leídas directamente de specs/Spec.md, para que
ningún error de transcripción pase desapercibido.
"""
from pathlib import Path

import pytest

from rotasat import crops
from rotasat.crops import CROPS, FIELD_CROPS, TEXTURES

SPEC = Path(__file__).resolve().parent.parent / "specs" / "Spec.md"


def _annex_a_rows(header_start: str) -> list[list[str]]:
    """Filas de la tabla del Anexo A cuyo encabezado empieza con `header_start`."""
    text = SPEC.read_text(encoding="utf-8")
    annex = text[text.index("## Anexo A."):text.index("## Anexo B.")]
    lines = annex.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(header_start))
    rows = []
    for ln in lines[start + 2:]:
        if not ln.startswith("|"):
            break
        rows.append([cell.strip() for cell in ln.strip("|").split("|")])
    return rows


def _range(s: str) -> tuple[float, float]:
    # "21–30", "-50–50", "-60–60", "5.8–8.0", "0–14"
    lo, hi = s.split("–")
    return float(lo), float(hi)


PARAM_ROWS = _annex_a_rows("| id | Nombre (ES)")
NOTE_ROWS = _annex_a_rows("| id | Nota (ES)")


def test_counts_and_order():
    assert len(CROPS) == 18
    assert len(FIELD_CROPS) == 17
    assert crops.FALLOW_ID not in {c.id for c in FIELD_CROPS}
    assert [c.id for c in CROPS] == [r[0].strip("`") for r in PARAM_ROWS]


@pytest.mark.parametrize("row", PARAM_ROWS, ids=lambda r: r[0].strip("`"))
def test_parameters_match_annex_a(row):
    (cid, name_es, name_en, family, months, kc, t_opt, t_lim, frost, heat, salt, n, cover, market, forage,
     textures, ph) = row
    c = crops.get(cid.strip("`"))
    assert c.name_es == name_es
    assert c.name_en == name_en
    assert c.family == family
    assert c.months == int(months)
    assert c.kc == float(kc)
    assert c.t_opt == _range(t_opt)
    assert c.t_lim == _range(t_lim)
    assert c.frost_sens == float(frost)
    assert c.heat_sens == float(heat)
    assert c.salt_tol == float(salt)
    assert c.n == int(n)
    assert c.cover == float(cover)
    assert c.market == int(market)
    assert c.forage == {"sí": True, "no": False}[forage]
    expected_tex = () if textures == "(cualquiera)" else tuple(t.strip() for t in textures.split(","))
    assert c.textures == expected_tex
    assert c.ph == _range(ph)


@pytest.mark.parametrize("row", NOTE_ROWS, ids=lambda r: r[0].strip("`"))
def test_notes_match_annex_a(row):
    cid, note_es, note_en = row
    c = crops.get(cid.strip("`"))
    assert c.note("es") == note_es
    assert c.note("en") == note_en


def test_textures_valid_and_legumes():
    for c in CROPS:
        assert set(c.textures) <= set(TEXTURES)
    # Glosario del Spec: las leguminosas son haba, tarwi, frijol, pallar y maní.
    assert {c.id for c in CROPS if c.is_legume} == {"haba", "tarwi", "frijol", "pallar", "mani"}


def test_name_by_language():
    assert crops.get("quinua").name("es") == "Quinua"
    assert crops.get("quinua").name("en") == "Quinoa"
