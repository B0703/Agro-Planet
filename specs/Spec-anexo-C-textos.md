# RotaSat — Anexo C del Spec: catálogo de textos (español / inglés)

Generado automáticamente desde el código de referencia. **Todo texto visible debe coincidir con este catálogo.**

Convenciones:
- `ES|` texto en español · `EN|` texto en inglés.
- `{...}` es un valor calculado; lo que va después de `:` es el formato numérico (`:,.0f` = entero con separador de miles; `:.1f` = un decimal; `:+.0f` = con signo).
- `\n` es un salto de línea. Los `**…**` son negritas (Markdown).
- El número entre corchetes es la línea del archivo de referencia; sirve solo para ubicar el texto.

## C.1 Interfaz (`app_simple.py`)

```text
[187]
ES| Actual
EN| Current

[196]
ES| Mi ubicación actual
EN| My current location

[198]
ES| Terreno en {n}
EN| Field in {n}

[198]
ES| Terreno marcado en el mapa
EN| Field marked on the map

[199]
ES| Coordenadas
EN| Coordinates

[212]
ES|  y 
EN|  and 

[224]
ES| ligeramente ácido
EN| slightly acidic

[224]
ES| ácido
EN| acidic

[225]
ES| alcalino
EN| alkaline

[225]
ES| neutro
EN| neutral

[290]
ES| English
EN| Español

[291]
ES| Switch the page to English
EN| Cambiar la página a español

[296]
ES| Inicio
EN| Home

[297]
ES| Volver a la pantalla de inicio
EN| Back to the home screen

[308]
ES| Dirección, pueblo o coordenadas
EN| Address, town or coordinates

[309]
ES| Dirección o pueblo…  o coordenadas: -14.13, -75.70
EN| Address or town…  or coordinates: -14.13, -75.70

[311]
ES| Buscar
EN| Search

[312]
ES| Mi ubicación
EN| My location

[313]
ES| Usar la ubicación de este dispositivo (GPS)
EN| Use this device's location (GPS)

[320]
ES| Buscando…
EN| Searching…

[324]
ES| El buscador no respondió. Pruebe otra vez, escriba coordenadas o haga clic en el mapa.
EN| The search did not respond. Try again, type coordinates or click on the map.

[327]
ES| No encontramos ese lugar. Pruebe con el nombre del distrito o escriba coordenadas.
EN| We could not find that place. Try the district name or type coordinates.

[335]
ES| ¿Cuál de estos lugares es?
EN| Which of these places is it?

[343]
ES| 📍 Buscando su ubicación… Si el navegador le pregunta, elija **Permitir**.
EN| 📍 Finding your location… If the browser asks, choose **Allow**.

[351]
ES| {e[0]} Escriba su ubicación.
EN| {e[1]} Please type your location.

[373]
ES| Leyendo 20 años de datos de la NASA para este lugar…
EN| Reading 20 years of NASA data for this place…

[377]
ES| No se pudieron obtener los datos de la NASA ({type(e).__name__}). Revise su internet.
EN| NASA data could not be retrieved ({type(e).__name__}). Check your internet connection.

[379]
ES| Reintentar
EN| Retry

[385]
ES| El servicio de lluvia satelital no respondió. Se usa la lluvia de NASA POWER, que **subestima la lluvia en sierra y selva**.
EN| The satellite rainfall service did not respond. NASA POWER rainfall is used instead, which **underestimates rain in the highlands and rainforest**.

[389]
ES| Reintentar lluvia satelital
EN| Retry satellite rainfall

[398]
ES| ⏳ Descargando 20 años de lluvia satelital de este lugar (1 a 5 min). Mientras tanto los resultados son **preliminares** y se actualizarán solos.
EN| ⏳ Downloading 20 years of satellite rainfall for this place (1 to 5 min). Meanwhile the results are **preliminary** and will update on their own.

[407]
ES|  · {ctx['elev']:,.0f} m de altitud
EN|  · {ctx['elev']:,.0f} m altitude

[418]
ES| 🌧️ **Casi no llueve**: {total:,.0f} mm al año. Aquí los cultivos dependen del riego.
EN| 🌧️ **It hardly rains**: {total:,.0f} mm a year. Crops here depend on irrigation.

[422]
ES| 🌧️ Llueven **{total:,.0f} mm al año**, sobre todo en {top}.
EN| 🌧️ It rains **{total:,.0f} mm a year**, mostly in {top}.

[426]
ES| 🌡️ El mes más caluroso es **{mes(mc)}** (máxima media de {tx:.0f} °C) y el más frío es **{mes(mf)}** (mínima media de {tn:.0f} °C).
EN| 🌡️ The hottest month is **{mes(mc)}** (mean maximum of {tx:.0f} °C) and the coldest is **{mes(mf)}** (mean minimum of {tn:.0f} °C).

[433]
ES| ❄️ Hay riesgo de helada unos **{h:.0f} días al año**, sobre todo en **{mh}**.
EN| ❄️ There is frost risk on about **{h:.0f} days a year**, mostly in **{mh}**.

[436]
ES| ❄️ Prácticamente **no hay heladas**.
EN| ❄️ There is practically **no frost**.

[438]
ES| 💨 El sol y el viento evaporan **{et0:,.0f} mm al año**: {et0 / total:.1f} veces lo que llueve.
EN| 💨 Sun and wind evaporate **{et0:,.0f} mm a year**: {et0 / total:.1f} times the rainfall.

[445]
ES| 🌧️ Lluvia al año
EN| 🌧️ Rain per year

[446]
ES| 🌡️ Temperatura media
EN| 🌡️ Mean temperature

[447]
ES| ❄️ Días con riesgo de helada
EN| ❄️ Frost-risk days

[448]
ES| {clim['dias_helada'].sum():.0f} al año
EN| {clim['dias_helada'].sum():.0f} per year

[453]
ES| ❄️ Días con riesgo de helada
EN| ❄️ Frost-risk days

[454]
ES| 🔥 Días de calor extremo
EN| 🔥 Extreme-heat days

[455]
ES| 🌡️ Temperatura media (°C)
EN| 🌡️ Mean temperature (°C)

[456]
ES| 🌧️ Lluvia (mm)
EN| 🌧️ Rain (mm)

[457]
ES| 💨 Evaporación (mm)
EN| 💨 Evaporation (mm)

[459]
ES| 🟫 Humedad del suelo, raíces (%)
EN| 🟫 Soil moisture, root zone (%)

[466]
ES| Cada casilla es el promedio de ese mes en 20 años. En cada fila, **más rojo = valor más alto**. Helada: mínima de 2 °C o menos. Calor extremo: días entre el 10% más caluroso del lugar.
EN| Each cell is that month's average over 20 years. In each row, **redder = higher value**. Frost: minimum of 2 °C or below. Extreme heat: days among the hottest 10% for this place.

[475]
ES| Lluvia
EN| Rain

[476]
ES| Evaporación
EN| Evaporation

[478]
ES| mm por mes
EN| mm per month

[481]
ES| Cuando la línea naranja (evaporación) está por encima de las barras (lluvia), al suelo le falta agua y el cultivo necesita riego o aguantar la sequía.
EN| When the orange line (evaporation) is above the bars (rain), the soil is short of water and the crop needs irrigation or must withstand drought.

[486]
ES| **Fuente de la lluvia:** {fuente_txt(info['fuente_lluvia'])} → **{total:,.0f} mm al año**.
EN| **Rainfall source:** {fuente_txt(info['fuente_lluvia'])} → **{total:,.0f} mm a year**.

[492]
ES| Comparación de productos en este punto (mm al año): {' · '.join(comp)}. Usamos CHIRPS en sierra y selva (calibrado con estaciones) y GPM IMERG en la costa.
EN| Comparison of products at this point (mm a year): {' · '.join(comp)}. We use CHIRPS in the highlands and rainforest (calibrated with rain gauges) and GPM IMERG on the coast.

[501]
ES| Media
EN| Mean

[501]
ES| Máxima
EN| Maximum

[502]
ES| Mínima
EN| Minimum

[507]
ES| **❄️ Días con riesgo de helada por mes**
EN| **❄️ Frost-risk days per month**

[510]
ES| Mínima de 2 °C o menos
EN| Minimum of 2 °C or below

[512]
ES| Mínima de 0 °C o menos
EN| Minimum of 0 °C or below

[513]
ES| días
EN| days

[517]
ES| ❄️ En este lugar prácticamente no hay heladas.
EN| ❄️ There is practically no frost at this location.

[519]
ES| Calor extremo para este lugar: días con máxima sobre {p90:.1f} °C (el 10% más caluroso). Mes con más calor extremo: {mcal}.
EN| Extreme heat for this place: days with a maximum above {p90:.1f} °C (the hottest 10%). Month with the most extreme heat: {mcal}.

[528]
ES| No se pudo obtener la humedad del suelo en este momento.
EN| Soil moisture could not be retrieved right now.

[533]
ES| Superficie (0–5 cm)
EN| Surface (0–5 cm)

[535]
ES| Zona de raíces (0–100 cm)
EN| Root zone (0–100 cm)

[537]
ES| % (0 seco · 100 saturado)
EN| % (0 dry · 100 saturated)

[540]
ES| La superficie del suelo está más seca en **{seco}** y más húmeda en **{humedo}**.
EN| The soil surface is driest in **{seco}** and wettest in **{humedo}**.

[542]
ES| Modelo MERRA-2 de NASA POWER (~50 km). Cumple el papel de SMAP y GLDAS sin requerir cuenta. 
EN| NASA POWER MERRA-2 model (~50 km). It plays the role of SMAP and GLDAS without requiring an account. 

[544]
ES| En la costa el modelo **no ve el riego**: úselo solo como referencia.
EN| On the coast the model **does not see irrigation**: use it only as a reference.

[553]
ES| Temperatura máxima media de cada año (°C)
EN| Mean maximum temperature of each year (°C)

[559]
ES| Días con riesgo de helada por año
EN| Frost-risk days per year

[560]
ES| Días de calor extremo por año
EN| Extreme-heat days per year

[563]
ES| Entre 2005–2009 y 2020–2024 la temperatura máxima media **{'subió' if d > 0 else 'bajó'} {abs(d):.1f} °C**.
EN| Between 2005–2009 and 2020–2024 the mean maximum temperature **{'rose' if d > 0 else 'fell'} {abs(d):.1f} °C**.

[569]
ES| El agua del río Ica nace como lluvia en la {cu['nombre']}. Si allá llueve poco, el río trae poco y se depende más de los pozos de un acuífero ya sobreexplotado.
EN| The Ica river's water starts as rain in the upper Huancavelica basin (Choclococha). If it rains little there, the river carries little water and farmers depend more on wells in an already overexploited aquifer.

[574]
ES| Calculando la lluvia de la cuenca alta…
EN| Calculating rainfall in the upper basin…

[577]
ES| No se pudo calcular la lluvia de la cuenca alta en este momento.
EN| Rainfall in the upper basin could not be calculated right now.

[581]
ES| Temporada {t['temporada']}
EN| Season {temporada_txt(t['temporada'])}

[582]
ES| {delta:+.0f}% frente al promedio
EN| {delta:+.0f}% vs. average

[583]
ES| 🔴 **Año seco**: priorizar cultivos de bajo consumo de agua.
EN| 🔴 **Dry year**: prioritize low-water crops.

[585]
ES| 🟢 **Año normal o húmedo**.
EN| 🟢 **Normal or wet year**.

[586]
ES| 🟡 **Ligeramente seco**.
EN| 🟡 **Slightly dry**.

[589]
ES| promedio
EN| average

[591]
ES| mm (setiembre a abril)
EN| mm (September to April)

[597]
ES| **Temperatura corregida por altitud**
EN| **Temperature corrected for altitude**

[599]
ES| Los datos de NASA POWER promedian un área de ~50 km cuya altitud media es **{info['elev_celda']:,.0f} m**, pero este lugar está a **{ctx['elev']:,.0f} m** (NASA SRTM). Como la temperatura cambia 6.5 °C por cada 1,000 m, se corrigió en **{info['ajuste_c']:+.1f} °C**.
EN| NASA POWER data average an area of ~50 km whose mean altitude is **{info['elev_celda']:,.0f} m**, but this place is at **{ctx['elev']:,.0f} m** (NASA SRTM). Since temperature changes 6.5 °C per 1,000 m, it was corrected by **{info['ajuste_c']:+.1f} °C**.

[605]
ES|  En la **costa** hay inversión térmica (la capa de nubes del mar): la corrección se aplica completa en verano y nada en invierno.
EN|  On the **coast** there is a thermal inversion (the marine cloud layer): the correction is applied fully in summer and not at all in winter.

[610]
ES| No se obtuvo la altitud real (SRTM): se usan las temperaturas sin corregir.
EN| The real altitude (SRTM) could not be obtained: uncorrected temperatures are used.

[612]
ES| **Fuentes**
EN| **Sources**

[613]
ES| - Temperatura, radiación y humedad del suelo: NASA POWER (2005–2024)\n- Lluvia: {info['fuente_lluvia']}\n- Altitud y pendiente: NASA SRTM (90 m)
EN| - Temperature, radiation and soil moisture: NASA POWER (2005–2024)\n- Rainfall: {fuente_txt(info['fuente_lluvia'])}\n- Altitude and slope: NASA SRTM (90 m)

[617]
ES| Los satélites promedian áreas grandes: en una quebrada el microclima real puede ser distinto. Conviene comparar con una estación del SENAMHI o un termómetro en el campo.
EN| Satellites average large areas: in a ravine the real microclimate may differ. It is worth comparing with a SENAMHI weather station or a thermometer in the field.

[625]
ES| 🌧️ Lluvia y evaporación
EN| 🌧️ Rain and evaporation

[629]
ES| 🌡️ Temperatura y heladas
EN| 🌡️ Temperature and frost

[633]
ES| 🟫 Humedad del suelo
EN| 🟫 Soil moisture

[637]
ES| 📈 ¿Está cambiando el clima aquí?
EN| 📈 Is the climate changing here?

[641]
ES| 💧 ¿Traerá agua el río?
EN| 💧 Will the river bring water?

[654]
ES| Calendario
EN| Calendar

[654]
ES| 📅 Calendario de riesgos
EN| 📅 Risk calendar

[655]
ES| Riesgos de cada mes: heladas, calor, lluvia
EN| Risks of each month: frost, heat, rain

[656]
ES| Lluvia
EN| Rain

[657]
ES| Cuánto llueve cada mes y cuánta agua se evapora
EN| How much it rains each month and how much water evaporates

[658]
ES| Temperatura
EN| Temperature

[659]
ES| Temperaturas de cada mes y heladas
EN| Temperatures of each month and frost

[660]
ES| Humedad del suelo
EN| Soil moisture

[661]
ES| Cuándo está seco o húmedo el suelo
EN| When the soil is dry or wet

[662]
ES| Tendencia
EN| Trend

[663]
ES| Cómo ha cambiado el clima en 20 años
EN| How the climate has changed in 20 years

[664]
ES| Río
EN| River

[665]
ES| Lluvia en la cuenca alta que alimenta el río Ica
EN| Rainfall in the upper basin that feeds the Ica river

[666]
ES| Sobre los datos
EN| About the data

[667]
ES| 🔬 Cómo se ajustaron los datos a este lugar
EN| 🔬 How the data were adjusted to this place

[668]
ES| De dónde salen los datos
EN| Where the data come from

[690]
ES| 🔬 Cómo se ajustaron los datos
EN| 🔬 How the data were adjusted

[704]
ES| ⏳ **Resultado preliminar**: aún no llega la lluvia satelital de este lugar. En sierra y selva muchos cultivos aparecerán limitados por agua hasta que llegue.
EN| ⏳ **Preliminary result**: satellite rainfall for this place has not arrived yet. In the highlands and rainforest many crops will appear water-limited until it does.

[709]
ES| 🟢 Aptos
EN| 🟢 Suitable

[710]
ES| 🟡 Con cuidado
EN| 🟡 With care

[711]
ES| 🔴 No recomendados
EN| 🔴 Not recommended

[712]
ES| ##### Los más recomendados para este terreno
EN| ##### Most recommended for this field

[717]
ES| sembrar en
EN| sow in

[720]
ES| El número es la aptitud de 0 a 100 según temperatura, heladas, agua, sal y suelo, sembrando en el mejor mes.
EN| The number is the suitability from 0 to 100 based on temperature, frost, water, salt and soil, sowing in the best month.

[724]
ES| ℹ️ Aún no indicó su tipo de suelo: la aptitud usa solo clima, agua y sal. Puede indicarlo en **Mis datos**.
EN| ℹ️ You have not entered your soil type yet: suitability uses only climate, water and salt. You can enter it in **My data**.

[727]
ES| 📋 Ver los {len(apt)} cultivos evaluados
EN| 📋 See the {len(apt)} crops evaluated

[736]
ES| 📆 ¿En qué mes conviene sembrar cada cultivo?
EN| 📆 Which month is best to sow each crop?

[737]
ES| Elija un cultivo
EN| Choose a crop

[742]
ES| Aptitud si siembra ese mes
EN| Suitability if sown that month

[744]
ES| 🤝 Es una **orientación**: las variedades locales, el manejo y el mercado pueden cambiar la decisión. Converse con su técnico agrario.
EN| 🤝 This is **guidance**: local varieties, management and the market can change the decision. Talk to your agricultural advisor.

[755]
ES| ✏️ Mi rotación actual: 
EN| ✏️ My current rotation: 

[756]
ES|  (toque para cambiarla)
EN|  (tap to change it)

[761]
ES| Campaña {i + 1}
EN| Season {i + 1}

[763]
ES| Mes de siembra
EN| Sowing month

[772]
ES| No se encontraron cultivos aptos suficientes para proponer alternativas en este lugar.
EN| Not enough suitable crops were found to propose alternatives at this location.

[775]
ES| ⭐ Recomendada
EN| ⭐ Recommended

[781]
ES| La alternativa A es la mejor para sus prioridades; la B conserva su cultivo principal cuando es apto. Puede cambiar sus prioridades en **Mis datos**.
EN| Alternative A is the best for your priorities; B keeps your main crop when it is suitable. You can change your priorities in **My data**.

[785]
ES| ##### 📅 Línea de tiempo (3 años)
EN| ##### 📅 Timeline (3 years)

[801]
ES| año
EN| year

[803]
ES| Los huecos son meses con el suelo desnudo.
EN| Gaps are months with bare soil.

[804]
ES| ##### 🔍 ¿Por qué? Toque una opción
EN| ##### 🔍 Why? Tap an option

[809]
ES| 🤔 Por qué se sugiere
EN| 🤔 Why it is suggested

[810]
ES| 🛰️ Evidencia (datos NASA)
EN| 🛰️ Evidence (NASA data)

[811]
ES| ✅ Beneficios frente a la rotación actual
EN| ✅ Benefits compared with the current rotation

[812]
ES| ⚠️ Riesgos a revisar con un experto local
EN| ⚠️ Risks to review with a local expert

[813]
ES| ❓ Vacíos de información
EN| ❓ Information gaps

[816]
ES| 🤝 RotaSat **apoya, no reemplaza** la experiencia del agricultor ni la asesoría de un agrónomo.
EN| 🤝 RotaSat **supports, it does not replace** the farmer's experience or an agronomist's advice.

[822]
ES| El índice **NDVI** del satélite MODIS mide qué tan verde está el terreno cada 16 días. Cuando baja de **0.2**, el suelo está prácticamente **desnudo**.
EN| The **NDVI** index from the MODIS satellite measures how green the land is every 16 days. When it drops below **0.2**, the soil is practically **bare**.

[828]
ES| Consultar el satélite (2023–2024)
EN| Query the satellite (2023–2024)

[829]
ES| Puede tardar si el servidor de la NASA está lento
EN| It may take a while if the NASA server is slow

[834]
ES| Consultando MODIS…
EN| Querying MODIS…

[838]
ES| El servidor de imágenes de la NASA (ORNL) no respondió. Inténtelo más tarde.
EN| NASA's image server (ORNL) did not respond. Try again later.

[843]
ES| dato crudo
EN| raw value

[845]
ES| NDVI filtrado
EN| filtered NDVI

[847]
ES| suelo desnudo
EN| bare soil

[851]
ES| ninguno
EN| none

[852]
ES| **Meses con el campo pelado:** {lista} · NDVI promedio {s.mean():.2f}
EN| **Months with a bare field:** {lista} · mean NDVI {s.mean():.2f}

[854]
ES| Un píxel de 250 m puede mezclar varias parcelas, caminos o cerros. Marque el centro de su campo.
EN| A 250 m pixel can mix several plots, roads or hills. Mark the centre of your field.

[856]
ES| 🛰️ Comparar con VIIRS, el sucesor de MODIS (opcional)
EN| 🛰️ Compare with VIIRS, the successor to MODIS (optional)

[858]
ES| Los satélites de MODIS están al final de su vida útil; VIIRS (500 m) asegura la continuidad. En este servicio VIIRS tiene datos hasta mayo de 2024.
EN| The MODIS satellites are at the end of their service life; VIIRS (500 m) ensures continuity. In this service VIIRS has data up to May 2024.

[862]
ES| Agregar VIIRS
EN| Add VIIRS

[864]
ES| Consultando VIIRS…
EN| Querying VIIRS…

[872]
ES| VIIRS no está disponible ahora. La app sigue funcionando con MODIS.
EN| VIIRS is not available right now. The app keeps working with MODIS.

[881]
ES| Un resumen sencillo para enviar al agricultor:
EN| A simple summary to send to the farmer:

[883]
ES| Abrir en WhatsApp
EN| Open in WhatsApp

[898]
ES| Estos valores se **dedujeron de la ubicación** con datos satelitales (altitud, lluvia y relieve). Cámbielos solo si conoce mejor su chacra: sus respuestas mandan.
EN| These values were **inferred from the location** using satellite data (altitude, rainfall and terrain). Change them only if you know your field better: your answers take priority.

[902]
ES| ##### 🧭 Zona y agua
EN| ##### 🧭 Zone and water

[904]
ES|  (detectada por altitud y lluvia)
EN|  (detected from altitude and rainfall)

[904]
ES| Región
EN| Region

[912]
ES| ⛰️ Pendiente del terreno
EN| ⛰️ Terrain slope

[913]
ES| {x}
EN| {PENDIENTES_EN[x]}

[914]
ES| El relieve SRTM estima {rel['pendiente_pct']:.0f}% de pendiente
EN| SRTM terrain data estimate a {rel['pendiente_pct']:.0f}% slope

[919]
ES| 💧 ¿Tiene riego?
EN| 💧 Do you have irrigation?

[924]
ES| ##### 🟫 Suelo
EN| ##### 🟫 Soil

[926]
ES| Tipo de suelo
EN| Soil type

[927]
ES| No sé
EN| I don't know

[929]
ES| ❓ ¿Cómo saber mi tipo de suelo? (prueba de la bolita)
EN| ❓ How do I find out my soil type? (ribbon test)

[931]
ES| Tome un puñado de tierra, humedézcala y amásela:\n1. **No forma bolita**, se desmorona → **arenoso**\n2. Forma bolita pero **se rompe** al apretarla → **franco-arenoso**\n3. Forma bolita y una **cinta corta** (menos de 2 cm) → **franco**\n4. Forma una **cinta de 2 a 5 cm** → **franco-arcilloso**\n5. Forma una **cinta larga**, pegajosa y brillante → **arcilloso**
EN| Take a handful of soil, moisten it and knead it:\n1. **It won't form a ball**, it crumbles → **sandy**\n2. It forms a ball but **breaks** when squeezed → **sandy loam**\n3. It forms a ball and a **short ribbon** (under 2 cm) → **loam**\n4. It forms a **ribbon of 2 to 5 cm** → **clay loam**\n5. It forms a **long ribbon**, sticky and shiny → **clay**

[944]
ES| pH (si tiene un análisis de suelo)
EN| pH (if you have a soil analysis)

[945]
ES| {PH[k][1]}
EN| {PH[k][2]}

[947]
ES| 🧂 ¿Ve costra blanca (salitre) o el agua es salobre?
EN| 🧂 Do you see a white crust (salt) or is the water brackish?

[952]
ES| Estimar mi suelo con satélite (SoilGrids)
EN| Estimate my soil by satellite (SoilGrids)

[953]
ES| Consultando SoilGrids…
EN| Querying SoilGrids…

[957]
ES| {e}. Indique su suelo a mano arriba.
EN| SoilGrids did not respond or has no data here. Enter your soil by hand above.

[961]
ES| Estimación satelital: **{est['textura']}**, pH {est['phh2o']:.1f} ({clase_ph(est['phh2o'])})
EN| Satellite estimate: **{agro.textura_txt(est['textura'])}**, pH {est['phh2o']:.1f} ({clase_ph(est['phh2o'])})

[963]
ES|  · punto cercano (en pueblos no hay dato)
EN|  · nearby point (no data inside towns)

[965]
ES| . Si usted conoce su suelo, su respuesta manda.
EN| . If you know your soil, your answer takes priority.

[966]
ES| ##### 🎯 ¿Qué es más importante para usted?
EN| ##### 🎯 What matters most to you?

[967]
ES| 0 = no me importa · 5 = es lo más importante
EN| 0 = I don't mind · 5 = it matters most

[970]
ES| Volver a los valores detectados
EN| Back to the detected values

[976]
ES| RotaSat convierte 20 años de datos satelitales de la NASA en una recomendación sencilla: **qué sembrar, cuándo y en qué orden**.
EN| RotaSat turns 20 years of NASA satellite data into a simple recommendation: **what to plant, when and in what order**.

[980]
ES| 🛰️ Datos que usa
EN| 🛰️ Data it uses

[981]
ES| \n| Dato | Para qué |\n|---|---|\n| **NASA POWER** (2005–2024) | Temperatura, heladas, calor, evaporación y humedad del suelo |\n| **NASA SRTM** (90 m) | Altitud real y pendiente del terreno |\n| **CHIRPS** (vía NASA SERVIR) | Lluvia en sierra, altiplano y selva |\n| **GPM IMERG** (NASA) | Lluvia en la costa |\n| **MODIS / VIIRS** | Verdor del campo (NDVI): meses con suelo desnudo |\n| **SoilGrids** (opcional) | Estimación del suelo; el dato del agricultor manda |\n
EN| \n| Data | What for |\n|---|---|\n| **NASA POWER** (2005–2024) | Temperature, frost, heat, evaporation and soil moisture |\n| **NASA SRTM** (90 m) | Real altitude and terrain slope |\n| **CHIRPS** (via NASA SERVIR) | Rainfall in the highlands, altiplano and rainforest |\n| **GPM IMERG** (NASA) | Rainfall on the coast |\n| **MODIS / VIIRS** | Field greenness (NDVI): months with bare soil |\n| **SoilGrids** (optional) | Soil estimate; the farmer's own answer takes priority |\n

[1000]
ES| 🧮 Cómo se calcula
EN| 🧮 How it is calculated

[1001]
ES| \n- **Aptitud de un cultivo:** temperatura × heladas × agua × sal × suelo, probando los 12 meses de siembra.\n- **Agua:** evaporación de referencia (FAO-56) × coeficiente del cultivo − lluvia aprovechable.\n- **Rotaciones:** todas las combinaciones de 3 cultivos aptos, sin repetir familia seguida y con una leguminosa.\n- **Puntaje:** aptitud, agua, nitrógeno, plagas, clima, ingresos, erosión y sal, según **sus prioridades**.\n
EN| \n- **Crop suitability:** temperature × frost × water × salt × soil, testing all 12 sowing months.\n- **Water:** reference evaporation (FAO-56) × crop coefficient − usable rainfall.\n- **Rotations:** every combination of 3 suitable crops, never repeating a family back to back and including a legume.\n- **Score:** suitability, water, nitrogen, pests, climate, income, erosion and salt, weighted by **your priorities**.\n

[1012]
ES| 📚 Recursos del reto: qué usamos y por qué
EN| 📚 Challenge resources: what we use and why

[1013]
ES| \n| Recurso | Decisión | Razón |\n|---|---|---|\n| NASA POWER, GPM IMERG, MODIS, VIIRS, SRTM | ✅ Usados | Ver «Datos que usa» |\n| SMAP y GLDAS | 🔁 Sustituidos | Piden cuenta; usamos la humedad del suelo de POWER (MERRA-2) |\n| NLDAS | ⛔ No aplica | Solo cubre Norteamérica |\n| ECOSTRESS | ⏭️ Próximo paso | Pasa a horas irregulares y solo desde 2018 |\n| Landsat | ⏭️ Próximo paso | Pocas imágenes sin nubes en la sierra; procesamiento pesado |\n\nLos recursos del USDA, USGS y PRISM solo cubren EE. UU. Sus equivalentes en Perú: PISCO del SENAMHI,\nSIEA y SISAP del MIDAGRI, la ANA y los estudios de suelos del INIA.\n
EN| \n| Resource | Decision | Reason |\n|---|---|---|\n| NASA POWER, GPM IMERG, MODIS, VIIRS, SRTM | ✅ Used | See “Data it uses” |\n| SMAP and GLDAS | 🔁 Replaced | They require an account; we use POWER soil moisture (MERRA-2) |\n| NLDAS | ⛔ Not applicable | Covers North America only |\n| ECOSTRESS | ⏭️ Next step | Irregular overpass times and data only since 2018 |\n| Landsat | ⏭️ Next step | Few cloud-free images in the highlands; heavy processing |\n\nThe USDA, USGS and PRISM resources cover the United States only. Their Peruvian equivalents: SENAMHI's PISCO,\nMIDAGRI's SIEA and SISAP, the ANA water authority and INIA soil studies.\n

[1036]
ES| ⚠️ Limitaciones
EN| ⚠️ Limitations

[1037]
ES| \n- Los satélites promedian áreas grandes: el microclima de una quebrada puede ser distinto.\n- Los datos de los 17 cultivos son referenciales y **deben validarse con agrónomos locales**.\n- No incluye precios de mercado actuales.\n- **RotaSat apoya, no reemplaza** al agricultor ni al agrónomo.\n
EN| \n- Satellites average large areas: the microclimate of a ravine may be different.\n- The data for the 17 crops are reference values and **must be validated with local agronomists**.\n- Current market prices are not included.\n- **RotaSat supports, it does not replace** the farmer or the agronomist.\n

[1051]
ES| Clima
EN| Climate

[1051]
ES| 🌦️ Clima de mi terreno
EN| 🌦️ Climate of my field

[1052]
ES| Lluvia, temperatura, heladas y riesgos de cada mes
EN| Rain, temperature, frost and risks of each month

[1053]
ES| Qué sembrar
EN| What to plant

[1053]
ES| 🌱 ¿Qué puedo sembrar aquí?
EN| 🌱 What can I plant here?

[1054]
ES| Cultivos aptos y su mejor mes de siembra
EN| Suitable crops and their best sowing month

[1055]
ES| Rotaciones
EN| Rotations

[1055]
ES| 🔄 Comparar rotaciones
EN| 🔄 Compare rotations

[1056]
ES| Su rotación actual frente a 2 alternativas
EN| Your current rotation against 2 alternatives

[1057]
ES| Satélite
EN| Satellite

[1057]
ES| 🛰️ ¿Cuándo está pelado el campo?
EN| 🛰️ When is the field bare?

[1058]
ES| Verdor del campo visto desde el satélite
EN| Field greenness seen from the satellite

[1059]
ES| 📱 Resumen para WhatsApp
EN| 📱 Summary for WhatsApp

[1060]
ES| Mensaje sencillo para enviar
EN| A simple message to send

[1061]
ES| Mis datos
EN| My data

[1062]
ES| ⚙️ Mis datos: riego, suelo y prioridades
EN| ⚙️ My data: irrigation, soil and priorities

[1063]
ES| Riego, suelo y lo que más le importa
EN| Irrigation, soil and what matters most to you

[1064]
ES| Ayuda
EN| Help

[1064]
ES| ℹ️ Cómo funciona RotaSat
EN| ℹ️ How RotaSat works

[1065]
ES| Datos usados, cálculos y limitaciones
EN| Data used, calculations and limitations

[1074]
ES| Qué sembrar, cuándo y en qué orden, con datos de la NASA
EN| What to plant, when and in what order, with NASA data

[1078]
ES| Mi terreno
EN| My field

[1079]
ES| Marque su chacra en el mapa y vea qué sembrar
EN| Mark your field on the map and see what to plant

[1080]
ES| Marque su chacra y vea qué sembrar
EN| Mark your field and see what to plant

[1083]
ES| Clima
EN| Climate

[1084]
ES| Vea el clima del lugar donde está ahora
EN| See the climate of the place where you are now

[1085]
ES| El clima del lugar donde está ahora
EN| The climate of the place where you are now

[1090]
ES| 🗺️ Mi terreno
EN| 🗺️ My field

[1104]
ES| Mi terreno
EN| My field

[1117]
ES| 👆 **Marque su terreno** para empezar: escriba su dirección o coordenadas, use su ubicación, o haga clic en el mapa.
EN| 👆 **Mark your field** to begin: type your address or coordinates, use your location, or click on the map.

[1128]
ES| Toque un icono para ver esa información:
EN| Tap an icon to see that information:

[1129]
ES| Estos iconos se activan al marcar su terreno:
EN| These icons are enabled once you mark your field:

[1136]
ES| 🌦️ Clima de mi ubicación
EN| 🌦️ Climate at my location

[1142]
ES| ¿No aparece el permiso o prefiere otro lugar? Escríbalo aquí:
EN| No permission prompt, or prefer another place? Type it here:

[1145]
ES| **¿De qué lugar quiere ver el clima?**
EN| **Which place do you want the climate for?**

[1158]
ES| Toque un icono para ver el detalle:
EN| Tap an icon to see the details:

[1161]
ES| Ver qué puedo sembrar aquí
EN| See what I can plant here

[1163]
ES| Cambiar de lugar
EN| Change place

```

