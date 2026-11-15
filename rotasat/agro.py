"""Motor de cálculo de RotaSat (Spec §6). Módulo puro: no usa la red ni Streamlit.

T06: RC-02 (corrección de temperatura por altitud) y RC-03 (tabla de clima mensual).
Los números de este archivo son parte del requisito: no se redondean ni se «mejoran».
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

YEARS = 20                      # 2005–2024 (RC-01)
LAPSE_RATE = 6.5                # °C por cada 1000 m (RC-02)
COAST_MAX_ELEV = 1500           # m (RC-02.2)
COAST_MAX_RAIN = 300            # mm/año (RC-02.2)
FROST_T = 2.0                   # °C: día con riesgo de helada (RC-03)
HARD_FROST_T = 0.0              # °C: día de helada fuerte (RC-03)
HEAT_PERCENTILE = 90            # RC-03

# RC-02.4: en la costa (inversión térmica) el ajuste se pondera según el mes.
COAST_MONTH_WEIGHT = {12: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.66, 5: 0.33,
                      6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0, 10: 0.33, 11: 0.66}

TEMP_COLS = ("t_mean", "t_max", "t_min")


# --- RC-02 Corrección de temperatura por altitud ----------------------------------------------------------------

def mean_annual_rain(daily: pd.DataFrame) -> float:
    """Lluvia media anual de los datos diarios: suma de los 20 años ÷ 20 (los faltantes se ignoran)."""
    return float(daily["rain"].sum(skipna=True)) / YEARS


def is_desert_coast(elev_real: float | None, annual_rain: float) -> bool:
    """RC-02.2: altitud real < 1500 m y lluvia media anual < 300 mm."""
    return elev_real is not None and elev_real < COAST_MAX_ELEV and annual_rain < COAST_MAX_RAIN


def altitude_adjustment(elev_area: float | None, elev_real: float | None) -> float:
    """RC-02.1: ajuste = 6.5 × (altitud_del_área − altitud_real) / 1000 (°C). Sin altitudes no hay ajuste (RC-02.5)."""
    if elev_area is None or elev_real is None:
        return 0.0
    return LAPSE_RATE * (elev_area - elev_real) / 1000


@dataclass(frozen=True)
class TempCorrection:
    ajuste_c: float      # ajuste completo (°C), el que se muestra en «Sobre los datos» (RF-57)
    coast: bool          # se aplicó la ponderación de costa (RC-02.4)
    elev_area: float | None
    elev_real: float | None


def correct_temperatures(daily: pd.DataFrame, elev_area: float | None,
                         elev_real: float | None) -> tuple[pd.DataFrame, TempCorrection]:
    """RC-02: devuelve una copia de los datos diarios con las temperaturas corregidas por altitud."""
    ajuste = altitude_adjustment(elev_area, elev_real)
    coast = is_desert_coast(elev_real, mean_annual_rain(daily))
    out = daily.copy()
    if ajuste != 0.0:
        if coast:
            weights = out.index.month.map(COAST_MONTH_WEIGHT).to_numpy(dtype="float64")
            delta = ajuste * weights
        else:
            delta = ajuste
        for col in TEMP_COLS:
            out[col] = out[col] + delta
    return out, TempCorrection(ajuste, coast, elev_area, elev_real)


# --- RC-03 Tabla de clima mensual -------------------------------------------------------------------------------

def et0_hargreaves(daily: pd.DataFrame) -> pd.Series:
    """ET0 diaria (Hargreaves-Samani, FAO-56) en mm/día:
    ET0 = 0.0023 × (0.408 × radiación) × (T_media + 17.8) × √(T_máx − T_mín); una diferencia negativa cuenta como 0."""
    spread = (daily["t_max"] - daily["t_min"]).clip(lower=0)
    return 0.0023 * (0.408 * daily["ra"]) * (daily["t_mean"] + 17.8) * np.sqrt(spread)


def heat_threshold(daily: pd.DataFrame) -> float:
    """Calor extremo del lugar: percentil 90 de la máxima diaria de los 20 años (RC-03)."""
    return float(np.nanpercentile(daily["t_max"].to_numpy(dtype="float64"), HEAT_PERCENTILE))


# Columnas de la tabla de clima (índice: mes 1–12).
CLIMATE_COLS = ("lluvia", "et0", "t_media", "t_max", "t_min", "dias_helada", "dias_helada_fuerte", "dias_calor")


def monthly_climate(daily: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """RC-03: tabla de 12 meses con los datos diarios YA corregidos (RC-02). Devuelve (tabla, umbral de calor P90).

    Sumas y conteos se dividen entre 20 años; las temperaturas son el promedio de los valores diarios del mes.
    Los faltantes se ignoran (en un conteo, un faltante no cuenta como día).
    """
    p90 = heat_threshold(daily)
    month = daily.index.month
    work = pd.DataFrame({
        "lluvia": daily["rain"],
        "et0": et0_hargreaves(daily),
        "t_media": daily["t_mean"],
        "t_max": daily["t_max"],
        "t_min": daily["t_min"],
        "dias_helada": (daily["t_min"] <= FROST_T).astype("float64"),
        "dias_helada_fuerte": (daily["t_min"] <= HARD_FROST_T).astype("float64"),
        "dias_calor": (daily["t_max"] >= p90).astype("float64"),
    }, index=daily.index)
    g = work.groupby(month)
    sums = g[["lluvia", "et0", "dias_helada", "dias_helada_fuerte", "dias_calor"]].sum(min_count=0) / YEARS
    means = g[["t_media", "t_max", "t_min"]].mean()
    clim = pd.concat([sums, means], axis=1).reindex(range(1, 13))[list(CLIMATE_COLS)]
    clim.index.name = "mes"
    return clim, p90


# --- RC-06 Pendiente y región ------------------------------------------------------------------------------------

SLOPE_STEP = 0.001              # grados entre puntos de la cuadrícula SRTM
M_PER_DEG_LON = 111320          # m por grado de longitud en el ecuador (se multiplica por cos(latitud))
M_PER_DEG_LAT = 110540          # m por grado de latitud
SLOPE_FLAT, SLOPE_GENTLE = 3, 12  # % (límites de clase, RC-06)
ELEV_HIGH_ANDES, ELEV_SIERRA = 3700, 2000  # m
REGION_COAST_MAX_RAIN = 300     # mm/año

SLOPE_CLASSES = ("plano", "suave", "ladera")
REGIONS = ("costa", "sierra", "altoandina", "selva")


def slope_pct(grid: list[list[float | None]], lat: float) -> float | None:
    """RC-06: pendiente (%) con la cuadrícula 3×3 de SRTM (filas de norte a sur, columnas de oeste a este).
    pendiente = 100 × √(dzdx² + dzdy²). Sin alguno de los 4 vecinos no hay dato."""
    north, south = grid[0][1], grid[2][1]
    west, east = grid[1][0], grid[1][2]
    if None in (north, south, west, east):
        return None
    dzdx = (east - west) / (2 * SLOPE_STEP * M_PER_DEG_LON * np.cos(np.radians(lat)))
    dzdy = (north - south) / (2 * SLOPE_STEP * M_PER_DEG_LAT)
    return float(100 * np.sqrt(dzdx ** 2 + dzdy ** 2))


def slope_class(pct: float | None) -> str:
    """RC-06: < 3 % plano; < 12 % suave; si no, ladera. Sin dato: suave."""
    if pct is None:
        return "suave"
    if pct < SLOPE_FLAT:
        return "plano"
    if pct < SLOPE_GENTLE:
        return "suave"
    return "ladera"


def detect_region(elev_real: float | None, elev_area: float | None, annual_rain: float) -> str:
    """RC-06: con la altitud real (o la del área si falta) y la lluvia anual de la tabla de clima (ya con RC-04)."""
    elev = elev_real if elev_real is not None else elev_area
    if elev is not None and elev >= ELEV_HIGH_ANDES:
        return "altoandina"
    if elev is not None and elev >= ELEV_SIERRA:
        return "sierra"
    if annual_rain < REGION_COAST_MAX_RAIN:
        return "costa"
    return "selva"


# --- RC-07 Valores por defecto y respuestas del usuario ----------------------------------------------------------

DEFAULT_PRIORITIES = {"aptitud": 3, "agua": 3, "suelo": 3, "plagas": 2, "clima": 3, "ingresos": 3, "erosion": 2}

# Rotación típica de cada región: 3 pasos (cultivo, mes de siembra).
DEFAULT_ROTATION = {
    "costa": (("algodon", 9), ("maiz", 4), ("algodon", 9)),
    "sierra": (("papa", 10), ("papa", 10), ("cebada", 12)),
    "altoandina": (("papa", 10), ("papa", 10), ("cebada", 12)),
    "selva": (("maiz", 10), ("maiz", 3), ("yuca", 10)),
}

SALT_LEVEL = {"baja": 0.0, "media": 0.5, "alta": 1.0}   # RC-08.4


def default_irrigation(region: str) -> str:
    return "limitada" if region == "costa" else "no"


def default_salt(region: str) -> str:
    return "media" if region == "costa" else "baja"


@dataclass(frozen=True)
class Detected:
    """Lo que se deduce de la ubicación (RC-06)."""
    region: str
    slope_pct: float | None
    slope_class: str


@dataclass(frozen=True)
class FarmInputs:
    """Datos con los que se calcula: los detectados, salvo lo que el usuario cambió (RC-07, RF-35)."""
    region: str
    slope_class: str
    irrigation: str                 # 'no' | 'limitada' | 'suficiente'
    salt: str                       # 'baja' | 'media' | 'alta'
    texture: str | None             # una de crops.TEXTURES, o None si no se conoce
    ph: float | None
    priorities: dict
    rotation: tuple                 # ((cultivo, mes), × 3)
    soil_from_satellite: bool       # la textura o el pH vienen de SoilGrids (RC-13, vacíos de información)

    @property
    def salt_level(self) -> float:
        return SALT_LEVEL[self.salt]


def resolve_inputs(detected: Detected, overrides: dict | None = None, soil_estimate: dict | None = None) -> FarmInputs:
    """RC-07. `overrides` tiene solo lo que el usuario cambió en «Mis datos», con las claves
    region, slope_class, irrigation, salt, texture, ph, priorities y rotation.

    - Si cambia la región, el riego, la sal y la rotación por defecto pasan a ser los de la nueva región,
      salvo los que el usuario ya cambió.
    - `soil_estimate` es la estimación satelital (RC-19: {'texture', 'ph'}). Lo que escribe el usuario tiene prioridad.
    """
    o = overrides or {}
    region = o.get("region", detected.region)
    texture, ph, from_sat = o.get("texture"), o.get("ph"), False
    if soil_estimate:
        if texture is None and soil_estimate.get("texture") is not None:
            texture, from_sat = soil_estimate["texture"], True
        if ph is None and soil_estimate.get("ph") is not None:
            ph, from_sat = soil_estimate["ph"], True
    return FarmInputs(
        region=region,
        slope_class=o.get("slope_class", detected.slope_class),
        irrigation=o.get("irrigation", default_irrigation(region)),
        salt=o.get("salt", default_salt(region)),
        texture=texture,
        ph=ph,
        priorities={**DEFAULT_PRIORITIES, **o.get("priorities", {})},
        rotation=tuple(tuple(step) for step in o.get("rotation", DEFAULT_ROTATION[region])),
        soil_from_satellite=from_sat,
    )
