# Agro Planet — Especificación del producto (Spec.md)

| | |
|---|---|
| **Versión** | 1.0 (borrador para aprobación) |
| **Fecha** | 15 de noviembre de 2026 |
| **Origen** | NASA Space Apps Challenge 2026 · Reto «Field Shift: Adapting Farms with NASA Data» |
| **Documentos hermanos** | `Plan.md` (cómo se construye) · `task.md` (pasos de trabajo) · `Spec-anexo-C-textos.md` (textos ES/EN) |

## 0. Cómo leer este documento

- **Spec.md dice QUÉ hace el producto y POR QUÉ.** No nombra lenguajes ni librerías; eso va en `Plan.md`.
- Cada requisito tiene un código (`RF` funcional, `RC` regla de cálculo, `RNF` no funcional, `CA` criterio de aceptación)
  para poder citarlo en el plan, en las tareas y en las pruebas.
- **Qué significa «igual al original»:** un equipo que siga este Spec debe obtener un producto con las mismas pantallas,
  los mismos textos (Anexo C) y los mismos resultados numéricos (Anexo B). No se exige el mismo código línea por línea.
- Los números de las reglas de cálculo (sección 6) y del Anexo A son parte del requisito: no se pueden «mejorar» ni redondear.

## 1. Propósito

**Problema.** Los pequeños agricultores del Perú deciden qué sembrar y en qué orden con un clima que está cambiando:
en la costa (Ica) el agua subterránea se agota y el río depende de la lluvia de la sierra; en la sierra las heladas y las
lluvias irregulares dañan los cultivos. Casi no hay técnicos agrarios para asesorarlos.

**Producto.** Agro Planet es una página web que, para **cualquier ubicación**, convierte 20 años de datos satelitales de la
NASA en una recomendación sencilla: **qué sembrar, cuándo y en qué orden (rotación de cultivos)**, explicando el porqué.

**Lo que pide el reto y Agro Planet debe cumplir:**
1. Combinar observaciones de la NASA con información local (suelo, cultivos, prioridades del agricultor).
2. Comparar al menos 3 rotaciones, incluida la actual.
3. Para cada una explicar: por qué se sugiere, evidencia, beneficios, vacíos de información y riesgos a revisar con un experto.
4. Mostrar cuándo el campo queda sin cultivo y cuándo el cultivo es más vulnerable.
5. Ser fácil de usar para personas sin formación técnica.
6. Dejar claro que apoya, no reemplaza, al agricultor ni al agrónomo.

## 2. Usuarios

| Usuario | Qué necesita |
|---|---|
| **Pequeño agricultor** (costa o sierra, cultivos anuales, poca experiencia digital, usa WhatsApp) | Saber qué sembrar en su chacra, en qué mes, y si le conviene cambiar su rotación |
| **Técnico agrario** (Agro Rural, Junta de Usuarios, municipalidad) | Mostrar el análisis al agricultor y enviarle un resumen por WhatsApp |
| **Jurado del hackathon** | Ver datos reales de la NASA funcionando, en español o en inglés |

## 3. Alcance

**Incluido**
- Una página web con tres vistas: **Inicio**, **Mi terreno** y **Clima**.
- Catorce paneles laterales de información (7 del terreno y 7 del clima).
- El motor de cálculo: clima del lugar, aptitud de 17 cultivos, rotaciones automáticas, puntajes y explicaciones.
- Dos idiomas: español (por defecto) e inglés.
- Funcionamiento sin conexión para 7 lugares de ejemplo cuyos datos se descargan por adelantado.

**Excluido**
- Cuentas de usuario, inicio de sesión y guardado entre sesiones.
- Precios de mercado en tiempo real.
- La interfaz «clásica» con pestañas (`app.py`), que existió como versión anterior. *(Decisión abierta: ver sección 11.)*
- Los documentos de estudio y de presentación del hackathon.

## 4. Principios del producto

| Código | Principio | Consecuencia |
|---|---|---|
| **P1** | **La información aparece solo cuando se pide.** | Al cargar hay 2 iconos. Cada bloque de información vive en un panel lateral que el usuario abre y cierra. |
| **P2** | **Funciona en cualquier ubicación.** | No hay valores fijos por zona: región, pendiente, riego y sal se deducen de la ubicación elegida. |
| **P3** | **Transparente.** | Todo puntaje se calcula con reglas explícitas (sección 6) y se explica en pantalla. No hay «caja negra». |
| **P4** | **Apoya, no reemplaza.** | Cada recomendación muestra riesgos, vacíos de información y un aviso de consultar a un experto. |
| **P5** | **Sin cuentas ni pagos.** | Solo se usan fuentes de datos abiertas que no exigen registro. |
| **P6** | **Honesto con los límites.** | Si un dato falta o es preliminar, se dice en pantalla. Si el usuario conoce su chacra, su respuesta manda sobre el satélite. |
| **P7** | **Tolerante a fallos.** | Si un servicio externo no responde, la página sigue funcionando con lo que tiene y lo avisa. |

## 5. Requisitos funcionales

### 5.1 Vista Inicio

- **RF-01** Al abrir la página se muestra solo: el botón de idioma (arriba a la derecha), el logotipo 🌱, el nombre «Agro Planet»,
  el lema, y **dos botones grandes** con icono y etiqueta: 🗺️ **Mi terreno** y 🌦️ **Clima**. Bajo cada botón hay una línea
  que explica qué hace. No hay barra lateral, pestañas ni ningún otro contenido.
- **RF-02** Los dos botones son tarjetas de al menos 200 px de alto, con el icono grande arriba y el texto debajo.
- **RF-03** «Mi terreno» lleva a la vista Mi terreno. «Clima» lleva a la vista Clima.

### 5.2 Vista Mi terreno

- **RF-10** Cabecera: botón «⬅️ Inicio», título «🗺️ Mi terreno» y botón de idioma a la derecha.
- **RF-11** Buscador en una fila: un campo de texto, el botón «🔍 Buscar» y el botón «📍 Mi ubicación». La tecla Enter envía la búsqueda.
- **RF-12** Mapa de imagen satelital con nombres de lugares superpuestos, de 370 px de alto.
  Sin terreno: centrado en (−9.5, −75.0) con zoom 5 (se ve todo el Perú).
  Con terreno: centrado en el punto con zoom 14 y un círculo amarillo sobre él.
- **RF-13** El usuario puede indicar su terreno de cuatro formas:
  1. **Clic en el mapa.**
  2. **Dirección o pueblo** escrito en el buscador.
  3. **Coordenadas** escritas como `latitud, longitud` en decimales con punto (por ejemplo `-14.13, -75.70`);
     el separador puede ser coma, punto y coma o espacio; latitud entre −90 y 90, longitud entre −180 y 180.
  4. **Ubicación del dispositivo (GPS).**
- **RF-14** Toda ubicación se redondea a 4 decimales.
- **RF-15** Búsqueda por nombre (RC-20): si hay un solo resultado se usa directamente; si hay varios, se listan como
  botones (máximo 5) bajo la pregunta «¿Cuál de estos lugares es?»; si no hay ninguno o el servicio falla, se muestra un aviso.
- **RF-16** El nombre que se muestra del lugar depende de cómo se eligió y se vuelve a escribir al cambiar de idioma:

  | Forma | Texto |
  |---|---|
  | GPS | «Mi ubicación actual (*pueblo, región*)» |
  | Clic en el mapa | «Terreno en *pueblo, región*»; si no se conoce el pueblo: «Terreno marcado en el mapa» |
  | Coordenadas | «*pueblo, región*»; si no se conoce: «Coordenadas *lat, lon*» |
  | Búsqueda | Las dos primeras partes del nombre encontrado |