## C.2 Textos que genera el motor (`agro.py`)

```text
[240]
ES| Sin limitaciones importantes
EN| No major limitations

[241]
ES| 🟡 Con cuidado
EN| 🟡 With care

[241]
ES| 🟢 Apto
EN| 🟢 Suitable

[242]
ES| 🔴 No recomendado
EN| 🔴 Not recommended

[246]
ES| {cu['meses']} meses
EN| {cu['meses']} months

[257]
ES| Muy frío para este cultivo (media {r['t_min_ciclo']:.0f} °C; prefiere {o0}–{o1} °C)
EN| Too cold for this crop (mean {r['t_min_ciclo']:.0f} °C; prefers {o0}–{o1} °C)

[259]
ES| Muy caluroso (media {r['t_max_ciclo']:.0f} °C; prefiere {o0}–{o1} °C)
EN| Too hot (mean {r['t_max_ciclo']:.0f} °C; prefers {o0}–{o1} °C)

[262]
ES| Riesgo de heladas durante la campaña ({r['expo_helada']:.0f} puntos de exposición)
EN| Frost risk during the season ({r['expo_helada']:.0f} exposure points)

[266]
ES| La lluvia solo cubre {r['lluvia_cubre'] * 100:.0f}% de lo que necesita: requiere riego
EN| Rainfall covers only {r['lluvia_cubre'] * 100:.0f}% of its needs: irrigation required

[268]
ES| Necesita mucha agua de riego (~{r['riego_m3ha']:,.0f} m³/ha)
EN| Needs a lot of irrigation water (~{r['riego_m3ha']:,.0f} m³/ha)

[271]
ES| Poco tolerante a la sal
EN| Low salt tolerance

[273]
ES| Prefiere suelos {', '.join(cu['texturas'])}
EN| Prefers {', '.join((TEXTURAS_EN.get(t, t) for t in cu['texturas']))} soils

[275]
ES| Prefiere pH {cu['ph'][0]}–{cu['ph'][1]}
EN| Prefers pH {cu['ph'][0]}–{cu['ph'][1]}

[438]
ES| Es la rotación que el agricultor usa hoy: sirve como punto de comparación.
EN| This is the rotation the farmer uses today: it is the baseline for comparison.

[441]
ES| Armada automáticamente con los cultivos más aptos para el clima y suelo de esta chacra, cada uno en su mejor mes de siembra.
EN| Built automatically from the crops best suited to this field's climate and soil, each in its best sowing month.

[447]
ES| Incluye leguminosas ({', '.join(legs)}) que fijan nitrógeno del aire y reducen la necesidad de fertilizante.
EN| Includes legumes ({', '.join(legs)}) that fix nitrogen from the air and reduce the need for fertilizer.

[450]
ES| Ninguna familia de cultivo se repite: se corta el ciclo de plagas y enfermedades.
EN| No crop family repeats: this breaks the pest and disease cycle.

[452]
ES| en
EN| in

[453]
ES| Siembras: {meses_txt}.
EN| Sowings: {meses_txt}.

[454]
ES| Aptitud promedio de sus cultivos en este lugar: **{c['aptitud']:.0f}/100**.
EN| Average suitability of its crops at this location: **{c['aptitud']:.0f}/100**.

[457]
ES| Necesidad de riego estimada en 3 años: **{c['agua_m3ha']:,.0f} m³/ha** (ET0 de NASA POWER × coeficiente de cultivo − lluvia efectiva).
EN| Estimated irrigation need over 3 years: **{c['agua_m3ha']:,.0f} m³/ha** (NASA POWER ET0 × crop coefficient − effective rainfall).

[462]
ES| Agua que la lluvia no cubre en 3 años: **{c['agua_m3ha']:,.0f} m³/ha** (NASA POWER).
EN| Water not covered by rainfall over 3 years: **{c['agua_m3ha']:,.0f} m³/ha** (NASA POWER).

[466]
ES| Mes con más riesgo de helada: **{_mes(mh)}** ({clim.loc[mh, 'dias_helada']:.0f} días/año con mínima ≤ 2 °C).
EN| Month with the highest frost risk: **{_mes(mh)}** ({clim.loc[mh, 'dias_helada']:.0f} days/year with minimum ≤ 2 °C).

[470]
ES| Mes con más calor extremo: **{_mes(mc)}** ({clim.loc[mc, 'dias_calor']:.0f} días/año sobre {p90:.1f} °C, el percentil 90 local).
EN| Month with the most extreme heat: **{_mes(mc)}** ({clim.loc[mc, 'dias_calor']:.0f} days/year above {p90:.1f} °C, the local 90th percentile).

[474]
ES| Meses con suelo desnudo en 3 años: **{c['meses_desnudo']}**.
EN| Months with bare soil over 3 years: **{c['meses_desnudo']}**.

[479]
ES| Ahorra ~**{d:,.0f} m³ de agua por hectárea** en 3 años frente a la rotación actual (≈ {d / 30:,.0f} camiones cisterna de 30 m³).
EN| Saves ~**{d:,.0f} m³ of water per hectare** over 3 years compared with the current rotation (≈ {d / 30:,.0f} tanker trucks of 30 m³).

[484]
ES| Requiere ~{-d:,.0f} m³/ha MÁS agua que la rotación actual.
EN| Needs ~{-d:,.0f} m³/ha MORE water than the current rotation.

[487]
ES| Cultivos mejor adaptados a este lugar (aptitud {c['aptitud']:.0f} vs {b['aptitud']:.0f}).
EN| Crops better suited to this location (suitability {c['aptitud']:.0f} vs {b['aptitud']:.0f}).

[490]
ES| Mejor balance de nitrógeno ({c['n_bal']:+d} vs {b['n_bal']:+d}): menos urea que comprar.
EN| Better nitrogen balance ({c['n_bal']:+d} vs {b['n_bal']:+d}): less urea to buy.

[493]
ES| Menos repetición de familias → menor presión de plagas del suelo.
EN| Less repetition of crop families → lower soil-pest pressure.

[496]
ES| Menor exposición a heladas/calor según el clima histórico del lugar.
EN| Lower exposure to frost and heat according to the location's historical climate.

[499]
ES| Suelo más protegido en meses de lluvia → menos erosión.
EN| Soil better protected in rainy months → less erosion.

[502]
ES| Valor de mercado referencial menor: verificar precios y compradores locales antes de cambiar.
EN| Lower reference market value: check prices and local buyers before switching.

[505]
ES| ⚠️ Al menos un cultivo tiene baja aptitud para este lugar (ver «¿Qué puedo sembrar aquí?»).
EN| ⚠️ At least one crop has low suitability for this location (see “What can I plant here?”).

[510]
ES| NASA POWER tiene celdas de ~50 km; la temperatura se corrigió por altitud con SRTM, pero en quebradas el microclima puede diferir. Validar con estación SENAMHI o un termómetro en campo.
EN| NASA POWER has ~50 km cells; temperature was corrected for altitude with SRTM, but in ravines the microclimate may differ. Validate with a SENAMHI weather station or a thermometer in the field.

[514]
ES| Coeficientes de cultivo, rangos de temperatura y fechas de siembra son referenciales; varían según variedad.
EN| Crop coefficients, temperature ranges and sowing dates are reference values; they vary by variety.

[516]
ES| No se conocen precios actuales ni acceso a mercados: el puntaje de ingresos es indicativo.
EN| Current prices and market access are unknown: the income score is indicative.

[520]
ES| El tipo de suelo es una estimación de SoilGrids (250 m): confírmelo con la prueba de la bolita o un análisis de suelo.
EN| The soil type is a SoilGrids estimate (250 m): confirm it with the ribbon test or a soil analysis.

[523]
ES| La salinidad real requiere un análisis de suelo y agua (conductividad eléctrica).
EN| Actual salinity requires a soil and water analysis (electrical conductivity).

[533]
ES| Cultivos más aptos para su chacra:
EN| Best-suited crops for your field:

[534]
ES| sembrar en
EN| sow in

[536]
ES| Su rotación actual obtiene *{actual.total:.0f}/100*.
EN| Your current rotation scores *{actual.total:.0f}/100*.

[540]
ES| La opción *{op}* obtiene *{mejor.total:.0f}/100*.
EN| The option *{op}* scores *{mejor.total:.0f}/100*.

[542]
ES| ¿Por qué?
EN| Why?

[544]
ES| Su rotación actual ya es la mejor de las comparadas. ¡Bien hecho!
EN| Your current rotation is already the best of those compared. Well done!

[546]
ES| ⚠️ Orientación con datos satelitales de la NASA. Converse con su técnico agrario antes de decidir.
EN| ⚠️ Guidance based on NASA satellite data. Talk to your agricultural advisor before deciding.

```

