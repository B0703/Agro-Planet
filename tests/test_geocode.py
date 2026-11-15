"""T14: coordenadas y nombre del lugar (RF-13, RF-14, RF-16) y buscador (RC-20) con Nominatim simulado. Sin red."""
import pytest

from rotasat import place
from rotasat.cache import SourceError
from rotasat.sources import geocode


# --- RF-13 / RF-14 Coordenadas -----------------------------------------------------------------------------------

@pytest.mark.parametrize("text,point", [
    ("-14.13, -75.70", (-14.13, -75.7)),
    ("-14.13;-75.70", (-14.13, -75.7)),
    ("  -14.13   -75.70 ", (-14.13, -75.7)),
    ("-14.123456, -75.700049", (-14.1235, -75.7)),           # RF-14: 4 decimales
    ("90, 180", (90.0, 180.0)),
    ("+5, .5", (5.0, 0.5)),
])
def test_parse_coords_valid(text, point):
    assert place.parse_coords(text) == point


@pytest.mark.parametrize("text", [
    "Tarma, Junin", "-14,13 -75,70", "-14.13", "-14.13, -75.70, 3", "91, 0", "0, -180.5", "", "1e2, 3",
])
def test_parse_coords_invalid(text):
    assert place.parse_coords(text) is None


# --- RF-16 Nombre que se muestra ---------------------------------------------------------------------------------

def test_labels_es_en():
    n = "Pueblo Nuevo, Ica"
    assert place.label(place.GPS, n, -14.13, -75.7, "es") == "Mi ubicación actual (Pueblo Nuevo, Ica)"
    assert place.label(place.GPS, n, -14.13, -75.7, "en") == "My current location (Pueblo Nuevo, Ica)"
    assert place.label(place.CLICK, n, -14.13, -75.7, "es") == "Terreno en Pueblo Nuevo, Ica"
    assert place.label(place.CLICK, n, -14.13, -75.7, "en") == "Field in Pueblo Nuevo, Ica"
    assert place.label(place.CLICK, None, -14.13, -75.7, "es") == "Terreno marcado en el mapa"
    assert place.label(place.COORDS, n, -14.13, -75.7, "en") == "Pueblo Nuevo, Ica"
    assert place.label(place.COORDS, None, -14.13, -75.7, "es") == "Coordenadas -14.1300, -75.7000"
    assert place.label(place.COORDS, None, -14.13, -75.7, "en") == "Coordinates -14.1300, -75.7000"
    assert place.label(place.SEARCH, "Tarma, Junín", -11.42, -75.69, "en") == "Tarma, Junín"


# --- RC-20 Buscador ----------------------------------------------------------------------------------------------

@pytest.fixture
def nominatim(monkeypatch, tmp_path):
    """Nominatim simulado: `answers[(path, peru_only)]` es la respuesta; anota cada llamada."""
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(geocode, "MIN_INTERVAL", 0)
    state = {"answers": {}, "calls": []}

    def fake(service, url, params=None, **kw):
        assert service == "geocode" and params["accept-language"] == "es"
        path = url.rsplit("/", 1)[-1]
        key = (path, "countrycodes" in params)
        state["calls"].append((key, params))
        ans = state["answers"][key]
        if isinstance(ans, Exception):
            raise ans
        return ans

    monkeypatch.setattr("rotasat.sources.http.get_json", fake)
    return state


def hit(display, kind, lat=-11.0, lon=-75.0):
    return {"display_name": display, "addresstype": kind, "lat": str(lat), "lon": str(lon)}


def test_coordinates_skip_the_service(nominatim):
    assert geocode.search("-14.13, -75.70") == [{"name": None, "lat": -14.13, "lon": -75.7}]
    assert nominatim["calls"] == []


def test_ca06_duplicates_collapse_to_one(nominatim):
    nominatim["answers"][("search", True)] = [
        hit("Tarma, Junín, 12651, Perú", "county", -11.3, -75.6),
        hit("Tarma, Junín, 12651, Perú", "town", -11.42001, -75.68769),
        hit("Tarma, Junín, 12651, Perú", "city", -11.5, -75.7),
    ]
    assert geocode.search("Tarma, Junin") == [{"name": "Tarma, Junín", "lat": -11.42, "lon": -75.6877}]
    params = nominatim["calls"][0][1]
    assert params["limit"] == 8 and params["countrycodes"] == "pe"


def test_order_by_place_type_and_max_five(nominatim):
    nominatim["answers"][("search", True)] = [
        hit("Región A, Perú", "state"), hit("Ciudad B, X", "city"), hit("Algo C, X", "peak"),
        hit("Pueblo D, X", "village"), hit("Barrio E, X", "suburb"), hit("Calle F, X", "road"),
        hit("Distrito G, X", "district"), hit("Caserío H, X", "hamlet"),
    ]
    names = [r["name"] for r in geocode.search("algo")]
    assert names == ["Pueblo D, X", "Calle F, X", "Caserío H, X", "Ciudad B, X", "Barrio E, X"]


def test_falls_back_to_the_world_when_peru_has_nothing(nominatim):
    nominatim["answers"][("search", True)] = []
    nominatim["answers"][("search", False)] = [hit("Madrid, Comunidad de Madrid, España", "city", 40.4, -3.7)]
    assert geocode.search("Madrid") == [{"name": "Madrid, Comunidad de Madrid", "lat": 40.4, "lon": -3.7}]
    assert [k for k, _ in nominatim["calls"]] == [("search", True), ("search", False)]


def test_no_results_and_failure(nominatim):
    nominatim["answers"][("search", True)] = []
    nominatim["answers"][("search", False)] = []
    assert geocode.search("zzzz") == []
    assert geocode.search("   ") == []
    nominatim["answers"][("search", True)] = SourceError("geocode", "timeout")
    with pytest.raises(SourceError):
        geocode.search("otra cosa")


def test_search_is_cached(nominatim):
    nominatim["answers"][("search", True)] = [hit("Tarma, Junín, Perú", "town")]
    geocode.search("Tarma,   Junin")
    geocode.search("Tarma, Junin")
    assert len(nominatim["calls"]) == 1


# --- RC-20 Nombre de un punto ------------------------------------------------------------------------------------

@pytest.mark.parametrize("address,name", [
    ({"hamlet": "Junchava", "village": "Pueblo Nuevo", "city": "Pueblo Nuevo", "region": "Ica", "state": "Ica"},
     "Pueblo Nuevo, Ica"),
    ({"city": "Ayacucho", "region": "Huamanga", "state": "Ayacucho"}, "Ayacucho, Huamanga"),
    ({"town": "Huancavelica", "city": "Huancavelica", "region": "Huancavelica", "state": "Huancavelica"},
     "Huancavelica"),
    ({"county": "Tarma", "state": "Junín"}, "Tarma, Junín"),
    ({"road": "Jirón X", "neighbourhood": "Centro"}, None),
    ({}, None),
])
def test_point_name(nominatim, address, name):
    nominatim["answers"][("reverse", False)] = {"address": address}
    assert geocode.point_name(-14.13, -75.70) == name


@pytest.mark.network
def test_ca06_real_nominatim(monkeypatch, tmp_path):
    """CA-06 contra el servicio real (pytest -m network)."""
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))
    assert [r["name"] for r in geocode.search("Tarma, Junin")] == ["Tarma, Junín"]
    assert geocode.point_name(-14.13, -75.70) == "Pueblo Nuevo, Ica"
