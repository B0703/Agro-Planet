"""Vista Mi terreno (RF-10 a RF-22). Tareas T15 (cabecera y barra) y T16 (buscador, mapa, línea del lugar y avisos)."""
from __future__ import annotations

import streamlit as st

from . import location, panels_terreno
from .common import TERRENO, header, icon_bar, show_panel, tr

SLOT = "terreno_place"


def render() -> None:
    header(tr("🗺️ Mi terreno"))
    location.search_box(SLOT)
    location.place_map(SLOT)
    has_place = location.get_place(SLOT) is not None
    pc = location.load_climate(SLOT) if has_place else None   # bajo el mapa, con su indicador de espera

    if not has_place:
        # RF-17: aviso para marcar el terreno e iconos deshabilitados.
        st.info(tr("👆 **Marque su terreno** para empezar: escriba su dirección o coordenadas, use su ubicación, o haga "
                   "clic en el mapa."))
    elif pc is not None:
        # RF-18 / RF-21: línea del lugar y, si aplica, aviso de lluvia preliminar.
        location.place_line(SLOT, pc)
        location.rain_notice(SLOT, pc)

    ready = pc is not None              # RF-22: si fallan los datos principales, los iconos quedan deshabilitados
    st.caption(tr("Toque un icono para ver esa información:") if ready
               else tr("Estos iconos se activan al marcar su terreno:"))
    icon_bar(TERRENO, panels_terreno.PANELS, enabled=ready)
    if ready:
        show_panel(panels_terreno.PANELS)