- **RF-17** **Antes de marcar el terreno** se muestra, bajo el mapa, un aviso que invita a marcarlo y la barra de 7 iconos
  **deshabilitados**, con la leyenda «Estos iconos se activan al marcar su terreno:».
- **RF-18** **Al marcar el terreno** se cargan los datos del lugar con un indicador de espera. Al terminar aparecen: la línea
  del lugar (nombre en negrita; debajo región, altitud y coordenadas), la leyenda «Toque un icono para ver esa información:»
  y los 7 iconos **habilitados**.
- **RF-19** La barra tiene 7 botones con icono y etiqueta, en este orden: 🌦️ Clima · 🌱 Qué sembrar · 🔄 Rotaciones ·
  🛰️ Satélite · 📱 WhatsApp · ⚙️ Mis datos · ℹ️ Ayuda. Cada uno tiene un texto de ayuda al pasar el cursor.
- **RF-20** **Panel lateral (off-canvas).** Al tocar un icono se abre un panel que entra desde la derecha, de 640 px de ancho
  (en pantallas angostas ocupa el ancho disponible), con título y botón de cerrar. Es modal: el mapa queda visible detrás,
  atenuado. Se cierra con la ✕, con la tecla Esc o tocando fuera. Solo hay un panel abierto a la vez.
- **RF-21** Si la lluvia satelital del lugar aún se está descargando (RC-05), bajo la línea del lugar se muestra el aviso de
  «resultados preliminares». La página consulta cada 6 segundos si ya llegó y, **si no hay un panel abierto**, se actualiza sola.
- **RF-22** Si la descarga de lluvia falla se muestra un aviso y un botón para reintentar. Si fallan los datos principales
  de clima se muestra un error y un botón «Reintentar»; los iconos quedan deshabilitados.

### 5.3 Paneles del terreno

- **RF-30 Clima.** Las 4 frases de resumen (RC-15), el calendario de riesgos (RF-51) y, plegadas, las secciones:
  Lluvia y evaporación · Temperatura y heladas · Humedad del suelo · ¿Está cambiando el clima aquí? ·
  ¿Traerá agua el río? (solo en la cuenca de Ica, RC-18) · Cómo se ajustaron los datos.
- **RF-31 Qué sembrar.**
  1. Si la lluvia es preliminar o falló, un aviso lo indica.
  2. Tres contadores: 🟢 Aptos, 🟡 Con cuidado, 🔴 No recomendados.
  3. Lista de los **6 cultivos mejor puntuados**: aptitud en un recuadro de color (verde ≥ 65, ámbar ≥ 40, rojo < 40),
     nombre, «sembrar en *mes*» y el factor limitante.
  4. Nota que explica el número. Si el usuario no indicó su suelo, una nota lo dice y remite a «Mis datos».
  5. Plegado: tabla de los 17 cultivos con las columnas Cultivo, Aptitud (barra 0–100), Nivel, Mejor mes de siembra, Ciclo,
     Lluvia cubre, Riego necesario (m³/ha) y Factor limitante.
  6. Plegado: selector de cultivo y gráfico de barras con la aptitud según el mes de siembra (mismos colores).
  7. Aviso final: es una orientación; consulte a su técnico.
- **RF-32 Rotaciones.**
  1. Plegado «Mi rotación actual»: tres campañas; en cada una se elige cultivo (los 17 y «Descanso») y mes de siembra.
     Por defecto es la rotación típica de la región (RC-07). Al cambiarla, todo el panel se recalcula.
  2. Tres tarjetas: **Actual**, **A** y **B**, con los cultivos y el puntaje total sobre 100. La de mayor puntaje lleva borde
     verde y la etiqueta «⭐ Recomendada».
  3. Línea de tiempo de 3 años: una fila por rotación, un bloque de color por cultivo; los huecos son meses con el suelo desnudo.
  4. «¿Por qué?»: un plegado por rotación con una barra por criterio y cinco listas: por qué se sugiere, evidencia (datos NASA),
     beneficios frente a la actual, riesgos a revisar con un experto y vacíos de información (RC-13).
  5. Aviso final: Agro Planet apoya, no reemplaza.
- **RF-33 Satélite.** Explica el índice de verdor (NDVI). Si los datos del lugar no están guardados, un botón los consulta
  (puede tardar). Muestra el gráfico 2023–2024 con los valores crudos, la línea filtrada y una franja «suelo desnudo»
  por debajo de 0.2; luego los meses con el campo pelado y el promedio. Un plegado opcional compara con VIIRS.
- **RF-34 WhatsApp.** Muestra el mensaje de resumen (RC-14) y un botón que abre WhatsApp con ese texto ya escrito.
- **RF-35 Mis datos.** Aviso: los valores se dedujeron de la ubicación y el usuario puede cambiarlos. Controles:
  región · pendiente (plano / suave / ladera) · riego (3 opciones) · tipo de suelo (5 texturas o «No sé») con la
  «prueba de la bolita» plegada · pH (4 rangos o «No sé») · salitre (No / Un poco / Mucho) · botón «Estimar mi suelo con
  satélite» · 7 prioridades de 0 a 5 · botón «Volver a los valores detectados».
  Lo que el usuario cambia se guarda para ese lugar mientras dure la sesión y se usa en los demás paneles.
- **RF-36 Ayuda.** Cuatro plegados: datos que usa · cómo se calcula · recursos del reto (qué se usó y por qué) · limitaciones.

### 5.4 Vista Clima

- **RF-40** Cabecera igual a RF-10 con el título «🌦️ Clima de mi ubicación».
- **RF-41** Al entrar sin un lugar definido, la página **pide la ubicación del dispositivo**. Mientras espera muestra un
  aviso y, debajo, el buscador para escribir un lugar.
- **RF-42** Si el usuario no da permiso, o la ubicación no llega en 15 segundos, o el navegador no la ofrece, se muestra el
  motivo y se pide **escribir la ubicación** (dirección, pueblo o coordenadas).
- **RF-43** Con el lugar definido se muestran: la línea del lugar, el aviso de lluvia preliminar si aplica, 3 cifras
  (lluvia al año, temperatura media, días con riesgo de helada), las 4 frases de resumen (RC-15) y la barra de iconos del clima.
- **RF-44** Debajo hay dos botones: «🌱 Ver qué puedo sembrar aquí» (lleva ese mismo lugar a la vista Mi terreno) y
  «✏️ Cambiar de lugar».
- **RF-45** El lugar del Clima y el del Terreno son independientes. Si ya hay un lugar del Clima, al volver a la vista se
  reutiliza sin pedir otra vez la ubicación.

### 5.5 Paneles del clima

Barra de iconos, en este orden: 📅 Calendario · 🌧️ Lluvia · 🌡️ Temperatura · 🟫 Humedad del suelo · 📈 Tendencia ·
💧 Río (solo en la cuenca de Ica) · 🔬 Sobre los datos. Se abren como paneles laterales (RF-20).

- **RF-51 Calendario de riesgos.** Cuadrícula de 12 meses por 5 o 6 filas: días con riesgo de helada, días de calor extremo,
  temperatura media, lluvia, evaporación y, si se pudo obtener, humedad del suelo en la zona de raíces. Cada casilla muestra
  el valor entero; el color va de amarillo a rojo según el valor **dentro de su fila**.
