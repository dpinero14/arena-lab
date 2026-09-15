"""Puntaje de prospectividad: dónde conviene ir a muestrear primero.

El puntaje combina lo que dice la roca (la clase de blanco y sus banderas) con
lo que dice el mapa (distancia al consumo, a la red vial y a depósitos de arena
ya conocidos). Los pesos están a la vista en `WEIGHTS`. El puntaje va de 0 a
100 y ordena polígonos; no dice si la arena pasa la norma, eso lo dice el
laboratorio.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from . import ANELO, CRS_GEO, CRS_METRIC

WEIGHTS = {
    "clase": {
        "arena eólica cuaternaria": 1.00,
        "arena fluvial cuaternaria": 0.65,
        "arenisca antigua": 0.45,
        "otra con arena": 0.20,
        "sin interés": 0.00,
    },
    "cuarzo": +0.15,      # la descripción menciona cuarzo o sílice
    "finos": -0.15,       # limos, arcillas, pelitas: turbidez y lavado
    "grava": -0.10,       # gravas y conglomerados: hay que separar
    "consumo_km": (100.0, 500.0),   # factor 1 hasta 100 km del centro de la demanda, 0 a 500 km
    "ruta_km": (5.0, 50.0),         # factor 1 a menos de 5 km de una ruta nacional, 0 a 50 km
    "deposito_km": 25.0,            # bono si hay un depósito de arena conocido a menos de 25 km
    "bono_deposito": 15.0,
}


def base_score(clase: str, f_cuarzo: bool = False, f_finos: bool = False, f_grava: bool = False, w: dict = WEIGHTS) -> float:
    """Puntaje geológico en [0, 1] a partir de la clase y las banderas."""
    b = w["clase"].get(clase, 0.0)
    if b == 0.0:
        return 0.0
    b += (w["cuarzo"] if f_cuarzo else 0.0) + (w["finos"] if f_finos else 0.0) + (w["grava"] if f_grava else 0.0)
    return float(np.clip(b, 0.0, 1.0))


def ramp(d_km: np.ndarray | float, d0: float, d1: float) -> np.ndarray:
    """1 hasta d0, baja linealmente a 0 en d1, 0 después."""
    d = np.asarray(d_km, dtype=float)
    return np.clip(1.0 - (d - d0) / (d1 - d0), 0.0, 1.0)


def distance_km(geoms: gpd.GeoSeries, target: gpd.GeoSeries | gpd.GeoDataFrame) -> np.ndarray:
    """Distancia mínima en km de cada geometría al conjunto `target`, medida en el CRS métrico."""
    g = geoms.to_crs(CRS_METRIC)
    t = target.to_crs(CRS_METRIC)
    tgeom = t.geometry if hasattr(t, "geometry") else t
    union = tgeom.union_all() if hasattr(tgeom, "union_all") else tgeom.unary_union
    return g.distance(union).to_numpy() / 1000.0


def demand_point(lon: float = ANELO[0], lat: float = ANELO[1]) -> gpd.GeoSeries:
    return gpd.GeoSeries([Point(lon, lat)], crs=CRS_GEO)


def prospectivity(units: gpd.GeoDataFrame, roads: gpd.GeoDataFrame | None = None, deposits: gpd.GeoDataFrame | None = None, demand: gpd.GeoSeries | None = None, w: dict = WEIGHTS) -> gpd.GeoDataFrame:
    """Agrega base, factores de distancia y `score` (0-100) a un GeoDataFrame ya clasificado."""
    out = units.copy()
    out["base"] = [base_score(c, q, f, g, w) for c, q, f, g in zip(out["clase"], out.get("f_cuarzo", False), out.get("f_finos", False), out.get("f_grava", False))]
    cent = out.geometry.representative_point()
    dem = demand if demand is not None else demand_point()
    out["d_consumo_km"] = distance_km(cent, dem)
    out["f_consumo"] = ramp(out["d_consumo_km"], *w["consumo_km"])
    if roads is not None and len(roads):
        out["d_ruta_km"] = distance_km(cent, roads)
        out["f_ruta"] = ramp(out["d_ruta_km"], *w["ruta_km"])
    else:
        out["d_ruta_km"] = np.nan
        out["f_ruta"] = 1.0
    if deposits is not None and len(deposits):
        out["d_deposito_km"] = distance_km(cent, deposits)
        out["f_deposito"] = (out["d_deposito_km"] <= w["deposito_km"]).astype(float)
    else:
        out["d_deposito_km"] = np.nan
        out["f_deposito"] = 0.0
    core = 100.0 * out["base"] * (0.5 + 0.5 * out["f_consumo"]) * (0.7 + 0.3 * out["f_ruta"])
    out["score"] = np.clip(core + w["bono_deposito"] * out["f_deposito"] * (out["base"] > 0), 0.0, 100.0).round(1)
    return out


def top_targets(scored: gpd.GeoDataFrame, n: int = 50, min_area_km2: float = 2.0) -> pd.DataFrame:
    """Los mejores polígonos, con superficie y distancias, para la tabla del README."""
    g = scored.copy()
    g["area_km2"] = g.geometry.to_crs(CRS_METRIC).area / 1e6
    g = g[g["area_km2"] >= min_area_km2]
    cols = ["nombre", "nom_hoja", "clase", "descrip_litologica", "edad_inf", "area_km2", "d_consumo_km", "d_ruta_km", "d_deposito_km", "score"]
    cols = [c for c in cols if c in g.columns]
    return g.sort_values(["score", "area_km2"], ascending=[False, False]).head(n)[cols].reset_index(drop=True)


__all__ = ["WEIGHTS", "base_score", "ramp", "distance_km", "demand_point", "prospectivity", "top_targets"]
