"""Paneles de la vista Mi terreno (RF-19, RF-30 a RF-36). T15 define la barra; el contenido llega en T17 y T18."""
from __future__ import annotations

from .common import Panel

# RF-19: en este orden. Cada uno: icono, etiqueta, título del panel y texto de ayuda (Anexo C [1051]–[1065]).
PANELS: list[Panel] = [
    Panel("clima", "🌦️", "Clima", "🌦️ Clima de mi terreno", "Lluvia, temperatura, heladas y riesgos de cada mes"),
    Panel("sembrar", "🌱", "Qué sembrar", "🌱 ¿Qué puedo sembrar aquí?", "Cultivos aptos y su mejor mes de siembra"),
    Panel("rotaciones", "🔄", "Rotaciones", "🔄 Comparar rotaciones", "Su rotación actual frente a 2 alternativas"),
    Panel("satelite", "🛰️", "Satélite", "🛰️ ¿Cuándo está pelado el campo?", "Verdor del campo visto desde el satélite"),
    Panel("whatsapp", "📱", None, "📱 Resumen para WhatsApp", "Mensaje sencillo para enviar", label_literal="WhatsApp"),
    Panel("datos", "⚙️", "Mis datos", "⚙️ Mis datos: riego, suelo y prioridades", "Riego, suelo y lo que más le importa"),
    Panel("ayuda", "ℹ️", "Ayuda", "ℹ️ Cómo funciona RotaSat", "Datos usados, cálculos y limitaciones"),
]
