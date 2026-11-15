"""Descarga por adelantado los datos de los 7 lugares del Anexo B a data/cache/ (RNF-03, tarea T13).

    python scripts/prefetch.py                  # descarga lo que falte (todo queda en la caché)
    python scripts/prefetch.py --check          # solo revisa qué falta, sin conectarse (sale con 1 si falta algo)
    python scripts/prefetch.py --site Ica       # solo los lugares cuyo nombre contiene «Ica»

Las peticiones van una por una, porque ClimateSERV responde 503 con varias en paralelo. CHIRPS tarda unos 70 s por
lugar e IMERG unos 7 min. Lo que ya está guardado no se vuelve a pedir (cache.get_or_fetch), así que el script se puede
cortar y volver a lanzar. En la costa se descarga IMERG; la app nunca lo descarga sola (Spec §10.2).

Los lugares dentro de la caja de la cuenca de Ica (RC-18) descargan además la lluvia de la cuenca alta (T20), hasta la
última temporada según la fecha de hoy.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rotasat import agro, cache, climate  # noqa: E402
from rotasat.sources import chirps, geocode, http, imerg, ndvi, power, soilgrids, srtm  # noqa: E402

# Anexo B: nombre → (lat, lon).
SITES: dict[str, tuple[float, float]] = {
    "Ica — Valle (Pueblo Nuevo)": (-14.13, -75.7),
    "Junín — Valle del Mantaro (Chupaca)": (-12.06, -75.29),
    "Huancavelica — zona altoandina": (-12.79, -74.97),
    "Ayacucho — Huamanga": (-13.16, -74.22),
    "Apurímac — Andahuaylas": (-13.66, -73.39),
    "Puno — Altiplano (Juliaca)": (-15.5, -70.13),
    "Junín — Selva central (Satipo)": (-11.25, -74.64),
}

# Búsquedas que usan las pruebas de aceptación (CA-06).
SEARCHES = ("Tarma, Junin",)


def _rain(lat: float, lon: float):
    """Lluvia satelital: IMERG en la costa (RC-04) y CHIRPS en el resto. Necesita NASA POWER y SRTM ya guardados."""
    pc = climate.build(lat, lon, start_download=False)
    if pc.correction.coast:
        return "GPM IMERG", lambda: imerg.download(lat, lon)
    return "CHIRPS", lambda: chirps.download(lat, lon)


def _soil(lat: float, lon: float):
    """SoilGrids: si el punto y sus 4 vecinos ya están guardados y ninguno tiene dato (pasa en las ciudades, RC-19), el
    paso está completo: sin red la app mostrará el mismo aviso de «sin dato» que con red."""
    try:
        return soilgrids.estimate(lat, lon)
    except cache.SourceError:
        points = [(0, 0), *soilgrids.NEARBY]
        if all(cache.has(soilgrids.SERVICE, {"lat": round(lat + a, 4), "lon": round(lon + b, 4)}) for a, b in points):
            return None
        raise


def river_basin():
    """RC-18: CHIRPS en el punto de la cuenca alta, de setiembre de 2005 hasta abril de la última temporada."""
    end = date(agro.last_river_season(date.today()), agro.RIVER_SEASON_END, 30)
    return chirps.river_download(*agro.RIVER_POINT, end)


def in_river_box(lat: float, lon: float) -> bool:
    return agro.RIVER_LAT[0] <= lat <= agro.RIVER_LAT[1] and agro.RIVER_LON[0] <= lon <= agro.RIVER_LON[1]


def steps(lat: float, lon: float) -> list[tuple[str, object]]:
    """Pasos de un lugar, en orden: (nombre, función sin argumentos). El de la lluvia depende de los dos primeros."""
    def rain():
        _, fetch = _rain(lat, lon)
        return fetch()

    def rain_name():
        try:
            return _rain(lat, lon)[0]
        except cache.SourceError:
            return "lluvia satelital"

    out = [
        ("NASA POWER (diario)", lambda: power.daily(lat, lon)),
        ("NASA SRTM", lambda: srtm.terrain(lat, lon)),
        ("NASA POWER (humedad del suelo)", lambda: power.soil_moisture(lat, lon)),
        (rain_name, rain),
        ("Nombre del lugar (OpenStreetMap)", lambda: geocode.point_name(lat, lon)),
        ("NDVI MODIS (ORNL)", lambda: ndvi.series(lat, lon, "modis")),
        ("NDVI VIIRS (ORNL)", lambda: ndvi.series(lat, lon, "viirs")),
        ("Suelo (SoilGrids)", lambda: _soil(lat, lon)),
    ]
    if in_river_box(lat, lon):
        out.append(("Lluvia de la cuenca alta del río Ica (CHIRPS)", river_basin))
    return out


def _offline(*_a, **_k):
    raise cache.SourceError("offline", "NotCached")


def run(sites: dict[str, tuple[float, float]], check: bool = False, out=print, searches=()) -> int:
    """Descarga (o, con `check`, solo revisa sin red) los lugares. Devuelve cuántos pasos faltan o fallaron."""
    real_get = http.get_json
    if check:
        http.get_json = _offline          # cualquier intento de ir a la red cuenta como «falta»
    try:
        return _run(sites, check, out, searches)
    finally:
        http.get_json = real_get


def _run(sites, check, out, searches=()) -> int:
    groups = [(f"{name} ({lat}, {lon})", steps(lat, lon)) for name, (lat, lon) in sites.items()]
    if searches:
        groups.append(("Búsquedas de ejemplo (OpenStreetMap)",
                       [(f"«{q}»", lambda q=q: geocode.search(q)) for q in searches]))
    missing = 0
    for title, group in groups:
        out(title)
        for label, fn in group:
            label = label() if callable(label) else label
            t0 = time.monotonic()
            try:
                fn()
            except cache.SourceError as e:
                missing += 1
                out(f"  ✗ {label}: {'falta en la caché' if check else f'{e.service}: {e.error_name}'}")
                continue
            out(f"  ✓ {label}" + ("" if check else f" ({time.monotonic() - t0:.0f} s)"))
    return missing


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="solo revisar la caché, sin conectarse")
    ap.add_argument("--site", help="solo los lugares cuyo nombre contiene este texto")
    args = ap.parse_args(argv)
    sites = {k: v for k, v in SITES.items() if not args.site or args.site.lower() in k.lower()}
    if not sites:
        print(f"Ningún lugar coincide con {args.site!r}.")
        return 2
    missing = run(sites, check=args.check, searches=() if args.site else SEARCHES)
    print(f"\n{'Todo guardado.' if not missing else f'Faltan o fallaron {missing} pasos.'} Caché: {cache.cache_dir()}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
