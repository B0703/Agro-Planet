"""Un lugar: coordenadas escritas (RF-13), redondeo (RF-14) y nombre que se muestra (RF-16). Tarea T14.

Módulo puro: no usa la red ni Streamlit. Los nombres de los lugares vienen de sources/geocode.py y no se traducen
(Spec §10.4); solo el texto que los rodea pasa por i18n.
"""
from __future__ import annotations

import re

from .i18n import t

DECIMALS = 4                                         # RF-14
_NUMBER = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)$")  # decimales con punto
_SEPARATORS = re.compile(r"[,;\s]+")

# Cómo se eligió el lugar (RF-16).
GPS, CLICK, COORDS, SEARCH = "gps", "click", "coords", "search"


def round_point(lat: float, lon: float) -> tuple[float, float]:
    """RF-14: toda ubicación se redondea a 4 decimales."""
    return round(float(lat), DECIMALS), round(float(lon), DECIMALS)


def parse_coords(text: str) -> tuple[float, float] | None:
    """RF-13.3: «latitud, longitud» en decimales con punto; separador coma, punto y coma o espacio.
    Devuelve el punto ya redondeado (RF-14), o None si el texto no son coordenadas válidas."""
    parts = [p for p in _SEPARATORS.split(text.strip()) if p]
    if len(parts) != 2 or not all(_NUMBER.match(p) for p in parts):
        return None
    lat, lon = float(parts[0]), float(parts[1])
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return round_point(lat, lon)


def label(kind: str, name: str | None, lat: float, lon: float, lang: str) -> str:
    """RF-16: el nombre del lugar según cómo se eligió. Se vuelve a llamar al cambiar de idioma.

    `name` es «pueblo, región» (geocode.point_name) o, en una búsqueda, el nombre del resultado; None si no se conoce.
    """
    if kind == GPS:
        return f"{t('Mi ubicación actual', lang)} ({name})" if name else t("Mi ubicación actual", lang)
    if kind == CLICK:
        return t("Terreno en {n}", lang, n=name) if name else t("Terreno marcado en el mapa", lang)
    if kind == COORDS:
        return name or f"{t('Coordenadas', lang)} {lat:.4f}, {lon:.4f}"
    if kind == SEARCH:
        return name or f"{lat:.4f}, {lon:.4f}"
    raise ValueError(f"forma desconocida: {kind!r}")
