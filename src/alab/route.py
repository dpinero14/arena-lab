"""La ruta de la arena: de las canteras de Ibicuy al pozo en Añelo, sobre caminos reales.

Los puntos de paso salen de los informes de prensa que describen el recorrido
tramo por tramo (Diario Neuquino y LM Neuquén, septiembre de 2026): RP 45 hasta
la RN 12, RN 12 y Acceso Oeste hasta Luján, RN 5 hasta Santa Rosa, RN 35 y
RN 152 hasta Puelches, RP 20 hasta 25 de Mayo, RN 151 por Catriel hasta el
Alto Valle, y RP 7 hasta Añelo. La traza entre puntos la calcula OSRM, un
ruteador abierto sobre OpenStreetMap; si no hay red, se une con rectas.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, Point

from . import CRS_GEO, CRS_METRIC

# nombre, lon, lat, qué pasa ahí
WAYPOINTS = [
    ("Ibicuy, Entre Ríos", -59.17, -33.74, "canteras y puerto; la arena sale lavada"),
    ("Ceibas", -58.77, -33.45, "empalme con la RN 12"),
    ("Luján", -59.10, -34.57, "fin del Acceso Oeste; empieza la RN 5 de mano y contramano"),
    ("Santa Rosa", -64.29, -36.62, "545 km de RN 5; sigue por RN 35 y RN 152"),
    ("Puelches", -65.91, -38.14, "empalme con la RP 20 de La Pampa"),
    ("25 de Mayo, La Pampa", -67.72, -37.77, "fin de la RP 20; empieza la RN 151"),
    ("Catriel", -67.79, -37.88, "RN 151, el tramo más deteriorado"),
    ("Cinco Saltos", -68.06, -38.82, "Alto Valle; cruce del río Neuquén"),
    ("Añelo", -68.79, -38.35, "RP 7; el corazón operativo de Vaca Muerta"),
]

OSRM = "https://router.project-osrm.org/route/v1/driving/"


def waypoints_frame() -> gpd.GeoDataFrame:
    df = pd.DataFrame(WAYPOINTS, columns=["lugar", "lon", "lat", "nota"])
    return gpd.GeoDataFrame(df, geometry=[Point(x, y) for x, y in zip(df.lon, df.lat)], crs=CRS_GEO)


def straight_route(waypoints: list[tuple] = WAYPOINTS) -> LineString:
    """Rectas entre puntos de paso: el plan B cuando no hay ruteador."""
    return LineString([(w[1], w[2]) for w in waypoints])


def fetch_osrm(waypoints: list[tuple] = WAYPOINTS, cache: str | Path | None = None, timeout: int = 90) -> dict:
    """Respuesta cruda de OSRM (geometría GeoJSON, distancia, duración), con caché en disco."""
    if cache is not None and Path(cache).exists():
        return json.loads(Path(cache).read_text(encoding="utf-8"))
    coords = ";".join(f"{w[1]},{w[2]}" for w in waypoints)
    r = requests.get(f"{OSRM}{coords}", params={"overview": "full", "geometries": "geojson"}, timeout=timeout, headers={"User-Agent": "arena-lab/0.1 (+https://github.com/dpinero14)"})
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM respondió {data.get('code')}")
    if cache is not None:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        Path(cache).write_text(json.dumps(data), encoding="utf-8")
    return data


def sand_route(cache: str | Path | None = None, log=print) -> gpd.GeoDataFrame:
    """Una fila: la traza completa, su largo en km, horas estimadas por OSRM y el origen (osrm o rectas)."""
    try:
        data = fetch_osrm(cache=cache)
        r = data["routes"][0]
        line = LineString(r["geometry"]["coordinates"])
        km = r["distance"] / 1000.0
        horas = r["duration"] / 3600.0
        src = "osrm"
    except Exception as e:  # pragma: no cover - depende de la red
        log(f"  sin ruteador ({e}); uso rectas entre puntos de paso")
        line = straight_route()
        km = gpd.GeoSeries([line], crs=CRS_GEO).to_crs(CRS_METRIC).length.iloc[0] / 1000.0
        horas = float("nan")
        src = "rectas"
    return gpd.GeoDataFrame({"nombre": ["ruta de la arena: Ibicuy a Añelo"], "km": [round(km)], "horas_osrm": [round(horas, 1)], "fuente": [src]}, geometry=[line], crs=CRS_GEO)


def distance_to_route(geoms: gpd.GeoSeries, route: gpd.GeoDataFrame) -> pd.Series:
    """Distancia en km de cada geometría a la traza."""
    g = geoms.to_crs(CRS_METRIC)
    line = route.to_crs(CRS_METRIC).geometry.iloc[0]
    return g.distance(line) / 1000.0


__all__ = ["WAYPOINTS", "OSRM", "waypoints_frame", "straight_route", "fetch_osrm", "sand_route", "distance_to_route"]
