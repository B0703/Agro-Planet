"""Paneles de la vista Clima (§5.5, RF-51 a RF-57). T15 define la barra; el contenido llega en T20."""
from __future__ import annotations

from .common import Panel

RIVER = "rio"                   # solo en la cuenca de Ica (la vista lo quita fuera de ella, T20)

# §5.5: en este orden. Etiqueta y ayuda: Anexo C [654]–[668]; títulos: [625]–[641], [654], [667].
PANELS: list[Panel] = [
    Panel("calendario", "📅", "Calendario", "📅 Calendario de riesgos", "Riesgos de cada mes: heladas, calor, lluvia"),
    Panel("lluvia", "🌧️", "Lluvia", "🌧️ Lluvia y evaporación", "Cuánto llueve cada mes y cuánta agua se evapora"),
    Panel("temperatura", "🌡️", "Temperatura", "🌡️ Temperatura y heladas", "Temperaturas de cada mes y heladas"),
    Panel("humedad", "🟫", "Humedad del suelo", "🟫 Humedad del suelo", "Cuándo está seco o húmedo el suelo"),
    Panel("tendencia", "📈", "Tendencia", "📈 ¿Está cambiando el clima aquí?", "Cómo ha cambiado el clima en 20 años"),
    Panel(RIVER, "💧", "Río", "💧 ¿Traerá agua el río?", "Lluvia en la cuenca alta que alimenta el río Ica"),
    Panel("datos", "🔬", "Sobre los datos", "🔬 Cómo se ajustaron los datos a este lugar", "De dónde salen los datos"),
]
