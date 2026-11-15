"""Paneles de la vista Mi terreno (RF-19, RF-30 a RF-36). T15: la barra. T17: el contenido de Clima, Qué sembrar,
Rotaciones, WhatsApp, Mis datos y Ayuda. El panel Satélite (RF-33) y el botón de SoilGrids de Mis datos llegan en T18.
"""
from __future__ import annotations

from urllib.parse import quote

import plotly.graph_objects as go
import streamlit as st

from .. import agro
from ..crops import CROPS, FALLOW_ID, FIELD_CROPS, get
from ..i18n import PH_VALUES, key_starting, month, options, t, vocab
from . import climate_sections as cs
from . import location
from .common import Panel, lang, tr
from .farm import crop_name, get_farm, level_color, limiting_text, overrides, reset_overrides, set_override

SLOT = "terreno_place"
CHART = {"displayModeBar": False}


def _farm():
    farm = get_farm(SLOT)
    if farm is None:
        st.stop()
    return farm


# --- RF-30 Clima -------------------------------------------------------------------------------------------------

def clima_body() -> None:
    f = _farm()
    lat, lon = f.key
    region = f.inputs.region
    cs.summary(f.pc)
    cs.calendar(f.pc, lat, lon)
    with st.expander(tr("🌧️ Lluvia y evaporación")):
        cs.rain(f.pc, lat, lon)
    with st.expander(tr("🌡️ Temperatura y heladas")):
        cs.temperature(f.pc)
    with st.expander(tr("🟫 Humedad del suelo")):
        cs.moisture(lat, lon, region)
    with st.expander(tr("📈 ¿Está cambiando el clima aquí?")):
        cs.trend(f.pc, region)
    # «¿Traerá agua el río?» (solo en la cuenca de Ica, RC-18): T20.
    with st.expander(tr("🔬 Cómo se ajustaron los datos")):
        cs.about(f.pc)


# --- RF-31 Qué sembrar -------------------------------------------------------------------------------------------

def _preliminary_notice(f) -> None:
    if f.pc.preliminary:
        st.warning(tr("⏳ **Resultado preliminar**: aún no llega la lluvia satelital de este lugar. En sierra y selva "
                      "muchos cultivos aparecerán limitados por agua hasta que llegue."))


def _crop_card(row, lg: str) -> str:
    return (f'<div class="rs-crop"><div class="rs-apt" style="background:{level_color(row.aptitud)}">{row.aptitud}</div>'
            f'<div><b>{crop_name(row.id, lg)}</b> · {tr("sembrar en")} {month(int(row.mes), lg)}<br>'
            f'<span class="rs-lim">{limiting_text(row.limitante, lg)}</span></div></div>')


CROP_CSS = """<style>
.rs-crop { display: flex; gap: .8rem; align-items: center; margin: .35rem 0; }
.rs-apt { min-width: 3rem; height: 3rem; border-radius: .5rem; color: #fff; font-weight: 700; font-size: 1.2rem;
          display: flex; align-items: center; justify-content: center; }
.rs-lim { color: #666; font-size: .9rem; }
</style>"""


