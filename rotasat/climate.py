"""Arma la tabla de clima de un lugar: fuentes + RC-02, RC-03 y RC-04. Tareas T06–T07.

Este módulo une las fuentes (que pueden consultar la red o la caché) con el motor puro de `agro.py`.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import agro
from .sources import chirps, imerg, power, srtm

# Identificadores de la fuente de lluvia. Son nombres propios: no se traducen (RF-63).
POWER_RAIN = "NASA POWER"
CHIRPS_RAIN = "CHIRPS"
IMERG_RAIN = "GPM IMERG"


def monthly_rain(series: dict, years: int) -> pd.Series:
    """RC-04: lluvia diaria sumada por mes calendario ÷ años. Los valores None (negativos en origen) se ignoran."""
    s = pd.Series(series["rain"], index=pd.to_datetime(series["dates"], format="%Y%m%d"), dtype="float64")
    out = s.groupby(s.index.month).sum(min_count=0).reindex(range(1, 13), fill_value=0.0) / years
    out.index.name = "mes"
    return out


@dataclass
class PlaceClimate:
    clim: pd.DataFrame            # tabla de 12 meses (RC-03) con la lluvia ya reemplazada (RC-04)
    rain_power: pd.Series         # lluvia mensual original de NASA POWER, para la comparación (RF-52)
    p90: float                    # umbral de calor extremo (°C)
    correction: agro.TempCorrection
    elev: float | None            # altitud real (SRTM)
    elev_area: float | None       # altitud media del área de NASA POWER
    terrain: dict                 # altitudes 3×3 de SRTM (para la pendiente, RC-06)
    rain_source: str              # POWER_RAIN, CHIRPS_RAIN o IMERG_RAIN
    rain_status: str              # estado de CHIRPS: chirps.READY / RUNNING / FAILED / MISSING (costa: READY)

    @property
    def preliminary(self) -> bool:
        """RF-21: la lluvia satelital aún se está descargando, o falló; la tabla usa la de NASA POWER."""
        return self.rain_source == POWER_RAIN and self.rain_status != chirps.READY


def build(lat: float, lon: float, *, start_download: bool = True) -> PlaceClimate:
    """Clima del lugar. Puede lanzar SourceError si fallan NASA POWER o SRTM (RF-22: «Reintentar»).

    Si el lugar no es de costa y CHIRPS no está guardado, lanza la descarga en segundo plano (RC-05) y devuelve
    resultados preliminares con la lluvia de NASA POWER. `start_download=False` no lanza nada (pruebas, prefetch).
    """
    daily = power.daily(lat, lon)
    terrain = srtm.terrain(lat, lon)
    df = power.daily_frame(daily)
    corrected, corr = agro.correct_temperatures(df, daily["elev_area"], terrain["elev"])
    clim, p90 = agro.monthly_climate(corrected)
    rain_power = clim["lluvia"].copy()

    source, status = POWER_RAIN, chirps.READY
    if corr.coast:
        # Costa: IMERG solo si ya está guardado; nunca se inicia descarga (Spec §10.2).
        series = imerg.cached(lat, lon)
        if series is not None:
            clim["lluvia"] = monthly_rain(series, imerg.YEARS)
            source = IMERG_RAIN
    else:
        series = chirps.cached(lat, lon)
        if series is not None:
            clim["lluvia"] = monthly_rain(series, chirps.YEARS)
            source = CHIRPS_RAIN
        else:
            status = chirps.ensure_background(lat, lon) if start_download else chirps.status(lat, lon)

    return PlaceClimate(clim=clim, rain_power=rain_power, p90=p90, correction=corr, elev=terrain["elev"],
                        elev_area=daily["elev_area"], terrain=terrain, rain_source=source, rain_status=status)
