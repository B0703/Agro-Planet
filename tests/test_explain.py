"""T12: textos que genera el motor (RC-13 explicación, RC-14 WhatsApp, RC-15 resumen del clima). Sin red."""
import pandas as pd

from rotasat import agro
from tests.test_suitability import clim, inputs

SIERRA = (("papa", 10), ("papa", 10), ("cebada", 12))


def result(label, rotation, c, inp, total=50.0):
    return agro.RotationResult(label, rotation, agro.evaluate_rotation(rotation, c, inp), {}, total)


# --- RC-15 Resumen del clima ---------------------------------------------------------------------------------------

def test_summary_little_rain_no_frost_es():
    c = clim(t=20, rain=10, et0=100, t_max={3: 31.0}, t_min={7: 12.6})
    out = agro.climate_summary(c, "es")
    assert out == [
        "🌧️ **Casi no llueve**: 120 mm al año. Aquí los cultivos dependen del riego.",
        "🌡️ El mes más caluroso es **marzo** (máxima media de 31 °C) y el más frío es **julio** "
        "(mínima media de 13 °C).",
        "❄️ Prácticamente **no hay heladas**.",
        "💨 El sol y el viento evaporan **1,200 mm al año**: 10.0 veces lo que llueve.",
    ]


def test_summary_rainy_months_in_season_order_en():
    # Los 4 más lluviosos son ene., feb., mar. y dic.; contando el año desde julio: dic., ene., feb., mar.
    rain = {1: 150.0, 2: 140.0, 3: 120.0, 12: 100.0}
    c = clim(t=10, rain=10, lluvia=rain, frost=2.0, dias_helada={7: 10.0})
    out = agro.climate_summary(c, "en")
    assert out[0] == "🌧️ It rains **590 mm a year**, mostly in December, January, February and March."
    assert out[2] == "❄️ There is frost risk on about **32 days a year**, mostly in **July**."


def test_summary_omits_evaporation_without_rain():
    out = agro.climate_summary(clim(rain=0), "es")
    assert len(out) == 3 and out[0].startswith("🌧️ **Casi no llueve**: 0 mm")


# --- RC-13 Explicación ---------------------------------------------------------------------------------------------

def test_current_rotation_explanation():
    c = clim(t=15, rain=100, et0=100, dias_calor={2: 4.0})
    inp = inputs()
    cur = result("Actual", SIERRA, c, inp)
    ex = agro.explain_rotation(cur, cur, c, 25.04, inp, "es")
    assert ex["por_que"] == ["Es la rotación que el agricultor usa hoy: sirve como punto de comparación."]
    assert ex["evidencia"][0] == "Siembras: Papa en octubre, Papa en octubre, Cebada en diciembre."
    assert ex["evidencia"][2].startswith("Agua que la lluvia no cubre en 3 años:")       # sin riego
    assert ex["evidencia"][3] == ("Mes con más calor extremo: **febrero** (4 días/año sobre 25.0 °C, "
                                  "el percentil 90 local).")                             # sin heladas: no hay mes
    assert ex["evidencia"][4] == "Meses con suelo desnudo en 3 años: **14**."
    assert ex["beneficios"] == []
    # Solo las notas, una vez por cultivo (papa se repite).
    assert len(ex["riesgos"]) == 2
    assert len(ex["vacios"]) == 3                                                        # sal baja, suelo sin satélite