def sembrar_body() -> None:
    f = _farm()
    lg = lang()
    _preliminary_notice(f)
    n_ok, n_care, n_no = agro.level_counts(f.table)
    for col, label, n in zip(st.columns(3), ("🟢 Aptos", "🟡 Con cuidado", "🔴 No recomendados"), (n_ok, n_care, n_no)):
        col.metric(tr(label), n)
    st.markdown(tr("##### Los más recomendados para este terreno"))
    st.html(CROP_CSS + "".join(_crop_card(r, lg) for r in f.table.head(6).itertuples()))
    st.caption(tr("El número es la aptitud de 0 a 100 según temperatura, heladas, agua, sal y suelo, sembrando en el "
                  "mejor mes."))
    if f.inputs.texture is None:
        st.info(tr("ℹ️ Aún no indicó su tipo de suelo: la aptitud usa solo clima, agua y sal. Puede indicarlo en "
                   "**Mis datos**."))

    with st.expander(tr("📋 Ver los {n} cultivos evaluados", n=len(f.table))):
        col = {k: vocab("columna", k, lg) for k in options("columna")}
        df = {
            col["Cultivo"]: [crop_name(i, lg) for i in f.table["id"]],
            col["Aptitud"]: f.table["aptitud"].tolist(),
            col["Nivel"]: [tr(x) for x in f.table["nivel"]],
            col["Mejor mes de siembra"]: [month(int(m), lg) for m in f.table["mes"]],
            col["Ciclo"]: [tr("{meses} meses", meses=m) for m in f.table["meses"]],
            col["Lluvia cubre"]: [f"{x:.0f}%" for x in f.table["lluvia_cubre"]],
            col["Riego necesario (m³/ha)"]: [int(x) for x in f.table["riego_m3ha"]],
            col["Factor limitante"]: [limiting_text(x, lg) for x in f.table["limitante"]],
        }
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            col["Aptitud"]: st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d")})

    with st.expander(tr("📆 ¿En qué mes conviene sembrar cada cultivo?")):
        ids = list(f.table["id"])
        crop_id = st.selectbox(tr("Elija un cultivo"), ids, format_func=lambda i: crop_name(i, lg),
                               key=f"sembrar_crop_{f.key}")
        apts = [agro.crop_suitability(get(crop_id), m, f.pc.clim, f.inputs)["aptitud"] for m in range(1, 13)]
        fig = go.Figure(go.Bar(x=[month(m, lg, abbr=True) for m in range(1, 13)], y=[round(a) for a in apts],
                               marker_color=[level_color(a) for a in apts], text=[round(a) for a in apts]))
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10))
        fig.update_yaxes(title_text=tr("Aptitud si siembra ese mes"), range=[0, 100])
        st.plotly_chart(fig, config=CHART, width="stretch")
    st.info(tr("🤝 Es una **orientación**: las variedades locales, el manejo y el mercado pueden cambiar la decisión. "
               "Converse con su técnico agrario."))


# --- RF-32 Rotaciones --------------------------------------------------------------------------------------------

ROTATION_CHOICES = [c.id for c in FIELD_CROPS] + [FALLOW_ID]          # los 17 y «Descanso»
CROP_COLORS = dict(zip([c.id for c in CROPS], [
    "#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#B07AA1", "#EDC948", "#76B7B2", "#FF9DA7", "#9C755F",
    "#BAB0AC", "#D37295", "#8CD17D", "#B6992D", "#499894", "#86BCB6", "#F1CE63", "#A0CBE8", "#C9C9C9"]))


def _set_step(key, i: int, field: int, widget_key: str) -> None:
    rot = [list(step) for step in _farm_inputs_rotation(key)]
    rot[i][field] = st.session_state[widget_key]
    set_override(key, "rotation", tuple(tuple(s) for s in rot))


def _farm_inputs_rotation(key):
    return st.session_state["_rot_current"][key]


def _rotation_editor(f, lg: str) -> None:
    """RF-32.1: tres campañas (cultivo y mes). Por defecto, la rotación típica de la región (RC-07)."""
    st.session_state.setdefault("_rot_current", {})[f.key] = f.inputs.rotation
    current = " → ".join(crop_name(c, lg) for c, _ in f.inputs.rotation)
    with st.expander(tr("✏️ Mi rotación actual: ") + current + tr(" (toque para cambiarla)")):
        for i, (col, (crop_id, sow)) in enumerate(zip(st.columns(3), f.inputs.rotation)):
            with col:
                st.markdown(f"**{tr('Campaña {n}', n=i + 1)}**")
                ck, mk = f"rot_crop_{f.key}_{i}_{crop_id}_{sow}", f"rot_month_{f.key}_{i}_{crop_id}_{sow}"
                st.selectbox(tr("Campaña {n}", n=i + 1), ROTATION_CHOICES, index=ROTATION_CHOICES.index(crop_id),
                             format_func=lambda c: crop_name(c, lg), key=ck, label_visibility="collapsed",
                             on_change=_set_step, args=(f.key, i, 0, ck))
                st.selectbox(tr("Mes de siembra"), list(range(1, 13)), index=sow - 1,
                             format_func=lambda m: month(m, lg), key=mk, on_change=_set_step, args=(f.key, i, 1, mk))


