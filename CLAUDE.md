# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

The repository holds **only specifications**; there is no code, build system or tests yet, and the git repo has no commits.
When code is added, update this file with the real build/run/test commands.

- `specs/Spec.md`: the product spec for **RotaSat** (NASA Space Apps Challenge 2026, challenge "Field Shift: Adapting Farms with NASA Data"), written in Spanish. It says *what* the product does and *why*.
- `specs/Spec-anexo-C-textos.md`: Annex C, the catalog of every visible string in Spanish/English (`ES|` / `EN|`), with `{placeholder:format}` formatting. It was generated from the reference implementation (`app_simple.py` for UI, `agro.py` for the engine), and the bracketed line numbers point into those files.
- The spec also refers to sibling documents that **don't exist yet**: `Plan.md` (how it's built: languages, libraries, service URLs, tie-break sort order) and `task.md` (work steps). Technology choices belong in `Plan.md`, not in `Spec.md`.

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
