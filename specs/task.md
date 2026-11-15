# RotaSat — Tareas (task.md)

Cada tarea cita lo que cumple del Spec y se da por terminada cuando pasan sus pruebas.
Orden: primero el motor sin red, luego los datos y al final la interfaz.

| N.º | Tarea | Cumple | Depende de | Hecho cuando |
|---|---|---|---|---|
| **T01** ✅ | Esqueleto del proyecto: estructura del Plan §2, `requirements.txt`, `pytest` configurado y un `app_simple.py` mínimo que arranca | — | — | `streamlit run app_simple.py` abre la página y `pytest` corre |
| **T02** ✅ | `crops.py`: Anexo A completo (18 entradas, con las notas ES/EN) | Anexo A | T01 | Una prueba verifica los 18 ids y algunos valores puntuales |
| **T03** ✅ | `i18n.py`: catálogo del Anexo C en ES/EN y la función `t()` | RF-60 a RF-64, Anexo C | T01 | Todas las claves existen en los dos idiomas |
| **T04** ✅ | `cache.py`, `SourceError` y `sources/http.py` | RNF-02, RNF-05 | T01 | Pruebas de acierto y fallo de caché con un servicio simulado |
| **T05** ✅ | `sources/power.py` (diario y humedad del suelo) y `sources/srtm.py` (punto y 3×3) | RC-01, RC-06, RC-17 | T04 | Ica descargado y guardado; la altitud SRTM da 405 m |
| **T06** ✅ | Motor del clima: corrección por altitud y tabla mensual | RC-02, RC-03 | T05 | Pruebas a mano: pesos de la costa, ET0 y P90 |
| **T07** ✅ | `sources/chirps.py` y `imerg.py`, con la descarga en segundo plano y el estado «preliminar» | RC-04, RC-05 | T04, T06 | Chupaca queda con CHIRPS en la caché y en Ica se usa IMERG desde la caché |
| **T08** ✅ | Región, pendiente y valores por defecto | RC-06, RC-07 | T06 | Región y pendiente del Anexo B.1 en los 7 lugares |
| **T09** ✅ | Aptitud de los cultivos, tabla del lugar y **verificación del desempate D-RC09** | RC-08, RC-09 | T02, T08 | El B.1 (aptos, con cuidado y no) y el B.2 coinciden exactamente; CA-05 |
| **T10** ✅ | Evaluación de rotaciones y puntajes | RC-10, RC-11 | T09 | Pruebas a mano de la línea de 36 meses y de la normalización |
| **T11** ✅ | Rotaciones automáticas A y B | RC-12 | T10 | El B.3 coincide con ±1 |
| **T12** ✅ | Textos que genera el motor: explicaciones, WhatsApp y resumen del clima | RC-13, RC-14, RC-15 | T03, T11 | CA-10 |
| **T13** ✅ | `scripts/prefetch.py` (7 lugares) y `tests/test_annex_b.py` sin red | RNF-03, CA-04 | T07, T11 | `pytest tests/test_annex_b.py` pasa sin conexión |
| **T14** ✅ | `sources/geocode.py`: coordenadas, búsqueda y nombre de un punto | RC-20, RF-13 a RF-16 | T04 | CA-06; `-14.13, -75.70` da «Pueblo Nuevo, Ica» |
| **T15** ✅ | Interfaz común: enrutador, botón de idioma, panel lateral y barra de iconos. Vista Inicio | RF-01 a RF-03, RF-20, RF-60, RNF-06, RNF-11 | T03 | CA-01 |
| **T16** ✅ | Vista Mi terreno: buscador, mapa, línea del lugar, aviso de preliminar y reintento | RF-10 a RF-22 | T14, T15, T07 | CA-02, CA-08 |
| **T17** ✅ | Paneles del terreno: Clima, Qué sembrar, Rotaciones, WhatsApp, Mis datos, Ayuda | RF-30 a RF-32, RF-34 a RF-36 | T12, T16 | CA-03 (terreno), CA-05 desde la interfaz |
| **T18** ✅ | NDVI (panel Satélite) y SoilGrids (botón en Mis datos) | RF-33, RC-16, RC-19 | T17 | CA-12 |
| **T19** | Vista Clima: pedido de GPS, plazo de 15 s y paso a escribir la ubicación | RF-40 a RF-45, RNF-09 | T16 | CA-07 |
| **T20** | Paneles del clima, incluido el río Ica | RF-51 a RF-57, RC-18 | T19 | CA-03 (clima) |
| **T21** | Cierre: cambio de idioma de punta a punta, prueba a 390 px y revisión de fallos de servicios | CA-09, CA-11, RNF-04, RNF-05 | T17 a T20 | Todos los CA pasan |
