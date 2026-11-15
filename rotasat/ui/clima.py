"""Vista Clima (RF-40 a RF-45). T15: cabecera y barra. T19: pedido de GPS al entrar, plazo de 15 s, paso a escribir la
ubicación, cifras y resumen del lugar, y los botones de RF-44. El contenido de los paneles llega en T20.

El lugar del Clima (`clima_place`) es independiente del de Mi terreno (RF-45).
"""
from __future__ import annotations

import streamlit as st

from . import climate_sections as cs
from . import location, panels_clima
from .common import CLIMA, TERRENO, go, header, icon_bar, show_panel, tr

SLOT = "clima_place"
TYPING = f"{SLOT}_typing"          # el usuario tocó «Cambiar de lugar»: se escribe, sin pedir el GPS otra vez


def _on_entry() -> None:
    """RF-41 / RF-45: al entrar sin lugar se pide la ubicación del dispositivo; con lugar se reutiliza."""
    if st.session_state.get("entered") != CLIMA:
        return
    st.session_state.entered = None
    if location.get_place(SLOT) is None and not location.gps_pending(SLOT):
        st.session_state[TYPING] = False
        location.start_gps(SLOT)


def _change_place() -> None:
    st.session_state[SLOT] = None
    st.session_state[TYPING] = True
    st.session_state.panel = None


def _to_terreno() -> None:
    """RF-44: lleva este mismo lugar (con su nombre y la forma en que se eligió) a Mi terreno."""
    st.session_state.terreno_place = dict(location.get_place(SLOT))
    go(TERRENO)


def _ask_place() -> None:
    if location.gps_pending(SLOT):
        # RF-41: aviso de espera y, debajo, el buscador.
        location.gps(SLOT)
        st.markdown(tr("¿No aparece el permiso o prefiere otro lugar? Escríbalo aquí:"))
    else:
        # RF-42: el motivo («… Escriba su ubicación.») y el buscador.
        location.gps(SLOT)
        st.markdown(tr("**¿De qué lugar quiere ver el clima?**"))
    location.search_box(SLOT, show_gps=False)


def _metrics(pc) -> None:
    """RF-43: lluvia al año, temperatura media y días con riesgo de helada."""
    c = pc.clim
    a, b, d = st.columns(3)
    a.metric(tr("🌧️ Lluvia al año"), f"{c['lluvia'].sum():,.0f} mm")
    b.metric(tr("🌡️ Temperatura media"), f"{c['t_media'].mean():.1f} °C")
    d.metric(tr("❄️ Días con riesgo de helada"), tr("{dias:.0f} al año", dias=c["dias_helada"].sum()))


def render() -> None:
    header(tr("🌦️ Clima de mi ubicación"))
    _on_entry()
    if location.get_place(SLOT) is None:
        _ask_place()
        if location.get_place(SLOT) is not None:    # el buscador acaba de fijar el lugar: se dibuja la vista con él
            st.rerun()
        return
    pc = location.load_climate(SLOT)
    if pc is None:                       # RF-22: error y «Reintentar» ya mostrados
        st.button(tr("Cambiar de lugar"), icon="✏️", key="clima_change", on_click=_change_place)
        return
    location.place_line(SLOT, pc)
    location.rain_notice(SLOT, pc)
    _metrics(pc)
    cs.summary(pc)
    st.caption(tr("Toque un icono para ver el detalle:"))
    icon_bar(CLIMA, panels_clima.PANELS, enabled=True)
    left, right = st.columns(2)
    left.button(tr("Ver qué puedo sembrar aquí"), icon="🌱", key="clima_to_terreno", on_click=_to_terreno,
                width="stretch")
    right.button(tr("Cambiar de lugar"), icon="✏️", key="clima_change", on_click=_change_place, width="stretch")
    show_panel(panels_clima.PANELS)
