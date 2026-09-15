"""Descarga de capas del SIGAM de SEGEMAR por WFS, con paginado.

El servidor es un GeoServer que acepta WFS 2.0 con `count` y `startIndex`, y
devuelve GeoJSON en EPSG:4326. Las capas grandes (el mapa geológico tiene
66.201 polígonos en todo el país) se bajan por páginas y se concatenan. La
licencia declarada del sitio es CC-BY 4.0.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlencode

import geopandas as gpd
import pandas as pd
import requests

WFS = "https://sigam.segemar.gov.ar/geoserver217/ows"

LAYERS = {
    "unidades": "sigam:e250K_UnidadGeologica",          # mapa geológico 1:250.000
    "depositos_industriales": "sigam:e250K.DepositMinIndust",
    "depositos_metaliferos": "sigam:e250K.DepositMetalif",
    "geoquimica": "sigam:e250K.MuestraGeoqMu",
    "fallas": "sigam:e250K.Fallas",
}


def wfs_url(layer: str, bbox: tuple | None = None, count: int | None = None, start_index: int | None = None, property_names: list[str] | None = None) -> str:
    """URL de GetFeature (WFS 2.0, GeoJSON) para una capa, con bbox y paginado opcionales."""
    params = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": LAYERS.get(layer, layer), "outputFormat": "application/json",
    }
    if bbox is not None:
        params["bbox"] = ",".join(f"{v}" for v in bbox) + ",EPSG:4326"
    if count is not None:
        params["count"] = str(count)
    if start_index is not None:
        params["startIndex"] = str(start_index)
    if property_names:
        params["propertyName"] = ",".join(property_names)
    return f"{WFS}?{urlencode(params)}"


def fetch_page(url: str, timeout: int = 600, retries: int = 3, session: requests.Session | None = None) -> dict:
    """Una página de GeoJSON como dict; reintenta ante errores de red."""
    s = session or requests.Session()
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = s.get(url, timeout=timeout, headers={"User-Agent": "arena-lab/0.1 (+https://github.com/dpinero14)"})
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, json.JSONDecodeError) as e:  # pragma: no cover - red
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"no se pudo bajar {url[:120]}...: {last}")


def fetch_layer(layer: str, bbox: tuple | None = None, page: int = 2000, property_names: list[str] | None = None, log=print) -> gpd.GeoDataFrame:
    """Baja una capa completa (o su recorte por bbox) paginando de a `page` features."""
    frames: list[gpd.GeoDataFrame] = []
    start = 0
    session = requests.Session()
    while True:
        url = wfs_url(layer, bbox=bbox, count=page, start_index=start, property_names=property_names)
        data = fetch_page(url, session=session)
        feats = data.get("features", [])
        if not feats:
            break
        frames.append(gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326"))
        matched = data.get("numberMatched")
        log(f"  {layer}: {start + len(feats)}" + (f" de {matched}" if matched else ""))
        start += len(feats)
        if matched is not None and start >= matched:
            break
        if len(feats) < page:
            break
    if not frames:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    gdf = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs="EPSG:4326")
    return gdf


def save_layer(gdf: gpd.GeoDataFrame, path: str | Path) -> Path:
    """Guarda como GeoParquet (rápido de releer) creando la carpeta si falta."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(path)
    return path


def load_layer(path: str | Path) -> gpd.GeoDataFrame:
    return gpd.read_parquet(path)


__all__ = ["WFS", "LAYERS", "wfs_url", "fetch_page", "fetch_layer", "save_layer", "load_layer"]
