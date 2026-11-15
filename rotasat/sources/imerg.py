"""Lluvia diaria GPM IMERG 2015–2024 (vía NASA SERVIR) para la costa (RC-04). Tarea T07.

Comportamiento conocido que se conserva (Spec §10.2): la página **solo lee** IMERG de la caché; nunca inicia una
descarga para un lugar nuevo. Solo scripts/prefetch.py llama a `download()`.
"""
from __future__ import annotations

from datetime import date

from .. import cache
from . import climateserv

SERVICE = "imerg"
DATATYPE = 26
START, END = date(2015, 1, 1), date(2024, 12, 31)
YEARS = 10
MAX_SECONDS = 600


def _params(lat: float, lon: float) -> dict:
    return {"lat": round(lat, 4), "lon": round(lon, 4), "start": START.isoformat(), "end": END.isoformat(),
            "half": climateserv.HALF_IMERG}


def cached(lat: float, lon: float) -> dict | None:
    """Serie guardada {'dates', 'rain'} o None. Nunca consulta la red."""
    return cache.load(SERVICE, _params(lat, lon))


def download(lat: float, lon: float) -> dict:
    """Solo para scripts/prefetch.py."""
    lat, lon = round(lat, 4), round(lon, 4)
    return cache.get_or_fetch(SERVICE, _params(lat, lon), lambda: climateserv.fetch_daily(
        SERVICE, DATATYPE, lat, lon, START, END, half=climateserv.HALF_IMERG, max_seconds=MAX_SECONDS))