- **RF-52 Lluvia y evaporación.** Barras de lluvia mensual y línea de evaporación; nota para interpretar; fuente de la lluvia
  y total anual; comparación de los productos de lluvia disponibles en ese punto.
- **RF-53 Temperatura y heladas.** Líneas de máxima, media y mínima por mes. Si hay al menos 1 día de helada al año:
  barras de días con mínima ≤ 2 °C y ≤ 0 °C; si no, un mensaje de que casi no hay heladas. Nota del umbral de calor extremo.
- **RF-54 Humedad del suelo.** Líneas de humedad de la superficie y de la zona de raíces (0–100 %); mes más seco y más
  húmedo; nota sobre la fuente y, en la costa, la advertencia de que el modelo no ve el riego.
- **RF-55 Tendencia.** Temperatura máxima media de cada año (2005–2024); barras por año de días con helada (sierra y zona
  altoandina) o de calor extremo (costa y selva); frase con la diferencia entre 2020–2024 y 2005–2009.
- **RF-56 Río** (RC-18). Texto explicativo, cifra de la última temporada con su diferencia frente al promedio, semáforo
  (seco / ligeramente seco / normal o húmedo) y barras del histórico con la línea del promedio.
- **RF-57 Sobre los datos.** Cómo se corrigió la temperatura por altitud, las fuentes usadas y la advertencia del microclima.

### 5.6 Idioma

- **RF-60** El idioma por defecto es español. En Inicio y en la cabecera de las otras vistas hay un botón 🌐 que muestra el
  nombre del **otro** idioma («English» o «Español») y cambia toda la página.
- **RF-61** Se traduce todo: interfaz, gráficos, nombres y notas de cultivos, meses, regiones, criterios, texturas, motivos,
  explicaciones de las rotaciones y el mensaje de WhatsApp. Los textos exactos están en el Anexo C.
- **RF-62** Cambiar de idioma conserva la vista, el lugar marcado y las respuestas del usuario.
- **RF-63** No se traducen los nombres propios de lugares ni de fuentes de datos.
- **RF-64** En frases, los meses van en minúscula en español («mayo») y con mayúscula en inglés («May»).

## 6. Reglas de cálculo

Todas las reglas usan, para un lugar, una **tabla de clima de 12 meses** (RC-03). «Mes» siempre es mes calendario (1 = enero).

### RC-01 Datos diarios del lugar
Para la ubicación se obtienen, del 1 de enero de 2005 al 31 de diciembre de 2024 (20 años), los valores **diarios** de:
temperatura media, máxima y mínima del aire a 2 m (°C), lluvia (mm/día) y radiación solar en el tope de la atmósfera
(MJ/m²/día). También la **altitud media del área** que representan esos datos (unos 50 km). Los valores marcados como
faltantes se ignoran.

### RC-02 Corrección de temperatura por altitud
1. `ajuste = 6.5 × (altitud_del_área − altitud_real) / 1000` en °C, donde la altitud real es la del punto exacto (RC-06).
2. **Lugar de costa desértica:** altitud real menor de 1500 m **y** lluvia media anual de RC-01 menor de 300 mm.
3. Si no es costa, el ajuste se suma completo a las temperaturas media, máxima y mínima de todos los días.
4. Si es costa (inversión térmica), el ajuste se multiplica por un peso según el mes:
   diciembre a marzo **1**; abril **0.66**; mayo **0.33**; junio a setiembre **0**; octubre **0.33**; noviembre **0.66**.
5. Si no se conoce la altitud real, no hay ajuste.

### RC-03 Tabla de clima mensual
Con los datos diarios ya corregidos:
- **Evaporación de referencia diaria** (método Hargreaves-Samani, FAO-56):
  `ET0 = 0.0023 × (0.408 × radiación) × (T_media + 17.8) × √(T_máx − T_mín)`; si la diferencia es negativa se toma 0.
- **Calor extremo del lugar:** el percentil 90 de la temperatura máxima diaria de los 20 años.
- Por cada mes del año:

| Variable | Cálculo |
|---|---|
| Lluvia (mm) | Suma de todos los días de ese mes en los 20 años ÷ 20 |
| Evaporación ET0 (mm) | Suma ÷ 20 |
| Temperatura media, máxima y mínima (°C) | Promedio de los valores diarios de ese mes |
| Días con riesgo de helada | N.º de días con mínima ≤ 2 °C ÷ 20 |
| Días de helada fuerte | N.º de días con mínima ≤ 0 °C ÷ 20 |
| Días de calor extremo | N.º de días con máxima ≥ percentil 90 ÷ 20 |

### RC-04 Lluvia satelital
- En lugares que **no** son de costa (RC-02) la lluvia mensual de la tabla se **reemplaza** por la de **CHIRPS**:
  lluvia diaria 2005–2024, sumada por mes y dividida entre 20.
- En lugares de costa se reemplaza por la de **GPM IMERG** (2015–2024, suma por mes ÷ 10) **solo si esos datos ya están
  guardados** para el lugar; si no, se usa la lluvia de RC-01. *(Comportamiento conocido: en la costa no se inicia descarga.)*
- Los valores negativos de estas series significan «sin dato» y se ignoran.
- La lluvia original de RC-01 se conserva aparte para mostrar la comparación (RF-52).

### RC-05 Descarga en segundo plano
La lluvia CHIRPS de un lugar nuevo tarda entre 1 y 5 minutos. Se descarga en segundo plano (máximo 300 s) y se guarda.
Mientras tanto la tabla usa la lluvia de RC-01 y la página marca los resultados como **preliminares**.

### RC-06 Altitud, pendiente y región
- **Altitud real:** la del punto exacto según el modelo de elevación SRTM.
- **Pendiente (%):** con las altitudes de una cuadrícula de 3 × 3 puntos separados 0.001° alrededor del lugar:
  `pendiente = 100 × √(dzdx² + dzdy²)`, donde `dzdx = (este − oeste) / (2 × 0.001 × 111320 × cos(latitud))` y
  `dzdy = (norte − sur) / (2 × 0.001 × 110540)`.
- **Clase de pendiente:** menos de 3 % **plano**; menos de 12 % **suave**; si no, **ladera**. Sin dato: **suave**.
- **Región**, con la altitud real (o la del área si falta) y la lluvia anual de la tabla:
  altitud ≥ 3700 m **zona altoandina**; ≥ 2000 m **sierra**; por debajo, lluvia < 300 mm **costa**; si no, **selva**.

### RC-07 Valores por defecto (deducidos del lugar)
| Dato | Valor por defecto |
|---|---|
| Región | La detectada (RC-06) |
| Pendiente | La clase detectada (RC-06) |
| Riego | Costa: «sí, pero limitada». Otras regiones: «no, solo lluvia» |
| Sal | Costa: «un poco» (media). Otras: «no» (baja) |
| Textura y pH del suelo | Desconocidos (no afectan el cálculo) |
| Prioridades (0–5) | Aptitud 3 · Agua 3 · Suelo 3 · Plagas 2 · Clima 3 · Ingresos 3 · Erosión 2 |
| Rotación actual (cultivo, mes de siembra) | Costa: algodón (set.) → maíz amarillo (abr.) → algodón (set.) · Sierra y zona altoandina: papa (oct.) → papa (oct.) → cebada (dic.) · Selva: maíz amarillo (oct.) → maíz amarillo (mar.) → yuca (oct.) |

