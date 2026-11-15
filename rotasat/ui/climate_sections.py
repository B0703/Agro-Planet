"""Secciones del clima de un lugar, compartidas por el panel Clima del terreno (RF-30, T17) y los paneles de la vista
Clima (RF-51 a RF-57, T20): resumen (RC-15), calendario de riesgos, lluvia y evaporación, temperatura y heladas,
humedad del suelo (RC-17), tendencia, río Ica (RF-56, RC-18) y «sobre los datos».
"""
from __future__ import annotations

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from .. import agro, climate
from ..cache import SourceError
from ..i18n import month, t
from ..sources import chirps, imerg, power
from .common import lang, tr

CHART = {"displayModeBar": False}
ORANGE, BLUE, RED, GREEN, GREY = "#F28E2B", "#4E79A7", "#E15759", "#59A14F", "#9C9C9C"
YELLOW_RGB, RED_RGB = (255, 243, 176), (215, 48, 31)        # calendario: de amarillo a rojo (RF-51)


def _months(abbr: bool = True) -> list[str]:
    return [month(m, lang(), abbr=abbr) for m in range(1, 13)]


def _plot(fig: go.Figure, height: int = 300) -> None:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, config=CHART, width="stretch")


# --- RC-15 Resumen -----------------------------------------------------------------------------------------------

def summary(pc: climate.PlaceClimate) -> None:
    for line in agro.climate_summary(pc.clim, lang()):
        st.markdown(line)


# --- RF-51 Calendario de riesgos ---------------------------------------------------------------------------------

def soil_moisture(lat: float, lon: float):
    """RC-17 (tabla mensual en %), o None si NASA POWER no respondió."""
    try:
        return agro.soil_moisture_monthly(power.soil_moisture(lat, lon))
    except SourceError:
        return None


def _cell_color(v: float, lo: float, hi: float) -> str:
    f = 0.0 if hi == lo else (v - lo) / (hi - lo)
    r, g, b = (round(a + (c - a) * f) for a, c in zip(YELLOW_RGB, RED_RGB))
    return f"rgb({r},{g},{b})"


def calendar(pc: climate.PlaceClimate, lat: float, lon: float) -> None:
    """Cuadrícula de 12 meses: heladas, calor extremo, temperatura media, lluvia, evaporación y, si hay dato, humedad
    del suelo en la zona de raíces. Valor entero en cada casilla; color de amarillo a rojo dentro de su fila."""
    c = pc.clim
    rows = [("❄️ Días con riesgo de helada", c["dias_helada"]), ("🔥 Días de calor extremo", c["dias_calor"]),
            ("🌡️ Temperatura media (°C)", c["t_media"]), ("🌧️ Lluvia (mm)", c["lluvia"]),
            ("💨 Evaporación (mm)", c["et0"])]
    sm = soil_moisture(lat, lon)
    if sm is not None:
        rows.append(("🟫 Humedad del suelo, raíces (%)", sm["raices"]))
    head = "".join(f"<th>{m}</th>" for m in _months())
    body = []
    for label, s in rows:
        values = [float(s.loc[m]) for m in range(1, 13)]
        lo, hi = min(values), max(values)
        cells = "".join(f'<td style="background:{_cell_color(v, lo, hi)}">{v:.0f}</td>' for v in values)
        body.append(f'<tr><th class="rs-cal-row">{tr(label)}</th>{cells}</tr>')
    st.html(f"""<div class="rs-cal"><table><thead><tr><th></th>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>
<style>
.rs-cal {{ overflow-x: auto; }}
.rs-cal table {{ border-collapse: collapse; width: 100%; font-size: .8rem; }}
.rs-cal th, .rs-cal td {{ border: 1px solid #fff; padding: 4px 3px; text-align: center; color: #222; }}
.rs-cal .rs-cal-row {{ text-align: left; white-space: nowrap; background: transparent; color: inherit; }}
</style></div>""")
    st.caption(tr("Cada casilla es el promedio de ese mes en 20 años. En cada fila, **más rojo = valor más alto**. "
                  "Helada: mínima de 2 °C o menos. Calor extremo: días entre el 10% más caluroso del lugar."))


# --- RF-52 Lluvia y evaporación ----------------------------------------------------------------------------------

def rain_totals(pc: climate.PlaceClimate, lat: float, lon: float) -> list[str]:
    """Totales anuales de los productos de lluvia disponibles en el punto (los nombres de las fuentes no se traducen)."""
    out = [f"NASA POWER {pc.rain_power.sum():,.0f}"]
    series = chirps.cached(lat, lon)
    if series is not None:
        out.append(f"CHIRPS {climate.monthly_rain(series, chirps.YEARS).sum():,.0f}")
    series = imerg.cached(lat, lon)
    if series is not None:
        out.append(f"GPM IMERG {climate.monthly_rain(series, imerg.YEARS).sum():,.0f}")
    return out