## C.3 Opciones de formularios y mensajes de error

**¿Tiene riego? (clave interna → ES / EN)**

| Clave | ES | EN |
|---|---|---|
| `no` | No, solo lluvia | No, rain only |
| `limitada` | Sí, pero el agua es limitada | Yes, but water is limited |
| `suficiente` | Sí, agua suficiente | Yes, enough water |

**¿Salitre o agua salobre?**

| Clave | ES | EN |
|---|---|---|
| `baja` | No | No |
| `media` | Un poco | A little |
| `alta` | Mucho | A lot |

**Errores de ubicación (GPS); al mostrarlos se añade « Escriba su ubicación.» / « Please type your location.»**

| Clave | ES | EN |
|---|---|---|
| `denegado` | No se dio permiso para usar la ubicación. | Location permission was not granted. |
| `tiempo` | La ubicación tardó demasiado en responder. | Getting the location took too long. |
| `no_disponible` | El dispositivo no pudo obtener la ubicación. | The device could not get the location. |
| `no_soportado` | Este navegador no permite obtener la ubicación. | This browser cannot provide the location. |

**Columnas de la tabla de cultivos (ES → EN)**

| Clave | ES | EN |
|---|---|---|
| — | Cultivo | Crop |
| — | Aptitud | Suitability |
| — | Nivel | Level |
| — | Mejor mes de siembra | Best sowing month |
| — | Ciclo | Cycle |
| — | Lluvia cubre | Rain covers |
| — | Riego necesario (m³/ha) | Irrigation needed (m³/ha) |
| — | Factor limitante | Limiting factor |

