"""Estimación satelital del suelo con ISRIC SoilGrids v2: arcilla, arena y pH de los primeros 15 cm. RC-19. Tarea T18.

Promedio de las capas 0–5 y 5–15 cm. La arcilla y la arena vienen en g/kg (÷ 10 da %) y el pH × 10. Si el punto no
tiene dato (pasa en los pueblos), se prueba a 0.01° al norte, sur, este y oeste, en ese orden, y se avisa que es un
punto cercano. Cada consulta se guarda en la caché, también la que no tiene dato (RNF-02).
"""
from __future__ import annotations

from .. import agro, cache
from ..cache import SourceError
from . import http

SERVICE = "soilgrids"
URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
PROPERTIES = {"clay": "clay", "sand": "sand", "phh2o": "ph"}
DEPTHS = ("0-5cm", "5-15cm")
NEARBY_STEP = 0.01
NEARBY = ((NEARBY_STEP, 0), (-NEARBY_STEP, 0), (0, NEARBY_STEP), (0, -NEARBY_STEP))   # norte, sur, este, oeste
TIMEOUT = 60


def _parse(raw: dict) -> dict:
    """{'clay': %, 'sand': %, 'ph': valor} con el promedio de las dos capas; None donde no hay dato."""
    out = {"clay": None, "sand": None, "ph": None}
    try:
        for layer in raw["properties"]["layers"]:
            name = PROPERTIES.get(layer["name"])
            if name is None:
                continue
            factor = layer["unit_measure"]["d_factor"]
            vals = [d["values"]["mean"] for d in layer["depths"] if d["label"] in DEPTHS]
            if len(vals) == len(DEPTHS) and None not in vals:
                out[name] = sum(vals) / len(vals) / factor
    except (KeyError, TypeError, ZeroDivisionError) as e:
        raise SourceError(SERVICE, "respuesta inesperada", cause=e) from e
    return out


def query(lat: float, lon: float) -> dict:
    """Arcilla (%), arena (%) y pH de un punto exacto; valores None si SoilGrids no tiene dato ahí."""
    lat, lon = round(lat, 4), round(lon, 4)

    def fetch():
        params = [("lon", lon), ("lat", lat)] + [("property", p) for p in PROPERTIES]
        params += [("depth", d) for d in DEPTHS] + [("value", "mean")]
        return _parse(http.get_json(SERVICE, URL, params, timeout=TIMEOUT))

    return cache.get_or_fetch(SERVICE, {"lat": lat, "lon": lon}, fetch)


def estimate(lat: float, lon: float) -> dict:
    """RC-19: {'texture', 'ph', 'ph_class', 'clay', 'sand', 'nearby'}. Lanza SourceError si el servicio falla o si ni el
    punto ni sus 4 vecinos tienen dato."""
    for dlat, dlon in ((0, 0), *NEARBY):
        d = query(lat + dlat, lon + dlon)
        if None not in (d["clay"], d["sand"], d["ph"]):
            return {"texture": agro.soil_texture(d["clay"], d["sand"]), "ph": d["ph"],
                    "ph_class": agro.ph_class(d["ph"]), "clay": d["clay"], "sand": d["sand"],
                    "nearby": (dlat, dlon) != (0, 0)}
    raise SourceError(SERVICE, "sin datos en este punto ni en los cercanos")
