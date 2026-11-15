"""Vista Clima (RF-40 a RF-45). T15: cabecera y barra de iconos. GPS, búsqueda y resumen: T19."""
from __future__ import annotations

import streamlit as st

from . import panels_clima
from .common import CLIMA, header, icon_bar, show_panel, tr


def render() -> None:
    header(tr("🌦️ Clima de mi ubicación"))
    if st.session_state.clima_place is None:
        return                       # RF-41: pedir la ubicación (T19)
    st.caption(tr("Toque un icono para ver el detalle:"))
    icon_bar(CLIMA, panels_clima.PANELS, enabled=True)
    show_panel(panels_clima.PANELS)
