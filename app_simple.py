"""Agro Planet: entrada de Streamlit (specs/Plan.md §2). Enrutador de vistas: Inicio / Mi terreno / Clima (T15)."""
import streamlit as st

from rotasat.ui import clima, common, home, terreno

st.set_page_config(page_title="Agro Planet", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

common.init_state()
common.inject_css()

VIEWS = {common.HOME: home.render, common.TERRENO: terreno.render, common.CLIMA: clima.render}
VIEWS.get(st.session_state.view, home.render)()
