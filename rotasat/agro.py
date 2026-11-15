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


# --- RC-08 Aptitud de un cultivo sembrado en un mes ---------------------------------------------------------------

FROST_K = 0.06                  # f_helada = e^(−0.06 × exposición)
WATER_MIN_FACTOR = 0.3          # sin riego: f_agua nunca baja de 0.3
WATER_FULL_COVER = 0.5          # sin riego: con cobertura ≥ 0.5, f_agua = 1
IRRIGATION_REF_MM = 900         # con riego: el castigo es completo a partir de 900 mm
IRRIGATION_PENALTY = {"limitada": 0.45, "suficiente": 0.12}
LIMITED_HIGH_KC = 0.9           # con agua limitada y Kc > 0.9, f_agua × 0.55
LIMITED_HIGH_KC_FACTOR = 0.55
SALT_K = 0.8
PH_NEAR = 0.5
FACTOR_ORDER = ("temp", "helada", "agua", "sal", "textura", "ph")  # orden de desempate del factor limitante
NO_LIMIT_THRESHOLD = 0.85
FALLOW_APTITUDE = 70            # RC-10: «Descanso» vale 70


def cycle_months(sow_month: int, months: int) -> list[int]:
    """Meses del ciclo, empezando en el de siembra y dando la vuelta al año."""
    return [(sow_month - 1 + i) % 12 + 1 for i in range(months)]


def effective_rain(p: float) -> float:
    """Lluvia aprovechable de un mes con lluvia p (mm)."""
    return max(0.0, 0.6 * p - 10) if p <= 70 else 0.8 * p - 24


def _temp_score(t: float, opt: tuple, lim: tuple) -> float:
    o1, o2 = opt
    l1, l2 = lim
    if o1 <= t <= o2:
        return 1.0
    if t < o1:
        return max(0.0, (t - l1) / (o1 - l1))
    return max(0.0, (l2 - t) / (l2 - o2))


def _texture_factor(texture: str | None, preferred: tuple) -> float:
    from .crops import TEXTURES
    if texture is None or not preferred or texture in preferred:
        return 1.0
    i = TEXTURES.index(texture)
    distance = min(abs(i - TEXTURES.index(p)) for p in preferred)
    return 0.75 if distance == 1 else 0.5


def _ph_factor(ph: float | None, rng: tuple) -> float:
    if ph is None:
        return 1.0
    lo, hi = rng
    if lo <= ph <= hi:
        return 1.0
    out = lo - ph if ph < lo else ph - hi
    return 0.75 if out <= PH_NEAR else 0.5


def crop_suitability(crop, sow_month: int, clim: pd.DataFrame, inputs: FarmInputs) -> dict:
    """RC-08: aptitud (0–100) y sus seis factores para `crop` sembrado en `sow_month`."""
    months = cycle_months(sow_month, crop.months)
    c = clim.loc[months]

    temps = [_temp_score(t, crop.t_opt, crop.t_lim) for t in c["t_media"]]
    f_temp = 0.6 * (sum(temps) / len(temps)) + 0.4 * min(temps)

    expo = float(((c["dias_helada"] + 2 * c["dias_helada_fuerte"]) * crop.frost_sens).sum())
    f_frost = float(np.exp(-FROST_K * expo))

    demand = c["et0"] * crop.kc
    eff = c["lluvia"].map(effective_rain)
    need = float(demand.sum())
    covered = float(np.minimum(eff, demand).sum())
    coverage = covered / need if need > 0 else 1.0
    irrigation_mm = max(0.0, need - covered)
    if inputs.irrigation == "no":
        f_water = min(1.0, max(WATER_MIN_FACTOR, coverage / WATER_FULL_COVER))
    else:
        f_water = 1 - IRRIGATION_PENALTY[inputs.irrigation] * min(1.0, irrigation_mm / IRRIGATION_REF_MM)
        if inputs.irrigation == "limitada" and crop.kc > LIMITED_HIGH_KC:
            f_water *= LIMITED_HIGH_KC_FACTOR

    f_salt = 1 - SALT_K * inputs.salt_level * (1 - crop.salt_tol)
    f_texture = _texture_factor(inputs.texture, crop.textures)
    f_ph = _ph_factor(inputs.ph, crop.ph)

    factors = {"temp": f_temp, "helada": f_frost, "agua": f_water, "sal": f_salt, "textura": f_texture, "ph": f_ph}
    return {
        "aptitud": 100 * float(np.prod(list(factors.values()))),
        "factors": factors,
        "lluvia_cubre": coverage,
        "riego_mm": irrigation_mm,
        "riego_m3ha": irrigation_mm * 10,
        "expo_helada": expo,
        "t_min_ciclo": float(c["t_media"].min()),
        "t_max_ciclo": float(c["t_media"].max()),
    }


