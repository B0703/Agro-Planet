"""Caché en disco de las respuestas de servicios externos (RNF-02, RNF-05). Tarea T04.

Hay un archivo JSON por respuesta en `data/cache/{servicio}/{sha1(parámetros)}.json`. Primero se mira el disco y solo
si no está se llama al servicio. Si el servicio falla no se guarda nada y se lanza `SourceError`.

Las coordenadas (cualquier float de los parámetros) se redondean a 4 decimales antes de armar la clave (RF-14), así un
mismo lugar siempre cae en el mismo archivo.

La carpeta se puede cambiar con la variable de entorno ROTASAT_CACHE_DIR, que usan las pruebas.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


class SourceError(Exception):
    """Un servicio externo no respondió o respondió algo inutilizable.

    `service` dice cuál falló y `cause` guarda la excepción original. La interfaz elige el texto sencillo
    del Anexo C según el servicio; `error_name` es el dato que usa el texto [377] («… ({error}). Revise su internet.»).
    """

    def __init__(self, service: str, detail: str = "", cause: BaseException | None = None):
        self.service = service
        self.detail = detail
        self.cause = cause
        super().__init__(f"{service}: {detail or (type(cause).__name__ if cause else 'error')}")

    @property
    def error_name(self) -> str:
        return type(self.cause).__name__ if self.cause is not None else "SourceError"


def cache_dir() -> Path:
    return Path(os.environ.get("ROTASAT_CACHE_DIR") or DEFAULT_DIR)


def _normalize(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return value


def cache_key(params: dict[str, Any]) -> str:
    canonical = json.dumps(_normalize(params), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()


def path_for(service: str, params: dict[str, Any]) -> Path:
    return cache_dir() / service / f"{cache_key(params)}.json"


def has(service: str, params: dict[str, Any]) -> bool:
    return path_for(service, params).is_file()


def load(service: str, params: dict[str, Any]) -> Any | None:
    """Datos guardados, o None si no están (o si el archivo está dañado)."""
    p = path_for(service, params)
    try:
        with p.open(encoding="utf-8") as f:
            return json.load(f)["data"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def save(service: str, params: dict[str, Any], data: Any) -> None:
    """Escritura atómica: se escribe un archivo temporal y luego se renombra, para que un hilo en segundo plano
    (descarga de CHIRPS, RC-05) nunca deje un archivo a medias que otro lea."""
    p = path_for(service, params)
    p.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "service": service,
        "params": _normalize(params),
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": data,
    }
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
        os.replace(tmp, p)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(service: str, params: dict[str, Any]) -> threading.Lock:
    key = f"{service}/{cache_key(params)}"
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def get_or_fetch(service: str, params: dict[str, Any], fetch: Callable[[], Any]) -> Any:
    """Datos de la caché o, si no están, los de `fetch()`, que se guardan.

    Cualquier excepción de `fetch` se convierte en SourceError (si no lo era ya) y no se guarda nada.
    Dos llamadas simultáneas con los mismos parámetros hacen una sola consulta.
    """
    cached = load(service, params)
    if cached is not None:
        return cached
    with _lock_for(service, params):
        cached = load(service, params)  # otro hilo pudo haberlo traído mientras esperábamos
        if cached is not None:
            return cached
        try:
            data = fetch()
        except SourceError:
            raise
        except Exception as e:  # noqa: BLE001 - todo fallo externo se informa igual (RNF-05)
            raise SourceError(service, cause=e) from e
        if data is None:
            raise SourceError(service, "respuesta vacía")
        save(service, params, data)
        return data
