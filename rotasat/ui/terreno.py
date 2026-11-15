"""Vista Mi terreno (RF-10 a RF-22). T15: cabecera y barra de iconos. Buscador, mapa y línea del lugar: T16."""
from __future__ import annotations

import streamlit as st

from . import panels_terreno
from .common import TERRENO, header, icon_bar, show_panel, tr


def render() -> None:
    header(tr("🗺️ Mi terreno"))
    has_place = st.session_state.terreno_place is not None
    # RF-17 / RF-18: leyenda e iconos deshabilitados hasta marcar el terreno.
    st.caption(tr("Toque un icono para ver esa información:") if has_place
               else tr("Estos iconos se activan al marcar su terreno:"))
    icon_bar(TERRENO, panels_terreno.PANELS, enabled=has_place)
    if has_place:
        show_panel(panels_terreno.PANELS)