def test_alternative_benefits_and_reasons():
    c = clim(t=15, rain=30, et0=120, frost=1.0)
    inp = inputs(irrigation="limitada", salt="media")
    cur = result("Actual", SIERRA, c, inp)
    alt = result("A", (("frijol", 10), ("quinua", 3), ("cebada", 10)), c, inp)
    ex = agro.explain_rotation(alt, cur, c, 20.0, inp, "es")
    assert ex["por_que"][0].startswith("Armada automáticamente")
    assert ex["por_que"][1] == ("Incluye leguminosas (Frijol) que fijan nitrógeno del aire y reducen la necesidad "
                                "de fertilizante.")
    assert ex["por_que"][2].startswith("Ninguna familia de cultivo se repite")
    assert ex["evidencia"][2].startswith("Necesidad de riego estimada en 3 años:")       # con riego
    assert ex["evidencia"][3].startswith("Mes con más riesgo de helada: **enero** (1 días/año")
    d = cur.evaluation["agua_m3ha"] - alt.evaluation["agua_m3ha"]
    assert d > 100
    assert ex["beneficios"][0] == (f"Ahorra ~**{d:,.0f} m³ de agua por hectárea** en 3 años frente a la rotación "
                                   f"actual (≈ {d / 30:,.0f} camiones cisterna de 30 m³).")
    assert any(x.startswith("Mejor balance de nitrógeno (-1 vs -8)") for x in ex["beneficios"])
    assert "Menos repetición de familias → menor presión de plagas del suelo." in ex["beneficios"]
    assert ex["vacios"][-1] == "La salinidad real requiere un análisis de suelo y agua (conductividad eléctrica)."


def test_alternative_risks():
    c = clim(t=15, rain=30, et0=120)
    inp = inputs(irrigation="limitada")
    cur = result("Actual", (("quinua", 5), ("haba", 11), ("cebada", 6)), c, inp)
    alt = result("B", (("arroz", 1), ("arroz", 7), ("descanso", 1)), c, inp)
    ex = agro.explain_rotation(alt, cur, c, 20.0, inp, "en")
    assert ex["riesgos"][0].startswith("Needs ~") and "MORE water" in ex["riesgos"][0]
    assert ex["riesgos"][1].startswith("Lower reference market value")
    assert ex["riesgos"][2].startswith("⚠️ At least one crop has low suitability")       # arroz con agua limitada
    assert ex["beneficios"] == [] or "Saves" not in ex["beneficios"][0]


def test_soil_from_satellite_gap():
    c = clim()
    inp = agro.resolve_inputs(agro.Detected("sierra", 5, "suave"), None, {"texture": "franco", "ph": 6.5})
    cur = result("Actual", SIERRA, c, inp)
    ex = agro.explain_rotation(cur, cur, c, 20.0, inp, "es")
    assert ex["vacios"][-1].startswith("El tipo de suelo es una estimación de SoilGrids")


# --- RC-14 WhatsApp ------------------------------------------------------------------------------------------------

def _table(*rows):
    return pd.DataFrame([{"id": i, "aptitud": a, "mes": m} for i, a, m in rows])


def test_whatsapp_well_done_when_current_is_best():
    c, inp = clim(), inputs()
    res = [result("Actual", SIERRA, c, inp, 80), result("A", SIERRA, c, inp, 70)]
    t = _table(("quinua", 90, 5), ("haba", 41, 6), ("papa", 39, 10), ("cebada", 38, 12))
    msg = agro.whatsapp_message("Chupaca, Junín", t, res, c, 20.0, inp, "es").split("\n")
    assert msg[0] == "🌱 *Agro Planet* — Chupaca, Junín"
    assert msg[3:5] == ["• Quinua: sembrar en mayo", "• Haba: sembrar en junio"]         # solo aptitud ≥ 40
    assert "Su rotación actual obtiene *80/100*." in msg
    assert "Su rotación actual ya es la mejor de las comparadas. ¡Bien hecho!" in msg
    assert msg[-1].startswith("⚠️ Orientación con datos satelitales")


def test_whatsapp_best_option_with_up_to_three_benefits():
    c = clim(t=15, rain=30, et0=120, frost=1.0)
    inp = inputs(irrigation="limitada")
    alt_rot = (("quinua", 5), ("haba", 11), ("cebada", 6))
    res = [result("Actual", SIERRA, c, inp, 60), result("A", alt_rot, c, inp, 85), result("B", alt_rot, c, inp, 90)]
    t = _table(("quinua", 90, 5), ("haba", 80, 11), ("cebada", 70, 6))
    msg = agro.whatsapp_message("X", t, res, c, 20.0, inp, "en").split("\n")
    i = msg.index("The option *B: Quinoa → Faba bean → Barley* scores *90/100*.")
    assert msg[i + 1] == "Why?"
    bullets = [x for x in msg[i + 2:] if x.startswith("• ")]
    assert 1 <= len(bullets) <= 3 and "**" not in "".join(bullets)                       # negrita de WhatsApp: *
