"""T09: aptitud de un cultivo (RC-08) y tabla de aptitud del lugar (RC-09), con climas sintéticos. Sin red."""
import math

import pandas as pd
import pytest

from rotasat import agro, i18n
from rotasat.agro import Detected, resolve_inputs
from rotasat.crops import FIELD_CROPS, get


def clim(t=15.0, rain=100.0, et0=100.0, frost=0.0, hard=0.0, **per_month):
    """Tabla de clima de 12 meses constante; `per_month` cambia columnas mes a mes: {'t_media': {1: 30, ...}}."""
    df = pd.DataFrame({"lluvia": rain, "et0": et0, "t_media": t, "t_max": t + 5, "t_min": t - 5,
                       "dias_helada": frost, "dias_helada_fuerte": hard, "dias_calor": 0.0}, index=range(1, 13),
                      dtype="float64")
    for col, values in per_month.items():
        for m, v in values.items():
            df.loc[m, col] = v
    return df


def inputs(**o):
    return resolve_inputs(Detected(o.pop("region", "sierra"), 5, "suave"), o)


def test_cycle_wraps_around_year():
    assert agro.cycle_months(11, 4) == [11, 12, 1, 2]
    assert agro.cycle_months(1, 12) == list(range(1, 13))


@pytest.mark.parametrize("p,eff", [(0, 0), (10, 0), (50, 20), (70, 32), (100, 56)])
def test_effective_rain(p, eff):
    assert agro.effective_rain(p) == pytest.approx(eff)


def test_temperature_factor():
    papa = get("papa")                                   # óptima 10–20, límite 5–25, 6 meses
    r = agro.crop_suitability(papa, 1, clim(t=15), inputs())
    assert r["factors"]["temp"] == 1
    # Un mes a 7.5 °C: puntaje (7.5−5)/(10−5) = 0.5 → 0.6 × promedio + 0.4 × mínimo.
    r = agro.crop_suitability(papa, 1, clim(t=15, t_media={3: 7.5}), inputs())
    assert r["factors"]["temp"] == pytest.approx(0.6 * (5.5 / 6) + 0.4 * 0.5)
    # Por encima: (25 − 22.5)/(25 − 20) = 0.5; fuera del límite: 0.
    r = agro.crop_suitability(papa, 1, clim(t=15, t_media={2: 22.5, 4: 30}), inputs())
    assert r["factors"]["temp"] == pytest.approx(0.6 * (4.5 / 6) + 0.4 * 0)


def test_frost_factor():
    papa = get("papa")                                   # sensibilidad 0.9
    r = agro.crop_suitability(papa, 1, clim(frost=1.0, hard=0.5), inputs())
    expo = 6 * (1.0 + 2 * 0.5) * 0.9
    assert r["expo_helada"] == pytest.approx(expo)
    assert r["factors"]["helada"] == pytest.approx(math.exp(-0.06 * expo))


def test_water_factor_rainfed_and_irrigated():
    frijol = get("frijol")                               # Kc 0.75, 4 meses
    # Lluvia 50 → aprovechable 20; demanda 75 por mes → cobertura 20/75.
    r = agro.crop_suitability(frijol, 1, clim(rain=50, et0=100), inputs(irrigation="no"))
    cov = 20 / 75
    assert r["lluvia_cubre"] == pytest.approx(cov)
    assert r["factors"]["agua"] == pytest.approx(min(1, max(0.3, cov / 0.5)))
    assert r["riego_mm"] == pytest.approx(4 * 55) and r["riego_m3ha"] == pytest.approx(4 * 550)
    r = agro.crop_suitability(frijol, 1, clim(rain=0, et0=100), inputs(irrigation="no"))
    assert r["factors"]["agua"] == 0.3                   # nunca baja de 0.3
    r = agro.crop_suitability(frijol, 1, clim(rain=50, et0=100), inputs(irrigation="limitada"))
    assert r["factors"]["agua"] == pytest.approx(1 - 0.45 * 220 / 900)
    r = agro.crop_suitability(frijol, 1, clim(rain=50, et0=100), inputs(irrigation="suficiente"))
    assert r["factors"]["agua"] == pytest.approx(1 - 0.12 * 220 / 900)


def test_water_limited_high_kc_penalty():
    arroz = get("arroz")                                 # Kc 1.15 > 0.9
    r = agro.crop_suitability(arroz, 1, clim(rain=0, et0=200), inputs(irrigation="limitada"))
    assert r["factors"]["agua"] == pytest.approx((1 - 0.45 * 1) * 0.55)


