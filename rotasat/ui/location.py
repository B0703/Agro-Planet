"""Elegir y mostrar un lugar: buscador, GPS, mapa, línea del lugar, carga de datos y aviso de lluvia preliminar.
Tarea T16 (RF-11 a RF-18, RF-21, RF-22). Lo usan Mi terreno y, en T19, Clima; cada vista guarda su lugar en su propia
clave de sesión (`slot`), así los dos lugares son independientes (RF-45).

Un lugar en la sesión es {'lat', 'lon', 'kind', 'name'}: `kind` es place.GPS / CLICK / COORDS / SEARCH y `name` el
nombre devuelto por el geocodificador (o None). El texto que se muestra se arma en cada ejecución con place.label(),
así cambia con el idioma (RF-16).
"""
from __future__ import annotations

import time

import folium
import streamlit as st
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

from .. import climate, place
from ..cache import SourceError
from ..i18n import gps_error, vocab
from ..sources import chirps, geocode
from .common import lang, tr

# RF-12: imagen satelital de Esri con nombres de lugares encima. Las teselas las pide el navegador (RNF-02: excepción).
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/{}/MapServer/tile/{{z}}/{{y}}/{{x}}"
ESRI_IMAGERY = ESRI.format("World_Imagery")
ESRI_LABELS = ESRI.format("Reference/World_Boundaries_and_Places")
MAP_HEIGHT = 370
PERU_CENTER, PERU_ZOOM = (-9.5, -75.0), 5
PLACE_ZOOM = 14
MARK_COLOR = "#FFD400"          # círculo amarillo sobre el terreno
POLL_SECONDS = 6                # RF-21
GPS_TIMEOUT = 15                # s sin respuesta del navegador → «tardó demasiado» (RF-42)

# Códigos de error de navigator.geolocation (streamlit_js_eval) → motivo del Anexo C.3.
GEO_ERRORS = {0: "no_soportado", 1: "denegado", 2: "no_disponible", 3: "tiempo"}


def _k(slot: str, name: str) -> str:
    return f"{slot}_{name}"


# --- Fijar el lugar ----------------------------------------------------------------------------------------------

def set_place(slot: str, lat: float, lon: float, kind: str, name: str | None = None) -> None:
    """Guarda el lugar (redondeado, RF-14). Para clic, coordenadas y GPS busca el nombre del punto (RC-20); si el
    servicio falla, el lugar queda sin nombre y RF-16 usa el texto de respaldo."""
    lat, lon = place.round_point(lat, lon)
    if name is None and kind != place.SEARCH:
        try:
            name = geocode.point_name(lat, lon)
        except SourceError:
            name = None
    st.session_state[slot] = {"lat": lat, "lon": lon, "kind": kind, "name": name}
    st.session_state[_k(slot, "choices")] = None
    st.session_state[_k(slot, "gps_error")] = None
    st.session_state.panel = None


def get_place(slot: str) -> dict | None:
    return st.session_state.get(slot)


def place_label(slot: str) -> str:
    p = get_place(slot)
    return place.label(p["kind"], p["name"], p["lat"], p["lon"], lang())


# --- Buscador (RF-11, RF-15) -------------------------------------------------------------------------------------

def _search(slot: str, text: str) -> None:
    if not text.strip():
        return
    try:
        with st.spinner(tr("Buscando…")):
            found = geocode.search(text)
    except SourceError:
        st.warning(tr("El buscador no respondió. Pruebe otra vez, escriba coordenadas o haga clic en el mapa."))
        return
    if not found:
        st.warning(tr("No encontramos ese lugar. Pruebe con el nombre del distrito o escriba coordenadas."))
    elif len(found) == 1:
        r = found[0]
        set_place(slot, r["lat"], r["lon"], place.SEARCH if r["name"] else place.COORDS, r["name"])
    else:
        st.session_state[_k(slot, "choices")] = found


def _choose(slot: str, r: dict) -> None:
    set_place(slot, r["lat"], r["lon"], place.SEARCH, r["name"])


