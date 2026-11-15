"""NASA POWER: clima diario 2005–2024 y humedad del suelo mensual (RC-01, RC-17). Tarea T05.

Se guarda en la caché una versión compacta (columnas), no la respuesta cruda. El valor de relleno -999 de POWER se
cambia por None (RC-01: «los valores marcados como faltantes se ignoran»).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from .. import cache
from ..cache import SourceError
from . import http

BASE = "https://power.larc.nasa.gov/api/temporal"
START, END = 2005, 2024
FILL = -999.0

# Nombre en POWER → nombre de columna en RotaSat.
DAILY_PARAMS = {
    "T2M": "t_mean",          # °C
    "T2M_MAX": "t_max",       # °C
    "T2M_MIN": "t_min",       # °C
    "PRECTOTCORR": "rain",    # mm/día
    "TOA_SW_DWN": "ra",       # MJ/m²/día, radiación en el tope de la atmósfera
}
SOIL_PARAMS = {"GWETTOP": "surface", "GWETROOT": "root"}  # 0 (seco) a 1 (saturado)


def _clean(v: Any) -> float | None:
    if v is None:
        return None
    v = float(v)
    return None if v <= FILL else v


def _point(lat: float, lon: float) -> tuple[float, float]:
    return round(lat, 4), round(lon, 4)


def _parse_daily(raw: dict) -> dict:
    try:
        series = raw["properties"]["parameter"]
        elev_area = _clean(raw["geometry"]["coordinates"][2])
        dates = sorted(series["T2M"])
        out = {"elev_area": elev_area, "dates": dates}
        for power_name, col in DAILY_PARAMS.items():
            out[col] = [_clean(series[power_name].get(d)) for d in dates]
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise SourceError("power", "respuesta diaria inesperada", cause=e) from e
    return out


def daily(lat: float, lon: float) -> dict:
    """Datos diarios: {'elev_area': m o None, 'dates': ['20050101', ...], 't_mean': [...], ...}."""
    lat, lon = _point(lat, lon)
    params = {"lat": lat, "lon": lon, "start": f"{START}0101", "end": f"{END}1231", "p": sorted(DAILY_PARAMS)}

    def fetch():
        raw = http.get_json("power", f"{BASE}/daily/point", {
            "parameters": ",".join(DAILY_PARAMS), "community": "AG", "latitude": lat, "longitude": lon,
            "start": params["start"], "end": params["end"], "format": "JSON",
        }, timeout=120)
        return _parse_daily(raw)

    return cache.get_or_fetch("power_daily", params, fetch)


def daily_frame(data: dict) -> pd.DataFrame:
    """Los datos diarios como DataFrame con índice de fechas; los faltantes quedan como NaN."""
    df = pd.DataFrame({col: data[col] for col in DAILY_PARAMS.values()},
                      index=pd.to_datetime(data["dates"], format="%Y%m%d"), dtype="float64")
    df.index.name = "date"
    return df


def _parse_monthly(raw: dict) -> dict:
    try:
        series = raw["properties"]["parameter"]
        # Las claves son AAAAMM; el «mes 13» es el promedio anual y se descarta.
        months = sorted(k for k in series["GWETTOP"] if not k.endswith("13"))
        out = {"months": months}
        for power_name, col in SOIL_PARAMS.items():
            out[col] = [_clean(series[power_name].get(m)) for m in months]
    except (KeyError, TypeError, ValueError) as e:
        raise SourceError("power", "respuesta mensual inesperada", cause=e) from e
    return out


def soil_moisture(lat: float, lon: float) -> dict:
    """Humedad del suelo mensual (MERRA-2): {'months': ['200501', ...], 'surface': [...], 'root': [...]}."""
    lat, lon = _point(lat, lon)
    params = {"lat": lat, "lon": lon, "start": START, "end": END, "p": sorted(SOIL_PARAMS)}

    def fetch():
        raw = http.get_json("power", f"{BASE}/monthly/point", {
            "parameters": ",".join(SOIL_PARAMS), "community": "AG", "latitude": lat, "longitude": lon,
            "start": START, "end": END, "format": "JSON",
        }, timeout=120)
        return _parse_monthly(raw)

    return cache.get_or_fetch("power_soil", params, fetch)