def test_salt_texture_ph_factors():
    frijol = get("frijol")                               # tol. sal 0.2; franco, franco-arenoso; pH 5.8–7.5
    assert agro.crop_suitability(frijol, 1, clim(), inputs(salt="alta"))["factors"]["sal"] == pytest.approx(1 - 0.8 * 0.8)
    assert agro.crop_suitability(frijol, 1, clim(), inputs(salt="media"))["factors"]["sal"] == pytest.approx(1 - 0.4 * 0.8)
    tex = lambda t: agro.crop_suitability(frijol, 1, clim(), inputs(texture=t))["factors"]["textura"]
    assert (tex(None), tex("franco"), tex("arenoso"), tex("franco-arcilloso"), tex("arcilloso")) == (1, 1, 0.75, 0.75, 0.5)
    ph = lambda v: agro.crop_suitability(frijol, 1, clim(), inputs(ph=v))["factors"]["ph"]
    assert (ph(None), ph(7.0), ph(5.3), ph(8.0), ph(5.0), ph(8.1)) == (1, 1, 0.75, 0.75, 0.5, 0.5)
    assert agro.crop_suitability(get("haba"), 1, clim(), inputs(texture="arenoso"))["factors"]["textura"] == 0.5


def test_aptitude_is_product_of_factors():
    r = agro.crop_suitability(get("frijol"), 1, clim(rain=50), inputs(salt="media", texture="arenoso", ph=5.3))
    assert r["aptitud"] == pytest.approx(100 * math.prod(r["factors"].values()))


def test_best_month_prefers_aptitude_then_coverage_then_earliest():
    papa = get("papa")
    # Fuera de mayo–octubre hace demasiado frío → el mejor mes empieza el ciclo en mayo.
    cold = {m: 2.0 for m in (11, 12, 1, 2, 3, 4)}
    m, _ = agro.best_sowing(papa, clim(t=15, t_media=cold), inputs())
    assert m == 5
    # Todo igual en todos los meses: gana enero.
    m, _ = agro.best_sowing(papa, clim(), inputs())
    assert m == 1
    # Misma aptitud (100): gana el de mayor cobertura de lluvia.
    m, r = agro.best_sowing(get("frijol"), clim(rain=40, et0=50, lluvia={8: 200, 9: 200, 10: 200, 11: 200}),
                            inputs(irrigation="suficiente"))
    assert m == 8


@pytest.mark.parametrize("apt,lv", [(65, "🟢 Apto"), (64, "🟡 Con cuidado"), (40, "🟡 Con cuidado"),
                                    (39, "🔴 No recomendado")])
def test_levels(apt, lv):
    assert agro.level(apt) == lv
    assert i18n.t(lv, "en") in ("🟢 Suitable", "🟡 With care", "🔴 Not recommended")


def test_limiting_factor_texts():
    papa = get("papa")
    inp = inputs()
    r = agro.crop_suitability(papa, 1, clim(), inp)
    assert agro.limiting_factor(papa, r, inp) == ("Sin limitaciones importantes", {})
    r = agro.crop_suitability(papa, 1, clim(t=6), inp)
    text, fields = agro.limiting_factor(papa, r, inp)
    assert i18n.t(text, "es", **fields) == "Muy frío para este cultivo (media 6 °C; prefiere 10–20 °C)"
    r = agro.crop_suitability(papa, 1, clim(t=24), inp)
    text, fields = agro.limiting_factor(papa, r, inp)
    assert i18n.t(text, "en", **fields) == "Too hot (mean 24 °C; prefers 10–20 °C)"
    r = agro.crop_suitability(papa, 1, clim(rain=0), inp)
    text, fields = agro.limiting_factor(papa, r, inp)
    assert i18n.t(text, "es", **fields) == "La lluvia solo cubre 0% de lo que necesita: requiere riego"
    inp_irr = inputs(irrigation="limitada")
    r = agro.crop_suitability(papa, 1, clim(rain=0, et0=200), inp_irr)
    text, fields = agro.limiting_factor(papa, r, inp_irr)
    assert i18n.t(text, "es", **fields) == "Necesita mucha agua de riego (~10,200 m³/ha)"
    inp_salt = inputs(salt="alta")
    r = agro.crop_suitability(papa, 1, clim(), inp_salt)
    assert agro.limiting_factor(papa, r, inp_salt) == ("Poco tolerante a la sal", {})
    inp_ph = inputs(ph=8.5)
    r = agro.crop_suitability(papa, 1, clim(), inp_ph)
    text, fields = agro.limiting_factor(papa, r, inp_ph)
    assert i18n.t(text, "es", **fields) == "Prefiere pH 5.0–7.0"


def test_table_shape_and_order():
    t = agro.suitability_table(clim(), inputs())
    assert len(t) == 17 and set(t["id"]) == {c.id for c in FIELD_CROPS}
    assert list(t["aptitud"]) == sorted(t["aptitud"], reverse=True)
    assert t["riego_m3ha"].mod(10).eq(0).all()
    assert t["lluvia_cubre"].le(100).all()
    assert sum(agro.level_counts(t)) == 17
