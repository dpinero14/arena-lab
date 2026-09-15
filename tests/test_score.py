import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Point, box

from alab.score import base_score, demand_point, distance_km, prospectivity, ramp, top_targets
from alab.validate import known_points, score_at, summary


def _units():
    # cuatro polígonos de ~10 km de lado alrededor de Añelo (-68.79, -38.35), en grados
    polys = [box(-68.85, -38.40, -68.75, -38.30), box(-68.95, -38.60, -68.85, -38.50), box(-67.0, -40.0, -66.9, -39.9), box(-65.0, -42.0, -64.9, -41.9)]
    return gpd.GeoDataFrame({
        "nombre": ["eólico cerca", "fluvial medio", "arenisca lejos", "sin interés"],
        "clase": ["arena eólica cuaternaria", "arena fluvial cuaternaria", "arenisca antigua", "sin interés"],
        "f_cuarzo": [True, False, True, False], "f_finos": [False, True, False, False], "f_grava": [False, False, False, False],
        "descrip_litologica": ["Arenas", "Arenas y limos", "Areniscas cuarzosas", "Basaltos"], "edad_inf": ["Holoceno", "Holoceno", "Cretácico", "Plioceno"], "nom_hoja": ["A"] * 4,
    }, geometry=polys, crs="EPSG:4326")


def test_base_score_ordena_clases_y_aplica_banderas():
    assert base_score("arena eólica cuaternaria") > base_score("arena fluvial cuaternaria") > base_score("arenisca antigua") > base_score("otra con arena") > base_score("sin interés") == 0
    assert base_score("arena eólica cuaternaria", f_cuarzo=True) == 1.0   # recortado a 1
    assert base_score("arena fluvial cuaternaria", f_finos=True) < base_score("arena fluvial cuaternaria")


def test_ramp():
    assert ramp(0, 150, 600) == 1.0 and ramp(600, 150, 600) == 0.0 and abs(ramp(375, 150, 600) - 0.5) < 1e-9


def test_distance_km_razonable():
    g = gpd.GeoSeries([Point(-68.79, -38.35)], crs="EPSG:4326")
    t = gpd.GeoSeries([Point(-68.79, -37.35)], crs="EPSG:4326")   # un grado de latitud al norte
    d = distance_km(g, t)[0]
    assert 105 < d < 118


def test_prospectivity_y_top_targets():
    u = _units()
    roads = gpd.GeoDataFrame(geometry=[LineString([(-68.79, -38.0), (-68.79, -39.0)])], crs="EPSG:4326")
    deps = gpd.GeoDataFrame({"nombre": ["cantera"], "commodity": ["arena"]}, geometry=[Point(-68.80, -38.36)], crs="EPSG:4326")
    s = prospectivity(u, roads=roads, deposits=deps)
    assert s.loc[0, "score"] > s.loc[1, "score"] > s.loc[2, "score"] and s.loc[3, "score"] == 0
    assert s.loc[0, "f_deposito"] == 1.0 and s.loc[2, "f_deposito"] == 0.0
    assert s["score"].between(0, 100).all()
    t = top_targets(s, n=3, min_area_km2=1.0)
    assert list(t["nombre"]) == ["eólico cerca", "fluvial medio", "arenisca lejos"]


def test_validate_score_at():
    s = prospectivity(_units(), demand=demand_point())
    k = known_points()
    chk = score_at(s, k, radius_km=20)
    assert len(chk) == len(k)
    row = chk[chk["lugar"].str.startswith("Bajo de Añelo")].iloc[0]
    assert row["mejor_score"] == s.loc[0, "score"] and row["clase"] == "arena eólica cuaternaria"
    res = summary(chk)
    assert res["n_favorables"] == 3 and (np.isnan(res["favorables_mediana_percentil"]) or 0 <= res["favorables_mediana_percentil"] <= 100)
