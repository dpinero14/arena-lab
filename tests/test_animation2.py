import json

import pandas as pd

from alab.animation import yearly_series
from alab.animation2 import CONTEXTO, UNIDADES, _path, chain_paths, logistics_animation_html
from alab.logistics import CHAINS
from alab.route import waypoints_frame


def _fake_osrm(tmp_path, name, coords):
    p = tmp_path / name
    p.write_text(json.dumps({"code": "Ok", "routes": [{"distance": 1000.0, "duration": 100.0, "geometry": {"type": "LineString", "coordinates": coords}}]}), encoding="utf-8")
    return p


def test_path_s_monotono_y_km():
    p = _path([(-59.18, -33.76), (-62.30, -38.78)])
    assert p["coords"][0][2] == 0.0 and abs(p["coords"][-1][2] - 1.0) < 1e-9 and 550 < p["km"] < 700


def test_chain_paths_cubre_todas_las_cadenas(tmp_path):
    a = _fake_osrm(tmp_path, "a.json", [[-59.17, -33.74], [-64.29, -36.62], [-68.79, -38.35]])
    b = _fake_osrm(tmp_path, "b.json", [[-62.27, -38.72], [-68.79, -38.35]])
    cp = chain_paths(a, b)
    assert [c["nombre"] for c in cp] == [c.nombre for c in CHAINS]
    assert all(len(c["paths"]) >= 1 and all(p["modo"] in UNIDADES for p in c["paths"]) for c in cp)
    tren = next(c for c in cp if "Tren" in c["nombre"])
    assert [p["modo"] for p in tren["paths"]] == ["maritimo", "tren", "camion"] and tren["usd_t"] == 35.2


def test_html_v2(tmp_path):
    a = _fake_osrm(tmp_path, "a.json", [[-59.17, -33.74], [-68.79, -38.35]]); b = _fake_osrm(tmp_path, "b.json", [[-62.27, -38.72], [-68.79, -38.35]])
    frac = pd.DataFrame({"well_id": [1, 2], "basin": ["NEUQUINA"] * 2, "reservoir_type": ["NO CONVENCIONAL"] * 2, "sand_domestic_t": [3000, 6000], "sand_imported_t": [0, 0], "frac_start": pd.to_datetime(["2015-01-01", "2016-01-01"])})
    y = yearly_series(frac, route_km=1461.0)
    layers = {"blancos": {"type": "FeatureCollection", "features": []}, "ferrocarril": {"type": "FeatureCollection", "features": []}, "rios": {"type": "FeatureCollection", "features": []}, "puertos": [{"nombre": "IBICUY", "lat": -33.76, "lon": -59.18}]}
    out = logistics_animation_html(y, chain_paths(a, b), layers, waypoints_frame(), tmp_path / "v2.html", partial_year=2016)
    html = out.read_text(encoding="utf-8")
    assert "__DATA__" not in html and "hidrovía" in html and CONTEXTO[2016] in html
