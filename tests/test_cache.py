"""T04: caché en disco y SourceError (RNF-02, RNF-05). Sin red: los servicios se simulan."""
import json
import threading
import time

import pytest
import requests

from rotasat import cache
from rotasat.cache import SourceError
from rotasat.sources import http


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ROTASAT_CACHE_DIR", str(tmp_path))
    return tmp_path


PARAMS = {"lat": -14.13, "lon": -75.7, "start": "20050101"}


def test_miss_fetches_and_saves_then_hits(tmp_cache):
    calls = []

    def fetch():
        calls.append(1)
        return {"t2m": [20.1, 21.3]}

    assert cache.get_or_fetch("power", PARAMS, fetch) == {"t2m": [20.1, 21.3]}
    assert cache.get_or_fetch("power", PARAMS, fetch) == {"t2m": [20.1, 21.3]}
    assert len(calls) == 1
    f = cache.path_for("power", PARAMS)
    assert f.parent == tmp_cache / "power" and f.suffix == ".json"
    record = json.loads(f.read_text(encoding="utf-8"))
    assert record["service"] == "power" and record["params"]["lat"] == -14.13 and "fetched_at" in record


def test_coordinates_rounded_to_4_decimals():
    # RF-14: el mismo punto con más decimales cae en el mismo archivo.
    assert cache.cache_key({"lat": -14.130000004, "lon": -75.70001}) == cache.cache_key({"lat": -14.13, "lon": -75.7})
    assert cache.cache_key({"lat": -14.1301}) != cache.cache_key({"lat": -14.13})
    # El orden de los parámetros no importa.
    assert cache.cache_key({"a": 1, "b": 2}) == cache.cache_key({"b": 2, "a": 1})


def test_failure_raises_source_error_and_saves_nothing():
    def fetch():
        raise ConnectionError("sin internet")

    with pytest.raises(SourceError) as exc:
        cache.get_or_fetch("chirps", PARAMS, fetch)
    assert exc.value.service == "chirps"
    assert exc.value.error_name == "ConnectionError"
    assert not cache.has("chirps", PARAMS)


def test_empty_response_is_an_error():
    with pytest.raises(SourceError):
        cache.get_or_fetch("ndvi", PARAMS, lambda: None)
    assert not cache.has("ndvi", PARAMS)


def test_works_offline_once_cached():
    cache.save("srtm", PARAMS, {"elevation": 405})

    def offline():
        raise AssertionError("no debía consultar la red")

    assert cache.get_or_fetch("srtm", PARAMS, offline) == {"elevation": 405}
    assert cache.load("srtm", {"lat": 0.0}) is None


def test_corrupt_file_is_refetched():
    p = cache.path_for("power", PARAMS)
    p.parent.mkdir(parents=True)
    p.write_text("{a medias", encoding="utf-8")
    assert cache.get_or_fetch("power", PARAMS, lambda: [1]) == [1]


def test_concurrent_calls_fetch_once():
    calls = []

    def slow():
        calls.append(1)
        time.sleep(0.2)
        return [1, 2, 3]

    results = []
    threads = [threading.Thread(target=lambda: results.append(cache.get_or_fetch("chirps", PARAMS, slow)))
               for _ in range(4)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert len(calls) == 1 and results == [[1, 2, 3]] * 4


class _Resp:
    def __init__(self, status=200, body=None, text="x"):
        self.status_code, self._body, self.text = status, body, text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        if self._body is None:
            raise ValueError("no JSON")
        return self._body


def test_http_get_json(monkeypatch):
    seen = {}

    def fake_get(url, params=None, timeout=None, headers=None):
        seen.update(url=url, timeout=timeout, headers=headers)
        return _Resp(body={"ok": True})

    monkeypatch.setattr(requests, "get", fake_get)
    assert http.get_json("power", "https://example.org", {"a": 1}) == {"ok": True}
    assert seen["timeout"] == http.DEFAULT_TIMEOUT
    assert seen["headers"]["User-Agent"] == "RotaSat/1.0"


@pytest.mark.parametrize("resp_or_exc", [_Resp(status=503, body={}), _Resp(body=None),
                                         requests.ConnectionError("down"), requests.Timeout("slow")])
def test_http_failures_become_source_error(monkeypatch, resp_or_exc):
    def fake_get(*a, **k):
        if isinstance(resp_or_exc, Exception):
            raise resp_or_exc
        return resp_or_exc

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(SourceError) as exc:
        http.get_json("soilgrids", "https://example.org")
    assert exc.value.service == "soilgrids"
