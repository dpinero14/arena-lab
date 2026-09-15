import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from alab.roads import AUTOS_POR_PASADA, by_route, exceeded, passages_by_chain, passages_per_day, pressure, route_segments, segments_geojson


def _route():
    return gpd.GeoDataFrame({"km": [300]}, geometry=[LineString([(-64.0, -36.0), (-65.0, -37.0), (-66.0, -38.0)])], crs="EPSG:4326")


def _tmda():
    # un tramo pegado a la ruta, uno que la cruza y otro lejos
    return gpd.GeoDataFrame({"cod_ruta": ["0152", "0035", "0022"], "tmda17": [200, 5000, 1000]},
                            geometry=[LineString([(-64.0, -36.005), (-65.0, -37.005)]), LineString([(-64.6, -36.4), (-64.4, -36.6)]), LineString([(-60.0, -36.0), (-60.0, -37.0)])], crs="EPSG:4326")


def test_route_segments_se_queda_con_lo_que_corre_junto_a_la_ruta():
    seg = route_segments(_tmda(), _route(), buffer_m=1500, min_km=20)
    assert list(seg.ruta) == ["RN 152"] and seg.corredor.iloc[0] == "Ibicuy"
    # la línea paralela cubre el primer tercio de la traza; el cruce se absorbe y el resto no tiene tránsito medido
    assert len(seg) == 1 and 130 < seg.km.iloc[0] < 160 and seg.km_desde.iloc[0] == 0


def test_pasadas_y_presion():
    assert passages_per_day(30 * 300 * 100) == 200.0        # 100 viajes por día, ida y vuelta
    assert passages_per_day(30 * 300 * 100, vuelta_vacia=False) == 100.0
    seg = route_segments(_tmda(), _route())
    y = pd.DataFrame({"anio": [2015, 2025], "nat_t": [30 * 300 * 50, 30 * 300 * 500]})
    pr = pressure(seg, y)
    assert list(pr.pasadas_dia) == [100, 1000] and list(pr.sobre_tmda_pct) == [50.0, 500.0]
    assert pr.autos_equiv_dia.iloc[1] == 1000 * AUTOS_POR_PASADA
    ex = exceeded(pr)
    assert list(ex.tramos_superados) == [0, 1] and ex.peor_ruta.iloc[1] == "RN 152"
    r = by_route(pr, 2025)
    assert r.loc[0, "ruta"] == "RN 152" and r.loc[0, "pct_max"] == 500.0


def test_pasadas_por_cadena_solo_cuenta_el_camion_largo():
    p = passages_by_chain(5e6)
    cam = p[p.cadena.str.startswith("camión")].iloc[0]
    tren = p[p.cadena.str.contains("Tren")].iloc[0]
    assert cam.pasadas_dia == round(2 * 5e6 / 30 / 300) and cam.km_camion_largo == 1461
    assert tren.pasadas_dia == 0 and p[p.cadena.str.contains("cercana")].pasadas_dia.iloc[0] == 0


def test_geojson_liviano():
    g = segments_geojson(route_segments(_tmda(), _route()))
    assert g["type"] == "FeatureCollection" and g["features"][0]["properties"]["ruta"] == "RN 152"