Si el usuario cambia la región, el riego y la sal por defecto pasan a ser los de la nueva región, salvo que ya los haya cambiado él.
Si el usuario indica textura o pH, o pide la estimación satelital (RC-19), se usan en el cálculo; lo que escribe el usuario
tiene prioridad sobre el satélite.

### RC-08 Aptitud de un cultivo sembrado en un mes
El ciclo ocupa tantos meses seguidos como dure el cultivo (Anexo A), empezando en el mes de siembra y dando la vuelta al año.
Se calculan seis factores entre 0 y 1:

1. **Temperatura.** Para cada mes del ciclo, con la temperatura media `T`, el rango óptimo `[o1, o2]` y el límite `[l1, l2]`:
   1 si `o1 ≤ T ≤ o2`; `max(0, (T − l1)/(o1 − l1))` si `T < o1`; `max(0, (l2 − T)/(l2 − o2))` si `T > o2`.
   `f_temp = 0.6 × promedio + 0.4 × mínimo` de los meses del ciclo.
2. **Heladas.** `exposición = Σ (días_helada + 2 × días_helada_fuerte) × sensibilidad_helada`; `f_helada = e^(−0.06 × exposición)`.
3. **Agua.** Lluvia aprovechable de un mes con lluvia `p`: `max(0, 0.6p − 10)` si `p ≤ 70`; `0.8p − 24` si `p > 70`.
   `necesidad = Σ ET0 × Kc`; `cubierto = Σ min(lluvia_aprovechable, ET0 × Kc)`; `cobertura = cubierto / necesidad`;
   `riego_mm = max(0, necesidad − cubierto)`; **riego en m³/ha = riego_mm × 10**.
   - Sin riego: `f_agua = min(1, max(0.3, cobertura / 0.5))`.
   - Con riego: `f_agua = 1 − castigo × min(1, riego_mm / 900)`, con castigo **0.45** si el agua es limitada y **0.12** si es
     suficiente. Si es limitada y el Kc del cultivo es mayor que 0.9, además se multiplica por **0.55**.
4. **Sal.** `f_sal = 1 − 0.8 × nivel × (1 − tolerancia_sal)`, con nivel 0 (baja), 0.5 (media) o 1 (alta).
5. **Textura.** 1 si no se conoce, si el cultivo no tiene preferencia o si la textura está entre sus preferidas. Si no, con el
   orden arenoso → franco-arenoso → franco → franco-arcilloso → arcilloso: **0.75** si está a un paso de una preferida; **0.5** si está más lejos.
6. **pH.** 1 si no se conoce o está en el rango del cultivo; **0.75** si se sale hasta 0.5 unidades; **0.5** si se sale más.

**Aptitud = 100 × producto de los seis factores.**

### RC-09 Tabla de aptitud del lugar
Para cada uno de los 17 cultivos (todos menos «Descanso»):
- Se prueba la siembra en los 12 meses y se elige el mejor comparando, en este orden: aptitud redondeada al entero;
  cobertura de lluvia (tope 1.5, redondeada a 2 decimales); menor exposición a heladas. En empate total gana el mes más temprano del año.
- **Nivel:** aptitud ≥ 65 «Apto»; ≥ 40 «Con cuidado»; menor «No recomendado», con la aptitud **redondeada al entero**
  (corregido en la v1.0: el texto anterior decía «sin redondear», pero el Anexo B.1 de Ica solo se reproduce con el valor
  redondeado; ver `Plan.md` D-RC09b).
- **Factor limitante:** el factor más bajo de RC-08 (en empate, el primero en el orden temperatura, heladas, agua, sal,
  textura, pH). Si es 0.85 o más: «Sin limitaciones importantes». Si no, el motivo correspondiente (Anexo C).
- Se muestran: aptitud redondeada, mejor mes, ciclo en meses, riego necesario redondeado a la decena, y
  «lluvia cubre» = `min(cobertura, 1) × 100` %.
- La tabla se ordena por aptitud redondeada, de mayor a menor.
- **Empates:** entre cultivos con la misma aptitud redondeada, el orden es el que produce la implementación de
  referencia (se fija en `Plan.md`). Importa porque RC-12 toma los primeros de esta tabla; el Anexo B muestra el orden esperado.

### RC-10 Evaluación de una rotación
Una rotación es una lista de 3 pasos (cultivo, mes de siembra) sobre una línea de **36 meses** que empieza en enero del año 1.
- Cada cultivo se coloca en la primera aparición de su mes de siembra que no sea anterior al fin del cultivo previo, y ocupa
  su duración. **Los meses que pasan del mes 36 no se cuentan** *(comportamiento conocido: el tercer cultivo puede quedar fuera)*.
- Se analiza desde el primer mes ocupado hasta el mes 36. Por cada mes:
  - **Sin cultivo:** `erosión += (lluvia/100) × factor_pendiente + 0.15`.
  - **Con cultivo:** `agua_mm += max(0, ET0 × Kc − lluvia_aprovechable)`;
    `helada += (días_helada + 2 × días_helada_fuerte) × sensibilidad_helada`; `calor += días_calor × sensibilidad_calor`;
    `erosión += (lluvia/100) × factor_pendiente × (1 − cobertura_del_cultivo)`.
  - Factor de pendiente: plano 0.3 · suave 0.7 · ladera 1.0.
- Además:
  - **Repetición de familias** = n.º de pasos seguidos con la misma familia + 0.5 × n.º de pasos con la misma familia separados por uno.
  - **Aptitud de la rotación** = promedio de la aptitud (RC-08) de cada cultivo en su mes de siembra («Descanso» vale 70); se guarda también la mínima.
  - **Nitrógeno** = suma del valor N de los cultivos. **Ingreso** = suma del valor de mercado + 0.5 por cada cultivo forrajero.
  - **Sal** = Σ (1 − tolerancia_sal) × nivel de sal. **Meses con suelo desnudo** = meses sin cultivo en el tramo analizado.
  - **Agua en m³/ha** = agua_mm × 10.

### RC-11 Puntajes y total
Los puntajes se calculan **dentro del grupo de rotaciones que se compara** (por eso cambian si cambia el grupo).

| Criterio | Dato (RC-10) | Puntaje |
|---|---|---|
| Aptitud | Aptitud de la rotación | El mismo valor, entre 0 y 100 |
| Agua | Agua en m³/ha | Relativo: `100 − 60 × (valor − mínimo) / máximo` |
| Clima | helada + calor | Relativo (igual que agua) |
| Erosión | erosión | Relativo |
| Sal *(solo si el nivel de sal no es «baja»)* | sal | Relativo |
| Suelo | Nitrógeno (más es mejor) | `40 + 60 × (valor − mínimo) / (máximo − mínimo)` |
| Ingresos | Ingreso (más es mejor) | Igual que suelo |
| Plagas | Repetición de familias (menos es mejor) | `100 − 60 × (valor − mínimo) / (máximo − mínimo)` |

- En los relativos, si el máximo es 0 todas reciben 100. En los otros, si máximo = mínimo todas reciben 100.
- **Total = promedio de los puntajes ponderado por las prioridades** del usuario. La sal pesa 2.
- Si la aptitud mínima de la rotación es menor de 40, el total se multiplica por **0.85**.

### RC-12 Rotaciones automáticas (A y B)
1. **Candidatos:** los cultivos con aptitud ≥ 45, como máximo los 8 primeros de la tabla (RC-09). Si son menos de 3, se toman los 3 primeros de la tabla.
2. Se forman todas las secuencias ordenadas de 3 candidatos distintos, cada uno en su mejor mes de siembra.
3. Se descartan las que tienen dos pasos seguidos de la misma familia. Si entre los candidatos hay alguna leguminosa,
   se descartan las que no incluyen ninguna.
