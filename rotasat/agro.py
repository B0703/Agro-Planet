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
