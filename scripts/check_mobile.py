"""Revisión a 390 px de ancho (CA-11, RNF-06), con Chrome sin ventana. Tarea T21.

    python scripts/check_mobile.py                 # 390 × 844, como un celular
    python scripts/check_mobile.py --width 1280 --height 800 --no-mobile   # computadora (RNF-06)
    python scripts/check_mobile.py --lang en       # en inglés

Arranca la app (`streamlit run app_simple.py`) en un puerto libre y abre Chrome (o Edge) con el protocolo de depuración
(CDP) mediante `websockets`, que ya viene con Streamlit: no hace falta instalar nada más. Recorre Inicio, Mi terreno con
Ica (`-14.13, -75.70`) y sus 7 paneles, y Clima con la ubicación del navegador simulada en Ica y sus 7 paneles. En cada
pantalla comprueba:

- que no hay desplazamiento horizontal (`scrollWidth` ≤ ancho de la ventana);
- que cada botón visible (los del panel, si hay uno abierto) cae dentro del ancho de la pantalla, mide al menos
  24 px de alto y recibe el toque en su centro (`elementFromPoint`).

Usa los datos de `data/cache/` (corra antes `scripts/prefetch.py`). Guarda capturas en `--shots` si se pide.
Sale con 1 si algo falla.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parent.parent
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "msedge",
]
ICA = (-14.13, -75.70)
TERRENO = ["clima", "sembrar", "rotaciones", "satelite", "whatsapp", "datos", "ayuda"]
CLIMA = ["calendario", "lluvia", "temperatura", "humedad", "tendencia", "rio", "datos"]
MIN_HEIGHT = 24                 # px: un botón más bajo es difícil de tocar
TOUCH_MIN = 0.5                 # al menos la mitad del ancho del botón dentro de la pantalla

CHECK_JS = r"""
(() => {
  const vw = window.innerWidth, de = document.documentElement;
  const out = {scrollWidth: Math.max(de.scrollWidth, document.body.scrollWidth), width: vw, problems: []};
  const dialog = document.querySelector('[role="dialog"]');
  if (dialog) {                                                         // RNF-06: en el celular el panel ocupa el ancho
    const r = dialog.getBoundingClientRect();
    if (vw <= 640 && (r.left > 1 || r.right < vw - 1)) out.problems.push(`el panel no ocupa el ancho (${r.left|0}–${r.right|0})`);
  }
  const scope = dialog || document;
  // Un elemento más ancho que la pantalla dentro del contenido principal o del panel también es un problema.
  for (const b of scope.querySelectorAll('button')) {
    const r = b.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;                    // oculto
    if (getComputedStyle(b).visibility !== 'visible') continue;         // p. ej. «Copiar» de st.code: solo al pasar el cursor
    if (b.closest('[data-testid="stToolbar"], [data-testid="stHeader"], .modebar')) continue;
    if (b.closest('details:not([open])') && !b.closest('summary')) continue;
    const label = (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 40);
    if (r.left < -1 || r.right > vw + 1) out.problems.push(`fuera de la pantalla: «${label}» (${r.left|0}–${r.right|0})`);
    if (r.height < %(min_h)d) out.problems.push(`muy bajo (${r.height|0} px): «${label}»`);
    const top = Math.max(r.top, 0), bottom = Math.min(r.bottom, window.innerHeight);
    if (bottom <= top) continue;                                        // fuera de la vista vertical: se llega con scroll
    const x = Math.min(Math.max((r.left + r.right) / 2, 1), vw - 1), y = (top + bottom) / 2;
    const hit = document.elementFromPoint(x, y);
    if (!(hit && (hit === b || b.contains(hit)))) {
      const who = hit ? (hit.getAttribute('data-testid') || hit.tagName) : 'nada';
      out.problems.push(`tapado por ${who}: «${label}»`);
    }
  }
  return JSON.stringify(out);
})()
""".replace("%(min_h)d", str(MIN_HEIGHT))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def find_browser() -> str:
    for b in BROWSERS:
        path = shutil.which(b) or (b if os.path.exists(b) else None)
        if path:
            return path
    raise SystemExit("No se encontró Chrome ni Edge.")


def wait_http(url: str, seconds: float = 60) -> str:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return r.read().decode()
        except OSError:
            time.sleep(0.5)
    raise SystemExit(f"No respondió {url}")


class Page:
    """Una pestaña de Chrome por CDP (solo lo necesario)."""

    def __init__(self, ws_url: str):
        self.ws = connect(ws_url, max_size=None, open_timeout=20).__enter__()
        self.n = 0

    def send(self, method: str, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv(timeout=120))
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def js(self, expr: str):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError(r["exceptionDetails"].get("text"))
        return r["result"].get("value")

    def wait(self, expr: str, seconds: float = 60, what: str = "") -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.js(f"!!({expr})"):
                return
            time.sleep(0.3)
        raise TimeoutError(what or expr)

    def idle(self, seconds: float = 90) -> None:
        """Espera a que Streamlit termine de ejecutar (sin el indicador «Running») y un respiro para dibujar."""
        time.sleep(0.6)
        self.wait("!document.querySelector('[data-testid=\"stStatusWidget\"] [data-testid=\"stStatusWidgetRunningIcon\"],"
                  " [data-testid=\"stStatusWidget\"] img') && !document.querySelector('[data-testid=\"stSpinner\"]')",
                  seconds, "la app sigue ejecutando")
        time.sleep(0.8)

    def click(self, css: str, what: str) -> None:
        self.wait(f"document.querySelector({json.dumps(css)})", 60, what)
        self.js(f"document.querySelector({json.dumps(css)}).click()")
        self.idle()

    def type_into(self, css: str, text: str) -> None:
        self.wait(f"document.querySelector({json.dumps(css)})", 60, css)
        self.js(f"""(() => {{
            const el = document.querySelector({json.dumps(css)});
            const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            el.focus(); set.call(el, {json.dumps(text)});
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
        }})()""")
        time.sleep(0.4)

    def escape(self) -> None:
        for kind in ("keyDown", "keyUp"):
            self.send("Input.dispatchKeyEvent", type=kind, key="Escape", code="Escape", windowsVirtualKeyCode=27)
        self.idle()

    def shot(self, path: Path) -> None:
        data = self.send("Page.captureScreenshot", format="png")["data"]
        path.write_bytes(base64.b64decode(data))


def run(args) -> int:
    port, cdp = free_port(), free_port()
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    app = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "app_simple.py"),
                            "--server.headless", "true", "--server.port", str(port),
                            "--browser.gatherUsageStats", "false"], cwd=ROOT, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    profile = tempfile.mkdtemp(prefix="rotasat-cdp-")
    browser = subprocess.Popen([find_browser(), "--headless=new", f"--remote-debugging-port={cdp}",
                                f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
                                f"--window-size={args.width},{args.height}", "about:blank"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shots = Path(args.shots) if args.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    failures = 0
    try:
        wait_http(f"http://127.0.0.1:{port}/_stcore/health")
        tabs = json.loads(wait_http(f"http://127.0.0.1:{cdp}/json"))
        page = Page(next(t for t in tabs if t["type"] == "page")["webSocketDebuggerUrl"])
        page.send("Runtime.enable")
        page.send("Page.enable")
        page.send("Emulation.setDeviceMetricsOverride", width=args.width, height=args.height,
                  deviceScaleFactor=3 if args.mobile else 1, mobile=args.mobile)
        if args.mobile:
            page.send("Emulation.setTouchEmulationEnabled", enabled=True)
        page.send("Browser.grantPermissions", permissions=["geolocation"])
        page.send("Emulation.setGeolocationOverride", latitude=ICA[0], longitude=ICA[1], accuracy=10)
        page.send("Page.navigate", url=f"http://127.0.0.1:{port}/")
        page.wait("document.querySelector('.st-key-home_terreno button')", 90, "Inicio")
        page.idle()

        def check(name: str) -> None:
            nonlocal failures
            r = json.loads(page.js(CHECK_JS))
            problems = list(r["problems"])
            if r["scrollWidth"] > r["width"] + 1:
                problems.insert(0, f"desplazamiento horizontal: {r['scrollWidth']} px > {r['width']} px")
            failures += bool(problems)
            print(f"{'✓' if not problems else '✗'} {name}")
            for p in problems:
                print(f"    {p}")
            if shots:
                page.shot(shots / f"{len(list(shots.glob('*.png'))):02d}-{name.replace('/', '-')}.png")

        if args.lang == "en":
            page.click(".st-key-lang_btn button", "botón de idioma")
        check("inicio")

        # Mi terreno con Ica y sus 7 paneles.
        page.click(".st-key-home_terreno button", "Mi terreno")
        check("terreno/sin-lugar")
        page.type_into(".st-key-terreno_place_q input", f"{ICA[0]}, {ICA[1]}")
        page.js("[...document.querySelectorAll('button')].find(b => /Buscar|Search/.test(b.innerText)).click()")
        page.wait("document.querySelector('.st-key-bar_terreno_clima button:not([disabled])')", 90, "iconos")
        page.idle()
        check("terreno")
        for p in TERRENO:
            page.click(f".st-key-bar_terreno_{p} button", p)
            page.wait("document.querySelector('[role=\"dialog\"]')", 60, f"panel {p}")
            page.idle()
            check(f"terreno/{p}")
            page.escape()
            page.wait("!document.querySelector('[role=\"dialog\"]')", 20, f"cerrar {p} con Esc")

        # Clima: la ubicación del navegador está simulada en Ica.
        page.click(".st-key-home_back button", "Inicio")
        page.click(".st-key-home_clima button", "Clima")
        page.wait("document.querySelector('.st-key-bar_clima_calendario button')", 90, "iconos del clima")
        page.idle()
        check("clima")
        for p in CLIMA:
            page.click(f".st-key-bar_clima_{p} button", p)
            page.wait("document.querySelector('[role=\"dialog\"]')", 120, f"panel {p}")
            page.idle(180)
            check(f"clima/{p}")
            page.escape()
            page.wait("!document.querySelector('[role=\"dialog\"]')", 20, f"cerrar {p} con Esc")
    finally:
        browser.terminate()
        app.terminate()
        for proc in (browser, app):
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(profile, ignore_errors=True)
    print(f"\n{'Todo bien' if not failures else f'{failures} pantallas con problemas'} a {args.width} × {args.height} px.")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--width", type=int, default=390)
    ap.add_argument("--height", type=int, default=844)
    ap.add_argument("--no-mobile", dest="mobile", action="store_false", help="sin emulación de celular")
    ap.add_argument("--lang", choices=["es", "en"], default="es")
    ap.add_argument("--shots", help="carpeta donde guardar una captura de cada pantalla")
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