def limiting_factor(crop, r: dict, inputs: FarmInputs) -> tuple[str, dict]:
    """RC-09: el factor más bajo como (texto ES del Anexo C, campos). El texto se traduce con i18n.t()."""
    name = min(FACTOR_ORDER, key=lambda k: r["factors"][k])   # min() se queda con el primero en un empate
    if r["factors"][name] >= NO_LIMIT_THRESHOLD:
        return "Sin limitaciones importantes", {}
    if name == "temp":
        o0, o1 = crop.t_opt
        if r["t_min_ciclo"] < o0:
            return ("Muy frío para este cultivo (media {t:.0f} °C; prefiere {o0}–{o1} °C)",
                    {"t": r["t_min_ciclo"], "o0": o0, "o1": o1})
        return "Muy caluroso (media {t:.0f} °C; prefiere {o0}–{o1} °C)", {"t": r["t_max_ciclo"], "o0": o0, "o1": o1}
    if name == "helada":
        return "Riesgo de heladas durante la campaña ({expo:.0f} puntos de exposición)", {"expo": r["expo_helada"]}
    if name == "agua":
        if inputs.irrigation == "no":
            return ("La lluvia solo cubre {pct:.0f}% de lo que necesita: requiere riego",
                    {"pct": r["lluvia_cubre"] * 100})
        return "Necesita mucha agua de riego (~{riego:,.0f} m³/ha)", {"riego": r["riego_m3ha"]}
    if name == "sal":
        return "Poco tolerante a la sal", {}
    if name == "textura":
        return "Prefiere suelos {texturas}", {"texturas": crop.textures}   # la interfaz traduce y une con ', '
    return "Prefiere pH {ph_min}–{ph_max}", {"ph_min": crop.ph[0], "ph_max": crop.ph[1]}


# --- RC-09 Tabla de aptitud del lugar ----------------------------------------------------------------------------

LEVEL_SUITABLE, LEVEL_CARE = 65, 40
LEVELS = ("🟢 Apto", "🟡 Con cuidado", "🔴 No recomendado")   # textos ES del Anexo C
COVERAGE_CAP = 1.5


def level(aptitude: float) -> str:
    """Nivel: ≥ 65 Apto; ≥ 40 Con cuidado; si no, No recomendado. Se llama con la aptitud REDONDEADA al entero
    (decisión D-RC09b, Plan.md §6: es lo que reproduce el Anexo B.1; en Ica el tarwi da 39.97 → 40 «Con cuidado»)."""
    if aptitude >= LEVEL_SUITABLE:
        return LEVELS[0]
    if aptitude >= LEVEL_CARE:
        return LEVELS[1]
    return LEVELS[2]


def best_sowing(crop, clim: pd.DataFrame, inputs: FarmInputs) -> tuple[int, dict]:
    """Mejor mes de siembra: mayor aptitud redondeada; luego mayor cobertura (tope 1.5, 2 decimales); luego menor
    exposición a heladas. En empate total gana el mes más temprano del año."""
    best_month, best, best_key = None, None, None
    for m in range(1, 13):
        r = crop_suitability(crop, m, clim, inputs)
        key = (round(r["aptitud"]), round(min(r["lluvia_cubre"], COVERAGE_CAP), 2), -r["expo_helada"])
        if best_key is None or key > best_key:
            best_month, best, best_key = m, r, key
    return best_month, best


def suitability_table(clim: pd.DataFrame, inputs: FarmInputs) -> pd.DataFrame:
    """RC-09: una fila por cultivo (los 17, sin «Descanso»), ordenada por aptitud redondeada de mayor a menor.

    Desempate D-RC09 (Plan.md §6): se arma el DataFrame en el orden del Anexo A y se ordena con
    `sort_values(ascending=False)` y el método por defecto de pandas (no estable), como el original.
    """
    from .crops import FIELD_CROPS
    rows = []
    for crop in FIELD_CROPS:
        m, r = best_sowing(crop, clim, inputs)
        rows.append({
            "id": crop.id,
            "aptitud": round(r["aptitud"]),
            "aptitud_raw": r["aptitud"],
            "nivel": level(round(r["aptitud"])),
            "mes": m,
            "meses": crop.months,
            "lluvia_cubre": min(r["lluvia_cubre"], 1) * 100,
            "riego_m3ha": round(r["riego_m3ha"], -1),
            "limitante": limiting_factor(crop, r, inputs),
            "expo_helada": r["expo_helada"],
            "factors": r["factors"],
        })
    df = pd.DataFrame(rows)
    return df.sort_values("aptitud", ascending=False).reset_index(drop=True)


def level_counts(table: pd.DataFrame) -> tuple[int, int, int]:
    """Contadores de «Qué sembrar» (RF-31.2): (aptos, con cuidado, no recomendados)."""
    return tuple(int((table["nivel"] == lv).sum()) for lv in LEVELS)


# --- RC-10 Evaluación de una rotación ----------------------------------------------------------------------------

TIMELINE_MONTHS = 36            # la línea empieza en enero del año 1; lo que pasa del mes 36 no se cuenta (§10.1)
SLOPE_FACTOR = {"plano": 0.3, "suave": 0.7, "ladera": 1.0}
BARE_EROSION = 0.15             # erosión extra por cada mes sin cultivo
FORAGE_INCOME = 0.5             # ingreso extra por cada cultivo forrajero
NONCONSECUTIVE_REPEAT = 0.5     # misma familia separada por un paso