4. Se puntúan todas **junto con la rotación actual** (RC-11) y se ordenan de mayor a menor total.
5. **A** = la de mayor total.
6. **B:** si el cultivo principal del agricultor (el que más se repite en su rotación actual) está entre los candidatos y
   no está en A, B es la mejor secuencia que lo contiene. En otro caso, B es la siguiente mejor que no use exactamente los
   mismos 3 cultivos que A.
7. Las rotaciones se nombran «A: *cultivo* → *cultivo* → *cultivo*» y «B: …». La actual: «Actual: …» («Current: …» en inglés).
8. **Los puntajes que se muestran** se recalculan comparando solo las tres: Actual, A y B.

### RC-13 Explicación de cada rotación
Textos exactos en el Anexo C.2. Condiciones:

| Lista | Entrada | Cuándo aparece |
|---|---|---|
| **Por qué** | Es la que usa hoy el agricultor | Solo en la actual |
| | Armada con los cultivos más aptos | En A y B |
| | Incluye leguminosas (lista) | Si algún cultivo tiene N positivo |
| | Ninguna familia se repite | Si las 3 familias son distintas |
| **Evidencia** | Siembras (cultivo y mes) · aptitud promedio · meses con suelo desnudo · mes con más calor extremo | Siempre |
| | Necesidad de riego en 3 años / agua que la lluvia no cubre | Según tenga riego o no |
| | Mes con más riesgo de helada | Si algún mes supera 0.5 días |
| **Beneficios** (solo A y B, frente a la actual) | Ahorro de agua (m³/ha y n.º de cisternas de 30 m³) | Si ahorra más de 100 m³/ha |
| | Cultivos mejor adaptados | Si la aptitud supera a la actual en más de 3 puntos |
| | Mejor balance de nitrógeno · menos repetición de familias | Si el dato es mejor que el de la actual |
| | Menor exposición a heladas y calor · suelo más protegido | Si el dato es menor que el 90 % del de la actual |
| **Riesgos** | Requiere más agua | Si gasta más de 100 m³/ha por encima de la actual |
| | Valor de mercado menor | Si su ingreso es menor que el de la actual |
| | Un cultivo con baja aptitud | Si la aptitud mínima es menor de 40 |
| | La nota de cada cultivo (Anexo A), una vez por cultivo | Siempre |
| **Vacíos** | Resolución de los datos · valores referenciales de los cultivos · precios desconocidos | Siempre |
| | El suelo es una estimación satelital | Si el suelo viene del satélite |
| | La salinidad requiere análisis | Si el nivel de sal no es «baja» |

### RC-14 Mensaje para WhatsApp
En el idioma elegido, en este orden: encabezado con el nombre del lugar; los 3 cultivos más aptos entre los de aptitud ≥ 40,
con su mes de siembra; el puntaje de la rotación actual; si otra rotación la supera, su nombre, su puntaje y hasta 3
beneficios (si no, una felicitación); y el aviso de consultar al técnico agrario.

### RC-15 Resumen del clima en 4 frases
1. **Lluvia:** si el total anual es menor de 150 mm, «casi no llueve»; si no, el total y los 4 meses más lluviosos en orden de temporada (el año contado desde julio).
2. **Temperatura:** el mes con la máxima media más alta y el mes con la mínima media más baja, con sus valores.
3. **Heladas:** si hay al menos 1 día al año, el total y el mes con más; si no, «prácticamente no hay heladas».
4. **Evaporación:** el total anual y cuántas veces supera a la lluvia (se omite si la lluvia es 0).

### RC-16 Verdor del campo (NDVI)
Serie del 1 de enero de 2023 al 31 de diciembre de 2024, una imagen cada 16 días con resolución de 250 m (MODIS). Los valores sin
dato se descartan. La línea filtrada es la **mediana móvil de 3 valores, centrada**. Hay «suelo desnudo» cuando el valor
filtrado es menor de **0.2**; se listan los meses en que ocurre. La comparación opcional usa VIIRS (500 m).

### RC-17 Humedad del suelo
Promedio 2005–2024, por mes, de la humedad de la capa superficial (0–5 cm) y de la zona de raíces (0–100 cm), en una escala
de 0 (seco) a 1 (saturado) que se muestra en porcentaje. Proviene de un modelo, no de una medición directa.

### RC-18 Lluvia que alimenta el río Ica
- Solo se muestra si la región es costa y el lugar está entre las latitudes −15.2 y −13.4 y las longitudes −76.4 y −75.2.
- Punto de referencia en la cuenca alta: latitud −13.15, longitud −75.07.
- **Temporada** = del 1 de setiembre al 30 de abril. **Promedio histórico** = media de las 19 temporadas de 2005–06 a 2023–24.
- **Última temporada:** la que terminó en abril del año actual si ya es mayo o después; si no, la del año anterior.
- Diferencia porcentual frente al promedio: menor de −15 % «año seco»; mayor de −5 % «normal o húmedo»; entre ambos «ligeramente seco».

### RC-19 Estimación satelital del suelo (opcional)
A pedido del usuario se obtienen arcilla, arena y pH de los primeros 15 cm (promedio de las capas 0–5 y 5–15 cm). Si el punto
no tiene dato (ocurre en pueblos), se prueba a 0.01° al norte, sur, este y oeste, en ese orden, y se avisa que es un punto cercano.
- **Textura:** arcilla ≥ 40 % arcilloso; ≥ 27 % franco-arcilloso; si no, arena ≥ 70 % arenoso; ≥ 50 % franco-arenoso; si no, franco.
- **Clase de pH:** menor de 5.5 ácido; menor de 6.5 ligeramente ácido; hasta 7.5 neutro; mayor alcalino.

### RC-20 Buscador de lugares
- Si el texto son coordenadas válidas (RF-13) se usan directamente.
- Si no, se busca primero en el Perú y, si no hay resultados, en todo el mundo. Hasta 8 resultados, que se ordenan dando
  prioridad a pueblos, caseríos y calles; luego ciudades y barrios; luego distritos, provincias, regiones y departamentos.
  Se eliminan los nombres repetidos y se muestran como máximo 5.
- **Nombre de un punto** (para clic, coordenadas y GPS): de la geocodificación inversa se toman, en este orden, pueblo, ciudad
  menor, ciudad, distrito, provincia y departamento; se muestran los dos primeros distintos.

## 7. Datos externos necesarios

Los servicios concretos, direcciones y parámetros están en `Plan.md`. Aquí solo qué se necesita.

| Dato | Fuente | Periodo y detalle | Uso |
|---|---|---|---|
| Clima diario: temperaturas, lluvia, radiación; altitud del área | NASA POWER | 2005–2024, área de ~50 km | RC-01 a RC-03 |
| Humedad del suelo mensual (superficie y raíces) | NASA POWER (modelo MERRA-2) | 2005–2024 | RC-17 |
| Altitud del punto | NASA SRTM | 90 m | RC-02, RC-06 |
| Lluvia diaria en sierra, altiplano y selva | CHIRPS, servido por NASA SERVIR | 2005–2024, ~5 km | RC-04 |
| Lluvia diaria en la costa | GPM IMERG (NASA) | 2015–2024, ~10 km | RC-04 |
| Verdor del campo (NDVI) | MODIS; VIIRS opcional | 2023–2024, 250 m / 500 m | RC-16 |
| Textura y pH del suelo (opcional) | SoilGrids (ISRIC) | 250 m | RC-19 |
| Búsqueda de lugares y nombre de un punto | OpenStreetMap | — | RC-20 |
| Imagen satelital y nombres para el mapa | Esri World Imagery | — | RF-12 |

