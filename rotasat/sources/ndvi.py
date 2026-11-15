"""Verdor del campo (NDVI) del ORNL DAAC MODIS Web Service: MODIS MOD13Q1 (250 m) y, opcional, VIIRS VNP13A1
(500 m). RC-16, RF-33. Tarea T18.

El servicio entrega como máximo 10 fechas por pedido, así que primero se piden las fechas disponibles del punto y
luego la serie de 2023–2024 en tandas de 10. La serie completa se guarda en la caché como una sola respuesta (RNF-02):
{'dates': ['2023-01-01', ...], 'values': [4228, ...]} con los valores crudos (× 10000; el motor descarta los sin dato).
"""
from __future__ import annotations

from .. import cache
from ..cache import SourceError
from . import http

SERVICE = "ndvi"
BASE = "https://modis.ornl.gov/rst/api/v1"
PRODUCTS = {"modis": ("MOD13Q1", "250m_16_days_NDVI"), "viirs": ("VNP13A1", "500_m_16_days_NDVI")}
START, END = "2023-01-01", "2024-12-31"      # RC-16
CHUNK = 10                                   # fechas por pedido (límite del servicio)
TIMEOUT = 90


def _params(lat: float, lon: float, product: str) -> dict:
    return {"lat": round(lat, 4), "lon": round(lon, 4), "product": product, "start": START, "end": END}


def cached(lat: float, lon: float, product: str = "modis") -> dict | None:
    """Serie guardada o None. Nunca consulta la red."""
    return cache.load(SERVICE, _params(lat, lon, product))


def _download(lat: float, lon: float, product: str) -> dict:
    code, band = PRODUCTS[product]
    point = {"latitude": lat, "longitude": lon}
    raw = http.get_json(SERVICE, f"{BASE}/{code}/dates", point, timeout=TIMEOUT)
    try:
        wanted = [d["modis_date"] for d in raw["dates"] if START <= d["calendar_date"] <= END]
    except (KeyError, TypeError) as e:
        raise SourceError(SERVICE, "respuesta inesperada", cause=e) from e
    if not wanted:
        raise SourceError(SERVICE, "sin fechas en 2023–2024")
    dates, values = [], []
    for i in range(0, len(wanted), CHUNK):
        part = wanted[i:i + CHUNK]
        raw = http.get_json(SERVICE, f"{BASE}/{code}/subset", {
            **point, "band": band, "startDate": part[0], "endDate": part[-1], "kmAboveBelow": 0, "kmLeftRight": 0,
        }, timeout=TIMEOUT)
        try:
            for item in raw["subset"]:
                dates.append(item["calendar_date"])
                values.append(item["data"][0] if item["data"] else None)
        except (KeyError, TypeError, IndexError) as e:
            raise SourceError(SERVICE, "respuesta inesperada", cause=e) from e
    return {"dates": dates, "values": values}


def series(lat: float, lon: float, product: str = "modis") -> dict:
    """Serie 2023–2024 del producto ('modis' o 'viirs'), de la caché o del servicio. Puede lanzar SourceError."""
    lat, lon = round(lat, 4), round(lon, 4)
    return cache.get_or_fetch(SERVICE, _params(lat, lon, product), lambda: _download(lat, lon, product))