def place_rotation(rotation) -> list[tuple[str, int, int]]:
    """RC-10: coloca los pasos (cultivo, mes de siembra) en la línea de 36 meses.

    Devuelve (cultivo, mes de inicio, mes de fin exclusivo), con los meses de la línea numerados desde 1 (1 = enero del
    año 1). Cada cultivo empieza en la primera aparición de su mes de siembra que no sea anterior al fin del cultivo
    previo. El inicio y el fin pueden pasar del mes 36: esos meses no se cuentan (comportamiento conocido §10.1).
    """
    from .crops import get
    placed, free = [], 1
    for crop_id, sow in rotation:
        start = free + (sow - 1 - (free - 1)) % 12      # primer mes ≥ free cuyo mes del año es `sow`
        end = start + get(crop_id).months
        placed.append((crop_id, start, end))
        free = end
    return placed


def family_repetition(rotation) -> float:
    """RC-10: n.º de pasos seguidos con la misma familia + 0.5 × n.º de pasos con la misma familia separados por uno."""
    from .crops import get
    fam = [get(c).family for c, _ in rotation]
    seguidos = sum(fam[i] == fam[i + 1] for i in range(len(fam) - 1))
    separados = sum(fam[i] == fam[i + 2] for i in range(len(fam) - 2))
    return seguidos + NONCONSECUTIVE_REPEAT * separados


def evaluate_rotation(rotation, clim: pd.DataFrame, inputs: FarmInputs) -> dict:
    """RC-10: los datos de una rotación (3 pasos) antes de puntuarla (RC-11)."""
    from .crops import FALLOW_ID, get
    placed = place_rotation(rotation)
    owner = {}                                  # mes de la línea → cultivo que lo ocupa (solo hasta el mes 36)
    for crop_id, start, end in placed:
        for t in range(start, min(end, TIMELINE_MONTHS + 1)):
            owner[t] = crop_id
    slope = SLOPE_FACTOR[inputs.slope_class]
    agua_mm = helada = calor = erosion = 0.0
    bare = 0
    for t in range(placed[0][1], TIMELINE_MONTHS + 1):     # desde el primer mes ocupado hasta el 36
        row = clim.loc[(t - 1) % 12 + 1]
        lluvia = row["lluvia"]
        crop_id = owner.get(t)
        if crop_id is None:
            erosion += (lluvia / 100) * slope + BARE_EROSION
            bare += 1
            continue
        crop = get(crop_id)
        agua_mm += max(0.0, row["et0"] * crop.kc - effective_rain(lluvia))
        helada += (row["dias_helada"] + 2 * row["dias_helada_fuerte"]) * crop.frost_sens
        calor += row["dias_calor"] * crop.heat_sens
        erosion += (lluvia / 100) * slope * (1 - crop.cover)

    apts = [FALLOW_APTITUDE if c == FALLOW_ID else crop_suitability(get(c), m, clim, inputs)["aptitud"]
            for c, m in rotation]
    crops = [get(c) for c, _ in rotation]
    return {
        "placed": placed,
        "aptitud": sum(apts) / len(apts),
        "aptitud_min": min(apts),
        "agua_m3ha": agua_mm * 10,
        "helada": helada,
        "calor": calor,
        "clima": helada + calor,
        "erosion": erosion,
        "sal": sum((1 - c.salt_tol) * inputs.salt_level for c in crops),
        "nitrogeno": sum(c.n for c in crops),
        "ingreso": sum(c.market + (FORAGE_INCOME if c.forage else 0) for c in crops),
        "repeticion": family_repetition(rotation),
        "meses_desnudo": bare,
    }


# --- RC-11 Puntajes y total --------------------------------------------------------------------------------------

LOW_APTITUDE_MIN = 40           # si la aptitud mínima de la rotación es menor, el total × 0.85
LOW_APTITUDE_FACTOR = 0.85
SALT_WEIGHT = 2                 # la sal pesa 2 (solo cuenta si el nivel de sal no es «baja»)
SCORE_KEYS = ("aptitud", "agua", "suelo", "plagas", "clima", "ingresos", "erosion", "sal")


def _relative(values: list[float]) -> list[float]:
    """Relativo (menos es mejor): 100 − 60 × (v − mín) / máx. Si el máximo es 0, todas reciben 100."""
    lo, hi = min(values), max(values)
    if hi == 0:
        return [100.0] * len(values)
    return [100 - 60 * (v - lo) / hi for v in values]


def _over_range(values: list[float], more_is_better: bool) -> list[float]:
    """Sobre el rango: 40 + 60 × (v − mín)/(máx − mín) si más es mejor; 100 − 60 × (v − mín)/(máx − mín) si menos.
    Si máx = mín, todas reciben 100."""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [100.0] * len(values)
    frac = [(v - lo) / (hi - lo) for v in values]
    return [40 + 60 * f for f in frac] if more_is_better else [100 - 60 * f for f in frac]