## 8. Requisitos no funcionales

- **RNF-01 Sin cuentas.** Ninguna fuente de datos puede exigir registro ni clave.
- **RNF-02 Guardado local.** Toda respuesta de un servicio externo se guarda en disco y se reutiliza. Un lugar ya consultado
  debe abrirse sin conexión a internet (excepto las imágenes del mapa).
- **RNF-03 Lugares de ejemplo.** Un procedimiento descarga por adelantado todos los datos de 7 lugares (Anexo B) para poder
  hacer una demostración sin internet.
- **RNF-04 Tiempos.** Un lugar ya guardado muestra sus iconos habilitados en menos de 5 segundos. Abrir un panel tarda menos
  de 3 segundos. Un lugar nuevo puede tardar hasta 30 segundos en habilitar los iconos y de 1 a 5 minutos en dejar de ser preliminar.
- **RNF-05 Fallos.** Ningún fallo de un servicio externo puede dejar la página en blanco ni mostrar un error técnico sin
  explicación: se informa en lenguaje sencillo y se ofrece reintentar o seguir con lo disponible.
- **RNF-06 Pantallas.** Debe usarse bien en una computadora (1280 × 800) y en un celular (390 px de ancho). En el celular
  los botones se apilan y el panel ocupa el ancho de la pantalla.
- **RNF-07 Accesibilidad.** Todo icono va acompañado de una etiqueta de texto. Los botones principales son grandes.
  El significado no depende solo del color: los niveles llevan también número o texto.
- **RNF-08 Lenguaje.** Frases cortas, sin jerga; los términos técnicos se explican la primera vez que aparecen.
- **RNF-09 Privacidad.** La ubicación del dispositivo solo se pide cuando el usuario toca «Clima» o «Mi ubicación»,
  y solo se usa para consultar los datos de ese punto.
- **RNF-10 Sesión.** Las respuestas del usuario viven mientras la página está abierta; no se guardan entre sesiones.
- **RNF-11 Ancho.** El contenido se centra con un ancho máximo de 1000 px.

## 9. Criterios de aceptación

- **CA-01** Al abrir la página se ven exactamente 2 botones grandes y el botón de idioma (RF-01).
- **CA-02** En Mi terreno, antes de marcar, los 7 iconos están deshabilitados; tras escribir `-14.13, -75.70` y pulsar Enter
  se habilitan y la línea del lugar dice «Pueblo Nuevo, Ica» · «🏜️ Costa desértica · 405 m de altitud · -14.1300, -75.7000».
- **CA-03** Cada uno de los 14 paneles se abre como panel lateral derecho, muestra su contenido sin errores y se cierra
  con Esc, en los 3 lugares de prueba (Ica, Chupaca, Satipo) y en ambos idiomas.
- **CA-04** Para los 7 lugares de ejemplo, con los valores por defecto y los datos guardados de referencia, los resultados
  coinciden con el **Anexo B**: región, fuente de lluvia y nombres exactos; números con una diferencia máxima de 1 unidad.
- **CA-05** En Ica, cambiar el riego a «Sí, agua suficiente» en Mis datos sube la aptitud de la quinua de 76 a 89 y su factor
  limitante pasa a «Sin limitaciones importantes».
- **CA-06** Buscar «Tarma, Junin» lleva directamente a un lugar llamado «Tarma, Junín» (un solo resultado tras quitar repetidos).
- **CA-07** Entrar a Clima con permiso de ubicación muestra «Mi ubicación actual (…)» y el clima de ese punto. Sin permiso
  o sin respuesta en 15 s aparece un aviso que termina en «Escriba su ubicación.» y el buscador.
- **CA-08** En un lugar nuevo de la sierra aparece el aviso de resultados preliminares y desaparece solo cuando llega la lluvia satelital.
- **CA-09** Al pulsar el botón de idioma, toda la página pasa a inglés; con el terreno de Ica, el único texto con tildes o
  «ñ» que queda (fuera de nombres propios) es el botón «Español». Al volver a español, el terreno sigue marcado.
- **CA-10** En inglés, el mensaje de WhatsApp de Ica empieza con «🌱 *Agro Planet* — Pueblo Nuevo, Ica», lista «Quinoa: sow in May»
  y termina con el aviso de consultar al «agricultural advisor».
- **CA-11** A 390 px de ancho no hay desplazamiento horizontal y todos los botones se pueden tocar.
- **CA-12** Con el servicio de imágenes NDVI caído, el panel Satélite muestra un mensaje de error comprensible y el resto de la página sigue funcionando.

## 10. Comportamientos conocidos que se deben conservar

Para que la réplica sea igual al original, estos comportamientos **no se corrigen** en esta versión:

1. La línea de tiempo de una rotación abarca 36 meses; lo que cae después no se cuenta (RC-10).
2. En la costa no se descarga lluvia GPM IMERG para lugares nuevos; se usa la de NASA POWER (RC-04).
3. Los cultivos y sus parámetros son valores referenciales sin validar con agrónomos (Anexo A).
4. El buscador devuelve los nombres de lugares en español aunque la página esté en inglés.
5. Los datos satelitales representan áreas de ~50 km (clima) y 250 m (verdor): no captan el microclima de una quebrada.
6. El orden entre cultivos con la misma aptitud no sigue una regla agronómica: es el del método de ordenación de la
   implementación de referencia (RC-09).

## 11. Decisiones abiertas para quien aprueba este Spec

| N.º | Decisión | Propuesta de este Spec |
|---|---|---|
| D1 | ¿Se incluye también la interfaz clásica con pestañas (`app.py`)? | **No.** El producto final es la interfaz de 2 iconos y paneles laterales. |
| D2 | ¿Se conservan los comportamientos de la sección 10 tal cual? | **Sí**, para que la réplica sea idéntica. Las mejoras irían en una versión 1.1. |
| D3 | ¿Qué tolerancia se acepta en los números del Anexo B? | **±1 unidad**, porque los proveedores pueden reprocesar sus datos. Con los mismos datos guardados la coincidencia es exacta. |

## 12. Glosario

| Término | Significado |
|---|---|
| **Rotación de cultivos** | Alternar cultivos en el mismo terreno, campaña tras campaña, en un orden planificado |
| **Campaña** | Un ciclo de siembra y cosecha |
| **Aptitud** | Número de 0 a 100 que indica qué tan bien se adapta un cultivo al lugar (RC-08) |
| **Evaporación de referencia (ET0)** | Agua que el sol y el viento sacan del suelo y de las plantas; indica cuánta agua necesita un cultivo |
| **Kc** | Coeficiente del cultivo: cuánta agua usa en relación con la ET0 |
| **Lluvia aprovechable** | Parte de la lluvia que realmente usa la planta |
| **NDVI** | Índice de verdor medido por satélite: cerca de 0 es suelo desnudo; cerca de 0.8, vegetación densa |
| **Leguminosa** | Cultivo que aporta nitrógeno al suelo (haba, tarwi, frijol, pallar, maní) |
| **Panel lateral (off-canvas)** | Panel que entra desde un lado de la pantalla y se cierra sin cambiar de página |
| **Inversión térmica** | En la costa peruana, en invierno, el aire de altura no es más frío que el del valle por la capa de nubes del mar |
| **Preliminar** | Resultado calculado antes de que llegue la lluvia satelital del lugar |

