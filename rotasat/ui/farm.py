"""Lo que necesitan los paneles del terreno para un lugar: clima, datos detectados, respuestas del usuario («Mis datos»),
tabla de aptitud (RC-09) y rotaciones (RC-12). Tarea T17.

Las respuestas del usuario se guardan por lugar en `st.session_state.overrides[(lat, lon)]`, solo con lo que cambió
(RC-07, RF-35), y duran lo que dure la sesión (RNF-10). Tabla y rotaciones se guardan en la sesión y se recalculan solo
si cambian las respuestas o la lluvia del lugar.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from .. import agro, climate
from ..crops import get
from ..i18n import t, vocab
from . import location


@dataclass(frozen=True)
class Farm:
    place: dict
    key: tuple[float, float]
    pc: climate.PlaceClimate
    detected: agro.Detected
    inputs: agro.FarmInputs
    table: pd.DataFrame
    rotations: list            # [Actual, A, B] (RotationResult); puede tener menos si no hay alternativas


def place_key(slot: str) -> tuple[float, float] | None:
    p = location.get_place(slot)
    return (p["lat"], p["lon"]) if p else None


def overrides(key: tuple[float, float]) -> dict:
    return st.session_state.setdefault("overrides", {}).setdefault(key, {})


def set_override(key: tuple[float, float], field: str, value) -> None:
    overrides(key)[field] = value


def reset_overrides(key: tuple[float, float]) -> None:
    st.session_state.setdefault("overrides", {})[key] = {}


def get_farm(slot: str) -> Farm | None:
    """Datos del lugar de `slot`, o None si no hay lugar o fallaron los datos principales (el error ya se mostró)."""
    p = location.get_place(slot)
    if p is None:
        return None
    pc = location.load_climate(slot)
    if pc is None:
        return None
    key = (p["lat"], p["lon"])
    ov = overrides(key)
    detected = climate.detect(pc, p["lat"])
    inputs = agro.resolve_inputs(detected, ov, st.session_state.get("soil_estimates", {}).get(key))
    cache = st.session_state.setdefault("farm_cache", {})
    ck = (key, repr(sorted(ov.items())), repr(inputs), pc.rain_source, pc.rain_status)
    if ck not in cache:
        table = agro.suitability_table(pc.clim, inputs)
        cache.clear()                                   # solo se guarda el último cálculo
        cache[ck] = (table, agro.auto_rotations(table, pc.clim, inputs))
    table, rotations = cache[ck]
    return Farm(p, key, pc, detected, inputs, table, rotations)


# --- Textos que dependen del idioma ------------------------------------------------------------------------------

def crop_name(crop_id: str, lang: str) -> str:
    return get(crop_id).name(lang)


def limiting_text(limiting: tuple[str, dict], lang: str) -> str:
    """Factor limitante (RC-09) en `lang`; las texturas preferidas se traducen y se unen con «, »."""
    key, fields = limiting
    if "texturas" in fields:
        fields = {**fields, "texturas": ", ".join(vocab("textura", x, lang) for x in fields["texturas"])}
    return t(key, lang, **fields)


LEVEL_COLORS = {agro.LEVELS[0]: "#2E7D32", agro.LEVELS[1]: "#F9A825", agro.LEVELS[2]: "#C62828"}


def level_color(aptitude: float) -> str:
    """RF-31: verde ≥ 65, ámbar ≥ 40, rojo < 40 (con la aptitud redondeada, como los niveles)."""
    return LEVEL_COLORS[agro.level(round(aptitude))]