def score_rotations(evals: list[dict], inputs: FarmInputs) -> list[dict]:
    """RC-11: puntajes de cada rotación DENTRO del grupo `evals` (salidas de evaluate_rotation) y su total.

    Devuelve, en el mismo orden, {'scores': {criterio: puntaje}, 'total': float}. Total = promedio ponderado por las
    prioridades del usuario; la sal (peso 2) solo entra si el nivel de sal no es «baja».
    """
    cols = {
        "aptitud": [e["aptitud"] for e in evals],
        "agua": _relative([e["agua_m3ha"] for e in evals]),
        "suelo": _over_range([e["nitrogeno"] for e in evals], more_is_better=True),
        "plagas": _over_range([e["repeticion"] for e in evals], more_is_better=False),
        "clima": _relative([e["clima"] for e in evals]),
        "ingresos": _over_range([e["ingreso"] for e in evals], more_is_better=True),
        "erosion": _relative([e["erosion"] for e in evals]),
    }
    weights = {k: inputs.priorities[k] for k in cols}
    if inputs.salt != "baja":
        cols["sal"] = _relative([e["sal"] for e in evals])
        weights["sal"] = SALT_WEIGHT
    wsum = sum(weights.values())
    out = []
    for i, e in enumerate(evals):
        scores = {k: cols[k][i] for k in SCORE_KEYS if k in cols}
        total = sum(weights[k] * scores[k] for k in scores) / wsum if wsum else 0.0
        if e["aptitud_min"] < LOW_APTITUDE_MIN:
            total *= LOW_APTITUDE_FACTOR
        out.append({"scores": {k: float(v) for k, v in scores.items()}, "total": float(total)})
    return out


# --- RC-12 Rotaciones automáticas (A y B) ------------------------------------------------------------------------

CANDIDATE_MIN_APTITUDE = 45
MAX_CANDIDATES = 8
MIN_CANDIDATES = 3


def candidates(table: pd.DataFrame) -> list[str]:
    """RC-12.1: cultivos con aptitud (redondeada, la de la tabla) ≥ 45, como máximo los 8 primeros de la tabla RC-09.
    Si son menos de 3, los 3 primeros de la tabla."""
    ok = table[table["aptitud"] >= CANDIDATE_MIN_APTITUDE].head(MAX_CANDIDATES)
    if len(ok) < MIN_CANDIDATES:
        ok = table.head(MIN_CANDIDATES)
    return list(ok["id"])


def candidate_sequences(cands: list[str], best_month: dict) -> list[tuple]:
    """RC-12.2–3: secuencias ordenadas de 3 candidatos distintos, cada uno en su mejor mes; sin dos pasos seguidos de
    la misma familia y, si hay alguna leguminosa entre los candidatos, con al menos una."""
    from itertools import permutations
    from .crops import get
    any_legume = any(get(c).is_legume for c in cands)
    out = []
    for seq in permutations(cands, 3):
        fam = [get(c).family for c in seq]
        if fam[0] == fam[1] or fam[1] == fam[2]:
            continue
        if any_legume and not any(get(c).is_legume for c in seq):
            continue
        out.append(tuple((c, best_month[c]) for c in seq))
    return out


def main_crop(rotation) -> str:
    """RC-12.6: el cultivo que más se repite en la rotación actual (en empate, el primero que aparece)."""
    ids = [c for c, _ in rotation]
    return max(ids, key=ids.count)       # max() se queda con el primero en un empate


@dataclass(frozen=True)
class RotationResult:
    label: str                  # 'Actual' | 'A' | 'B'
    rotation: tuple             # ((cultivo, mes), × 3)
    evaluation: dict            # RC-10
    scores: dict                # RC-11, recalculados entre Actual, A y B (RC-12.8)
    total: float


def auto_rotations(table: pd.DataFrame, clim: pd.DataFrame, inputs: FarmInputs) -> list[RotationResult]:
    """RC-12: devuelve [Actual, A, B] con los puntajes recalculados comparando solo las tres.

    Si no hay ninguna secuencia válida, devuelve solo la actual; si hay una sola, Actual y A.
    """
    current = inputs.rotation
    cands = candidates(table)
    best_month = dict(zip(table["id"], table["mes"].astype(int)))
    seqs = candidate_sequences(cands, best_month)
    evals = {r: evaluate_rotation(r, clim, inputs) for r in seqs}

    # RC-12.4: se puntúan todas junto con la actual y se ordenan de mayor a menor total (orden estable).
    group = [current, *seqs]
    totals = score_rotations([evaluate_rotation(current, clim, inputs), *(evals[r] for r in seqs)], inputs)
    ranked = sorted(range(1, len(group)), key=lambda i: -totals[i]["total"])
    ranked = [group[i] for i in ranked]

    chosen = [("Actual", current)]
    if ranked:
        a = ranked[0]
        chosen.append(("A", a))
        a_crops = {c for c, _ in a}
        main = main_crop(current)
        if main in cands and main not in a_crops:
            b = next((r for r in ranked if main in {c for c, _ in r}), None)
        else:
            b = next((r for r in ranked[1:] if {c for c, _ in r} != a_crops), None)
        if b is not None:
            chosen.append(("B", b))

    # RC-12.8: puntajes que se muestran, comparando solo Actual, A y B.
    shown_evals = [evaluate_rotation(current, clim, inputs) if lbl == "Actual" else evals[r] for lbl, r in chosen]
    shown = score_rotations(shown_evals, inputs)
    return [RotationResult(lbl, r, ev, s["scores"], s["total"])
            for (lbl, r), ev, s in zip(chosen, shown_evals, shown)]


