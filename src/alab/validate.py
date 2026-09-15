"""Control contra lo que ya se sabe: ¿el puntaje marca alto donde ya se encontró arena?

No hay ensayos de laboratorio públicos en Argentina. Lo que hay son lugares
donde la industria dijo, en público, que la arena funciona o que no: las zonas
que Cormine dio por favorables en 2026, las canteras de Río Negro que las
operadoras dejaron por calidad, y las plantas históricas. Si el puntaje los
marca alto, el mapa tiene algo. Si no, se dice.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from . import CRS_GEO, CRS_METRIC

# nombre, lon, lat, qué se sabe, fuente. Coordenadas aproximadas de la localidad.
KNOWN = [
    ("Senillosa, Neuquén", -68.43, -39.02, "favorable", "Cormine, Mejor Energía 8/9/2026: resultados favorables"),
    ("Cutral Có, Neuquén", -69.23, -38.94, "favorable", "Cormine, Mejor Energía 8/9/2026: corredor Cutral Có-Zapala positivo"),
    ("Zapala, Neuquén", -70.07, -38.90, "favorable", "Cormine, Mejor Energía 8/9/2026: corredor Cutral Có-Zapala positivo"),
    ("Bajo de Añelo, Neuquén", -68.79, -38.35, "en estudio", "Diario Río Negro 8/1/2025: una de las tres zonas con cateos"),
    ("Bajada del Palo, Neuquén", -68.60, -38.20, "explotada", "Vista: cantera propia y planta, Vaca Muerta News 2/5/2026"),
    ("Allen, Río Negro", -67.83, -38.98, "explotada, calidad cuestionada", "NRG Argentina, planta en Allen; las operadoras dejaron la arena patagónica por rotura y arcillas"),
    ("Dolavon, Chubut", -65.71, -43.31, "explotada", "Arenas Patagónicas, planta pionera en Dolavon"),
]


def known_points() -> gpd.GeoDataFrame:
    df = pd.DataFrame(KNOWN, columns=["lugar", "lon", "lat", "estado", "fuente"])
    return gpd.GeoDataFrame(df, geometry=[Point(x, y) for x, y in zip(df.lon, df.lat)], crs=CRS_GEO)


def score_at(scored: gpd.GeoDataFrame, points: gpd.GeoDataFrame, radius_km: float = 15.0) -> pd.DataFrame:
    """Para cada punto conocido: mejor puntaje dentro del radio, su clase, y el percentil de ese puntaje entre todos los polígonos con arena."""
    s = scored.to_crs(CRS_METRIC)
    p = points.to_crs(CRS_METRIC)
    pool = s.loc[s["base"] > 0, "score"].to_numpy()
    rows = []
    for _, pt in p.iterrows():
        dist = s.geometry.distance(pt.geometry)
        nearest_km = float(dist.min() / 1000.0) if len(dist) else np.nan
        near = s[dist <= radius_km * 1000.0]
        if len(near) == 0:
            rows.append({"lugar": pt["lugar"], "estado": pt["estado"], "mejor_score": np.nan, "clase": "sin cobertura del mapa 1:250.000", "unidad": None, "percentil": np.nan, "mapa_mas_cercano_km": round(nearest_km, 1)})
            continue
        best = near.sort_values("score", ascending=False).iloc[0]
        pct = float((pool < best["score"]).mean() * 100) if len(pool) else np.nan
        rows.append({"lugar": pt["lugar"], "estado": pt["estado"], "mejor_score": float(best["score"]), "clase": best["clase"], "unidad": str(best.get("nombre", ""))[:60], "percentil": round(pct, 1), "mapa_mas_cercano_km": 0.0})
    return pd.DataFrame(rows)


def summary(check: pd.DataFrame) -> dict:
    """Resumen honesto: mediana del percentil en los lugares favorables y en los cuestionados."""
    fav = check[check["estado"].str.startswith("favorable")]["percentil"]
    bad = check[check["estado"].str.contains("cuestionada")]["percentil"]
    return {"favorables_mediana_percentil": float(fav.median()) if len(fav) else np.nan, "cuestionados_mediana_percentil": float(bad.median()) if len(bad) else np.nan, "n_favorables": int(len(fav)), "n_cuestionados": int(len(bad))}


__all__ = ["KNOWN", "known_points", "score_at", "summary"]
