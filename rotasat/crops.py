"""Cultivos y sus parámetros: Anexo A del Spec, copiado tal cual.

Estos valores son parte de las reglas de cálculo (RC-08, RC-10, RC-12). No se redondean ni se «mejoran».
El orden de `CROPS` es el del Anexo A e importa: es el orden de entrada de la tabla de aptitud
(RC-09, desempate D-RC09 en Plan.md §6).

Módulo puro: no usa la red ni Streamlit.
"""
from __future__ import annotations

from dataclasses import dataclass

# Orden de texturas usado por RC-08.5 (de más gruesa a más fina). Las claves son los nombres en español (Anexo C.4).
TEXTURES: tuple[str, ...] = ("arenoso", "franco-arenoso", "franco", "franco-arcilloso", "arcilloso")

FALLOW_ID = "descanso"


@dataclass(frozen=True)
class Crop:
    id: str
    name_es: str
    name_en: str
    family: str
    months: int                     # duración del ciclo
    kc: float                       # coeficiente de agua
    t_opt: tuple[float, float]      # temperatura media mensual óptima [o1, o2] (°C)
    t_lim: tuple[float, float]      # temperatura media mensual límite [l1, l2] (°C)
    frost_sens: float               # sensibilidad a heladas, 0–1
    heat_sens: float                # sensibilidad al calor, 0–1
    salt_tol: float                 # tolerancia a la sal, 0–1
    n: int                          # efecto en el nitrógeno del suelo
    cover: float                    # fracción del suelo que cubre, 0–1
    market: int                     # valor de mercado referencial, 0–5
    forage: bool                    # cultivo forrajero
    textures: tuple[str, ...]       # texturas preferidas; vacío = sin preferencia
    ph: tuple[float, float]         # rango de pH
    note_es: str
    note_en: str

    def name(self, lang: str) -> str:
        return self.name_en if lang == "en" else self.name_es

    def note(self, lang: str) -> str:
        return self.note_en if lang == "en" else self.note_es

    @property
    def is_legume(self) -> bool:
        return self.family == "leguminosas"


def _c(id, name_es, name_en, family, months, kc, t_opt, t_lim, frost, heat, salt, n, cover, market, forage,
       textures, ph, note_es, note_en) -> Crop:
    return Crop(id, name_es, name_en, family, months, kc, t_opt, t_lim, frost, heat, salt, n, cover, market, forage,
                tuple(textures), ph, note_es, note_en)