def search_box(slot: str, show_gps: bool = True) -> None:
    """Campo de texto, «🔍 Buscar» y «📍 Mi ubicación» en una fila. Enter envía la búsqueda (formulario).
    Con `show_gps=False` el estado del GPS (aviso de espera o motivo del fallo) lo dibuja quien llama, con gps()."""
    left, right = st.columns([5, 1.5], vertical_alignment="bottom")
    with left:
        with st.form(_k(slot, "search"), border=False, enter_to_submit=True):
            c1, c2 = st.columns([4, 1.3], vertical_alignment="bottom")
            text = c1.text_input(tr("Dirección, pueblo o coordenadas"), key=_k(slot, "q"),
                                 placeholder=tr("Dirección o pueblo…  o coordenadas: -14.13, -75.70"),
                                 label_visibility="collapsed")
            submitted = c2.form_submit_button(tr("Buscar"), icon="🔍", width="stretch")
    with right:
        st.button(tr("Mi ubicación"), icon="📍", key=_k(slot, "gps_btn"), width="stretch",
                  help=tr("Usar la ubicación de este dispositivo (GPS)"), on_click=start_gps, args=(slot,))
    if submitted:
        _search(slot, text)

    choices = st.session_state.get(_k(slot, "choices"))
    if choices:
        st.markdown(tr("¿Cuál de estos lugares es?"))
        for i, r in enumerate(choices):
            st.button(r["name"], key=_k(slot, f"choice_{i}"), on_click=_choose, args=(slot, r))
    if show_gps:
        gps(slot)


# --- GPS (RF-13.4) -----------------------------------------------------------------------------------------------

def start_gps(slot: str) -> None:
    """Pide la ubicación al navegador. Solo se llama al tocar «📍 Mi ubicación» o al entrar a Clima (RNF-09)."""
    st.session_state[_k(slot, "gps_n")] = st.session_state.get(_k(slot, "gps_n"), 0) + 1   # componente nuevo
    st.session_state[_k(slot, "gps")] = True
    st.session_state[_k(slot, "gps_t0")] = time.monotonic()
    st.session_state[_k(slot, "gps_error")] = None


def gps_pending(slot: str) -> bool:
    return bool(st.session_state.get(_k(slot, "gps")))


def gps_failed(slot: str) -> bool:
    return bool(st.session_state.get(_k(slot, "gps_error")))


@st.fragment(run_every=1)
def _gps_watch(slot: str) -> None:
    """RF-42: si el navegador no responde en 15 s, se deja de esperar y se pide escribir la ubicación."""
    if gps_pending(slot) and time.monotonic() - st.session_state.get(_k(slot, "gps_t0"), 0) > GPS_TIMEOUT:
        st.session_state[_k(slot, "gps")] = False
        st.session_state[_k(slot, "gps_error")] = "tiempo"
        st.rerun(scope="app")


def gps(slot: str) -> None:
    """Estado del pedido de ubicación: el motivo del último fallo («… Escriba su ubicación.») o, mientras espera, el
    aviso y el componente que pregunta al navegador."""
    err = st.session_state.get(_k(slot, "gps_error"))
    if err:
        st.warning(gps_error(err, lang()))
    if not gps_pending(slot):
        return
    st.info(tr("📍 Buscando su ubicación… Si el navegador le pregunta, elija **Permitir**."))
    _gps_watch(slot)
    loc = get_geolocation(component_key=_k(slot, f"geo_{st.session_state.get(_k(slot, 'gps_n'), 0)}"))
    if loc is None:
        return                                  # el navegador aún no responde
    st.session_state[_k(slot, "gps")] = False
    coords = loc.get("coords") if isinstance(loc, dict) else None
    if coords and coords.get("latitude") is not None:
        set_place(slot, coords["latitude"], coords["longitude"], place.GPS)
    else:
        code = (loc.get("error") or {}).get("code") if isinstance(loc, dict) else None
        st.session_state[_k(slot, "gps_error")] = GEO_ERRORS.get(code, "no_disponible")
    st.rerun()


# --- Mapa (RF-12, RF-13.1) ---------------------------------------------------------------------------------------