def _cards(results, lg: str) -> None:
    best = max(results, key=lambda r: r.total)
    for col, r in zip(st.columns(len(results)), results):
        top = r is best
        badge = f'<div class="rs-best">{tr("⭐ Recomendada")}</div>' if top else ""
        crops = " → ".join(crop_name(c, lg) for c, _ in r.rotation)
        label = tr("Actual") if r.label == "Actual" else r.label
        col.html(f'<div class="rs-card{" rs-top" if top else ""}">{badge}<div class="rs-card-label">{label}</div>'
                 f'<div class="rs-card-crops">{crops}</div><div class="rs-card-total">{r.total:.0f}<span>/100</span>'
                 f'</div></div>' + CARD_CSS)


CARD_CSS = """<style>
.rs-card { border: 2px solid #ddd; border-radius: .7rem; padding: .7rem; min-height: 9.5rem; }
.rs-card.rs-top { border-color: #2E7D32; }
.rs-best { color: #2E7D32; font-weight: 700; font-size: .85rem; }
.rs-card-label { font-weight: 700; font-size: 1.1rem; }
.rs-card-crops { font-size: .9rem; margin: .3rem 0; }
.rs-card-total { font-size: 1.8rem; font-weight: 700; }
.rs-card-total span { font-size: .9rem; color: #777; }
</style>"""


def _timeline(results, lg: str) -> None:
    """RF-32.3: una fila por rotación y un bloque por cultivo; lo que pasa del mes 36 no se dibuja (§10.1)."""
    fig = go.Figure()
    names = [tr("Actual") if r.label == "Actual" else r.label for r in results]
    shown = set()
    for name, r in zip(names, results):
        for crop_id, start, end in r.evaluation["placed"]:
            stop = min(end, agro.TIMELINE_MONTHS + 1)
            if start > agro.TIMELINE_MONTHS:
                continue
            label = crop_name(crop_id, lg)
            fig.add_bar(y=[name], x=[stop - start], base=[start - 1], orientation="h", name=label,
                        marker_color=CROP_COLORS[crop_id], text=label, textposition="inside",
                        showlegend=label not in shown, hovertemplate=f"{label}<extra></extra>")
            shown.add(label)
    year = tr("año")
    fig.update_layout(barmode="overlay", height=90 + 45 * len(results), margin=dict(l=10, r=10, t=10, b=10),
                      showlegend=False)
    fig.update_xaxes(range=[0, agro.TIMELINE_MONTHS], tickvals=[6, 18, 30],
                     ticktext=[f"{year} {n}" for n in (1, 2, 3)], showgrid=False)
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, config=CHART, width="stretch")


def _criteria_chart(r, lg: str) -> None:
    keys = [k for k in agro.SCORE_KEYS if k in r.scores]
    fig = go.Figure(go.Bar(y=[vocab("criterio", k, lg) for k in keys], x=[r.scores[k] for k in keys],
                           orientation="h", marker_color="#59A14F", text=[f"{r.scores[k]:.0f}" for k in keys]))
    fig.update_layout(height=40 + 32 * len(keys), margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, config=CHART, width="stretch")


EXPLAIN_TITLES = (("por_que", "🤔 Por qué se sugiere"), ("evidencia", "🛰️ Evidencia (datos NASA)"),
                  ("beneficios", "✅ Beneficios frente a la rotación actual"),
                  ("riesgos", "⚠️ Riesgos a revisar con un experto local"), ("vacios", "❓ Vacíos de información"))


def rotaciones_body() -> None:
    f = _farm()
    lg = lang()
    _rotation_editor(f, lg)
    results = f.rotations
    if len(results) < 3:
        st.warning(tr("No se encontraron cultivos aptos suficientes para proponer alternativas en este lugar."))
    _cards(results, lg)
    st.caption(tr("La alternativa A es la mejor para sus prioridades; la B conserva su cultivo principal cuando es apto. "
                  "Puede cambiar sus prioridades en **Mis datos**."))
    st.markdown(tr("##### 📅 Línea de tiempo (3 años)"))
    _timeline(results, lg)
    st.caption(tr("Los huecos son meses con el suelo desnudo."))
    st.markdown(tr("##### 🔍 ¿Por qué? Toque una opción"))
    current = results[0]
    for r in results:
        with st.expander(agro.rotation_name(r, lg)):
            _criteria_chart(r, lg)
            ex = agro.explain_rotation(r, current, f.pc.clim, f.pc.p90, f.inputs, lg)
            for key, title in EXPLAIN_TITLES:
                if ex[key]:
                    st.markdown(f"**{tr(title)}**\n\n" + "\n".join(f"- {x}" for x in ex[key]))
    st.info(tr("🤝 RotaSat **apoya, no reemplaza** la experiencia del agricultor ni la asesoría de un agrónomo."))


