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
| CHIRPS | SERVIR ClimateSERV | `https://climateserv.servirglobal.net/api/submitDataRequest/?datatype=0&intervaltype=0&operationtype=5&begintime=01/01/2005&endtime=12/31/2024&geometry={polígono}`, luego `getDataRequestProgress/?id=` (hasta 100; −1 es error) y luego `getDataFromRequest/?id=`. El polígono es un cuadrado de **medio lado 0.025°** (un píxel CHIRPS). Tarda 60–80 s. Tiempo máximo 300 s |
| GPM IMERG | SERVIR ClimateSERV | Igual que CHIRPS con `datatype=26`, de 2015 a 2024, con un cuadrado de **medio lado 0.05°** (un píxel IMERG). Tarda unos 7 min. La serie termina el 2024-06-01, pero igual se divide entre 10 años (es lo que reproduce el Anexo B). **Solo se lee de la caché** (Spec §10.2); `prefetch.py` lo descarga para Ica |
| NDVI | ORNL DAAC MODIS Web Service | `GET https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?latitude=..&longitude=..&band=250m_16_days_NDVI&startDate=A2023001&endDate=A2024366&kmAboveBelow=0&kmLeftRight=0` (escala ×0.0001). Para VIIRS se usa `VNP13A1` |
| Suelo | ISRIC SoilGrids v2 | `GET https://rest.isric.org/soilgrids/v2.0/properties/query?lon=..&lat=..&property=clay&property=sand&property=phh2o&depth=0-5cm&depth=5-15cm&value=mean`. La arcilla y la arena vienen en g/kg (÷10 da %) y el pH viene ×10 |
| Búsqueda y nombre | Nominatim (OSM) | `/search` con `countrycodes=pe` y luego sin él, `limit=8`, `accept-language=es`; `/reverse`. Se envía un `User-Agent` genérico (`RotaSat/1.0`) y como máximo una llamada por segundo |
| Mapa | Esri | Teselas `World_Imagery` y la capa `Reference/World_Boundaries_and_Places` |

**Calibración de la lluvia (T07).** El Spec no fija el área que se promedia. Se probaron varios tamaños contra la lluvia
anual del Anexo B.1. Un píxel nativo de cada producto reproduce los 7 lugares exactamente: CHIRPS (0.025) da Chupaca 792,
Huancavelica 902, Huamanga 642, Andahuaylas 907, Juliaca 498 y Satipo 1582; IMERG (0.05) da Ica 49. Con 0.001 y 0.01 en
CHIRPS, o con 0.025 en IMERG, salen números distintos. ClimateSERV responde 503 si recibe muchos pedidos a la vez:
los pedidos se hacen de uno en uno.

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
  no la quinua. **Confirmada en T09:** reproduce el top 5 del B.2 en los 7 lugares, incluidos todos los empates a 100.
  Con `kind="stable"` el orden no coincide. La columna que se ordena es la aptitud redondeada (entero).
- **D-RC09b · Nivel con la aptitud redondeada.** El texto original de RC-09 decía «sin redondear», pero en Ica el tarwi da
  39.97. Sin redondear queda «No recomendado» y los contadores dan 3/10/4; el Anexo B.1 dice 3/11/3. Con la aptitud redondeada
  (40, «Con cuidado») coinciden los 7 lugares, y en los otros 6 las dos reglas dan lo mismo. Se aprobó usar el valor redondeado
  y se corrigió el Spec.
- **D-RC12 · Desempates entre secuencias (RC-12.4).** Las secuencias se generan con `itertools.permutations` sobre los
  candidatos en el orden de la tabla RC-09, y se ordenan por total con un orden **estable** (`sorted` de Python). Hay
  empates exactos en el primer puesto en Ica (4 secuencias), Huancavelica, Apurímac y Puno, siempre entre permutaciones de
  los mismos 3 cultivos. **Confirmada en T11:** el orden estable reproduce A y B del B.3 en los 7 lugares; con el
  `sort_values` por defecto de pandas (no estable), en Apurímac A sale «Avena forrajera → Quinua → Tarwi» y no coincide.
