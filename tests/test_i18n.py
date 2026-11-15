"""T03: catálogo de textos del Anexo C."""
import re
import string
import subprocess
import sys
from pathlib import Path

import pytest

from rotasat import i18n, texts_data
from rotasat.i18n import month, other_lang, t, vocab

ROOT = Path(__file__).resolve().parent.parent
ANNEX = (ROOT / "specs" / "Spec-anexo-C-textos.md").read_text(encoding="utf-8")

# Entradas cuyo texto EN es fijo y no usa el dato de ES (así está en el Anexo C).
EN_FIXED = {
    "El agua del río Ica nace como lluvia en la {cuenca}. Si allá llueve poco, el río trae poco y se depende más "
    "de los pozos de un acuífero ya sobreexplotado.",
    "{error}. Indique su suelo a mano arriba.",
}


def _fields(s: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


def test_generated_file_is_up_to_date():
    r = subprocess.run([sys.executable, "scripts/build_texts.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_annex_entry_is_in_catalog():
    entries = re.findall(r"^\[\d+\]\nES\| ?(.*)\nEN\| ?(.*)$", ANNEX, re.M)
    assert len(entries) == 280
    plain = [(es, en) for es, en in entries if "{" not in es]
    for es, en in plain:
        assert t(es.replace("\\n", "\n"), "es") == es.replace("\\n", "\n")
        assert t(es.replace("\\n", "\n"), "en") == en.replace("\\n", "\n")


@pytest.mark.parametrize("es", sorted({**texts_data.UI, **texts_data.ENGINE}))
def test_both_languages_use_same_fields(es):
    en = {**texts_data.UI, **texts_data.ENGINE}[es]
    assert en.strip(), "falta la traducción EN"
    if es not in EN_FIXED:
        assert _fields(es) == _fields(en)


def test_lookup_and_formatting():
    assert t("Buscar", "es") == "Buscar"
    assert t("Buscar", "en") == "Search"
    assert t(" · {elev:,.0f} m de altitud", "es", elev=3272) == " · 3,272 m de altitud"
    assert t(" · {elev:,.0f} m de altitud", "en", elev=405) == " · 405 m altitude"
    assert t("{delta:+.0f}% frente al promedio", "en", delta=-12.4) == "-12% vs. average"
    assert t("Campaña {n}", "en", n=2) == "Season 2"


def test_unknown_text_and_language_rejected():
    with pytest.raises(KeyError):
        t("Texto inventado", "es")
    with pytest.raises(ValueError):
        t("Buscar", "fr")


def test_language_button():
    # RF-60: el botón muestra el nombre del otro idioma.
    assert other_lang("es") == "en" and other_lang("en") == "es"
    assert t("English", "es") == "English"
    assert t("English", "en") == "Español"


def test_months():
    # RF-64: minúscula en ES, mayúscula en EN.
    assert month(5, "es") == "mayo" and month(5, "en") == "May"
    assert month(9, "es") == "setiembre"
    assert month(12, "es", abbr=True) == "Dic" and month(12, "en", abbr=True) == "Dec"
    assert [month(m, "en") for m in range(1, 13)][0] == "January"


def test_vocabulary():
    assert vocab("region", "costa", "es") == "🏜️ Costa desértica"
    assert vocab("region", "altoandina", "en") == "🏔️ High Andes / altiplano"
    assert vocab("riego", "limitada", "en") == "Yes, but water is limited"
    assert vocab("sal", "media", "es") == "Un poco"
    assert vocab("textura", "franco-arcilloso", "en") == "clay loam"
    assert vocab("pendiente", "ladera", "en") == "steep"
    assert vocab("columna", "Riego necesario (m³/ha)", "en") == "Irrigation needed (m³/ha)"
    assert vocab("criterio", "sal", "es") == "🧂 Salinidad"
    assert i18n.options("textura") == ["arenoso", "franco-arenoso", "franco", "franco-arcilloso", "arcilloso"]
    assert i18n.options("riego") == ["no", "limitada", "suficiente"]
    assert i18n.PH_VALUES == {"nose": None, "acido": 5.0, "lig": 6.0, "neutro": 7.0, "alcalino": 8.0}


def test_gps_error_message():
    # CA-07: el aviso termina en «Escriba su ubicación.»
    assert i18n.gps_error("denegado", "es") == "No se dio permiso para usar la ubicación. Escriba su ubicación."
    assert i18n.gps_error("tiempo", "en") == "Getting the location took too long. Please type your location."


def test_regions_match_crop_vocab_keys():
    from rotasat.crops import TEXTURES
    assert tuple(i18n.options("textura")) == TEXTURES
    assert set(i18n.options("region")) == {"costa", "sierra", "altoandina", "selva"}
