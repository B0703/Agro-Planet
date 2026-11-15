# RotaSat — Plan técnico (Plan.md)

| | |
|---|---|
| **Versión** | 0.1 (borrador para aprobación) |
| **Fecha** | 15 de noviembre de 2026 |
| **Documentos hermanos** | `Spec.md` (qué y por qué) · `task.md` (pasos de trabajo) · `Spec-anexo-C-textos.md` (textos ES/EN) |

Este documento dice **CÓMO** se construye lo que pide `Spec.md`. Cita los códigos `RF`/`RC`/`RNF`/`CA` del Spec.
Si algo de aquí contradice al Spec, manda el Spec.

## 1. Tecnología

| Pieza | Elección | Motivo |
|---|---|---|
| Lenguaje | Python 3.11+ | Es el lenguaje del original (`app_simple.py`, `agro.py`) |
| Interfaz | Streamlit ≥ 1.40 | Es la forma más corta de replicar el original. Los plegados son `st.expander`, los paneles son `st.dialog` y la consulta cada 6 s es `st.fragment(run_every=6)` |
| Mapa | `folium` + `streamlit-folium` | Mapa con imagen Esri y lectura del clic (RF-12, RF-13.1) |
| GPS | `streamlit-js-eval` (`get_geolocation`) | Pide la ubicación del navegador (RF-13.4, RF-41) |
| Gráficos | Plotly | Gráficos interactivos que se pueden traducir |
| Cálculo | `pandas`, `numpy` | Tablas de clima y aptitud |
| HTTP | `requests` con tiempos de espera explícitos | — |
| Pruebas | `pytest` y `streamlit.testing.v1.AppTest` | Pruebas del motor (CA-04, CA-05) y de la interfaz (CA-01 a CA-03 y CA-09) |

## 2. Estructura del proyecto

```
app_simple.py            # Entrada de Streamlit: enrutador de vistas (Inicio / Mi terreno / Clima)
rotasat/
  crops.py               # Anexo A tal cual: parámetros y notas ES/EN
  agro.py                # Motor puro sin red: RC-02, RC-03 y RC-06 a RC-15
  climate.py             # Arma la tabla de clima de un lugar: fuentes + RC-02/03/04
  place.py               # Lugar: coordenadas, nombre (RF-16), región y valores por defecto
  i18n.py                # Catálogo de textos del Anexo C: t(texto_es, idioma, **valores), vocab(), month()
  texts_data.py          # GENERADO por scripts/build_texts.py desde el Anexo C (no editar a mano)
  cache.py               # Caché en disco (RNF-02)
  sources/
    power.py             # NASA POWER, datos diarios y mensuales
    srtm.py              # Altitud del punto y cuadrícula 3×3
    chirps.py            # CHIRPS vía ClimateSERV, con descarga en segundo plano (RC-05)
    imerg.py             # GPM IMERG, que solo se lee de la caché en la costa (RC-04)
    ndvi.py              # MODIS / VIIRS (RC-16)
    soilgrids.py         # Arcilla, arena y pH (RC-19)
    geocode.py           # Nominatim: búsqueda y geocodificación inversa (RC-20)
  ui/
    common.py            # Cabecera, botón de idioma, panel lateral (CSS) y barra de iconos
    home.py · terreno.py · clima.py
    panels_terreno.py    # RF-30 a RF-36
    panels_clima.py      # RF-51 a RF-57
scripts/prefetch.py      # Descarga los 7 lugares del Anexo B (RNF-03)
data/cache/              # Respuestas guardadas; se versiona para la demo sin conexión
tests/
```

**Regla de capas:** `agro.py` y `crops.py` no hacen llamadas a la red ni usan Streamlit. Reciben tablas y devuelven datos y
claves de texto. Así las pruebas del Anexo B corren sin conexión.

## 3. Comandos

```bash
pip install -r requirements.txt
streamlit run app_simple.py            # http://localhost:8501
pytest                                  # todas las pruebas
pytest tests/test_agro.py::test_ica     # una sola prueba
python scripts/prefetch.py              # descarga los 7 lugares de ejemplo a data/cache/
```

## 4. Servicios externos (§7 del Spec)

Ninguno necesita clave (RNF-01). Todas las llamadas pasan por `cache.py`.