- **RC-12 en los bordes:** la aptitud de los candidatos es la redondeada de la tabla. El cultivo principal es el más
  repetido de la rotación actual (en empate, el primero). Si no hay ninguna secuencia válida, solo se muestra la actual; si
  ninguna sirve como B, se muestran Actual y A.
- **RC-13 a RC-15 · Formato de los textos (T12).** El Spec da las frases (Anexo C.2) y sus condiciones, pero no cómo se
  unen. Se fijó así:
  - «Siembras»: «Cultivo en mes», separados por «, ». La lista de leguminosas (cultivos con N > 0) y las notas de los
    cultivos aparecen una vez por cultivo, en el orden de la rotación.
  - Los meses con más helada y con más calor extremo salen de la tabla de clima del lugar, no de los meses de la rotación.
    En un empate gana el mes más temprano.
  - Los beneficios y los riesgos que comparan con la actual solo se calculan para A y B. «Baja aptitud» y las notas
    aparecen en las tres rotaciones.
  - En el resumen del clima, los meses lluviosos se unen con «, » y « y » / « and » (Anexo C.1).
  - WhatsApp: encabezado «🌱 *RotaSat* — lugar», viñetas «• », líneas en blanco entre bloques y `**` pasado a `*`
    (la negrita de WhatsApp). Se compara con la mejor de A y B; si empatan, gana A.
- **RC-20 · Tipos de lugar y campos de la dirección (T14).** Para ordenar los resultados se usa el `addresstype` de
  Nominatim: pueblos, caseríos y calles = `village`, `town`, `hamlet`, `isolated_dwelling`, `locality`, `road`; ciudades
  y barrios = `city`, `suburb`, `neighbourhood`, `quarter`, `city_block`; distritos a departamentos = `district`,
  `city_district`, `municipality`, `county`, `province`, `region`, `state`; lo demás va al final. El orden es estable.
  El nombre de un resultado son las dos primeras partes de `display_name`. Para el nombre de un punto se toman, en orden,
  `village`, `town`, `city`, `district`, `county`, `region` y `state`: en el Perú OSM pone la provincia unas veces en
  `county` (Tarma) y otras en `region` (Huamanga). Verificado con el servicio real: CA-06 da «Tarma, Junín» y el punto
  de Ica, «Pueblo Nuevo, Ica».
- **Mejor mes (RC-09):** de enero a diciembre, se queda el mes con la mayor tupla
  `(round(aptitud), round(min(cobertura, 1.5), 2), −exposición_helada)`; solo se reemplaza si es estrictamente mayor,
  así en un empate total gana el mes más temprano.
- **Factor limitante por temperatura:** «Muy frío» si la temperatura media más baja del ciclo es menor que el óptimo
  inferior; si no, «Muy caluroso». Agua: sin riego se usa el texto de «La lluvia solo cubre…»; con riego, «Necesita mucha
  agua de riego…».
- **Panel lateral (RF-20):** se usa `st.dialog(título, width=640, position="right", on_dismiss=cerrar)`, que en
  Streamlit 1.67 ya es un cajón modal de alto completo a la derecha; no hace falta CSS. En pantallas angostas se encoge
  solo (a 390 px mide 366 px). Se cierra con Esc, con la ✕ o con un clic fuera, y `on_dismiss` borra `panel` de la sesión
  para que no se vuelva a abrir en la siguiente ejecución. Solo hay uno abierto a la vez porque `panel` guarda una sola
  clave. Verificado en Chrome a 1280 px y a 390 px (T15).
- **Botones con texto de ayuda:** Streamlit los dibuja dos veces (con y sin tooltip) y muestra uno según la pantalla.
  Las tarjetas de Inicio y el botón de idioma se ajustan con CSS sobre la clase `st-key-<clave>`. La barra de iconos usa
  `width="stretch"` y `wrap=True`, para que ninguna etiqueta se corte (RNF-07).
