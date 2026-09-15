import geopandas as gpd
import pandas as pd

from alab.animation import SUPUESTOS, route_animation_html, route_vertices, yearly_series
from alab.route import straight_route, waypoints_frame


def _frac():
    return pd.DataFrame({
        "well_id": [1, 2, 3, 4], "basin": ["NEUQUINA"] * 4, "reservoir_type": ["NO CONVENCIONAL"] * 4,
        "sand_domestic_t": [3000, 0, 6000, 300], "sand_imported_t": [0, 3000, 0, 0],
        "frac_start": pd.to_datetime(["2015-03-01", "2015-06-01", "2016-01-01", "2016-02-01"]),
    })


def test_yearly_series_cuenta_viajes_y_flete():
    y = yearly_series(_frac(), route_km=1000.0)
    assert list(y["anio"]) == [2015, 2016]
    r16 = y[y.anio == 2016].iloc[0]
    assert r16["nat_t"] == 6300 and r16["viajes"] == 210 and r16["flete_musd"] == round(6300 * SUPUESTOS["usd_flete_por_t"] / 1e6, 1)
    assert r16["usd_km_anio"] == round(6300 * SUPUESTOS["usd_flete_por_t"] / 1000.0)
    assert y["flete_acum_musd"].iloc[-1] >= y["flete_musd"].iloc[-1]


def test_route_vertices_y_html(tmp_path):
    route = gpd.GeoDataFrame({"nombre": ["r"], "km": [1200.0], "horas_osrm": [0.0], "fuente": ["rectas"]}, geometry=[straight_route()], crs="EPSG:4326")
    v = route_vertices(route)
    assert v[0][2] == 0.0 and abs(v[-1][2] - 1.0) < 1e-9 and all(v[i][2] <= v[i + 1][2] for i in range(len(v) - 1))
    y = yearly_series(_frac(), route_km=1200.0)
    out = route_animation_html(route, waypoints_frame(), y, tmp_path / "anim.html", partial_year=2016)
    html = out.read_text(encoding="utf-8")
    assert "__DATA__" not in html and "camiones" in html and '"partial": 2016' in html