def rotation_name(result: RotationResult, lang: str) -> str:
    """RC-12.7: «A: cultivo → cultivo → cultivo», «B: …» y «Actual: …» («Current: …» en inglés)."""
    from .crops import get
    from .i18n import t
    label = t("Actual", lang) if result.label == "Actual" else result.label
    return f"{label}: " + " → ".join(get(c).name(lang) for c, _ in result.rotation)


# --- RC-13 Explicación de cada rotación --------------------------------------------------------------------------

WATER_DIFF_M3HA = 100           # ahorro / exceso de agua que se menciona (m³/ha en 3 años)
TANKER_M3 = 30                  # camión cisterna
APTITUDE_GAIN = 3               # «mejor adaptados» si la aptitud supera a la actual en más de 3 puntos
LOWER_RATIO = 0.9               # heladas/calor y erosión: «menor» si es < 90 % del de la actual
FROST_MONTH_MIN_DAYS = 0.5      # se menciona el mes con más helada si algún mes supera 0.5 días


def _join_list(items: list[str], lang: str) -> str:
    """«a, b y c» / «a, b and c» (la conjunción viene del Anexo C)."""
    from .i18n import t
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + t(" y ", lang) + items[-1]


def explain_rotation(result: RotationResult, current: RotationResult, clim: pd.DataFrame, p90: float,
                     inputs: FarmInputs, lang: str) -> dict[str, list[str]]:
    """RC-13: las cinco listas de la explicación (textos del Anexo C.2 ya traducidos), en el orden del original:
    'por_que', 'evidencia', 'beneficios', 'riesgos' y 'vacios'. `current` es la rotación actual (para comparar)."""
    from .crops import get
    from .i18n import month, t
    c, b = result.evaluation, current.evaluation
    crops = [get(cid) for cid, _ in result.rotation]
    is_current = result.label == "Actual"

    por_que = [t("Es la rotación que el agricultor usa hoy: sirve como punto de comparación." if is_current else
                 "Armada automáticamente con los cultivos más aptos para el clima y suelo de esta chacra, cada uno en "
                 "su mejor mes de siembra.", lang)]
    legs = list(dict.fromkeys(cr.name(lang) for cr in crops if cr.n > 0))
    if legs:
        por_que.append(t("Incluye leguminosas ({legs}) que fijan nitrógeno del aire y reducen la necesidad de "
                         "fertilizante.", lang, legs=", ".join(legs)))
    if len({cr.family for cr in crops}) == len(crops):
        por_que.append(t("Ninguna familia de cultivo se repite: se corta el ciclo de plagas y enfermedades.", lang))

    meses_txt = ", ".join(f"{get(cid).name(lang)} {t('en', lang)} {month(m, lang)}" for cid, m in result.rotation)
    evidencia = [
        t("Siembras: {meses_txt}.", lang, meses_txt=meses_txt),
        t("Aptitud promedio de sus cultivos en este lugar: **{aptitud:.0f}/100**.", lang, aptitud=c["aptitud"]),
    ]
    if inputs.irrigation != "no":
        evidencia.append(t("Necesidad de riego estimada en 3 años: **{agua:,.0f} m³/ha** (ET0 de NASA POWER × "
                           "coeficiente de cultivo − lluvia efectiva).", lang, agua=c["agua_m3ha"]))
    else:
        evidencia.append(t("Agua que la lluvia no cubre en 3 años: **{agua:,.0f} m³/ha** (NASA POWER).", lang,
                           agua=c["agua_m3ha"]))
    if (clim["dias_helada"] > FROST_MONTH_MIN_DAYS).any():
        mh = int(clim["dias_helada"].idxmax())
        evidencia.append(t("Mes con más riesgo de helada: **{mes}** ({dias:.0f} días/año con mínima ≤ 2 °C).", lang,
                           mes=month(mh, lang), dias=clim.loc[mh, "dias_helada"]))
    mc = int(clim["dias_calor"].idxmax())
    evidencia.append(t("Mes con más calor extremo: **{mes}** ({dias:.0f} días/año sobre {p90:.1f} °C, el percentil 90 "
                       "local).", lang, mes=month(mc, lang), dias=clim.loc[mc, "dias_calor"], p90=p90))
    evidencia.append(t("Meses con suelo desnudo en 3 años: **{meses}**.", lang, meses=c["meses_desnudo"]))

    beneficios, riesgos = [], []
    d = b["agua_m3ha"] - c["agua_m3ha"]                  # > 0: ahorra agua frente a la actual
    if not is_current:
        if d > WATER_DIFF_M3HA:
            beneficios.append(t("Ahorra ~**{d:,.0f} m³ de agua por hectárea** en 3 años frente a la rotación actual "
                                "(≈ {cisternas:,.0f} camiones cisterna de 30 m³).", lang, d=d, cisternas=d / TANKER_M3))
        if c["aptitud"] > b["aptitud"] + APTITUDE_GAIN:
            beneficios.append(t("Cultivos mejor adaptados a este lugar (aptitud {aptitud:.0f} vs {aptitud_actual:.0f}).",
                                lang, aptitud=c["aptitud"], aptitud_actual=b["aptitud"]))
        if c["nitrogeno"] > b["nitrogeno"]:
            beneficios.append(t("Mejor balance de nitrógeno ({n_bal:+d} vs {n_bal_actual:+d}): menos urea que comprar.",
                                lang, n_bal=int(c["nitrogeno"]), n_bal_actual=int(b["nitrogeno"])))
        if c["repeticion"] < b["repeticion"]:
            beneficios.append(t("Menos repetición de familias → menor presión de plagas del suelo.", lang))
        if c["clima"] < LOWER_RATIO * b["clima"]:
            beneficios.append(t("Menor exposición a heladas/calor según el clima histórico del lugar.", lang))
        if c["erosion"] < LOWER_RATIO * b["erosion"]:
            beneficios.append(t("Suelo más protegido en meses de lluvia → menos erosión.", lang))
        if -d > WATER_DIFF_M3HA:
            riesgos.append(t("Requiere ~{extra:,.0f} m³/ha MÁS agua que la rotación actual.", lang, extra=-d))
        if c["ingreso"] < b["ingreso"]:
            riesgos.append(t("Valor de mercado referencial menor: verificar precios y compradores locales antes de "
                             "cambiar.", lang))
    if c["aptitud_min"] < LOW_APTITUDE_MIN:
        riesgos.append(t("⚠️ Al menos un cultivo tiene baja aptitud para este lugar (ver «¿Qué puedo sembrar aquí?»).",
                         lang))
    riesgos += list(dict.fromkeys(cr.note(lang) for cr in crops))      # una vez por cultivo

    vacios = [
        t("NASA POWER tiene celdas de ~50 km; la temperatura se corrigió por altitud con SRTM, pero en quebradas el "
          "microclima puede diferir. Validar con estación SENAMHI o un termómetro en campo.", lang),
        t("Coeficientes de cultivo, rangos de temperatura y fechas de siembra son referenciales; varían según "
          "variedad.", lang),
        t("No se conocen precios actuales ni acceso a mercados: el puntaje de ingresos es indicativo.", lang),
    ]
    if inputs.soil_from_satellite:
        vacios.append(t("El tipo de suelo es una estimación de SoilGrids (250 m): confírmelo con la prueba de la bolita "
                        "o un análisis de suelo.", lang))
    if inputs.salt != "baja":
        vacios.append(t("La salinidad real requiere un análisis de suelo y agua (conductividad eléctrica).", lang))
    return {"por_que": por_que, "evidencia": evidencia, "beneficios": beneficios, "riesgos": riesgos, "vacios": vacios}