- **Estado de la sesión:** `view`, `lang`, `panel`, `terreno_place`, `clima_place` y `overrides[(lat,lon)]`. El botón de
  idioma usa la clave de widget `lang_btn`, porque `lang` ya es una clave de la sesión. No se guarda nada entre sesiones
  (RNF-10).
- **Elegir un lugar (T16):** `rotasat/ui/location.py` reúne el buscador, el GPS, el mapa, la línea del lugar y los
  avisos de lluvia. Lo usan Mi terreno y Clima, cada una con su clave de sesión (`terreno_place`, `clima_place`), así los
  dos lugares son independientes (RF-45). Un lugar es `{lat, lon, kind, name}` y el texto de RF-16 se arma en cada
  ejecución, así cambia con el idioma. Detalles:
  - El buscador va en un `st.form` para que Enter lo envíe.
  - El mapa usa como clave el punto marcado, para volver a centrarse cuando cambia el lugar.
  - El clima de cada punto se guarda en `st.session_state.place_climate` y se vuelve a armar cuando cambia el estado de
    la descarga de CHIRPS.
  - El sondeo de RF-21 es un `st.fragment(run_every=6)` que actualiza la página solo si no hay un panel abierto.
  - Los códigos de error del GPS: 1 → `denegado`, 2 → `no_disponible`, 3 → `tiempo` y 0 → `no_soportado`.
- **Paneles del terreno (T17):**
  - `rotasat/ui/farm.py` arma lo que necesitan los paneles: clima, datos detectados, respuestas de «Mis datos», tabla
    RC-09 y rotaciones RC-12. Lo guarda en la sesión y lo recalcula solo cuando cambian las respuestas o la lluvia.
  - Las respuestas se guardan en `overrides[(lat, lon)]`, solo con lo que el usuario cambió (RC-07).
  - `rotasat/ui/climate_sections.py` tiene las secciones de RF-51 a RF-55 y RF-57. Las usan el panel Clima del terreno
    (RF-30) y, en T20, los paneles de la vista Clima. El río (RF-56) y el panel Satélite con el botón de SoilGrids
    quedan para T20 y T18.
  - Los controles de «Mis datos» llevan en su clave una versión que sube con cada respuesta. Así se vuelven a crear con
    los valores ya recalculados; por ejemplo, el riego por defecto de la región nueva.
  - Los `format_func` usan el idioma capturado al dibujar (`t(..., lg)`), nunca `tr()`. Streamlit y `AppTest` pueden
    llamarlos fuera de una ejecución de la app, donde `st.session_state` no existe.
  - Los bloques largos de Ayuda se buscan en el catálogo con `i18n.key_starting()`, que exige una sola coincidencia.
  - `st.info` y `st.warning` muestran el emoji inicial del texto como icono del aviso.
- **Idioma:** se guarda en `st.session_state.lang`. Los textos se piden con `t(clave)` y **nunca** se escriben sueltos en la
  interfaz. Las claves del catálogo salen del Anexo C, y una prueba verifica que todas existen en ES y EN.

## 7. Estrategia de pruebas

| Nivel | Qué | Cómo |
|---|---|---|
| Unidad | Cada regla RC con casos a mano | `tests/test_agro.py` y `tests/test_climate.py` |
| Referencia | CA-04 y CA-05: los 7 lugares contra el Anexo B, con tolerancia ±1 | `tests/test_annex_b.py`, que lee de `data/cache/` (sin red) |
| Textos | Todas las claves del Anexo C en ES y EN; CA-09 y CA-10 | `tests/test_i18n.py` |
| Interfaz | CA-01, CA-02, CA-03, CA-06, CA-07 y CA-12 | `AppTest`, más una revisión manual a 1280×800 y a 390 px (CA-11) |
