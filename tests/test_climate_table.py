"""T06: RC-02 (corrección por altitud) y RC-03 (tabla de clima mensual), con datos sintéticos."""
import math

import numpy as np
import pandas as pd
import pytest

from rotasat import agro


def synthetic(t_mean=15.0, t_max=20.0, t_min=10.0, rain=1.0, ra=30.0) -> pd.DataFrame:
    """20 años de datos diarios constantes (2005–2024)."""
    idx = pd.date_range("2005-01-01", "2024-12-31", freq="D")
    n = len(idx)
    return pd.DataFrame({"t_mean": np.full(n, t_mean), "t_max": np.full(n, t_max), "t_min": np.full(n, t_min),
                         "rain": np.full(n, rain), "ra": np.full(n, ra)}, index=idx)


def test_adjustment_formula():
    assert agro.altitude_adjustment(1319.63, 405.0) == pytest.approx(6.5 * 914.63 / 1000)
    assert agro.altitude_adjustment(3000, 3500) == pytest.approx(-3.25)
    assert agro.altitude_adjustment(1000, None) == 0.0     # RC-02.5
    assert agro.altitude_adjustment(None, 1000) == 0.0


def test_coast_definition():
    assert agro.is_desert_coast(405, 101)
    assert not agro.is_desert_coast(1500, 100)              # altitud no menor de 1500
    assert not agro.is_desert_coast(405, 300)               # lluvia no menor de 300
    assert not agro.is_desert_coast(None, 50)


def test_non_coast_full_adjustment():
    df = synthetic(rain=2.0)                                # 730 mm/año → no es costa
    out, info = agro.correct_temperatures(df, elev_area=2000, elev_real=1000)
    assert not info.coast and info.ajuste_c == pytest.approx(6.5)
    for col in ("t_mean", "t_max", "t_min"):
        assert (out[col] - df[col]).eq(6.5).all()
    assert out["rain"].equals(df["rain"])
    assert df["t_mean"].iloc[0] == 15.0                     # no modifica la entrada


def test_coast_monthly_weights():
    df = synthetic(rain=0.1)                                # 36.5 mm/año, altitud 400 → costa
    out, info = agro.correct_temperatures(df, elev_area=1400, elev_real=400)
    assert info.coast
    delta = (out["t_mean"] - df["t_mean"]).groupby(df.index.month).first()
    expected = {1: 1, 2: 1, 3: 1, 4: 0.66, 5: 0.33, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0.33, 11: 0.66, 12: 1}
    for m, w in expected.items():
        assert delta[m] == pytest.approx(6.5 * w), m


def test_et0_hargreaves():
    df = synthetic(t_mean=15, t_max=20, t_min=10, ra=30)
    expected = 0.0023 * (0.408 * 30) * (15 + 17.8) * math.sqrt(10)
    assert agro.et0_hargreaves(df).iloc[0] == pytest.approx(expected)
    inverted = synthetic(t_max=10, t_min=12)                # diferencia negativa → 0
    assert agro.et0_hargreaves(inverted).iloc[0] == 0


def test_monthly_table_sums_divide_by_20_and_counts():
    df = synthetic(rain=1.0)
    df.loc["2010-07-01":"2010-07-10", "t_min"] = 1.0         # 10 días con riesgo de helada
    df.loc["2010-07-01":"2010-07-04", "t_min"] = -1.0        # 4 de ellos de helada fuerte
    df.loc["2012-01-01", "t_max"] = 40.0
    clim, p90 = agro.monthly_climate(df)
    assert list(clim.index) == list(range(1, 13))
    assert list(clim.columns) == list(agro.CLIMATE_COLS)
    assert clim.loc[1, "lluvia"] == pytest.approx(31.0)      # 31 días × 20 años × 1 mm ÷ 20
    assert clim.loc[2, "lluvia"] == pytest.approx((28 * 20 + 5) / 20)   # 5 años bisiestos
    assert clim.loc[7, "dias_helada"] == pytest.approx(10 / 20)
    assert clim.loc[7, "dias_helada_fuerte"] == pytest.approx(4 / 20)
    assert clim.loc[1, "dias_helada"] == 0
    assert clim.loc[3, "t_media"] == pytest.approx(15.0)
    # P90 con casi todos los valores en 20 °C: el umbral es 20 y todos los días cuentan como «≥ P90».
    assert p90 == pytest.approx(20.0)
    assert clim.loc[1, "dias_calor"] == pytest.approx(31.0)


def test_missing_values_ignored():
    df = synthetic(rain=1.0)
    df.loc["2005-01-01":"2005-01-31", ["rain", "t_min", "t_mean", "t_max", "ra"]] = np.nan
    clim, _ = agro.monthly_climate(df)
    assert clim.loc[1, "lluvia"] == pytest.approx(31 * 19 / 20)       # el mes faltante no suma
    assert clim.loc[1, "t_media"] == pytest.approx(15.0)               # promedio de los días con dato
    assert clim.loc[1, "et0"] < clim.loc[3, "et0"]