# --- RC-14 Mensaje para WhatsApp ---------------------------------------------------------------------------------

WHATSAPP_TOP = 3
WHATSAPP_MIN_APTITUDE = 40
WHATSAPP_MAX_BENEFITS = 3


def whatsapp_message(place_name: str, table: pd.DataFrame, results: list[RotationResult], clim: pd.DataFrame,
                     p90: float, inputs: FarmInputs, lang: str) -> str:
    """RC-14: el resumen para WhatsApp en `lang`. `results` es la salida de auto_rotations ([Actual, A, B]).

    WhatsApp marca la negrita con un solo asterisco: los `**…**` de los beneficios se pasan a `*…*`.
    """
    from .crops import get
    from .i18n import month, t
    lines = [f"🌱 *RotaSat* — {place_name}", "", t("Cultivos más aptos para su chacra:", lang)]
    top = table[table["aptitud"] >= WHATSAPP_MIN_APTITUDE].head(WHATSAPP_TOP)
    lines += [f"• {get(r.id).name(lang)}: {t('sembrar en', lang)} {month(int(r.mes), lang)}" for r in top.itertuples()]
    current = results[0]
    lines += ["", t("Su rotación actual obtiene *{total:.0f}/100*.", lang, total=current.total)]
    others = results[1:]
    best = max(others, key=lambda r: r.total) if others else None   # max() se queda con A en un empate
    if best is not None and best.total > current.total:
        lines.append(t("La opción *{op}* obtiene *{total:.0f}/100*.", lang, op=rotation_name(best, lang),
                       total=best.total))
        benefits = explain_rotation(best, current, clim, p90, inputs, lang)["beneficios"][:WHATSAPP_MAX_BENEFITS]
        if benefits:
            lines.append(t("¿Por qué?", lang))
            lines += [f"• {x.replace('**', '*')}" for x in benefits]
    else:
        lines.append(t("Su rotación actual ya es la mejor de las comparadas. ¡Bien hecho!", lang))
    lines += ["", t("⚠️ Orientación con datos satelitales de la NASA. Converse con su técnico agrario antes de decidir.",
                    lang)]
    return "\n".join(lines)


