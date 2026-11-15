"""Búsqueda de lugares y nombre de un punto con Nominatim (OpenStreetMap). RC-20, RF-15, RF-16. Tarea T14.

- Se pide siempre en español (`accept-language=es`): los nombres no se traducen (Spec §10.4).
- Como máximo una llamada por segundo (política de uso de Nominatim), con el User-Agent genérico de http.py.
- Toda respuesta se guarda en la caché (RNF-02); un fallo sale como SourceError("geocode").
"""
from __future__ import annotations

import threading
import time

from .. import cache
from ..cache import SourceError
from ..place import parse_coords, round_point
from . import http

SERVICE = "geocode"
BASE = "https://nominatim.openstreetmap.org"
LANG = "es"
LIMIT = 8                   # resultados que se piden (RC-20)
MAX_SHOWN = 5               # resultados que se muestran (RF-15)
MIN_INTERVAL = 1.0          # s entre llamadas
TIMEOUT = 20

# RC-20: prioridad de orden según el tipo de lugar (`addresstype` de Nominatim). Lo que no aparece va al final.
_RANK = {
    # pueblos, caseríos y calles
    **dict.fromkeys(("village", "town", "hamlet", "isolated_dwelling", "locality", "road"), 0),
    # ciudades y barrios
    **dict.fromkeys(("city", "suburb", "neighbourhood", "quarter", "city_block"), 1),
    # distritos, provincias, regiones y departamentos
    **dict.fromkeys(("district", "city_district", "municipality", "county", "province", "region", "state"), 2),
}
_OTHER = 3

# RC-20, nombre de un punto: pueblo, ciudad menor, ciudad, distrito, provincia y departamento. En el Perú OSM pone la
# provincia en `county` (Tarma) o en `region` (Huamanga); el departamento va en `state`.
POINT_FIELDS = ("village", "town", "city", "district", "county", "region", "state")

_throttle = threading.Lock()
_last_call = 0.0


def _wait_turn() -> None:
    global _last_call
    with _throttle:
        delay = MIN_INTERVAL - (time.monotonic() - _last_call)
        if delay > 0:
            time.sleep(delay)
        _last_call = time.monotonic()


def _get(path: str, params: dict):
    _wait_turn()
    return http.get_json(SERVICE, f"{BASE}/{path}", {**params, "format": "jsonv2", "accept-language": LANG},
                         timeout=TIMEOUT)


def _short_name(display_name: str) -> str:
    """Las dos primeras partes del nombre encontrado (RF-16)."""
    return ", ".join(p.strip() for p in display_name.split(",")[:2])


def _raw_search(query: str, peru_only: bool) -> list[dict]:
    params = {"q": query, "limit": LIMIT, "addressdetails": 0}
    if peru_only:
        params["countrycodes"] = "pe"

    def fetch():
        raw = _get("search", params)
        if not isinstance(raw, list):
            raise SourceError(SERVICE, "respuesta inesperada")
        try:
            return [{"name": _short_name(x["display_name"]), "lat": float(x["lat"]), "lon": float(x["lon"]),
                     "type": x.get("addresstype") or x.get("type") or ""} for x in raw]
        except (KeyError, TypeError, ValueError) as e:
            raise SourceError(SERVICE, "respuesta inesperada", cause=e) from e

    return cache.get_or_fetch(SERVICE, {"op": "search", "q": query, "pe": peru_only}, fetch)


def search(text: str) -> list[dict]:
    """RC-20: lugares para el texto del buscador, como [{'name', 'lat', 'lon'}] (máximo 5, ya redondeados).

    Coordenadas válidas se devuelven directamente, sin consultar el servicio (nombre None: lo pone point_name).
    Si no, se busca en el Perú y, sin resultados, en todo el mundo; se ordena por tipo de lugar (orden estable) y se
    quitan los nombres repetidos. Lista vacía: no se encontró nada. Puede lanzar SourceError.
    """
    coords = parse_coords(text)
    if coords is not None:
        return [{"name": None, "lat": coords[0], "lon": coords[1]}]
    query = " ".join(text.split())
    if not query:
        return []
    results = _raw_search(query, peru_only=True) or _raw_search(query, peru_only=False)
    out, seen = [], set()
    for r in sorted(results, key=lambda r: _RANK.get(r["type"], _OTHER)):
        if r["name"] in seen:
            continue
        seen.add(r["name"])
        lat, lon = round_point(r["lat"], r["lon"])
        out.append({"name": r["name"], "lat": lat, "lon": lon})
    return out[:MAX_SHOWN]


def point_name(lat: float, lon: float) -> str | None:
    """RC-20: «pueblo, región» de un punto (clic, coordenadas, GPS): los dos primeros nombres distintos entre pueblo,
    ciudad menor, ciudad, distrito, provincia y departamento. None si no hay ninguno. Puede lanzar SourceError."""
    lat, lon = round_point(lat, lon)

    def fetch():
        raw = _get("reverse", {"lat": lat, "lon": lon, "addressdetails": 1, "zoom": 18})
        if not isinstance(raw, dict):
            raise SourceError(SERVICE, "respuesta inesperada")
        return {"address": raw.get("address") or {}}       # sin dirección (mar): se guarda vacía

    address = cache.get_or_fetch(SERVICE, {"op": "reverse", "lat": lat, "lon": lon}, fetch)["address"]
    names = []
    for field in POINT_FIELDS:
        value = address.get(field)
        if value and value not in names:
            names.append(value)
        if len(names) == 2:
            break
    return ", ".join(names) if names else None
