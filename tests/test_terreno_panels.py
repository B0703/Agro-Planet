"""T17: paneles del terreno (RF-30 a RF-32, RF-34 a RF-36), CA-03 (parte del terreno) y CA-05 desde la interfaz.
AppTest sin red, con los datos guardados en data/cache/. El panel Satélite (RF-33) se prueba en T18."""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rotasat.cache import SourceError

APP = str(Path(__file__).resolve().parent.parent / "app_simple.py")
SITES = {
    "ica": {"lat": -14.13, "lon": -75.7, "kind": "coords", "name": "Pueblo Nuevo, Ica"},
    "chupaca": {"lat": -12.06, "lon": -75.29, "kind": "coords", "name": "Chupaca, Junín"},
    "satipo": {"lat": -11.25, "lon": -74.64, "kind": "coords", "name": "Satipo, Junín"},
}
PANELS = ["clima", "sembrar", "rotaciones", "whatsapp", "datos", "ayuda"]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("ROTASAT_CACHE_DIR", raising=False)
    monkeypatch.setattr("rotasat.sources.http.get_json", lambda *a, **k: (_ for _ in ()).throw(
        SourceError("red", "sin conexión en las pruebas")))


def open_panel(site: str, panel: str, lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP).run(timeout=60)
    at.session_state.view = "terreno"
    at.session_state.lang = lang
    at.session_state.terreno_place = dict(SITES[site])
    at.run(timeout=60)
    next(b for b in at.button if b.key == f"bar_terreno_{panel}").click().run(timeout=120)
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state.panel == panel
    return at


def html(at) -> str:
    return "\n".join(h.proto.body for h in at.get("html"))


def text(at) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption] + [i.value for i in at.info]
    parts += [w.value for w in at.warning] + [e.label for e in at.expander]
    return "\n".join(parts)


# --- CA-03 (terreno): cada panel se abre sin errores, en los 3 lugares y en los 2 idiomas -------------------------

@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("site", list(SITES))
@pytest.mark.parametrize("panel", PANELS)
def test_ca03_panels_open_without_errors(site, panel, lang):
    open_panel(site, panel, lang)


# --- RF-30 Clima -------------------------------------------------------------------------------------------------

def test_clima_panel_summary_calendar_and_sections():
    at = open_panel("ica", "clima")
    assert "🌧️ **Casi no llueve**: 49 mm al año. Aquí los cultivos dependen del riego." in text(at)
    cal = html(at)
    assert cal.count('<th class="rs-cal-row">') == 6                     # 5 filas + humedad de raíces
    assert "❄️ Días con riesgo de helada" in cal and "🟫 Humedad del suelo, raíces (%)" in cal
    assert [e.label for e in at.expander] == ["🌧️ Lluvia y evaporación", "🌡️ Temperatura y heladas",
                                              "🟫 Humedad del suelo", "📈 ¿Está cambiando el clima aquí?",
                                              "💧 ¿Traerá agua el río?", "🔬 Cómo se ajustaron los datos"]
    t = text(at)
    assert "**Fuente de la lluvia:** GPM IMERG → **49 mm al año**." in t
    assert "En la costa el modelo **no ve el riego**" in t
    # st.info muestra el emoji inicial como icono del aviso: el texto llega sin él.
    frost = next(i for i in at.info if "prácticamente no hay heladas" in i.value)
    assert (frost.icon, frost.value) == ("❄️", "En este lugar prácticamente no hay heladas.")
    assert " En la **costa** hay inversión térmica" in t


# --- RF-31 Qué sembrar -------------------------------------------------------------------------------------------

def test_sembrar_counters_top6_and_soil_note():
    at = open_panel("ica", "sembrar")
    assert [(m.label, m.value) for m in at.metric] == [("🟢 Aptos", "3"), ("🟡 Con cuidado", "11"),
                                                      ("🔴 No recomendados", "3")]
    cards = html(at)
    assert cards.count('class="rs-crop"') == 6
    assert "<b>Quinua</b> · sembrar en mayo" in cards and ">76</div>" in cards
    assert any(i.icon == "ℹ️" and i.value.startswith("Aún no indicó su tipo de suelo") for i in at.info)
    table = at.dataframe[0].value
    assert len(table) == 17 and list(table.columns) == ["Cultivo", "Aptitud", "Nivel", "Mejor mes de siembra", "Ciclo",
                                                        "Lluvia cubre", "Riego necesario (m³/ha)", "Factor limitante"]