CROPS: tuple[Crop, ...] = (
    _c("algodon", "Algodón", "Cotton", "malváceas", 7, 0.85, (21, 30), (15, 38), 0.6, 0.2, 0.9, -2, 0.6, 3, False,
       ["franco", "franco-arenoso", "franco-arcilloso"], (5.8, 8.0),
       "Muy tolerante a la sal pero consume mucha agua; atención al gusano rosado y picudo.",
       "Very salt-tolerant but uses a lot of water; watch for pink bollworm and boll weevil."),
    _c("maiz", "Maíz amarillo duro", "Yellow maize", "gramíneas", 5, 0.85, (18, 30), (12, 35), 0.8, 0.5, 0.3, -3, 0.6,
       3, True, ["franco", "franco-arenoso", "franco-arcilloso"], (5.5, 7.8),
       "Gran demandante de nitrógeno; el rastrojo sirve de forraje. Sensible a sal.",
       "Heavy nitrogen feeder; the stover can be used as fodder. Salt-sensitive."),
    _c("pallar", "Pallar", "Lima bean (pallar)", "leguminosas", 6, 0.75, (17, 27), (12, 32), 0.7, 0.5, 0.3, 2, 0.7, 4,
       False, ["franco-arenoso", "franco", "arenoso"], (6.0, 8.0),
       "Leguminosa (en Ica con Denominación de Origen): fija nitrógeno y tiene buen precio. Sensible a sal.",
       "Legume (in Ica with Denomination of Origin): fixes nitrogen and fetches a good price. Salt-sensitive."),
    _c("frijol", "Frijol", "Common bean", "leguminosas", 4, 0.75, (16, 25), (10, 30), 0.8, 0.6, 0.2, 2, 0.6, 3, False,
       ["franco", "franco-arenoso"], (5.8, 7.5),
       "Ciclo corto y bajo consumo de agua; fija nitrógeno. Muy sensible a sal.",
       "Short cycle and low water use; fixes nitrogen. Very salt-sensitive."),
    _c("camote", "Camote", "Sweet potato", "convolvuláceas", 5, 0.80, (20, 28), (14, 34), 0.8, 0.3, 0.5, -1, 0.9, 2,
       True, ["arenoso", "franco-arenoso", "franco"], (5.2, 7.5),
       "Cubre muy bien el suelo (menos erosión y evaporación); el follaje es forraje.",
       "Covers the soil very well (less erosion and evaporation); the foliage is fodder."),
    _c("sorgo", "Sorgo", "Sorghum", "gramíneas", 4, 0.75, (22, 32), (14, 38), 0.7, 0.2, 0.7, -2, 0.6, 2, True,
       ["franco", "franco-arcilloso", "arcilloso", "franco-arenoso"], (5.5, 8.5),
       "Tolerante a sequía, calor y sal moderada; buen forraje. Mercado más pequeño.",
       "Tolerates drought, heat and moderate salinity; good fodder. Smaller market."),
    _c("quinua", "Quinua", "Quinoa", "amarantáceas", 5, 0.70, (10, 20), (4, 28), 0.35, 0.6, 0.9, -1, 0.5, 4, False,
       ["franco-arenoso", "franco", "arenoso"], (5.5, 8.5),
       "Tolera helada leve, sequía y sal; precio variable. En costa vigilar mildiu y aves.",
       "Tolerates light frost, drought and salt; variable price. On the coast watch for mildew and birds."),
    _c("papa", "Papa", "Potato", "solanáceas", 6, 0.85, (10, 20), (5, 25), 0.9, 0.5, 0.3, -3, 0.6, 4, False,
       ["franco-arenoso", "franco"], (5.0, 7.0),
       "Base de la alimentación; repetirla multiplica gorgojo de los Andes, nematodos y rancha.",
       "Staple food; repeating it multiplies Andean potato weevil, nematodes and late blight."),
    _c("haba", "Haba", "Faba bean", "leguminosas", 6, 0.80, (10, 20), (5, 26), 0.5, 0.5, 0.4, 3, 0.6, 3, True,
       ["franco", "franco-arcilloso", "arcilloso"], (6.0, 8.0),
       "Fija nitrógeno; tolera heladas leves mejor que la papa.",
       "Fixes nitrogen; tolerates light frost better than potato."),
    _c("tarwi", "Tarwi (chocho)", "Tarwi (Andean lupin)", "leguminosas", 7, 0.70, (10, 20), (5, 25), 0.4, 0.4, 0.4, 3,
       0.6, 4, False, ["franco-arenoso", "arenoso", "franco"], (5.0, 7.0),
       "Leguminosa andina de raíz profunda: fija mucho nitrógeno y aguanta sequía. Requiere desamargado.",
       "Deep-rooted Andean legume: fixes a lot of nitrogen and withstands drought. Needs debittering."),
    _c("cebada", "Cebada", "Barley", "gramíneas", 5, 0.75, (10, 20), (4, 28), 0.3, 0.5, 0.8, -2, 0.7, 2, True,
       ["franco", "franco-arenoso", "franco-arcilloso"], (6.0, 8.5),
       "Rústica y tolerante al frío; grano y forraje.",
       "Hardy and cold-tolerant; grain and fodder."),
    _c("avena", "Avena forrajera", "Forage oats", "gramíneas", 5, 0.80, (10, 22), (4, 28), 0.25, 0.5, 0.5, -2, 0.8, 3,
       True, ["franco", "franco-arcilloso", "franco-arenoso", "arcilloso"], (5.0, 7.5),
       "Buen forraje para ganado lechero; cubre bien el suelo.",
       "Good fodder for dairy cattle; covers the soil well."),
    _c("maiz_amilaceo", "Maíz amiláceo", "Starchy maize", "gramíneas", 7, 0.85, (13, 22), (9, 28), 0.8, 0.4, 0.3, -3,
       0.6, 3, True, ["franco", "franco-arenoso", "franco-arcilloso"], (5.5, 7.5),
       "Ciclo largo: más expuesto a heladas al final de campaña.",
       "Long cycle: more exposed to frost at the end of the season."),
    _c("olluco", "Olluco", "Olluco (ulluco)", "baseláceas", 7, 0.80, (9, 17), (5, 22), 0.6, 0.5, 0.3, -1, 0.6, 3, False,
       ["franco", "franco-arenoso"], (5.0, 7.0),
       "Tubérculo andino de otra familia: rompe el ciclo de plagas de la papa.",
       "Andean tuber from a different family: breaks the potato pest cycle."),
    _c("yuca", "Yuca", "Cassava", "euforbiáceas", 10, 0.80, (22, 30), (16, 36), 0.9, 0.2, 0.3, -1, 0.7, 2, True,
       ["arenoso", "franco-arenoso", "franco"], (4.5, 7.5),
       "Muy rústica y tolera suelos ácidos y pobres; ciclo largo.",
       "Very hardy and tolerates acidic, poor soils; long cycle."),
    _c("arroz", "Arroz", "Rice", "gramíneas", 5, 1.15, (22, 30), (15, 36), 0.9, 0.4, 0.4, -3, 0.8, 3, False,
       ["arcilloso", "franco-arcilloso"], (5.0, 7.5),
       "El cultivo que más agua consume: solo donde el agua sobra.",
       "The most water-demanding crop: only where water is plentiful."),
    _c("mani", "Maní", "Peanut", "leguminosas", 4, 0.75, (22, 30), (16, 35), 0.9, 0.3, 0.4, 2, 0.6, 3, True,
       ["arenoso", "franco-arenoso"], (5.5, 7.5),
       "Leguminosa de clima cálido para suelos sueltos; fija nitrógeno.",
       "Warm-climate legume for loose soils; fixes nitrogen."),
    _c(FALLOW_ID, "Descanso / pasto natural", "Fallow / natural pasture", "descanso", 12, 0.30, (-50, 50), (-60, 60),
       0.0, 0.0, 1.0, 1, 0.5, 0, True, [], (0, 14),
       "Recupera el suelo (como en los laymes), pero no genera ingresos ese año.",
       "Restores the soil (as in the traditional Andean fallow), but earns no income that year."),
)

BY_ID: dict[str, Crop] = {c.id: c for c in CROPS}

# Los 17 cultivos evaluables (RC-09: todos menos «Descanso»), en el orden del Anexo A.
FIELD_CROPS: tuple[Crop, ...] = tuple(c for c in CROPS if c.id != FALLOW_ID)


def get(crop_id: str) -> Crop:
    return BY_ID[crop_id]