def rain(pc: climate.PlaceClimate, lat: float, lon: float) -> None:
    c = pc.clim
    fig = go.Figure()
    fig.add_bar(x=_months(), y=c["lluvia"].tolist(), name=tr("Lluvia"), marker_color=BLUE)
    fig.add_scatter(x=_months(), y=c["et0"].tolist(), name=tr("Evaporación"), mode="lines+markers",
                    line=dict(color=ORANGE, width=3))
    fig.update_yaxes(title_text=tr("mm por mes"))
    _plot(fig)
    st.caption(tr("Cuando la línea naranja (evaporación) está por encima de las barras (lluvia), al suelo le falta agua y "
                  "el cultivo necesita riego o aguantar la sequía."))
    st.markdown(tr("**Fuente de la lluvia:** {fuente} → **{total:,.0f} mm al año**.", fuente=pc.rain_source,
                   total=c["lluvia"].sum()))
    st.caption(tr("Comparación de productos en este punto (mm al año): {comp}. Usamos CHIRPS en sierra y selva "
                  "(calibrado con estaciones) y GPM IMERG en la costa.", comp=" · ".join(rain_totals(pc, lat, lon))))


# --- RF-53 Temperatura y heladas ---------------------------------------------------------------------------------

def temperature(pc: climate.PlaceClimate) -> None:
    c = pc.clim
    fig = go.Figure()
    for col, key, color in (("t_max", "Máxima", RED), ("t_media", "Media", ORANGE), ("t_min", "Mínima", BLUE)):
        fig.add_scatter(x=_months(), y=c[col].tolist(), name=tr(key), mode="lines+markers", line=dict(color=color))
    fig.update_yaxes(title_text="°C")
    _plot(fig)
    if c["dias_helada"].sum() >= 1:
        st.markdown(tr("**❄️ Días con riesgo de helada por mes**"))
        fig = go.Figure()
        fig.add_bar(x=_months(), y=c["dias_helada"].tolist(), name=tr("Mínima de 2 °C o menos"), marker_color=BLUE)
        fig.add_bar(x=_months(), y=c["dias_helada_fuerte"].tolist(), name=tr("Mínima de 0 °C o menos"),
                    marker_color="#1F3A93")
        fig.update_layout(barmode="group")
        fig.update_yaxes(title_text=tr("días"))
        _plot(fig, 260)
    else:
        st.info(tr("❄️ En este lugar prácticamente no hay heladas."))
    mc = int(c["dias_calor"].idxmax())
    st.caption(tr("Calor extremo para este lugar: días con máxima sobre {p90:.1f} °C (el 10% más caluroso). Mes con más "
                  "calor extremo: {mcal}.", p90=pc.p90, mcal=month(mc, lang())))


# --- RF-54 Humedad del suelo -------------------------------------------------------------------------------------

def moisture(lat: float, lon: float, region: str) -> None:
    sm = soil_moisture(lat, lon)
    if sm is None:
        st.warning(tr("No se pudo obtener la humedad del suelo en este momento."))
        return
    fig = go.Figure()
    fig.add_scatter(x=_months(), y=sm["superficie"].tolist(), name=tr("Superficie (0–5 cm)"), mode="lines+markers",
                    line=dict(color=ORANGE))
    fig.add_scatter(x=_months(), y=sm["raices"].tolist(), name=tr("Zona de raíces (0–100 cm)"), mode="lines+markers",
                    line=dict(color=GREEN))
    fig.update_yaxes(title_text=tr("% (0 seco · 100 saturado)"), range=[0, 100])
    _plot(fig)
    surface = sm["superficie"]
    st.markdown(tr("La superficie del suelo está más seca en **{seco}** y más húmeda en **{humedo}**.",
                   seco=month(int(surface.idxmin()), lang()), humedo=month(int(surface.idxmax()), lang())))
    note = tr("Modelo MERRA-2 de NASA POWER (~50 km). Cumple el papel de SMAP y GLDAS sin requerir cuenta. ")
    if region == "costa":
        note += tr("En la costa el modelo **no ve el riego**: úselo solo como referencia.")
    st.caption(note)


# --- RF-55 Tendencia ---------------------------------------------------------------------------------------------

