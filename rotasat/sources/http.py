"""Llamadas HTTP comunes a todas las fuentes (Plan.md §4). Tarea T04.

Siempre hay un tiempo de espera, se envía un User-Agent genérico (sin datos del usuario) y todo fallo se convierte
en SourceError con el nombre del servicio.
"""
from __future__ import annotations

from typing import Any

import requests

from ..cache import SourceError

USER_AGENT = "RotaSat/1.0"
DEFAULT_TIMEOUT = 60  # segundos


def get_json(service: str, url: str, params: dict[str, Any] | None = None, *, timeout: float = DEFAULT_TIMEOUT,
             headers: dict[str, str] | None = None) -> Any:
    try:
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})})
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise SourceError(service, str(e), cause=e) from e
    except ValueError as e:  # el cuerpo no era JSON
        raise SourceError(service, "respuesta no es JSON", cause=e) from e
