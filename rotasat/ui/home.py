"""Vista Inicio (RF-01 a RF-03). Tarea T15.

Solo se muestran: el botón de idioma arriba a la derecha, el logotipo 🌱, el nombre «Agro Planet», el lema y dos tarjetas
grandes (🗺️ Mi terreno y 🌦️ Clima), cada una con una línea debajo que explica qué hace.
"""
from __future__ import annotations

import streamlit as st

from .common import CLIMA, TERRENO, go, lang_button, tr


def render() -> None:
    lang_button()                     # arriba a la derecha (CSS .st-key-lang_btn), también en el celular
    st.html(f'<div class="rs-home-title"><div class="rs-logo">🌱</div><h1>Agro Planet</h1>'
            f'<p>{tr("Qué sembrar, cuándo y en qué orden, con datos de la NASA")}</p></div>')
    left, right = st.columns(2, gap="large")
    with left:
        st.button(tr("Mi terreno"), icon="🗺️", key="home_terreno", help=tr("Marque su chacra y vea qué sembrar"),
                  width="stretch", on_click=go, args=(TERRENO,))
        st.caption(tr("Marque su chacra en el mapa y vea qué sembrar"))
    with right:
        st.button(tr("Clima"), icon="🌦️", key="home_clima", help=tr("El clima del lugar donde está ahora"),
                  width="stretch", on_click=go, args=(CLIMA,))
        st.caption(tr("Vea el clima del lugar donde está ahora"))
