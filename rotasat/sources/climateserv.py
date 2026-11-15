"""Cliente de NASA SERVIR ClimateSERV para series diarias de lluvia (CHIRPS, GPM IMERG). Tarea T07.

Flujo: submitDataRequest → getDataRequestProgress (hasta 100; -1 es error) → getDataFromRequest.
Se pide el promedio («avg», operationtype=5) de un cuadrado pequeño alrededor del punto.
Los valores negativos significan «sin dato» y se guardan como None (RC-04).
"""
from __future__ import annotations

import json
import time
from datetime import date, datetime

from ..cache import SourceError
from . import http

BASE = "https://climateserv.servirglobal.net/api/"
OP_AVERAGE = 5
INTERVAL_DAILY = 0
POLL_SECONDS = 3.0

# Medio lado (grados) del cuadrado que se promedia: un píxel nativo de cada producto. Calibrado en T07 contra la
# lluvia anual del Anexo B.1:
#   CHIRPS (píxel 0.05°): 0.025 reproduce Chupaca 792, Juliaca 498 y Satipo 1582 (0.001 y 0.01 no).
#   IMERG  (píxel 0.1°):  0.05 reproduce Ica 49 (0.025 da 52).
HALF_CHIRPS = 0.025
HALF_IMERG = 0.05


def square(lat: float, lon: float, half: float) -> dict:
    ring = [[lon - half, lat - half], [lon + half, lat - half], [lon + half, lat + half], [lon - half, lat + half],
            [lon - half, lat - half]]
    return {"type": "Polygon", "coordinates": [[[round(x, 6), round(y, 6)] for x, y in ring]]}


def _parse(service: str, raw: dict) -> dict:
    try:
        rows = []
        for item in raw["data"]:
            d = datetime.strptime(item["date"], "%m/%d/%Y").strftime("%Y%m%d")
            v = item["value"]["avg"]
            v = None if v is None or float(v) < 0 else float(v)
            rows.append((d, v))
    except (KeyError, TypeError, ValueError) as e:
        raise SourceError(service, "respuesta inesperada", cause=e) from e
    if not rows:
        raise SourceError(service, "sin datos")
    rows.sort()
    return {"dates": [d for d, _ in rows], "rain": [v for _, v in rows]}


def fetch_daily(service: str, datatype: int, lat: float, lon: float, start: date, end: date, *, half: float,
                max_seconds: float = 300) -> dict:
    """Serie diaria {'dates': ['AAAAMMDD', ...], 'rain': [mm o None, ...]} del promedio de un cuadrado de medio lado
    `half` alrededor del punto. Bloquea hasta `max_seconds`."""
    submitted = http.get_json(service, BASE + "submitDataRequest/", {
        "datatype": datatype,
        "begintime": start.strftime("%m/%d/%Y"),
        "endtime": end.strftime("%m/%d/%Y"),
        "intervaltype": INTERVAL_DAILY,
        "operationtype": OP_AVERAGE,
        "geometry": json.dumps(square(lat, lon, half)),
        "isZip_CurrentDataType": "false",
    }, timeout=60)
    try:
        job = submitted[0]
    except (IndexError, KeyError, TypeError) as e:
        raise SourceError(service, "no se aceptó el pedido", cause=e) from e

    deadline = time.monotonic() + max_seconds
    while True:
        progress = http.get_json(service, BASE + "getDataRequestProgress/", {"id": job}, timeout=30)
        value = float(progress[0]) if isinstance(progress, list) and progress else -1.0
        if value >= 100:
            break
        if value < 0:
            raise SourceError(service, "el servicio informó un error al procesar el pedido")
        if time.monotonic() > deadline:
            raise SourceError(service, f"no terminó en {max_seconds:.0f} s", cause=TimeoutError())
        time.sleep(POLL_SECONDS)

    return _parse(service, http.get_json(service, BASE + "getDataFromRequest/", {"id": job}, timeout=120))
