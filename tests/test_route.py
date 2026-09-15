import geopandas as gpd
from shapely.geometry import Point

from alab.route import WAYPOINTS, distance_to_route, straight_route, waypoints_frame


def test_waypoints_van_de_ibicuy_a_anelo():
    assert WAYPOINTS[0][0].startswith("Ibicuy") and WAYPOINTS[-1][0] == "Añelo"
    w = waypoints_frame()
    assert len(w) == len(WAYPOINTS) and w.crs.to_epsg() == 4326
    # de este a oeste y de norte a sur, a grandes rasgos
    assert w.lon.iloc[0] > w.lon.iloc[-1] and w.lat.iloc[0] > w.lat.iloc[-1]


def test_straight_route_y_distancia():
    line = straight_route()
    route = gpd.GeoDataFrame({"nombre": ["rectas"], "km": [0], "horas_osrm": [0.0], "fuente": ["rectas"]}, geometry=[line], crs="EPSG:4326")
    km = route.to_crs("EPSG:5344").length.iloc[0] / 1000.0
    assert 1100 < km < 1500   # las rectas son más cortas que los 1.474 km reales, pero no mucho
    pts = gpd.GeoSeries([Point(-64.29, -36.62), Point(-70.0, -40.0)], crs="EPSG:4326")   # Santa Rosa, y un punto lejos
    d = distance_to_route(pts, route)
    assert d.iloc[0] < 2 and d.iloc[1] > 100
