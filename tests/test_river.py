"""T20: lluvia que alimenta el río Ica (RC-18, RF-56). Motor puro, más la serie real guardada en data/cache/."""
from datetime import date

import pandas as pd
import pytest

from rotasat import agro
from rotasat.sources import chirps


@pytest.mark.parametrize("region,lat,lon,shown", [
    ("costa", -14.13, -75.70, True),          # Ica
    ("costa", -15.2, -76.4, True),            # esquinas incluidas
    ("costa", -13.4, -75.2, True),
    ("costa", -13.39, -75.70, False),         # al norte de la caja
    ("costa", -14.13, -75.19, False),         # al este
    ("sierra", -14.13, -75.70, False),        # dentro de la caja pero no es costa
    ("sierra", -12.06, -75.29, False),        # Chupaca
])
def test_shown_only_on_the_coast_inside_the_box(region, lat, lon, shown):
    assert agro.in_ica_basin(region, lat, lon) is shown


@pytest.mark.parametrize("today,last", [(date(2026, 11, 15), 2026), (date(2026, 5, 1), 2026),
                                        (date(2026, 4, 30), 2025), (date(2027, 1, 10), 2026)])
def test_last_season_ends_in_april_of_this_year_from_may(today, last):
    assert agro.last_river_season(today) == last


def _daily(start: str, end: str, value: float = 1.0, overrides: dict | None = None):
    days = pd.date_range(start, end, freq="D")
    rain = [value] * len(days)
    for d, v in (overrides or {}).items():
        rain[days.get_loc(pd.Timestamp(d))] = v
    return [d.strftime("%Y%m%d") for d in days], rain


def test_season_is_september_to_april_indexed_by_april_year():
    dates, rain = _daily("2005-09-01", "2007-04-30", overrides={"2006-05-15": 500.0, "2006-02-01": None})
    s = agro.river_seasons(dates, rain, 2007)
    # 2005–06: 30+31+30+31 (set–dic) + 31+28+31+30 (ene–abr) = 242 días, uno sin dato. Mayo–agosto no cuentan.
    assert s.loc[2006] == 241.0
    assert s.loc[2007] == 242.0
    assert list(s.index) == list(range(2006, 2008))


def test_outlook_average_of_19_seasons_and_levels():
    base = pd.Series(100.0, index=range(2006, 2025))
    for total, level in [(84.9, "seco"), (85.0, "ligeramente"), (95.0, "ligeramente"), (95.1, "normal"),
                         (130.0, "normal")]:
        seasons = pd.concat([base, pd.Series([999.0, total], index=[2025, 2026])])   # 2025 no entra al promedio
        out = agro.river_outlook(seasons)
        assert (out.season, out.average, out.total) == (2026, 100.0, total)
        assert out.delta == pytest.approx(total - 100.0)
        assert out.level == level, total


def test_real_series_cached_for_the_demo():
    """La serie de la cuenca alta guardada por el prefetch: 2005–06 a 2025–26, sin huecos."""
    end = date(2026, 4, 30)
    series = chirps.river_cached(*agro.RIVER_POINT, end)
    if series is None:
        pytest.skip("la lluvia de la cuenca alta no está en data/cache/ (scripts/prefetch.py)")
    assert (series["dates"][0], series["dates"][-1]) == ("20050901", "20260430")
    seasons = agro.river_seasons(series["dates"], series["rain"], 2026)
    assert len(seasons) == 21
    out = agro.river_outlook(seasons)
    assert round(out.total) == 975 and round(out.average) == 900 and round(out.delta) == 8
    assert out.level == "normal"