| Dato | Servicio | Llamada |
|---|---|---|
| Clima diario + altitud del área | NASA POWER | `GET https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,TOA_SW_DWN&community=AG&latitude={lat}&longitude={lon}&start=20050101&end=20241231&format=JSON`. La altitud del área está en `geometry.coordinates[2]` y el valor `-999` significa que falta el dato |
| Humedad del suelo | NASA POWER | `.../temporal/monthly/point?parameters=GWETTOP,GWETROOT&start=2005&end=2024` |
| Altitud SRTM | OpenTopoData (SRTM 90 m) | `GET https://api.opentopodata.org/v1/srtm90m?locations=lat,lon\|...`: los 9 puntos (RC-06) van en una sola llamada |
| CHIRPS | SERVIR ClimateSERV | `submitDataRequest` (CHIRPS, operación promedio, polígono pequeño alrededor del punto, 2005–2024), luego `getDataRequestProgress` y luego `getDataFromRequest`. Tiempo máximo 300 s |
| GPM IMERG | SERVIR ClimateSERV | Igual que CHIRPS, para 2015–2024. **Solo se lee de la caché** (Spec §10.2); `prefetch.py` lo descarga para Ica |
| NDVI | ORNL DAAC MODIS Web Service | `GET https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?latitude=..&longitude=..&band=250m_16_days_NDVI&startDate=A2023001&endDate=A2024366&kmAboveBelow=0&kmLeftRight=0` (escala ×0.0001). Para VIIRS se usa `VNP13A1` |
| Suelo | ISRIC SoilGrids v2 | `GET https://rest.isric.org/soilgrids/v2.0/properties/query?lon=..&lat=..&property=clay&property=sand&property=phh2o&depth=0-5cm&depth=5-15cm&value=mean`. La arcilla y la arena vienen en g/kg (÷10 da %) y el pH viene ×10 |
| Búsqueda y nombre | Nominatim (OSM) | `/search` con `countrycodes=pe` y luego sin él, `limit=8`, `accept-language=es`; `/reverse`. Se envía un `User-Agent` genérico (`RotaSat/1.0`) y como máximo una llamada por segundo |
| Mapa | Esri | Teselas `World_Imagery` y la capa `Reference/World_Boundaries_and_Places` |

Los identificadores exactos de los conjuntos de datos de ClimateSERV para CHIRPS e IMERG se confirman en la tarea T07.

## 5. Caché (RNF-02)

- Hay un archivo JSON por respuesta en `data/cache/{servicio}/{sha1(parámetros)}.json`. La clave usa las coordenadas
  redondeadas a 4 decimales (RF-14).
- Al leer, primero se mira el disco. Si un servicio falla no se guarda nada y se lanza `SourceError` con un mensaje
  sencillo para el usuario (RNF-05).
- CHIRPS en segundo plano: un `threading.Thread` por lugar, registrado en un diccionario del proceso. Al terminar escribe en
  la caché. La interfaz consulta su estado cada 6 s (RF-21).

## 6. Decisiones de implementación que fija el Spec

- **D-RC09 · Desempates en la tabla de aptitud.** El Spec deja que este Plan fije el orden. Hipótesis: el original arma un
  `DataFrame` con los cultivos en el orden del Anexo A y llama a `sort_values("aptitud", ascending=False)` con el método de
  ordenación por defecto de pandas, que **no es estable**. Eso explica que en el Anexo B.2 de Chupaca salga primero la papa y
  no la quinua. En la tarea T09 se comprueba esta hipótesis contra los 7 lugares del B.2. Si falla, se prueban otras variantes
  (`kind`, orden de entrada) hasta reproducir el B.2 exacto, y aquí se anota cuál quedó.
- **Mejor mes (RC-09):** se ordena por la tupla `(-round(aptitud), -round(min(cobertura,1.5),2), exposición_helada, mes)`.
- **Panel lateral (RF-20):** se usa `st.dialog(width="large")` con CSS que lo fija a la derecha, con 640 px de ancho y 100 %
  en pantallas angostas. Streamlit ya lo cierra con Esc, con la ✕ y con un clic fuera. Solo se abre uno a la vez.
- **Idioma:** se guarda en `st.session_state.lang`. Los textos se piden con `t(clave)` y **nunca** se escriben sueltos en la
  interfaz. Las claves del catálogo salen del Anexo C, y una prueba verifica que todas existen en ES y EN.
- **Estado de la sesión:** `view`, `lang`, `terreno_place`, `clima_place` y `overrides[(lat,lon)]`. No se guarda nada entre
  sesiones (RNF-10).

## 7. Estrategia de pruebas

| Nivel | Qué | Cómo |
|---|---|---|
| Unidad | Cada regla RC con casos a mano | `tests/test_agro.py` y `tests/test_climate.py` |
| Referencia | CA-04 y CA-05: los 7 lugares contra el Anexo B, con tolerancia ±1 | `tests/test_annex_b.py`, que lee de `data/cache/` (sin red) |
| Textos | Todas las claves del Anexo C en ES y EN; CA-09 y CA-10 | `tests/test_i18n.py` |
| Interfaz | CA-01, CA-02, CA-03, CA-06, CA-07 y CA-12 | `AppTest`, más una revisión manual a 1280×800 y a 390 px (CA-11) |
