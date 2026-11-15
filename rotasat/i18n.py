"""Textos ES/EN (RF-60 a RF-64, Anexo C). Tarea T03.

Los textos se piden con el texto exacto en español como clave:

    t("Buscar", "en")                                      → "Search"
    t("Llueven **{total:,.0f} mm al año**, ...", lang, total=792, top=...)

Una clave que no esté en el Anexo C lanza KeyError: así ningún texto suelto se cuela en la interfaz.
Los nombres de los campos `{...}` están en scripts/build_texts.py (PLACEHOLDERS).
El catálogo vive en texts_data.py, que se genera con `python scripts/build_texts.py`.

Módulo puro: el idioma se pasa siempre como argumento (la interfaz lo toma de st.session_state.lang).
"""
from __future__ import annotations

from . import texts_data

LANGS = ("es", "en")
DEFAULT_LANG = "es"

_STRINGS: dict[str, str] = {**texts_data.UI, **texts_data.ENGINE}


def _check(lang: str) -> None:
    if lang not in LANGS:
        raise ValueError(f"idioma desconocido: {lang!r}")


def t(es: str, lang: str, /, **values) -> str:
    """Texto en `lang` para la clave en español `es`, con `values` puestos en sus campos."""
    _check(lang)
    if es not in _STRINGS:
        raise KeyError(f"texto fuera del Anexo C: {es!r}")
    template = es if lang == "es" else _STRINGS[es]
    return template.format(**values) if values else template


def other_lang(lang: str) -> str:
    """El idioma al que lleva el botón 🌐 (RF-60)."""
    _check(lang)
    return "en" if lang == "es" else "es"


# --- Vocabulario (C.3 y C.4) ------------------------------------------------------------------------------------

def _pairs(group: str, key_col: int, es_col: int, en_col: int) -> dict[str, tuple[str, str]]:
    return {row[key_col]: (row[es_col], row[en_col]) for row in texts_data.TABLES[group]}


# grupo → {clave interna: (es, en)}. En las tablas sin clave (columnas, texturas, pendiente) la clave es el texto ES.
VOCAB: dict[str, dict[str, tuple[str, str]]] = {
    "riego": _pairs("riego", 0, 1, 2),
    "sal": _pairs("sal", 0, 1, 2),
    "gps_error": _pairs("gps_error", 0, 1, 2),
    "columna": _pairs("columna", 1, 1, 2),
    "ph": _pairs("ph", 0, 2, 3),
    "region": _pairs("region", 0, 1, 2),
    "criterio": _pairs("criterio", 0, 1, 2),
    "textura": _pairs("textura", 0, 0, 1),
    "pendiente": _pairs("pendiente", 0, 0, 1),
}

# Valor de pH usado en el cálculo para cada opción del formulario (C.3); «No sé» es None.
PH_VALUES: dict[str, float | None] = {
    row[0]: (None if row[1] == "None" else float(row[1])) for row in texts_data.TABLES["ph"]
}

_MONTHS = {int(row[0]): row[1:] for row in texts_data.TABLES["mes"]}  # n → (es, en, abrev_es, abrev_en)


def vocab(group: str, key: str, lang: str) -> str:
    """Texto de una opción o término del dominio: vocab('region', 'costa', 'en') → '🏜️ Desert coast'."""
    _check(lang)
    es, en = VOCAB[group][key]
    return en if lang == "en" else es


def options(group: str) -> list[str]:
    """Claves de un grupo en el orden del Anexo C (para selectores)."""
    return list(VOCAB[group])


def month(n: int, lang: str, abbr: bool = False) -> str:
    """Mes calendario (1 = enero). En frases: minúscula en ES, mayúscula en EN (RF-64)."""
    _check(lang)
    es, en, abbr_es, abbr_en = _MONTHS[n]
    if abbr:
        return abbr_en if lang == "en" else abbr_es
    return en if lang == "en" else es


def gps_error(key: str, lang: str) -> str:
    """Motivo del fallo de GPS más « Escriba su ubicación.» (C.3, RF-42, CA-07)."""
    return t("{motivo} Escriba su ubicación.", lang, motivo=vocab("gps_error", key, lang))
