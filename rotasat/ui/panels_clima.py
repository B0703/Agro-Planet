"""Paneles de la vista Clima (§5.5, RF-51 a RF-57). T15: la barra. T20: el contenido de cada panel, con las secciones
de `climate_sections` que también usa el panel Clima del terreno (RF-30). El río (RF-56, RC-18) solo aparece en la
cuenca de Ica: `panels_for()` lo quita de la barra fuera de ella.
"""
from __future__ import annotations

import streamlit as st

from . import climate_sections as cs
from . import location
from .common import Panel

SLOT = "clima_place"
RIVER = "rio"


def _context():
    """(lugar, clima, región) del lugar del Clima. Si no hay lugar o fallaron los datos, el panel queda vacío."""
    p = location.get_place(SLOT)
    pc = location.load_climate(SLOT) if p is not None else None
    if pc is None:
        st.stop()
    return p, pc, location.region_of(SLOT, pc)


def calendario_body() -> None:
    p, pc, _ = _context()
    cs.calendar(pc, p["lat"], p["lon"])


def lluvia_body() -> None:
    p, pc, _ = _context()
    cs.rain(pc, p["lat"], p["lon"])


def temperatura_body() -> None:
    _, pc, _ = _context()
    cs.temperature(pc)


def humedad_body() -> None:
    p, _, region = _context()
    cs.moisture(p["lat"], p["lon"], region)


def tendencia_body() -> None:
    _, pc, region = _context()
    cs.trend(pc, region)


def rio_body() -> None:
    _context()
    cs.river()


def datos_body() -> None:
    _, pc, _ = _context()
    cs.about(pc)


# §5.5: en este orden. Etiqueta y ayuda: Anexo C [654]–[668]; títulos: [625]–[641], [654], [667].
PANELS: list[Panel] = [
    Panel("calendario", "📅", "Calendario", "📅 Calendario de riesgos", "Riesgos de cada mes: heladas, calor, lluvia",
          calendario_body),
    Panel("lluvia", "🌧️", "Lluvia", "🌧️ Lluvia y evaporación", "Cuánto llueve cada mes y cuánta agua se evapora",
          lluvia_body),
    Panel("temperatura", "🌡️", "Temperatura", "🌡️ Temperatura y heladas", "Temperaturas de cada mes y heladas",
          temperatura_body),
    Panel("humedad", "🟫", "Humedad del suelo", "🟫 Humedad del suelo", "Cuándo está seco o húmedo el suelo",
          humedad_body),
    Panel("tendencia", "📈", "Tendencia", "📈 ¿Está cambiando el clima aquí?", "Cómo ha cambiado el clima en 20 años",
          tendencia_body),
    Panel(RIVER, "💧", "Río", "💧 ¿Traerá agua el río?", "Lluvia en la cuenca alta que alimenta el río Ica", rio_body),
    Panel("datos", "🔬", "Sobre los datos", "🔬 Cómo se ajustaron los datos a este lugar", "De dónde salen los datos",
          datos_body),
]


def panels_for(region: str, lat: float, lon: float) -> list[Panel]:
    """La barra del lugar: los 7 paneles en la cuenca de Ica; fuera de ella, sin el río (RC-18)."""
    if cs.show_river(region, lat, lon):
        return PANELS
    return [p for p in PANELS if p.key != RIVER]