# --- RC-15 Resumen del clima en 4 frases -------------------------------------------------------------------------

LITTLE_RAIN_MM = 150
RAINY_MONTHS = 4
SEASON_START = 7                # para ordenar los meses lluviosos, el año se cuenta desde julio


def climate_summary(clim: pd.DataFrame, lang: str) -> list[str]:
    """RC-15: las frases de lluvia, temperatura, heladas y evaporación (la última se omite si la lluvia es 0)."""
    from .i18n import month, t
    total = float(clim["lluvia"].sum())
    if total < LITTLE_RAIN_MM:
        out = [t("🌧️ **Casi no llueve**: {total:,.0f} mm al año. Aquí los cultivos dependen del riego.", lang,
                 total=total)]
    else:
        wettest = clim["lluvia"].sort_values(ascending=False, kind="stable").index[:RAINY_MONTHS]
        ordered = sorted(wettest, key=lambda m: (m - SEASON_START) % 12)
        out = [t("🌧️ Llueven **{total:,.0f} mm al año**, sobre todo en {top}.", lang, total=total,
                 top=_join_list([month(int(m), lang) for m in ordered], lang))]
    mc, mf = int(clim["t_max"].idxmax()), int(clim["t_min"].idxmin())
    out.append(t("🌡️ El mes más caluroso es **{mes_calor}** (máxima media de {tx:.0f} °C) y el más frío es "
                 "**{mes_frio}** (mínima media de {tn:.0f} °C).", lang, mes_calor=month(mc, lang),
                 tx=clim.loc[mc, "t_max"], mes_frio=month(mf, lang), tn=clim.loc[mf, "t_min"]))
    h = float(clim["dias_helada"].sum())
    if h >= 1:
        out.append(t("❄️ Hay riesgo de helada unos **{h:.0f} días al año**, sobre todo en **{mh}**.", lang, h=h,
                     mh=month(int(clim["dias_helada"].idxmax()), lang)))
    else:
        out.append(t("❄️ Prácticamente **no hay heladas**.", lang))
    if total > 0:
        et0 = float(clim["et0"].sum())
        out.append(t("💨 El sol y el viento evaporan **{et0:,.0f} mm al año**: {ratio:.1f} veces lo que llueve.", lang,
                     et0=et0, ratio=et0 / total))
    return out


# --- Series por año (RF-55) y humedad del suelo (RC-17) ----------------------------------------------------------

TREND_EARLY = (2005, 2009)      # RF-55: se compara 2020–2024 con 2005–2009
TREND_LATE = (2020, 2024)


def yearly_climate(daily: pd.DataFrame, p90: float) -> pd.DataFrame:
    """RF-55: por año (índice), con los datos diarios YA corregidos (RC-02): máxima media (°C), días con riesgo de
    helada (mínima ≤ 2 °C) y días de calor extremo (máxima ≥ P90 del lugar)."""
    year = daily.index.year
    out = pd.DataFrame({
        "t_max": daily["t_max"].groupby(year).mean(),
        "dias_helada": (daily["t_min"] <= FROST_T).groupby(year).sum(),
        "dias_calor": (daily["t_max"] >= p90).groupby(year).sum(),
    })
    out.index.name = "anio"
    return out


def tmax_change(yearly: pd.DataFrame) -> float:
    """RF-55: máxima media de 2020–2024 menos la de 2005–2009 (°C)."""
    early = yearly.loc[TREND_EARLY[0]:TREND_EARLY[1], "t_max"].mean()
    late = yearly.loc[TREND_LATE[0]:TREND_LATE[1], "t_max"].mean()
    return float(late - early)


def soil_moisture_monthly(data: dict) -> pd.DataFrame:
    """RC-17: promedio 2005–2024 por mes (1–12) de la humedad de superficie y de raíces, en % (0 seco · 100 saturado).
    `data` es la salida de sources.power.soil_moisture; los meses sin dato se ignoran."""
    df = pd.DataFrame({"mes": [int(m[4:6]) for m in data["months"]],
                       "superficie": data["surface"], "raices": data["root"]}, dtype="float64")
    out = df.groupby("mes")[["superficie", "raices"]].mean().reindex(range(1, 13)) * 100
    out.index.name = "mes"
    return out


# --- RC-16 Verdor del campo (NDVI) -------------------------------------------------------------------------------

NDVI_SCALE = 0.0001             # MODIS y VIIRS entregan el NDVI × 10000
NDVI_VALID_MIN = -2000          # por debajo es «sin dato» (MODIS usa −3000; VIIRS, −15000)
BARE_SOIL_NDVI = 0.2            # filtrado < 0.2: suelo desnudo
NDVI_WINDOW = 3                 # mediana móvil de 3 valores, centrada


