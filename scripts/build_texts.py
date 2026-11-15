"""Genera rotasat/texts_data.py a partir del Anexo C (specs/Spec-anexo-C-textos.md). Tarea T03.

    python scripts/build_texts.py           # escribe rotasat/texts_data.py
    python scripts/build_texts.py --check   # sale con código 1 si el archivo generado está desactualizado

El Anexo C se generó desde el código de referencia, así que sus marcadores `{...}` son expresiones de Python
(`{ctx['elev']:,.0f}`). Aquí cada expresión se cambia por un nombre de campo (`{elev:,.0f}`) según PLACEHOLDERS.
El formato numérico se conserva tal cual. Si aparece una expresión que no está en la tabla, el script falla.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANNEX = ROOT / "specs" / "Spec-anexo-C-textos.md"
OUT = ROOT / "rotasat" / "texts_data.py"

# Expresión del código de referencia → nombre del campo. Cuando ES y EN usan expresiones distintas para el mismo
# dato (porque EN lo traduce), las dos van al mismo campo: quien llama pasa el valor ya traducido.
PLACEHOLDERS: dict[str, str] = {
    "n": "n",
    "e[0]": "motivo", "e[1]": "motivo",
    "e": "error", "type(e).__name__": "error",
    "ctx['elev']": "elev",
    "total": "total", "top": "top",
    "mes(mc)": "mes_calor", "mes(mf)": "mes_frio", "tx": "tx", "tn": "tn",
    "h": "h", "mh": "mh",
    "et0": "et0", "et0 / total": "ratio",
    "clim['dias_helada'].sum()": "dias",
    "fuente_txt(info['fuente_lluvia'])": "fuente", "info['fuente_lluvia']": "fuente",
    "' · '.join(comp)": "comp",
    "p90": "p90", "mcal": "mcal",
    "seco": "seco", "humedo": "humedo",
    "'subió' if d > 0 else 'bajó'": "direccion", "'rose' if d > 0 else 'fell'": "direccion",
    "abs(d)": "d_abs",
    "cu['nombre']": "cuenca",
    "t['temporada']": "temporada", "temporada_txt(t['temporada'])": "temporada",
    "delta": "delta",
    "info['elev_celda']": "elev_celda", "info['ajuste_c']": "ajuste",
    "len(apt)": "n", "i + 1": "n",
    "lista": "lista", "s.mean()": "ndvi",
    "rel['pendiente_pct']": "pendiente",
    "est['textura']": "textura", "agro.textura_txt(est['textura'])": "textura",
    "est['phh2o']": "ph", "clase_ph(est['phh2o'])": "ph_clase",
    "cu['meses']": "meses",
    "r['t_min_ciclo']": "t", "r['t_max_ciclo']": "t", "o0": "o0", "o1": "o1",
    "r['expo_helada']": "expo", "r['lluvia_cubre'] * 100": "pct", "r['riego_m3ha']": "riego",
    "', '.join(cu['texturas'])": "texturas",
    "', '.join((TEXTURAS_EN.get(t, t) for t in cu['texturas']))": "texturas",
    "cu['ph'][0]": "ph_min", "cu['ph'][1]": "ph_max",
    "', '.join(legs)": "legs", "meses_txt": "meses_txt",
    "c['aptitud']": "aptitud", "b['aptitud']": "aptitud_actual",
    "c['agua_m3ha']": "agua",
    "_mes(mh)": "mes", "clim.loc[mh, 'dias_helada']": "dias",
    "_mes(mc)": "mes", "clim.loc[mc, 'dias_calor']": "dias",
    "c['meses_desnudo']": "meses",
    "d": "d", "d / 30": "cisternas", "-d": "extra",
    "c['n_bal']": "n_bal", "b['n_bal']": "n_bal_actual",
    "actual.total": "total", "op": "op", "mejor.total": "total",
}

# Entradas que son solo un valor del vocabulario (`{x}` / `{PENDIENTES_EN[x]}`) y que ya cubre la sección C.3/C.4.
VALUE_ONLY = {"{x}", "{PH[k][1]}"}

# Palabras que el original metía dentro de un marcador condicional ([563]); se agregan como entradas propias.
EXTRA = {"subió": "rose", "bajó": "fell"}

# Encabezado en negrita de cada tabla de C.3/C.4 → nombre del grupo.
TABLES = {
    "¿Tiene riego?": "riego",
    "¿Salitre o agua salobre?": "sal",
    "Errores de ubicación (GPS)": "gps_error",
    "Columnas de la tabla de cultivos": "columna",
    "pH del suelo": "ph",
    "Regiones": "region",
    "Criterios de puntaje": "criterio",
    "Texturas de suelo": "textura",
    "Pendiente": "pendiente",
    "Meses": "mes",
}

_FORMAT = re.compile(r"^[+,]*(\.\d+)?[fd]$")
_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")


def _rename(text: str, ref: str) -> str:
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        expr, fmt = inner, ""
        if ":" in inner:
            head, tail = inner.rsplit(":", 1)
            if _FORMAT.match(tail):
                expr, fmt = head, ":" + tail
        if expr not in PLACEHOLDERS:
            raise SystemExit(f"[{ref}] marcador sin nombre en PLACEHOLDERS: {{{inner}}}")
        return "{" + PLACEHOLDERS[expr] + fmt + "}"

    return _PLACEHOLDER.sub(repl, text).replace("\\n", "\n")


def parse_strings(text: str) -> dict[str, dict[str, str]]:
    """Secciones C.1 y C.2: {'ui': {es: en}, 'engine': {es: en}}."""
    out: dict[str, dict[str, str]] = {}
    for section, name in (("## C.1", "ui"), ("## C.2", "engine")):
        start = text.index(section)
        block = text[text.index("```text\n", start) + 8:]
        block = block[:block.index("\n```")]
        table: dict[str, str] = {}
        for ref, es, en in re.findall(r"^\[(\d+)\]\nES\| ?(.*)\nEN\| ?(.*)$", block, re.M):
            if es in VALUE_ONLY:
                continue
            es_r, en_r = _rename(es, ref), _rename(en, ref)
            if table.get(es_r, en_r) != en_r:
                raise SystemExit(f"[{ref}] el mismo texto ES tiene dos traducciones: {es_r!r}")
            table[es_r] = en_r
        out[name] = table
    out["engine"].update(EXTRA)
    return out


def parse_tables(text: str) -> dict[str, list[list[str]]]:
    """Secciones C.3 y C.4: {grupo: [[celdas de la fila], ...]} sin el encabezado."""
    out: dict[str, list[list[str]]] = {}
    lines = text[text.index("## C.3"):].splitlines()
    for i, ln in enumerate(lines):
        if not ln.startswith("**"):
            continue
        title = ln.strip("*").split("**")[0]
        group = next((g for prefix, g in TABLES.items() if title.startswith(prefix)), None)
        if group is None:
            raise SystemExit(f"tabla desconocida en el Anexo C: {title!r}")
        rows = []
        j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith("|")) + 2  # salta encabezado y ---
        while j < len(lines) and lines[j].startswith("|"):
            rows.append([c.strip().strip("`") for c in lines[j].strip("|").split("|")])
            j += 1
        out[group] = rows
    missing = set(TABLES.values()) - set(out)
    if missing:
        raise SystemExit(f"faltan tablas en el Anexo C: {sorted(missing)}")
    return out


def render() -> str:
    text = ANNEX.read_text(encoding="utf-8")
    strings = parse_strings(text)
    tables = parse_tables(text)
    parts = [
        '"""Catálogo de textos ES/EN. GENERADO por scripts/build_texts.py desde el Anexo C. No editar a mano."""\n',
        "# fmt: off\n",
        f"UI = {strings['ui']!r}\n",
        f"ENGINE = {strings['engine']!r}\n",
        f"TABLES = {tables!r}\n",
    ]
    return "".join(parts)


def main() -> None:
    content = render()
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != content:
            print("rotasat/texts_data.py está desactualizado: ejecute python scripts/build_texts.py")
            sys.exit(1)
        print("rotasat/texts_data.py al día")
        return
    OUT.write_text(content, encoding="utf-8")
    print(f"escrito {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
