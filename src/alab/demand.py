"""Dónde se consume la arena: toneladas bombeadas por área, con coordenadas.

El registro de fractura (Adjunto IV) trae las toneladas de arena por pozo y el
área; el registro de producción (Capítulo IV) trae las coordenadas de cada
pozo. Cruzándolos sale un mapa de demanda: cuánta arena entró a cada área y
dónde queda. Es el lado que le falta a la matriz origen-destino oficial.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from . import CRS_GEO

FRAC_COLS = {"idpozo": "well_id", "areapermisoconcesion": "area", "arena_bombeada_nacional_tn": "sand_domestic_t", "arena_bombeada_importada_tn": "sand_imported_t", "fecha_inicio_fractura": "frac_start", "cuenca": "basin", "tipo_reservorio": "reservoir_type"}


def read_fracture(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False, usecols=list(FRAC_COLS)).rename(columns=FRAC_COLS)
    df["frac_start"] = pd.to_datetime(df["frac_start"], errors="coerce")
    df["sand_t"] = df["sand_domestic_t"].fillna(0) + df["sand_imported_t"].fillna(0)
    return df


def read_well_coords(path: str | Path) -> pd.DataFrame:
    """Coordenadas por pozo desde el archivo de producción (una fila por pozo)."""
    cols = ["idpozo", "coordenadax", "coordenaday", "areapermisoconcesion", "cuenca"]
    df = pd.read_csv(path, low_memory=False, usecols=cols).rename(columns={"idpozo": "well_id", "coordenadax": "lon", "coordenaday": "lat", "areapermisoconcesion": "area", "cuenca": "basin"})
    df = df.dropna(subset=["lon", "lat"]).drop_duplicates("well_id")
    return df[(df.lon.between(-75, -55)) & (df.lat.between(-55, -20))]


def demand_by_area(frac: pd.DataFrame, coords: pd.DataFrame, since: int = 2021, basin: str = "NEUQUINA") -> gpd.GeoDataFrame:
    """Toneladas de arena por área desde `since`, con el centroide de sus pozos."""
    frac = frac.copy()
    if "sand_t" not in frac.columns:
        frac["sand_t"] = frac["sand_domestic_t"].fillna(0) + frac["sand_imported_t"].fillna(0)
    f = frac[(frac["frac_start"].dt.year >= since) & (frac["basin"].str.upper() == basin) & (frac["reservoir_type"].str.upper() == "NO CONVENCIONAL")]
    f = f.merge(coords[["well_id", "lon", "lat"]], on="well_id", how="inner")
    g = f.groupby("area").agg(sand_t=("sand_t", "sum"), wells=("well_id", "nunique"), lon=("lon", "median"), lat=("lat", "median")).reset_index()
    g = g[g["sand_t"] > 0].sort_values("sand_t", ascending=False)
    return gpd.GeoDataFrame(g, geometry=[Point(x, y) for x, y in zip(g.lon, g.lat)], crs=CRS_GEO)


def demand_centroid(demand: gpd.GeoDataFrame) -> gpd.GeoSeries:
    """Centro de gravedad de la demanda, ponderado por toneladas."""
    w = demand["sand_t"] / demand["sand_t"].sum()
    return gpd.GeoSeries([Point((demand.lon * w).sum(), (demand.lat * w).sum())], crs=CRS_GEO)


__all__ = ["read_fracture", "read_well_coords", "demand_by_area", "demand_centroid"]