def trend(pc: climate.PlaceClimate, region: str) -> None:
    y = pc.yearly
    years = [str(a) for a in y.index]
    fig = go.Figure()
    fig.add_scatter(x=years, y=y["t_max"].tolist(), mode="lines+markers", line=dict(color=RED), showlegend=False)
    fig.update_layout(title=tr("Temperatura máxima media de cada año (°C)"))
    _plot(fig, 260)
    cold = region in ("sierra", "altoandina")          # heladas en sierra y zona altoandina; calor en costa y selva
    col, title, color = (("dias_helada", "Días con riesgo de helada por año", BLUE) if cold
                         else ("dias_calor", "Días de calor extremo por año", RED))
    fig = go.Figure()
    fig.add_bar(x=years, y=y[col].tolist(), marker_color=color, showlegend=False)
    fig.update_layout(title=tr(title))
    _plot(fig, 240)
    d = agro.tmax_change(y)
    st.markdown(tr("Entre 2005–2009 y 2020–2024 la temperatura máxima media **{direccion} {d_abs:.1f} °C**.",
                   direccion=tr("subió") if d > 0 else tr("bajó"), d_abs=abs(d)))


# --- RF-56 Río Ica (RC-18) --------------------------------------------------------------------------------------

BASIN_NAME = "cuenca alta de Huancavelica (Choclococha)"    # nombre propio: no se traduce (RF-63)
RIVER_LEVEL_TEXT = {"seco": "🔴 **Año seco**: priorizar cultivos de bajo consumo de agua.",
                    "ligeramente": "🟡 **Ligeramente seco**.", "normal": "🟢 **Año normal o húmedo**."}


def _today() -> date:
    return date.today()


def season_label(end_year: int) -> str:
    """Temporada que termina en abril de `end_year`: «2025–26» (igual en los dos idiomas)."""
    return f"{end_year - 1}–{end_year % 100:02d}"


def show_river(region: str, lat: float, lon: float) -> bool:
    return agro.in_ica_basin(region, lat, lon)


def river() -> None:
    """Texto, cifra de la última temporada con su diferencia frente al promedio, semáforo y barras del histórico."""
    st.markdown(tr("El agua del río Ica nace como lluvia en la {cuenca}. Si allá llueve poco, el río trae poco y se "
                   "depende más de los pozos de un acuífero ya sobreexplotado.", cuenca=BASIN_NAME))
    last = agro.last_river_season(_today())
    end = date(last, agro.RIVER_SEASON_END, 30)
    lat, lon = agro.RIVER_POINT
    series = chirps.river_cached(lat, lon, end)
    if series is None:
        try:
            with st.spinner(tr("Calculando la lluvia de la cuenca alta…")):
                series = chirps.river_download(lat, lon, end)
        except SourceError:
            st.warning(tr("No se pudo calcular la lluvia de la cuenca alta en este momento."))
            return
    seasons = agro.river_seasons(series["dates"], series["rain"], last)
    out = agro.river_outlook(seasons)
    st.metric(tr("Temporada {temporada}", temporada=season_label(out.season)), f"{out.total:,.0f} mm",
              delta=tr("{delta:+.0f}% frente al promedio", delta=out.delta))
    text = tr(RIVER_LEVEL_TEXT[out.level])
    {"seco": st.error, "ligeramente": st.warning, "normal": st.success}[out.level](text)
    labels = [season_label(y) for y in seasons.index]
    fig = go.Figure()
    fig.add_bar(x=labels, y=seasons.tolist(), marker_color=BLUE, showlegend=False)
    fig.add_scatter(x=labels, y=[out.average] * len(labels), mode="lines", name=tr("promedio"),
                    line=dict(color=GREY, dash="dash"))
    fig.update_yaxes(title_text=tr("mm (setiembre a abril)"))
    _plot(fig)


# --- RF-57 Sobre los datos ---------------------------------------------------------------------------------------

def about(pc: climate.PlaceClimate) -> None:
    st.markdown(tr("**Temperatura corregida por altitud**"))
    if pc.elev is not None and pc.elev_area is not None:
        text = tr("Los datos de NASA POWER promedian un área de ~50 km cuya altitud media es **{elev_celda:,.0f} m**, "
                  "pero este lugar está a **{elev:,.0f} m** (NASA SRTM). Como la temperatura cambia 6.5 °C por cada "
                  "1,000 m, se corrigió en **{ajuste:+.1f} °C**.", elev_celda=pc.elev_area, elev=pc.elev,
                  ajuste=pc.correction.ajuste_c)
        if pc.correction.coast:
            text += tr(" En la **costa** hay inversión térmica (la capa de nubes del mar): la corrección se aplica "
                       "completa en verano y nada en invierno.")
        st.markdown(text)
    else:
        st.markdown(tr("No se obtuvo la altitud real (SRTM): se usan las temperaturas sin corregir."))
    st.markdown(tr("**Fuentes**"))
    st.markdown(tr("- Temperatura, radiación y humedad del suelo: NASA POWER (2005–2024)\n- Lluvia: {fuente}\n- Altitud "
                   "y pendiente: NASA SRTM (90 m)", fuente=pc.rain_source))
    st.caption(tr("Los satélites promedian áreas grandes: en una quebrada el microclima real puede ser distinto. Conviene "
                  "comparar con una estación del SENAMHI o un termómetro en el campo."))