# --- RF-34 WhatsApp ----------------------------------------------------------------------------------------------

def whatsapp_body() -> None:
    f = _farm()
    lg = lang()
    name = f.place["name"] or location.place_label(SLOT)
    msg = agro.whatsapp_message(name, f.table, f.rotations, f.pc.clim, f.pc.p90, f.inputs, lg)
    st.markdown(tr("Un resumen sencillo para enviar al agricultor:"))
    st.code(msg, language=None, wrap_lines=True)
    st.link_button(tr("Abrir en WhatsApp"), "https://wa.me/?text=" + quote(msg), icon="📱", width="stretch")


# --- RF-35 Mis datos ---------------------------------------------------------------------------------------------

def _wkey(f, name: str) -> str:
    # La versión cambia con cada respuesta: los controles se vuelven a crear con los valores ya recalculados
    # (por ejemplo, el riego por defecto de la región nueva, RC-07).
    return f"md_{name}_{f.key}_{st.session_state.get('md_ver', 0)}"


def _answer(key, field: str, widget_key: str, transform=None) -> None:
    value = st.session_state[widget_key]
    set_override(key, field, transform(value) if transform else value)
    st.session_state.md_ver = st.session_state.get("md_ver", 0) + 1


def _set_priority(key, crit: str, widget_key: str) -> None:
    pr = dict(overrides(key).get("priorities", {}))
    pr[crit] = st.session_state[widget_key]
    set_override(key, "priorities", pr)
    st.session_state.md_ver = st.session_state.get("md_ver", 0) + 1


def _reset(key) -> None:
    reset_overrides(key)
    st.session_state.md_ver = st.session_state.get("md_ver", 0) + 1


def _ph_key(ph: float | None) -> str:
    return next((k for k, v in PH_VALUES.items() if v == ph), "nose")


def datos_body() -> None:
    f = _farm()
    lg, inp, key = lang(), f.inputs, f.key
    st.info(tr("Estos valores se **dedujeron de la ubicación** con datos satelitales (altitud, lluvia y relieve). "
               "Cámbielos solo si conoce mejor su chacra: sus respuestas mandan."))

    st.markdown(tr("##### 🧭 Zona y agua"))
    regions = options("region")
    k = _wkey(f, "region")
    st.selectbox(tr("Región"), regions, index=regions.index(inp.region), key=k,
                 format_func=lambda r: vocab("region", r, lg) + (t(" (detectada por altitud y lluvia)", lg)
                                                                 if r == f.detected.region else ""),
                 on_change=_answer, args=(key, "region", k))
    slopes = options("pendiente")
    k = _wkey(f, "slope")
    st.radio(tr("⛰️ Pendiente del terreno"), slopes, index=slopes.index(inp.slope_class), key=k, horizontal=True,
             format_func=lambda x: vocab("pendiente", x, lg), on_change=_answer, args=(key, "slope_class", k))
    if f.detected.slope_pct is not None:
        st.caption(tr("El relieve SRTM estima {pendiente:.0f}% de pendiente", pendiente=f.detected.slope_pct))
    irrig = options("riego")
    k = _wkey(f, "irrigation")
    st.radio(tr("💧 ¿Tiene riego?"), irrig, index=irrig.index(inp.irrigation), key=k,
             format_func=lambda x: vocab("riego", x, lg), on_change=_answer, args=(key, "irrigation", k))

    st.markdown(tr("##### 🟫 Suelo"))
    textures = [None] + options("textura")
    k = _wkey(f, "texture")
    st.selectbox(tr("Tipo de suelo"), textures, index=textures.index(inp.texture), key=k,
                 format_func=lambda x: t("No sé", lg) if x is None else vocab("textura", x, lg),
                 on_change=_answer, args=(key, "texture", k))
    with st.expander(tr("❓ ¿Cómo saber mi tipo de suelo? (prueba de la bolita)")):
        st.markdown(tr("Tome un puñado de tierra, humedézcala y amásela:\n1. **No forma bolita**, se desmorona → "
                       "**arenoso**\n2. Forma bolita pero **se rompe** al apretarla → **franco-arenoso**\n3. Forma bolita "
                       "y una **cinta corta** (menos de 2 cm) → **franco**\n4. Forma una **cinta de 2 a 5 cm** → "
                       "**franco-arcilloso**\n5. Forma una **cinta larga**, pegajosa y brillante → **arcilloso**"))
    phs = options("ph")
    k = _wkey(f, "ph")
    st.selectbox(tr("pH (si tiene un análisis de suelo)"), phs, index=phs.index(_ph_key(inp.ph)), key=k,
                 format_func=lambda x: vocab("ph", x, lg), on_change=_answer, args=(key, "ph", k, PH_VALUES.get))
    salts = options("sal")
    k = _wkey(f, "salt")
    st.radio(tr("🧂 ¿Ve costra blanca (salitre) o el agua es salobre?"), salts, index=salts.index(inp.salt), key=k,
             horizontal=True, format_func=lambda x: vocab("sal", x, lg), on_change=_answer, args=(key, "salt", k))
    # «Estimar mi suelo con satélite (SoilGrids)» (RC-19): T18.

    st.markdown(tr("##### 🎯 ¿Qué es más importante para usted?"))
    st.caption(tr("0 = no me importa · 5 = es lo más importante"))
    for crit in agro.DEFAULT_PRIORITIES:
        k = _wkey(f, f"prio_{crit}")
        st.slider(vocab("criterio", crit, lg), 0, 5, inp.priorities[crit], key=k,
                  on_change=_set_priority, args=(key, crit, k))
    st.button(tr("Volver a los valores detectados"), icon="↩️", on_click=_reset, args=(key,), width="stretch")


