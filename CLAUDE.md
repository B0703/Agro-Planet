# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

Progress is tracked in `specs/task.md`; T01–T08 are done. The git repo has no commits yet.

## Commands

A local venv lives in `.venv/`. On Windows, call it directly:

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m streamlit run app_simple.py          # http://localhost:8501
.venv/Scripts/python -m pytest                                # all tests (config in pyproject.toml)
.venv/Scripts/python -m pytest tests/test_smoke.py::test_app_starts   # single test
.venv/Scripts/python -m pytest -m network                     # tests that call the real services (deselected by default)
```

### External data

Every external call goes through `rotasat.cache.get_or_fetch(service, params, fetch)`, which stores one JSON file per response in `data/cache/{service}/{sha1}.json`. Float parameters are rounded to 4 decimals before the key is built. Writes are atomic, and nothing is cached when a fetch fails. Any failure surfaces as `rotasat.cache.SourceError` (with `.service` and `.error_name`), which the UI turns into an Annex C message. HTTP requests use `rotasat.sources.http.get_json`, which sets a timeout and a generic `RotaSat/1.0` User-Agent. Tests isolate the cache by setting `ROTASAT_CACHE_DIR` to a temporary folder, and they never touch the network. The exception is `tests/test_annex_b.py`, which reads the real `data/cache/` offline and skips any site that hasn't been downloaded.

`rotasat/climate.py` is the bridge between the sources (network or cache) and the pure engine in `agro.py`: `climate.build(lat, lon)` returns a `PlaceClimate`. Rainfall comes from NASA SERVIR ClimateSERV, using CHIRPS (`datatype=0`) or IMERG (`datatype=26`). Each source averages a square exactly one native pixel wide (half-side 0.025° for CHIRPS, 0.05° for IMERG). These sizes were calibrated so that Annex B.1 is reproduced exactly; don't change them (see `specs/Plan.md` §4). ClimateSERV returns 503 under parallel load, so send its requests one at a time. A CHIRPS download takes about 70 s per site and IMERG takes about 7 min.

### Texts (i18n)

Every visible string goes through `rotasat.i18n.t(spanish_text, lang, **fields)`, keyed by the **exact Spanish text from Annex C**. An unknown key raises `KeyError`, so a string that isn't in the annex can't reach the UI. Annex C placeholders were Python expressions from the reference code; `scripts/build_texts.py` (`PLACEHOLDERS`) renames them to field names (`{ctx['elev']:,.0f}` becomes `{elev:,.0f}`). `rotasat/texts_data.py` is generated, so never hand-edit it. If Annex C changes, run `.venv/Scripts/python scripts/build_texts.py`; a test fails when the generated file is stale. Domain vocabulary (regions, textures, months, form options) is available through `vocab()`, `options()` and `month()`.

UI tests use `streamlit.testing.v1.AppTest` (see `tests/test_smoke.py`). The layout follows `specs/Plan.md` §2. Keep the layers separate: `rotasat/agro.py` and `rotasat/crops.py` must stay pure, with no network access and no Streamlit, so that the Annex B tests can run offline from `data/cache/`.

- `specs/Spec.md`: the product spec for **RotaSat** (NASA Space Apps Challenge 2026, challenge "Field Shift: Adapting Farms with NASA Data"), written in Spanish. It says *what* the product does and *why*.
- `specs/Spec-anexo-C-textos.md`: Annex C, the catalog of every visible string in Spanish/English (`ES|` / `EN|`), with `{placeholder:format}` formatting. It was generated from the reference implementation (`app_simple.py` for UI, `agro.py` for the engine), and the bracketed line numbers point into those files.
- `specs/Plan.md`: how it's built: Python + Streamlit, project layout, service URLs, cache design and the D-RC09 tie-break decision. Technology choices belong here, not in `Spec.md`.
- `specs/task.md`: the ordered task list (T01–T21), each with the requirements it covers and when it counts as done. Work through it in order.

## Spec conventions that govern all work

- Requirements have codes: `RF-xx` (functional), `RC-xx` (calculation rule), `RNF-xx` (non-functional), `CA-xx` (acceptance criterion). Cite these codes in plans, tasks, code comments and tests.
- The goal is a **faithful replica** of a reference implementation. That means the same screens, the same texts (Annex C) and the same numbers (Annex B, ±1 unit). The numbers in the calculation rules (§6) and the crop table (Annex A) are requirements, so never "improve" or round them.
- **Known behaviors in §10 must be preserved, not fixed.** Examples: the 36-month rotation timeline truncates the third crop; no GPM IMERG download for new coastal sites; the tie order between crops with equal aptitude comes from the reference sort (RC-09), and this affects which crops RC-12 picks.
- Open decisions D1–D3 (§11): the proposal is no classic tabbed UI (`app.py`), keep the §10 behaviors as-is, and use a ±1 tolerance.

## Product architecture (from the spec)

**UI:** a web page with three views: **Inicio**, which shows only 2 large buttons and the language toggle; **Mi terreno**; and **Clima**. Each view has a 7-icon bar that opens right-side off-canvas modal panels (14 panels in total, one open at a time, closed with Esc, ✕ or a click outside). The rule is "information appears only on request" (P1). The Terreno and Clima locations are independent of each other. User overrides ("Mis datos") are kept per location for the session only. There are no accounts and no persistence between sessions.

**Calculation engine pipeline** (the order matters, and each step feeds the next):
1. RC-01: 20 years (2005–2024) of daily NASA POWER data for the point.
2. RC-02: lapse-rate temperature correction using SRTM altitude. On the desert coast it is weighted by month (thermal inversion).
3. RC-03: a 12-month climate table (Hargreaves ET0, frost days, extreme-heat days at P90).
4. RC-04/05: rainfall is replaced by CHIRPS (non-coast, background download of up to 300 s that marks results as "preliminar" meanwhile) or by cached IMERG (coast only).
5. RC-06/07: region, slope and defaults are derived from the location. Nothing is hard-coded per zone (P2), and user input overrides satellite estimates.
6. RC-08/09: aptitude is a product of 6 factors (temperature, frost, water, salt, texture, pH) for 17 crops × 12 sowing months, giving each crop's best month.
7. RC-10/11: each rotation is evaluated over 36 months and scored **relative to the group being compared**, so scores change with the group. Displayed scores are recomputed over only Actual, A and B.
8. RC-12/13/14: rotations A and B are generated automatically, along with their explanations and the WhatsApp message.

**External data (§7):** NASA POWER (climate and MERRA-2 soil moisture), SRTM, CHIRPS via SERVIR, GPM IMERG, MODIS/VIIRS NDVI, SoilGrids, OpenStreetMap (geocoding) and Esri imagery. All sources must be keyless (RNF-01). Every external response is cached to disk so that a location seen before works offline (RNF-02). A prefetch procedure downloads the 7 demo sites in Annex B (RNF-03). An external failure must never blank the page; show a plain-language message and offer a retry (P7, RNF-05).

**i18n:** Spanish is the default and English is available; switching language keeps the view, the location and the user's answers. Place names and data-source names are not translated. Month names are lowercase in Spanish sentences and capitalized in English.

## Verification

Acceptance criteria CA-01 to CA-12 (§9) are the test suite to implement. Annex B (7 sites, default values, no soil input) gives the expected region, rainfall source, top 5 crops and rotation scores. CA-02, CA-05, CA-06, CA-09 and CA-10 give exact strings and values for Ica (`-14.13, -75.70`).