def ndvi_series(dates: list[str], raw: list) -> pd.DataFrame:
    """RC-16: tabla por fecha con 'ndvi' (sin los valores sin dato) y 'filtrado' (mediana móvil de 3, centrada; los
    extremos quedan sin valor, como hace pandas por defecto)."""
    s = pd.Series([None if v is None or v < NDVI_VALID_MIN else v * NDVI_SCALE for v in raw],
                  index=pd.to_datetime(dates), dtype="float64").dropna()
    return pd.DataFrame({"ndvi": s, "filtrado": s.rolling(NDVI_WINDOW, center=True).median()})


def bare_months(series: pd.DataFrame) -> list[int]:
    """RC-16: meses del año (1–12, en orden) en que el NDVI filtrado baja de 0.2."""
    low = series.index[series["filtrado"] < BARE_SOIL_NDVI]
    return sorted(set(low.month))


# --- RC-19 Estimación satelital del suelo ------------------------------------------------------------------------

def soil_texture(clay_pct: float, sand_pct: float) -> str:
    """RC-19: arcilla ≥ 40 % arcilloso; ≥ 27 % franco-arcilloso; si no, arena ≥ 70 % arenoso; ≥ 50 % franco-arenoso;
    si no, franco."""
    if clay_pct >= 40:
        return "arcilloso"
    if clay_pct >= 27:
        return "franco-arcilloso"
    if sand_pct >= 70:
        return "arenoso"
    if sand_pct >= 50:
        return "franco-arenoso"
    return "franco"


PH_CLASS_TEXT = {"acido": "ácido", "lig": "ligeramente ácido", "neutro": "neutro", "alcalino": "alcalino"}  # Anexo C


def ph_class(ph: float) -> str:
    """RC-19: menor de 5.5 ácido; menor de 6.5 ligeramente ácido; hasta 7.5 neutro; mayor, alcalino.
    Devuelve la clave del rango de pH de «Mis datos» (Anexo C.3)."""
    if ph < 5.5:
        return "acido"
    if ph < 6.5:
        return "lig"
    if ph <= 7.5:
        return "neutro"
    return "alcalino"


# --- RC-18 Lluvia que alimenta el río Ica ------------------------------------------------------------------------

RIVER_LAT = (-15.2, -13.4)      # caja de la cuenca de Ica (solo en la costa)
RIVER_LON = (-76.4, -75.2)
RIVER_POINT = (-13.15, -75.07)  # punto de referencia en la cuenca alta
RIVER_SEASON_START = 9          # temporada: 1 de setiembre al 30 de abril
RIVER_SEASON_END = 4
RIVER_AVG_FIRST, RIVER_AVG_LAST = 2006, 2024   # promedio: 19 temporadas, de 2005–06 a 2023–24 (año de abril)
RIVER_DRY = -15.0               # % frente al promedio: menor → año seco
RIVER_NORMAL = -5.0             # mayor → normal o húmedo; entre ambos → ligeramente seco


def in_ica_basin(region: str, lat: float, lon: float) -> bool:
    """RC-18: el río se muestra solo en la costa y dentro de la caja de la cuenca de Ica."""
    return (region == "costa" and RIVER_LAT[0] <= lat <= RIVER_LAT[1]
            and RIVER_LON[0] <= lon <= RIVER_LON[1])


def last_river_season(today) -> int:
    """Año (de abril) de la última temporada: la que terminó en abril de este año si ya es mayo o después; si no, la
    del año anterior."""
    return today.year if today.month >= RIVER_SEASON_END + 1 else today.year - 1


def river_seasons(dates: list[str], rain: list, last: int) -> pd.Series:
    """Lluvia de cada temporada (setiembre a abril), indexada por el año en que termina, de 2006 a `last`. Los días
    sin dato se ignoran."""
    s = pd.Series(rain, index=pd.to_datetime(dates, format="%Y%m%d"), dtype="float64")
    m = s.index.month
    s = s[(m >= RIVER_SEASON_START) | (m <= RIVER_SEASON_END)]
    end_year = s.index.year + (s.index.month >= RIVER_SEASON_START)
    out = s.groupby(end_year).sum(min_count=0).reindex(range(RIVER_AVG_FIRST, last + 1), fill_value=0.0)
    out.index.name = "temporada"
    return out


@dataclass(frozen=True)
class RiverOutlook:
    season: int                 # año de abril de la última temporada
    total: float                # mm de la última temporada
    average: float              # mm, promedio de 2005–06 a 2023–24
    delta: float                # % frente al promedio
    level: str                  # "seco" | "ligeramente" | "normal"


def river_outlook(seasons: pd.Series) -> RiverOutlook:
    last = int(seasons.index[-1])
    avg = float(seasons.loc[RIVER_AVG_FIRST:RIVER_AVG_LAST].mean())
    total = float(seasons.loc[last])
    delta = (total - avg) / avg * 100
    level = "seco" if delta < RIVER_DRY else "normal" if delta > RIVER_NORMAL else "ligeramente"
    return RiverOutlook(last, total, avg, delta, level)