---

## Anexo A. Cultivos y sus parámetros

Dieciocho entradas: 17 cultivos y «Descanso». Estos valores son parte de las reglas de cálculo.
Columnas: **Meses** = duración del ciclo · **Kc** = coeficiente de agua · **T óptima / T límite** = temperatura media mensual ·
**Sens.** = sensibilidad de 0 a 1 · **Tol. sal** = tolerancia de 0 a 1 · **N** = efecto en el nitrógeno del suelo ·
**Cobertura** = fracción del suelo que cubre (0 a 1) · **Mercado** = valor referencial de 0 a 5.

| id | Nombre (ES) | Nombre (EN) | Familia | Meses | Kc | T óptima °C | T límite °C | Sens. helada | Sens. calor | Tol. sal | N | Cobertura | Mercado | Forraje | Texturas preferidas | pH |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `algodon` | Algodón | Cotton | malváceas | 7 | 0.85 | 21–30 | 15–38 | 0.6 | 0.2 | 0.9 | -2 | 0.6 | 3 | no | franco, franco-arenoso, franco-arcilloso | 5.8–8.0 |
| `maiz` | Maíz amarillo duro | Yellow maize | gramíneas | 5 | 0.85 | 18–30 | 12–35 | 0.8 | 0.5 | 0.3 | -3 | 0.6 | 3 | sí | franco, franco-arenoso, franco-arcilloso | 5.5–7.8 |
| `pallar` | Pallar | Lima bean (pallar) | leguminosas | 6 | 0.75 | 17–27 | 12–32 | 0.7 | 0.5 | 0.3 | +2 | 0.7 | 4 | no | franco-arenoso, franco, arenoso | 6.0–8.0 |
| `frijol` | Frijol | Common bean | leguminosas | 4 | 0.75 | 16–25 | 10–30 | 0.8 | 0.6 | 0.2 | +2 | 0.6 | 3 | no | franco, franco-arenoso | 5.8–7.5 |
| `camote` | Camote | Sweet potato | convolvuláceas | 5 | 0.80 | 20–28 | 14–34 | 0.8 | 0.3 | 0.5 | -1 | 0.9 | 2 | sí | arenoso, franco-arenoso, franco | 5.2–7.5 |
| `sorgo` | Sorgo | Sorghum | gramíneas | 4 | 0.75 | 22–32 | 14–38 | 0.7 | 0.2 | 0.7 | -2 | 0.6 | 2 | sí | franco, franco-arcilloso, arcilloso, franco-arenoso | 5.5–8.5 |
| `quinua` | Quinua | Quinoa | amarantáceas | 5 | 0.70 | 10–20 | 4–28 | 0.35 | 0.6 | 0.9 | -1 | 0.5 | 4 | no | franco-arenoso, franco, arenoso | 5.5–8.5 |
| `papa` | Papa | Potato | solanáceas | 6 | 0.85 | 10–20 | 5–25 | 0.9 | 0.5 | 0.3 | -3 | 0.6 | 4 | no | franco-arenoso, franco | 5.0–7.0 |
| `haba` | Haba | Faba bean | leguminosas | 6 | 0.80 | 10–20 | 5–26 | 0.5 | 0.5 | 0.4 | +3 | 0.6 | 3 | sí | franco, franco-arcilloso, arcilloso | 6.0–8.0 |
| `tarwi` | Tarwi (chocho) | Tarwi (Andean lupin) | leguminosas | 7 | 0.70 | 10–20 | 5–25 | 0.4 | 0.4 | 0.4 | +3 | 0.6 | 4 | no | franco-arenoso, arenoso, franco | 5.0–7.0 |
| `cebada` | Cebada | Barley | gramíneas | 5 | 0.75 | 10–20 | 4–28 | 0.3 | 0.5 | 0.8 | -2 | 0.7 | 2 | sí | franco, franco-arenoso, franco-arcilloso | 6.0–8.5 |
| `avena` | Avena forrajera | Forage oats | gramíneas | 5 | 0.80 | 10–22 | 4–28 | 0.25 | 0.5 | 0.5 | -2 | 0.8 | 3 | sí | franco, franco-arcilloso, franco-arenoso, arcilloso | 5.0–7.5 |
| `maiz_amilaceo` | Maíz amiláceo | Starchy maize | gramíneas | 7 | 0.85 | 13–22 | 9–28 | 0.8 | 0.4 | 0.3 | -3 | 0.6 | 3 | sí | franco, franco-arenoso, franco-arcilloso | 5.5–7.5 |
| `olluco` | Olluco | Olluco (ulluco) | baseláceas | 7 | 0.80 | 9–17 | 5–22 | 0.6 | 0.5 | 0.3 | -1 | 0.6 | 3 | no | franco, franco-arenoso | 5.0–7.0 |
| `yuca` | Yuca | Cassava | euforbiáceas | 10 | 0.80 | 22–30 | 16–36 | 0.9 | 0.2 | 0.3 | -1 | 0.7 | 2 | sí | arenoso, franco-arenoso, franco | 4.5–7.5 |
| `arroz` | Arroz | Rice | gramíneas | 5 | 1.15 | 22–30 | 15–36 | 0.9 | 0.4 | 0.4 | -3 | 0.8 | 3 | no | arcilloso, franco-arcilloso | 5.0–7.5 |
| `mani` | Maní | Peanut | leguminosas | 4 | 0.75 | 22–30 | 16–35 | 0.9 | 0.3 | 0.4 | +2 | 0.6 | 3 | sí | arenoso, franco-arenoso | 5.5–7.5 |
| `descanso` | Descanso / pasto natural | Fallow / natural pasture | descanso | 12 | 0.30 | -50–50 | -60–60 | 0.0 | 0.0 | 1.0 | +1 | 0.5 | 0 | sí | (cualquiera) | 0–14 |

**Notas de cada cultivo** (se muestran como «riesgos a revisar» de las rotaciones que lo incluyen):

