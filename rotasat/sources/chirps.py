"""Lluvia diaria CHIRPS 2005–2024 (vía NASA SERVIR) con descarga en segundo plano (RC-04, RC-05). Tarea T07.

Un lugar nuevo tarda de 1 a 5 minutos. `ensure_background()` lanza la descarga en un hilo (máximo 300 s) y vuelve
de inmediato; la interfaz consulta `status()` cada 6 s (RF-21). Al terminar, los datos quedan en la caché.
"""
from __future__ import annotations

import threading
from datetime import date

from .. import cache
from ..cache import SourceError
from . import climateserv

SERVICE = "chirps"
DATATYPE = 0
START, END = date(2005, 1, 1), date(2024, 12, 31)
YEARS = 20
MAX_SECONDS = 300  # RC-05

# Estados de la descarga de un lugar.
READY = "ready"        # en la caché
RUNNING = "running"    # descargando en segundo plano → resultados preliminares
FAILED = "failed"      # la última descarga falló → aviso y botón de reintentar (RF-22)
MISSING = "missing"    # no se ha pedido


def _params(lat: float, lon: float) -> dict:
    return {"lat": round(lat, 4), "lon": round(lon, 4), "start": START.isoformat(), "end": END.isoformat(),
            "half": climateserv.HALF_CHIRPS}


def cached(lat: float, lon: float) -> dict | None:
    """Serie guardada {'dates', 'rain'} o None. Nunca consulta la red."""
    return cache.load(SERVICE, _params(lat, lon))


def download(lat: float, lon: float) -> dict:
    """Descarga bloqueante (para scripts/prefetch.py y el hilo de fondo)."""
    lat, lon = round(lat, 4), round(lon, 4)
    return cache.get_or_fetch(SERVICE, _params(lat, lon), lambda: climateserv.fetch_daily(
        SERVICE, DATATYPE, lat, lon, START, END, half=climateserv.HALF_CHIRPS, max_seconds=MAX_SECONDS))


# --- Descarga en segundo plano (RC-05) ---------------------------------------------------------------------------

_jobs: dict[tuple[float, float], threading.Thread] = {}
_errors: dict[tuple[float, float], SourceError] = {}
_guard = threading.Lock()


def _key(lat: float, lon: float) -> tuple[float, float]:
    return round(lat, 4), round(lon, 4)


def _run(key: tuple[float, float]) -> None:
    try:
        download(*key)
    except SourceError as e:
        with _guard:
            _errors[key] = e
    except Exception as e:  # noqa: BLE001 - el hilo nunca debe morir en silencio
        with _guard:
            _errors[key] = SourceError(SERVICE, cause=e)


def ensure_background(lat: float, lon: float) -> str:
    """Si la lluvia no está guardada ni descargándose, lanza la descarga. Devuelve el estado resultante.
    Un lugar cuya descarga falló no se reintenta solo: hay que llamar a `retry()` (botón de RF-22)."""
    key = _key(lat, lon)
    if cached(*key) is not None:
        return READY
    with _guard:
        job = _jobs.get(key)
        if job is not None and job.is_alive():
            return RUNNING
        if key in _errors:
            return FAILED
        job = threading.Thread(target=_run, args=(key,), name=f"chirps-{key[0]},{key[1]}", daemon=True)
        _jobs[key] = job
        job.start()
    return RUNNING


def retry(lat: float, lon: float) -> str:
    with _guard:
        _errors.pop(_key(lat, lon), None)
    return ensure_background(lat, lon)


def status(lat: float, lon: float) -> str:
    key = _key(lat, lon)
    if cached(*key) is not None:
        return READY
    with _guard:
        job = _jobs.get(key)
        if job is not None and job.is_alive():
            return RUNNING
        if key in _errors:
            return FAILED
    return MISSING


def last_error(lat: float, lon: float) -> SourceError | None:
    with _guard:
        return _errors.get(_key(lat, lon))
