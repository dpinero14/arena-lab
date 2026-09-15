"""La ruta como costo oculto: cuánto pesan los camiones de arena en el tránsito de cada tramo.

IDE Transporte publica el tránsito medio diario anual (TMDA) de 2017 por tramo
de ruta nacional. Este módulo recorta esos tramos a la traza de la ruta de la
arena, cuenta las pasadas de camión por día que salen del registro de
fractura, ida cargada y vuelta vacía, y las compara con el tránsito total que
cada tramo tenía en 2017, antes del salto de Vaca Muerta. Para el desgaste usa
la ley de la cuarta potencia del AASHO Road Test: el daño de un eje crece con
la cuarta potencia de su carga, y una pasada de un semirremolque de cinco ejes
equivale a unos 10.000 autos.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from . import CRS_GEO, CRS_METRIC
from .animation import SUPUESTOS
from .logistics import CHAINS, Chain

# Ejes equivalentes (ESAL) por pasada, AASHTO 1993 en pavimento rígido: semirremolque de 5 ejes y 36 t
# contra un auto de dos ejes de 900 kg. Fuente: American Trucking Associations, "Analysis of car and
# truck pavement impacts" (2022), sobre la Guía AASHTO 1993.
ESAL = {"semi_5_ejes": 4.26, "auto": 0.0004}
AUTOS_POR_PASADA = round(ESAL["semi_5_ejes"] / ESAL["auto"])   # 10.650 autos por cada camión que pasa

NOMBRES = {"0003": "RN 3", "0005": "RN 5", "0007": "RN 7", "0008": "RN 8", "0009": "RN 9", "0012": "RN 12", "0014": "RN 14", "0022": "RN 22",
           "0033": "RN 33", "0035": "RN 35", "0143": "RN 143", "0151": "RN 151", "0152": "RN 152", "0226": "RN 226", "0232": "RN 232"}


def route_segments(tmda: gpd.GeoDataFrame, route: gpd.GeoDataFrame, corredor: str = "Ibicuy", buffer_m: float = 1500.0, step_km: float = 2.0, min_km: float = 10.0) -> gpd.GeoDataFrame:
    """La traza partida en tramos según el tramo de TMDA más cercano: ruta, km sobre la traza, posición y tránsito 2017.

    Se muestrea la traza cada `step_km`, se busca el tramo de TMDA más cercano a menos de `buffer_m` (si hay varios
    a la misma distancia, el de más tránsito, que es la opción conservadora) y se unen las muestras consecutivas
    del mismo tramo. Las corridas más cortas que `min_km` son cruces de otras rutas y se absorben en la anterior.
    La geometría de cada tramo es el pedazo de la traza, no la línea de IDE, que trae calzadas dobles y partes repetidas.
    """
    from shapely.ops import substring

    t = tmda.to_crs(CRS_METRIC)
    line = route.to_crs(CRS_METRIC).geometry.iloc[0]
    total = line.length
    ds = np.arange(0.0, total, step_km * 1000.0)
    cand = t[t.intersects(line.buffer(buffer_m))]
    picks = []
    for d in ds:
        p = line.interpolate(d)
        near = cand[cand.distance(p) <= buffer_m] if len(cand) else cand
        if near.empty:
            picks.append(None)
            continue
        dist = near.distance(p)
        tie = near[dist <= dist.min() + 200.0]
        picks.append(int(tie["tmda17"].astype(float).idxmax()))
    # corridas de muestras consecutivas con el mismo tramo
    runs: list[list] = []
    for i, g in enumerate(picks):
        if g is None:
            continue
        if runs and runs[-1][0] == g and runs[-1][2] == i - 1:
            runs[-1][2] = i
        else:
            runs.append([g, i, i])
    merged: list[list] = []
    for g, a, b in runs:
        # una corrida corta pegada a la anterior es un cruce y se absorbe; suelta, es ruido y se descarta;
        # si después de un cruce vuelve el mismo tramo, se sigue en la misma fila
        corta = (b - a + 1) * step_km < min_km
        pegada = bool(merged) and merged[-1][2] >= a - 1
        if pegada and (corta or merged[-1][0] == g):
            merged[-1][2] = b
        elif not corta:
            merged.append([g, a, b])
    rows = []
    for g, a, b in merged:
        d0 = float(ds[a]); d1 = min(total, float(ds[b]) + step_km * 1000.0)
        src = t.loc[g]
        rows.append({"cod_ruta": src["cod_ruta"], "ruta": NOMBRES.get(src["cod_ruta"], "RN " + str(src["cod_ruta"]).lstrip("0")), "corredor": corredor,
                     "km": round((d1 - d0) / 1000.0, 1), "km_desde": round(d0 / 1000.0), "tmda17": int(src["tmda17"]), "geometry": substring(line, d0, d1)})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=CRS_METRIC).to_crs(CRS_GEO)


def passages_per_day(tons: float, t_por_camion: float = SUPUESTOS["t_por_camion"], dias: int = SUPUESTOS["dias_operativos"], vuelta_vacia: bool = True) -> float:
    """Pasadas de camión por día que genera un tonelaje anual: viajes cargados más la vuelta vacía."""
    return tons / t_por_camion / dias * (2.0 if vuelta_vacia else 1.0)


def pressure(segments: gpd.GeoDataFrame, yearly: pd.DataFrame, s: dict = SUPUESTOS) -> pd.DataFrame:
    """Año por tramo: pasadas por día, porcentaje sobre el tránsito total de 2017 y autos equivalentes en desgaste."""
    rows = []
    for _, y in yearly.iterrows():
        p = passages_per_day(float(y["nat_t"]), s["t_por_camion"], s["dias_operativos"])
        for _, g in segments.iterrows():
            rows.append({"anio": int(y["anio"]), "corredor": g["corredor"], "ruta": g["ruta"], "km_desde": g["km_desde"], "km": g["km"], "tmda17": int(g["tmda17"]),
                         "pasadas_dia": round(p), "sobre_tmda_pct": round(100.0 * p / g["tmda17"], 1), "autos_equiv_dia": round(p * AUTOS_POR_PASADA)})
    return pd.DataFrame(rows)


def exceeded(pr: pd.DataFrame) -> pd.DataFrame:
    """Por año: cuántos tramos y km tienen más pasadas de arena que todo su tránsito de 2017, y cuál es el peor."""
    out = []
    for anio, d in pr.groupby("anio"):
        worst = d.loc[d["sobre_tmda_pct"].idxmax()]
        sup = d[d["sobre_tmda_pct"] > 100.0]
        out.append({"anio": int(anio), "pasadas_dia": int(d["pasadas_dia"].iloc[0]), "tramos": len(d), "tramos_superados": len(sup), "km_superados": round(float(sup["km"].sum())),
                    "peor_ruta": worst["ruta"], "peor_pct": float(worst["sobre_tmda_pct"])})
    return pd.DataFrame(out)


def by_route(pr: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Resumen por ruta nacional en un año: km, rango de tránsito 2017, pasadas y rango del porcentaje."""
    d = pr[pr["anio"] == anio]
    g = d.groupby("ruta").agg(km=("km", "sum"), tmda17_min=("tmda17", "min"), tmda17_max=("tmda17", "max"), pasadas_dia=("pasadas_dia", "first"),
                              pct_min=("sobre_tmda_pct", "min"), pct_max=("sobre_tmda_pct", "max"), km_desde=("km_desde", "min"))
    return g.sort_values("km_desde").drop(columns="km_desde").round(1).reset_index()


