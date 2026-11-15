"""T15: enrutador, botón de idioma, cabecera, barra de iconos, panel lateral y vista Inicio (CA-01, RF-01 a RF-03,
RF-10, RF-17, RF-19, RF-20, RF-60, RF-62). Sin red."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rotasat.i18n import t
from rotasat.ui import panels_clima, panels_terreno

APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
# Un lugar ya marcado (Ica está en data/cache/, así que se abre sin red).
ICA = {"lat": -14.13, "lon": -75.7, "kind": "coords", "name": "Pueblo Nuevo, Ica"}


def app() -> AppTest:
    at = AppTest.from_file(APP).run(timeout=30)
    assert not at.exception
    return at


def button(at, key):
    return next(b for b in at.button if b.key == key)


# --- CA-01 / RF-01 Inicio ----------------------------------------------------------------------------------------

def test_ca01_home_has_exactly_two_big_buttons_and_language():
    at = app()
    assert sorted(b.key for b in at.button) == ["home_clima", "home_terreno", "lang_btn"]
    assert [b.label for b in at.button if b.key.startswith("home_")] == ["Mi terreno", "Clima"]
    assert button(at, "lang_btn").label == "🌐 English"
    assert [c.value for c in at.caption] == ["Marque su chacra en el mapa y vea qué sembrar",
                                             "Vea el clima del lugar donde está ahora"]
    html = " ".join(h.proto.body for h in at.get("html"))
    assert "Agro Planet" in html and "Qué sembrar, cuándo y en qué orden, con datos de la NASA" in html
    assert not at.tabs and not at.sidebar.children                        # sin pestañas ni barra lateral


@pytest.mark.parametrize("key,view,title", [("home_terreno", "terreno", "### 🗺️ Mi terreno"),
                                            ("home_clima", "clima", "### 🌦️ Clima de mi ubicación")])
def test_rf03_cards_open_views_and_back_home(key, view, title):
    at = app()
    button(at, key).click().run()
    assert at.session_state.view == view
    assert title in [m.value for m in at.markdown]
    back = button(at, "home_back")
    assert back.label == "Inicio"
    back.click().run()
    assert at.session_state.view == "home"


# --- RF-17 / RF-19 Barra del terreno -----------------------------------------------------------------------------

def test_terreno_bar_disabled_until_place_is_marked():
    at = app()
    button(at, "home_terreno").click().run()
    bar = [b for b in at.button if b.key.startswith("bar_terreno_")]
    assert [b.label for b in bar] == ["Clima", "Qué sembrar", "Rotaciones", "Satélite", "WhatsApp", "Mis datos",
                                      "Ayuda"]
    assert all(b.disabled for b in bar)
    assert "Estos iconos se activan al marcar su terreno:" in [c.value for c in at.caption]


def test_icon_opens_one_panel_at_a_time():
    at = app()
    button(at, "home_terreno").click().run()
    at.session_state.terreno_place = ICA       # el lugar se marca en T16
    at.run()
    bar = [b for b in at.button if b.key.startswith("bar_terreno_")]
    assert not any(b.disabled for b in bar)
    assert "Toque un icono para ver esa información:" in [c.value for c in at.caption]
    button(at, "bar_terreno_rotaciones").click().run()
    assert not at.exception and at.session_state.panel == "rotaciones"
    button(at, "bar_terreno_ayuda").click().run()
    assert at.session_state.panel == "ayuda"                             # reemplaza al anterior


def test_changing_view_closes_the_panel():
    at = app()
    button(at, "home_terreno").click().run()
    at.session_state.terreno_place = ICA
    at.run()
    button(at, "bar_terreno_clima").click().run()
    button(at, "home_back").click().run()
    assert at.session_state.panel is None


# --- RF-60 / RF-62 Idioma ----------------------------------------------------------------------------------------

def test_language_toggle_keeps_view_and_place():
    at = app()
    button(at, "lang_btn").click().run()
    assert button(at, "lang_btn").label == "🌐 Español"
    assert [b.label for b in at.button if b.key.startswith("home_")] == ["My field", "Climate"]
    button(at, "home_terreno").click().run()
    at.session_state.terreno_place = ICA
    at.run()
    assert "### 🗺️ My field" in [m.value for m in at.markdown]
    assert button(at, "home_back").label == "Home"
    button(at, "lang_btn").click().run()                                     # vuelve a español en la misma vista
    assert at.session_state.view == "terreno" and at.session_state.terreno_place == ICA
    assert "### 🗺️ Mi terreno" in [m.value for m in at.markdown]


# --- Textos de las barras: todos en el Anexo C -------------------------------------------------------------------

@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("panels", [panels_terreno.PANELS, panels_clima.PANELS], ids=["terreno", "clima"])
def test_bar_texts_exist_in_annex_c(panels, lang):
    assert len(panels) == 7 and len({p.key for p in panels}) == 7
    for p in panels:
        if p.label:
            t(p.label, lang)
        t(p.title, lang)
        t(p.help, lang)


def test_clima_bar_order():
    assert [p.icon for p in panels_clima.PANELS] == ["📅", "🌧️", "🌡️", "🟫", "📈", "💧", "🔬"]
    assert [p.icon for p in panels_terreno.PANELS] == ["🌦️", "🌱", "🔄", "🛰️", "📱", "⚙️", "ℹ️"]
