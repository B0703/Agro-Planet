"""NASA SRTM (90 m) vía OpenTopoData: altitud del punto y cuadrícula 3×3 para la pendiente (RC-06). Tarea T05.

Los 9 puntos van en una sola llamada. La cuadrícula se guarda de norte a sur y de oeste a este:

    grid[0] = [NO, N, NE]
    grid[1] = [O,  C, E ]
    grid[2] = [SO, S, SE]

El cálculo de la pendiente (RC-06) está en el motor (T08), no aquí. Un punto sin dato (mar) queda como None.
"""
from __future__ import annotations

import threading
import time

from .. import cache
from ..cache import SourceError
from . import http

URL = "https://api.opentopodata.org/v1/srtm90m"
STEP = 0.001  # grados entre puntos de la cuadrícula (RC-06)
MIN_INTERVAL = 1.0  # OpenTopoData pública: como máximo 1 llamada por segundo

_throttle = threading.Lock()
_last_call = 0.0


def _wait_turn() -> None:
    global _last_call
    with _throttle:
        delay = MIN_INTERVAL - (time.monotonic() - _last_call)
        if delay > 0:
            time.sleep(delay)
        _last_call = time.monotonic()


def grid_points(lat: float, lon: float) -> list[list[tuple[float, float]]]:
    return [[(round(lat + dy * STEP, 6), round(lon + dx * STEP, 6)) for dx in (-1, 0, 1)] for dy in (1, 0, -1)]


def terrain(lat: float, lon: float) -> dict:
    """{'elev': altitud del punto en m o None, 'grid': 3×3 altitudes (ver arriba)}."""
    lat, lon = round(lat, 4), round(lon, 4)
    points = [p for row in grid_points(lat, lon) for p in row]

    def fetch():
        _wait_turn()
        raw = http.get_json("srtm", URL, {"locations": "|".join(f"{a},{b}" for a, b in points)}, timeout=30)
        try:
            if raw.get("status") != "OK":
                raise ValueError(raw.get("error") or raw.get("status"))
            elevs = [r["elevation"] for r in raw["results"]]
            if len(elevs) != 9:
                raise ValueError(f"{len(elevs)} resultados")
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            raise SourceError("srtm", "respuesta inesperada", cause=e) from e
        elevs = [None if e is None else float(e) for e in elevs]
        return {"elev": elevs[4], "grid": [elevs[0:3], elevs[3:6], elevs[6:9]]}

    return cache.get_or_fetch("srtm", {"lat": lat, "lon": lon}, fetch)


def elevation(lat: float, lon: float) -> float | None:
    """Altitud real del punto (RC-02, RC-06)."""
    return terrain(lat, lon)["elev"]
