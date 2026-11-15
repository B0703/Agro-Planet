"""Piezas comunes de la interfaz (Plan.md §2): estado de la sesión, CSS, botón de idioma, cabecera, barra de iconos y
panel lateral. Tarea T15 (RF-10, RF-19, RF-20, RF-60, RF-62, RNF-06, RNF-11).

Todo texto visible pasa por `i18n.t()` con la clave en español del Anexo C.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import streamlit as st

from ..i18n import other_lang, t

HOME, TERRENO, CLIMA = "home", "terreno", "clima"
PANEL_WIDTH = 640               # RF-20 (en pantallas angostas el panel se encoge solo)
MAX_WIDTH = 1000                # RNF-11

# Estado de la sesión (Plan.md §6). Nada se guarda entre sesiones (RNF-10).
DEFAULTS = {"view": HOME, "lang": "es", "panel": None, "terreno_place": None, "clima_place": None}


def init_state() -> None:
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    st.session_state.setdefault("overrides", {})


def lang() -> str:
    return st.session_state.lang


def tr(es: str, **values) -> str:
    """t() con el idioma de la sesión."""
    return t(es, lang(), **values)


def go(view: str) -> None:
    """Cambia de vista y cierra el panel abierto (RF-03). `entered` avisa a la vista que se acaba de entrar a ella
    (Clima la usa para pedir la ubicación al entrar, RF-41); cambiar de idioma no la marca (RF-62)."""
    st.session_state.view = view
    st.session_state.panel = None
    st.session_state.entered = view


def _toggle_lang() -> None:
    # RF-62: solo cambia el idioma; la vista, los lugares y las respuestas quedan como estaban.
    st.session_state.lang = other_lang(st.session_state.lang)


# --- CSS ---------------------------------------------------------------------------------------------------------

CSS = f"""
<style>
[data-testid="stMainBlockContainer"] {{ max-width: {MAX_WIDTH}px; padding-left: 1rem; padding-right: 1rem; }}
.st-key-home_terreno button, .st-key-home_clima button {{ min-height: 200px; width: 100%; }}
.st-key-home_terreno button span[data-has-shortcut], .st-key-home_clima button span[data-has-shortcut] {{
  flex-direction: column; align-items: center; gap: .6rem;
}}
.st-key-home_terreno button span:has(> [data-testid="stIconEmoji"]),
.st-key-home_clima button span:has(> [data-testid="stIconEmoji"]) {{ width: auto; height: auto; }}
.st-key-home_terreno [data-testid="stIconEmoji"], .st-key-home_clima [data-testid="stIconEmoji"] {{
  font-size: 3.5rem; line-height: 1.1;
}}
.st-key-home_terreno button p, .st-key-home_clima button p {{ font-size: 1.5rem; font-weight: 600; }}
.st-key-lang_btn {{ align-self: flex-end; margin-left: auto; }}
.rs-home-title {{ text-align: center; }}
.rs-home-title .rs-logo {{ font-size: 4rem; line-height: 1; }}
[class*="st-key-bar_"] button {{ min-height: 3.2rem; padding-left: .35rem; padding-right: .35rem; }}
[class*="st-key-bar_"] button p {{ word-break: normal; overflow-wrap: normal; hyphens: none; }}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


# --- Botón de idioma y cabecera ----------------------------------------------------------------------------------

def lang_button(key: str = "lang_btn") -> None:
    """RF-60: 🌐 con el nombre del OTRO idioma («English» / «Español»)."""
    st.button(f"🌐 {tr('English')}", key=key, help=tr("Switch the page to English"), on_click=_toggle_lang)


def header(title: str) -> None:
    """RF-10 / RF-40: «⬅️ Inicio», el título de la vista y el botón de idioma a la derecha."""
    left, mid, right = st.columns([1.2, 4, 1.2], vertical_alignment="center")
    with left:
        st.button(tr("Inicio"), icon="⬅️", key="home_back", help=tr("Volver a la pantalla de inicio"),
                  on_click=go, args=(HOME,))
    with mid:
        st.markdown(f"### {title}")
    with right:
        lang_button()


# --- Barra de iconos y panel lateral -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Panel:
    """Un icono de la barra y el panel que abre. Los textos son claves del Anexo C, salvo `label_literal`
    (nombres propios como «WhatsApp», que no se traducen: RF-63)."""
    key: str
    icon: str
    label: str | None           # clave del Anexo C de la etiqueta del botón
    title: str                  # clave del título del panel
    help: str                   # clave del texto de ayuda al pasar el cursor (RF-19)
    body: Callable[[], None] | None = None   # dibuja el contenido (T17, T18, T20)
    label_literal: str | None = None

    def label_text(self) -> str:
        return self.label_literal if self.label_literal else tr(self.label)


def _open(key: str) -> None:
    st.session_state.panel = key


def _close() -> None:
    st.session_state.panel = None


def icon_bar(view: str, panels: list[Panel], enabled: bool) -> None:
    """RF-19 / RF-17: los botones en orden, con icono y etiqueta; deshabilitados si aún no hay lugar.
    En el celular las columnas se apilan (RNF-06)."""
    cols = st.columns(len(panels))
    for col, p in zip(cols, panels):
        with col:
            st.button(p.label_text(), icon=p.icon, key=f"bar_{view}_{p.key}", help=tr(p.help), disabled=not enabled,
                      width="stretch", wrap=True, on_click=_open, args=(p.key,))


def show_panel(panels: list[Panel]) -> None:
    """RF-20: si hay un panel pedido, se abre como cajón modal a la derecha (640 px). Se cierra con la ✕, con Esc o
    tocando fuera (on_dismiss), y solo hay uno abierto a la vez (un único `panel` en la sesión)."""
    key = st.session_state.panel
    panel = next((p for p in panels if p.key == key), None)
    if panel is None:
        st.session_state.panel = None
        return

    def body():
        if panel.body is not None:
            panel.body()

    st.dialog(tr(panel.title), width=PANEL_WIDTH, position="right", on_dismiss=_close)(body)()