# --- RF-36 Ayuda -------------------------------------------------------------------------------------------------

# RF-36: título y comienzo del cuerpo de cada plegado (Anexo C [980]–[1037]); el cuerpo completo sale del catálogo.
HELP_SECTIONS = (("🛰️ Datos que usa", "\n| Dato | Para qué |"), ("🧮 Cómo se calcula", "\n- **Aptitud de un cultivo:**"),
                 ("📚 Recursos del reto: qué usamos y por qué", "\n| Recurso | Decisión | Razón |"),
                 ("⚠️ Limitaciones", "\n- Los satélites promedian áreas grandes"))


def ayuda_body() -> None:
    st.markdown(tr("RotaSat convierte 20 años de datos satelitales de la NASA en una recomendación sencilla: **qué "
                   "sembrar, cuándo y en qué orden**."))
    for title, start in HELP_SECTIONS:
        with st.expander(tr(title)):
            st.markdown(tr(key_starting(start)))


# --- Barra (RF-19) -----------------------------------------------------------------------------------------------

# RF-19: en este orden. Cada uno: icono, etiqueta, título del panel y texto de ayuda (Anexo C [1051]–[1065]).
PANELS: list[Panel] = [
    Panel("clima", "🌦️", "Clima", "🌦️ Clima de mi terreno", "Lluvia, temperatura, heladas y riesgos de cada mes",
          body=clima_body),
    Panel("sembrar", "🌱", "Qué sembrar", "🌱 ¿Qué puedo sembrar aquí?", "Cultivos aptos y su mejor mes de siembra",
          body=sembrar_body),
    Panel("rotaciones", "🔄", "Rotaciones", "🔄 Comparar rotaciones", "Su rotación actual frente a 2 alternativas",
          body=rotaciones_body),
    Panel("satelite", "🛰️", "Satélite", "🛰️ ¿Cuándo está pelado el campo?", "Verdor del campo visto desde el satélite"),
    Panel("whatsapp", "📱", None, "📱 Resumen para WhatsApp", "Mensaje sencillo para enviar", label_literal="WhatsApp",
          body=whatsapp_body),
    Panel("datos", "⚙️", "Mis datos", "⚙️ Mis datos: riego, suelo y prioridades", "Riego, suelo y lo que más le importa",
          body=datos_body),
    Panel("ayuda", "ℹ️", "Ayuda", "ℹ️ Cómo funciona RotaSat", "Datos usados, cálculos y limitaciones", body=ayuda_body),
]