| id | Nota (ES) | Nota (EN) |
|---|---|---|
| `algodon` | Muy tolerante a la sal pero consume mucha agua; atención al gusano rosado y picudo. | Very salt-tolerant but uses a lot of water; watch for pink bollworm and boll weevil. |
| `maiz` | Gran demandante de nitrógeno; el rastrojo sirve de forraje. Sensible a sal. | Heavy nitrogen feeder; the stover can be used as fodder. Salt-sensitive. |
| `pallar` | Leguminosa (en Ica con Denominación de Origen): fija nitrógeno y tiene buen precio. Sensible a sal. | Legume (in Ica with Denomination of Origin): fixes nitrogen and fetches a good price. Salt-sensitive. |
| `frijol` | Ciclo corto y bajo consumo de agua; fija nitrógeno. Muy sensible a sal. | Short cycle and low water use; fixes nitrogen. Very salt-sensitive. |
| `camote` | Cubre muy bien el suelo (menos erosión y evaporación); el follaje es forraje. | Covers the soil very well (less erosion and evaporation); the foliage is fodder. |
| `sorgo` | Tolerante a sequía, calor y sal moderada; buen forraje. Mercado más pequeño. | Tolerates drought, heat and moderate salinity; good fodder. Smaller market. |
| `quinua` | Tolera helada leve, sequía y sal; precio variable. En costa vigilar mildiu y aves. | Tolerates light frost, drought and salt; variable price. On the coast watch for mildew and birds. |
| `papa` | Base de la alimentación; repetirla multiplica gorgojo de los Andes, nematodos y rancha. | Staple food; repeating it multiplies Andean potato weevil, nematodes and late blight. |
| `haba` | Fija nitrógeno; tolera heladas leves mejor que la papa. | Fixes nitrogen; tolerates light frost better than potato. |
| `tarwi` | Leguminosa andina de raíz profunda: fija mucho nitrógeno y aguanta sequía. Requiere desamargado. | Deep-rooted Andean legume: fixes a lot of nitrogen and withstands drought. Needs debittering. |
| `cebada` | Rústica y tolerante al frío; grano y forraje. | Hardy and cold-tolerant; grain and fodder. |
| `avena` | Buen forraje para ganado lechero; cubre bien el suelo. | Good fodder for dairy cattle; covers the soil well. |
| `maiz_amilaceo` | Ciclo largo: más expuesto a heladas al final de campaña. | Long cycle: more exposed to frost at the end of the season. |
| `olluco` | Tubérculo andino de otra familia: rompe el ciclo de plagas de la papa. | Andean tuber from a different family: breaks the potato pest cycle. |
| `yuca` | Muy rústica y tolera suelos ácidos y pobres; ciclo largo. | Very hardy and tolerates acidic, poor soils; long cycle. |
| `arroz` | El cultivo que más agua consume: solo donde el agua sobra. | The most water-demanding crop: only where water is plentiful. |
| `mani` | Leguminosa de clima cálido para suelos sueltos; fija nitrógeno. | Warm-climate legume for loose soils; fixes nitrogen. |
| `descanso` | Recupera el suelo (como en los laymes), pero no genera ingresos ese año. | Restores the soil (as in the traditional Andean fallow), but earns no income that year. |

## Anexo B. Resultados de referencia

Calculados el 15 de noviembre de 2026 con la implementación de referencia y los valores por defecto (RC-07), sin indicar suelo,
en español. Sirven como prueba de aceptación (CA-04).

**B.1 Clima y zona**

| Lugar | Lat, lon | Altitud SRTM | Pendiente | Región detectada | Fuente de lluvia | Lluvia anual | T media anual | Días helada/año | Aptos / Con cuidado / No |
|---|---|---|---|---|---|---|---|---|---|
| Ica — Valle (Pueblo Nuevo) | -14.13, -75.7 | 405 m | 0% (plano) | costa | IMERG | 49 mm | 21.8 °C | 0 | 3 / 11 / 3 |
| Junín — Valle del Mantaro (Chupaca) | -12.06, -75.29 | 3272 m | 15% (ladera) | sierra | CHIRPS | 792 mm | 12.1 °C | 4 | 8 / 1 / 8 |
| Huancavelica — zona altoandina | -12.79, -74.97 | 3788 m | 64% (ladera) | altoandina | CHIRPS | 902 mm | 9.1 °C | 48 | 7 / 0 / 10 |
| Ayacucho — Huamanga | -13.16, -74.22 | 2733 m | 8% (suave) | sierra | CHIRPS | 642 mm | 14.9 °C | 0 | 10 / 1 / 6 |
| Apurímac — Andahuaylas | -13.66, -73.39 | 2894 m | 28% (ladera) | sierra | CHIRPS | 907 mm | 14.2 °C | 0 | 9 / 2 / 6 |
| Puno — Altiplano (Juliaca) | -15.5, -70.13 | 3832 m | 3% (plano) | altoandina | CHIRPS | 498 mm | 9.9 °C | 101 | 4 / 3 / 10 |
| Junín — Selva central (Satipo) | -11.25, -74.64 | 623 m | 2% (plano) | selva | CHIRPS | 1582 mm | 26.7 °C | 0 | 9 / 0 / 8 |

**B.2 Los 5 cultivos más aptos** (aptitud y mejor mes de siembra)

| Lugar | 1.º | 2.º | 3.º | 4.º | 5.º |
|---|---|---|---|---|---|
| Ica — Valle (Pueblo Nuevo) | Quinua **76** (mayo) | Cebada **72** (mayo) | Sorgo **70** (enero) | Avena forrajera **64** (mayo) | Maní **60** (enero) |
| Junín — Valle del Mantaro (Chupaca) | Papa **100** (noviembre) | Olluco **100** (octubre) | Haba **100** (noviembre) | Quinua **100** (diciembre) | Tarwi (chocho) **100** (octubre) |
| Huancavelica — zona altoandina | Avena forrajera **86** (noviembre) | Cebada **85** (noviembre) | Quinua **84** (noviembre) | Olluco **78** (octubre) | Haba **76** (noviembre) |
| Ayacucho — Huamanga | Haba **100** (noviembre) | Avena forrajera **100** (diciembre) | Quinua **100** (diciembre) | Cebada **100** (diciembre) | Tarwi (chocho) **100** (octubre) |
| Apurímac — Andahuaylas | Papa **100** (noviembre) | Maíz amiláceo **100** (noviembre) | Haba **100** (noviembre) | Quinua **100** (noviembre) | Olluco **100** (noviembre) |
| Puno — Altiplano (Juliaca) | Cebada **93** (noviembre) | Quinua **92** (noviembre) | Avena forrajera **91** (noviembre) | Haba **66** (noviembre) | Tarwi (chocho) **63** (octubre) |
| Junín — Selva central (Satipo) | Algodón **100** (octubre) | Maíz amarillo duro **100** (noviembre) | Pallar **100** (diciembre) | Camote **100** (noviembre) | Sorgo **100** (diciembre) |

**B.3 Rotaciones y puntaje total (0–100)**

| Lugar | Rotación actual (típica de la región) | Alternativa A | Alternativa B |
|---|---|---|---|
| Ica — Valle (Pueblo Nuevo) | Algodón → Maíz amarillo duro → Algodón — **56** | Quinua → Avena forrajera → Frijol — **90** | Algodón → Quinua → Maní — **89** |
| Junín — Valle del Mantaro (Chupaca) | Papa → Papa → Cebada — **67** | Avena forrajera → Tarwi (chocho) → Quinua — **97** | Quinua → Tarwi (chocho) → Papa — **96** |
| Huancavelica — zona altoandina | Papa → Papa → Cebada — **65** | Avena forrajera → Quinua → Tarwi (chocho) — **94** | Quinua → Tarwi (chocho) → Papa — **92** |
| Ayacucho — Huamanga | Papa → Papa → Cebada — **67** | Avena forrajera → Tarwi (chocho) → Quinua — **97** | Quinua → Tarwi (chocho) → Papa — **96** |
| Apurímac — Andahuaylas | Papa → Papa → Cebada — **67** | Quinua → Avena forrajera → Tarwi (chocho) — **97** | Quinua → Papa → Tarwi (chocho) — **96** |
| Puno — Altiplano (Juliaca) | Papa → Papa → Cebada — **65** | Quinua → Avena forrajera → Tarwi (chocho) — **94** | Quinua → Tarwi (chocho) → Papa — **93** |
| Junín — Selva central (Satipo) | Maíz amarillo duro → Maíz amarillo duro → Yuca — **58** | Maní → Maíz amarillo duro → Pallar — **96** | Maní → Camote → Pallar — **93** |

## Anexo C. Catálogo de textos

Todos los textos visibles, en español e inglés, están en el archivo **`Spec-anexo-C-textos.md`**.