def test_sembrar_in_english():
    at = open_panel("ica", "sembrar", "en")
    assert "<b>Quinoa</b> · sow in May" in html(at)
    assert list(at.dataframe[0].value.columns)[0] == "Crop"


# --- CA-05 desde la interfaz -------------------------------------------------------------------------------------

def test_ca05_irrigation_from_my_data_updates_what_to_plant():
    at = open_panel("ica", "datos")
    radio = next(r for r in at.radio if r.label == "💧 ¿Tiene riego?")
    assert radio.value == "limitada"                                     # costa: riego limitado por defecto
    radio.set_value("suficiente").run(timeout=120)
    assert at.session_state.overrides[(-14.13, -75.7)] == {"irrigation": "suficiente"}
    next(b for b in at.button if b.key == "bar_terreno_sembrar").click().run(timeout=120)
    cards = html(at)
    quinua = cards[cards.index("<b>Quinua</b>") - 200: cards.index("<b>Quinua</b>") + 200]
    assert ">89</div>" in quinua and "Sin limitaciones importantes" in quinua


# --- RF-35 Mis datos ---------------------------------------------------------------------------------------------

def test_region_change_brings_its_defaults_and_reset_restores():
    at = open_panel("ica", "datos")
    region = next(s for s in at.selectbox if s.label == "Región")
    assert region.value == "costa"
    region.set_value("sierra").run(timeout=120)
    irrigation = next(r for r in at.radio if r.label == "💧 ¿Tiene riego?")
    salt = next(r for r in at.radio if r.label.startswith("🧂"))
    assert (irrigation.value, salt.value) == ("no", "baja")              # RC-07: los de la región nueva
    next(b for b in at.button if b.label == "Volver a los valores detectados").click().run(timeout=120)
    assert at.session_state.overrides[(-14.13, -75.7)] == {}
    assert next(s for s in at.selectbox if s.label == "Región").value == "costa"


def test_priorities_are_saved():
    at = open_panel("ica", "datos")
    slider = next(s for s in at.slider if s.label == "💧 Agua")
    assert slider.value == 3
    slider.set_value(5).run(timeout=120)
    assert at.session_state.overrides[(-14.13, -75.7)]["priorities"] == {"agua": 5}


# --- RF-32 Rotaciones --------------------------------------------------------------------------------------------

def test_rotations_cards_match_annex_b3_and_best_is_recommended():
    at = open_panel("ica", "rotaciones")
    cards = html(at)
    assert len(re.findall(r'<div class="rs-card( rs-top)?">', cards)) == 3
    for total in ("56", "90", "89"):
        assert f'class="rs-card-total">{total}<span>/100' in cards
    top = cards[cards.index("rs-card rs-top"):]
    assert "⭐ Recomendada" in top[:200] and ">A</div>" in top[:300]
    assert [e.label for e in at.expander][1:] == [
        "Actual: Algodón → Maíz amarillo duro → Algodón", "A: Quinua → Avena forrajera → Frijol",
        "B: Algodón → Quinua → Maní"]
    assert "**🤔 Por qué se sugiere**" in text(at)


def test_editing_current_rotation_recalculates():
    at = open_panel("chupaca", "rotaciones")
    first = next(s for s in at.selectbox if s.label == "Campaña 1")
    assert first.value == "papa"
    first.set_value("haba").run(timeout=120)
    assert at.session_state.overrides[(-12.06, -75.29)]["rotation"] == (("haba", 10), ("papa", 10), ("cebada", 12))
    assert any(e.label == "Actual: Haba → Papa → Cebada" for e in at.expander)


# --- RF-34 WhatsApp / RF-36 Ayuda --------------------------------------------------------------------------------

def test_whatsapp_message_and_link():
    at = open_panel("ica", "whatsapp", "en")
    msg = at.code[0].value
    assert msg.startswith("🌱 *RotaSat* — Pueblo Nuevo, Ica") and "Quinoa: sow in May" in msg
    link = at.get("link_button")[0].proto
    assert link.url.startswith("https://wa.me/?text=%F0%9F%8C%B1") and link.label == "Open in WhatsApp"


def test_help_has_four_sections():
    at = open_panel("ica", "ayuda")
    assert [e.label for e in at.expander] == ["🛰️ Datos que usa", "🧮 Cómo se calcula",
                                              "📚 Recursos del reto: qué usamos y por qué", "⚠️ Limitaciones"]