def place_map(slot: str) -> None:
    p = get_place(slot)
    center, zoom = ((p["lat"], p["lon"]), PLACE_ZOOM) if p else (PERU_CENTER, PERU_ZOOM)
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=False)
    folium.TileLayer(tiles=ESRI_IMAGERY, attr="Esri", name="Esri World Imagery").add_to(m)
    folium.TileLayer(tiles=ESRI_LABELS, attr="Esri", name="Esri", overlay=True).add_to(m)
    if p:
        folium.CircleMarker((p["lat"], p["lon"]), radius=12, color=MARK_COLOR, weight=3, fill=True,
                            fill_color=MARK_COLOR, fill_opacity=0.3).add_to(m)
    # La clave cambia con el lugar: así el mapa se vuelve a centrar en el punto nuevo.
    key = _k(slot, f"map_{p['lat']}_{p['lon']}" if p else "map")
    out = st_folium(m, key=key, height=MAP_HEIGHT, use_container_width=True, returned_objects=["last_clicked"])
    click = (out or {}).get("last_clicked")
    if click and click != st.session_state.get(_k(slot, "last_click")):
        st.session_state[_k(slot, "last_click")] = click
        set_place(slot, click["lat"], click["lng"], place.CLICK)
        st.rerun()


# --- Datos del lugar (RF-18, RF-22) ------------------------------------------------------------------------------

def load_climate(slot: str) -> climate.PlaceClimate | None:
    """Clima del lugar, guardado en la sesión por punto. Se vuelve a armar cuando cambia el estado de la descarga de
    CHIRPS (llegó, falló o se reintentó). Si fallan NASA POWER o SRTM: error en lenguaje sencillo y «Reintentar»."""
    p = get_place(slot)
    key = (p["lat"], p["lon"])
    store = st.session_state.setdefault("place_climate", {})
    pc = store.get(key)
    if pc is not None and pc.preliminary and chirps.status(*key) != pc.rain_status:
        pc = None
    if pc is None:
        try:
            with st.spinner(tr("Leyendo 20 años de datos de la NASA para este lugar…")):
                pc = climate.build(*key)
        except SourceError as e:
            st.error(tr("No se pudieron obtener los datos de la NASA ({error}). Revise su internet.",
                        error=e.error_name))
            st.button(tr("Reintentar"), key=_k(slot, "retry"))       # el clic vuelve a ejecutar y reintenta
            return None
        store[key] = pc
    return pc


def region_of(slot: str, pc: climate.PlaceClimate) -> str:
    """Región detectada (RC-06), salvo que el usuario la cambió en «Mis datos» (RC-07)."""
    p = get_place(slot)
    overrides = st.session_state.get("overrides", {}).get((p["lat"], p["lon"]), {})
    return overrides.get("region") or climate.detect(pc, p["lat"]).region


def place_line(slot: str, pc: climate.PlaceClimate) -> None:
    """RF-18: nombre en negrita; debajo región, altitud y coordenadas."""
    p = get_place(slot)
    st.markdown(f"**{place_label(slot)}**")
    line = vocab("region", region_of(slot, pc), lang())
    if pc.elev is not None:
        line += tr(" · {elev:,.0f} m de altitud", elev=pc.elev)
    line += f" · {p['lat']:.4f}, {p['lon']:.4f}"
    st.caption(line)


def rain_notice(slot: str, pc: climate.PlaceClimate) -> None:
    """RF-21 / RF-22: aviso de resultados preliminares mientras llega CHIRPS, o aviso de fallo con reintento."""
    if not pc.preliminary:
        return
    p = get_place(slot)
    if chirps.status(p["lat"], p["lon"]) == chirps.FAILED:
        st.warning(tr("El servicio de lluvia satelital no respondió. Se usa la lluvia de NASA POWER, que **subestima "
                      "la lluvia en sierra y selva**."))
        if st.button(tr("Reintentar lluvia satelital"), key=_k(slot, "rain_retry")):
            chirps.retry(p["lat"], p["lon"])
            st.rerun()
        return
    st.info(tr("⏳ Descargando 20 años de lluvia satelital de este lugar (1 a 5 min). Mientras tanto los resultados "
               "son **preliminares** y se actualizarán solos."))
    _poll(p["lat"], p["lon"])


@st.fragment(run_every=POLL_SECONDS)
def _poll(lat: float, lon: float) -> None:
    """RF-21: cada 6 s mira si terminó la descarga; si terminó y no hay un panel abierto, actualiza la página."""
    if st.session_state.get("panel") is None and chirps.status(lat, lon) in (chirps.READY, chirps.FAILED):
        st.rerun(scope="app")