**pH del suelo (clave → valor usado en el cálculo, ES, EN)**

| Clave | Valor | ES | EN |
|---|---|---|---|
| `nose` | None | No sé | I don't know |
| `acido` | 5.0 | Ácido (menos de 5.5) | Acidic (below 5.5) |
| `lig` | 6.0 | Ligeramente ácido (5.5–6.5) | Slightly acidic (5.5–6.5) |
| `neutro` | 7.0 | Neutro (6.5–7.5) | Neutral (6.5–7.5) |
| `alcalino` | 8.0 | Alcalino (más de 7.5) | Alkaline (above 7.5) |

## C.4 Vocabulario del dominio

**Regiones**

| Clave | ES | EN |
|---|---|---|
| `costa` | 🏜️ Costa desértica | 🏜️ Desert coast |
| `sierra` | ⛰️ Sierra (valles interandinos) | ⛰️ Highlands (inter-Andean valleys) |
| `altoandina` | 🏔️ Zona altoandina / altiplano | 🏔️ High Andes / altiplano |
| `selva` | 🌴 Selva / ceja de selva | 🌴 Rainforest / cloud forest |

**Criterios de puntaje**

| Clave | ES | EN |
|---|---|---|
| `aptitud` | 🌍 Aptitud al lugar | 🌍 Suitability to the place |
| `agua` | 💧 Agua | 💧 Water |
| `suelo` | 🌱 Suelo (nitrógeno) | 🌱 Soil (nitrogen) |
| `plagas` | 🐛 Plagas | 🐛 Pests |
| `clima` | ❄️🌡️ Riesgo climático | ❄️🌡️ Climate risk |
| `ingresos` | 💰 Ingresos | 💰 Income |
| `erosion` | ⛰️ Erosión / suelo desnudo | ⛰️ Erosion / bare soil |
| `sal` | 🧂 Salinidad | 🧂 Salinity |

**Texturas de suelo** (la clave interna es el nombre en español)

| ES | EN |
|---|---|
| arenoso | sandy |
| franco-arenoso | sandy loam |
| franco | loam |
| franco-arcilloso | clay loam |
| arcilloso | clay |

**Pendiente**

| ES | EN |
|---|---|
| plano | flat |
| suave | gentle |
| ladera | steep |

**Meses** (en frases: español en minúscula, inglés con mayúscula)

| N.º | ES | EN | Abrev. ES | Abrev. EN |
|---|---|---|---|---|
| 1 | enero | January | Ene | Jan |
| 2 | febrero | February | Feb | Feb |
| 3 | marzo | March | Mar | Mar |
| 4 | abril | April | Abr | Apr |
| 5 | mayo | May | May | May |
| 6 | junio | June | Jun | Jun |
| 7 | julio | July | Jul | Jul |
| 8 | agosto | August | Ago | Aug |
| 9 | setiembre | September | Sep | Sep |
| 10 | octubre | October | Oct | Oct |
| 11 | noviembre | November | Nov | Nov |
| 12 | diciembre | December | Dic | Dec |

Los nombres y notas de los cultivos están en el Anexo A del Spec.