def passages_by_chain(tons: float, chains: list[Chain] = CHAINS, t_por_camion: float = SUPUESTOS["t_por_camion"], dias: int = SUPUESTOS["dias_operativos"], min_km: float = 200.0) -> pd.DataFrame:
    """Pasadas de camión de larga distancia por día sobre rutas nacionales, por cadena.

    Cuenta solo los tramos en camión de más de `min_km`: la última milla y la arena cercana no tocan la ruta larga.
    """
    rows = []
    for c in chains:
        largo = sum(l.km for l in c.legs if l.modo == "camion" and l.km >= min_km)
        p = passages_per_day(tons, t_por_camion, dias) if largo > 0 else 0.0
        rows.append({"cadena": c.nombre, "km_camion_largo": round(largo), "pasadas_dia": round(p), "autos_equiv_dia": round(p * AUTOS_POR_PASADA)})
    return pd.DataFrame(rows)


def segments_geojson(segments: gpd.GeoDataFrame, tol_deg: float = 0.003) -> dict:
    """GeoJSON liviano de los tramos para la página animada, con las propiedades que usa el color por año."""
    g = segments.copy()
    g["geometry"] = g.geometry.simplify(tol_deg, preserve_topology=True)
    g["km_desde"] = g["km_desde"].astype(float)
    return g[["ruta", "corredor", "km", "km_desde", "tmda17", "geometry"]].__geo_interface__


def pressure_figure(pr: pd.DataFrame, anio: int, path, corredor: str = "Ibicuy") -> None:
    """Barras a lo largo de la ruta: cada tramo con su ancho en km y su altura en pasadas de arena sobre el tránsito de 2017."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = pr[(pr["anio"] == anio) & (pr["corredor"] == corredor)].sort_values("km_desde")
    fig, ax = plt.subplots(figsize=(11, 4.2))
    colors = ["#d7301f" if p >= 100 else "#fc8d59" if p >= 50 else "#fee08b" if p >= 20 else "#4caf50" for p in d["sobre_tmda_pct"]]
    ax.bar(d["km_desde"], d["sobre_tmda_pct"], width=d["km"], align="edge", color=colors, edgecolor="#333", linewidth=.4)
    ax.axhline(100, color="#d7301f", lw=1, ls="--")
    ax.text(d["km_desde"].min() + 5, 104, "la arena supera todo el tránsito de 2017", color="#d7301f", fontsize=8.5, va="bottom")
    top = max(120.0, float(d["sobre_tmda_pct"].max()) * 1.12)
    for ruta, g in d.groupby("ruta"):
        x0 = g["km_desde"].min(); x1 = (g["km_desde"] + g["km"]).max()
        ax.text((x0 + x1) / 2, top * 0.97, ruta, ha="center", va="top", fontsize=8.5, color="#333", bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#bbb", "lw": .5})
    p = f"{int(d['pasadas_dia'].iloc[0]):,}".replace(",", ".")
    ax.set_title(f"La ruta de la arena en {anio}: {p} pasadas de camión por día contra el tránsito total de 2017, tramo por tramo", fontsize=10.5, loc="left")
    ax.set_xlabel("km desde Ibicuy"); ax.set_ylabel("pasadas de arena / tránsito 2017, %")
    ax.set_xlim(0, (d["km_desde"] + d["km"]).max()); ax.set_ylim(0, top)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.text(0.01, 0.005, "Datos: IDE Transporte (TMDA 2017), Secretaría de Energía (registro de fractura), OSRM sobre OpenStreetMap. Supuestos: 30 t por camión, 300 días, vuelta vacía. arena-lab", fontsize=7, color="#666")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(path, dpi=150); plt.close(fig)


__all__ = ["ESAL", "AUTOS_POR_PASADA", "NOMBRES", "route_segments", "passages_per_day", "pressure", "exceeded", "by_route", "passages_by_chain", "segments_geojson", "pressure_figure"]
