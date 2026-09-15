"""Figuras: el mapa interactivo para GitHub Pages y las imágenes del README."""

from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import shapely

from . import CRS_GEO

CLASS_COLORS = {
    "arena eólica cuaternaria": "#f2b134",
    "arena fluvial cuaternaria": "#7fb3d5",
    "arenisca antigua": "#c0504d",
    "otra con arena": "#b0b0b0",
}


def simplify(gdf: gpd.GeoDataFrame, tol_deg: float = 0.002, grid_deg: float = 0.0005) -> gpd.GeoDataFrame:
    """Geometrías simplificadas y con coordenadas redondeadas, para que el HTML pese poco.

    0,002° de tolerancia son unos 200 m; la grilla de 0,0005° (~50 m) recorta los
    decimales, que es lo que más pesa en un GeoJSON.
    """
    g = gdf.copy()
    geom = g.geometry.simplify(tol_deg, preserve_topology=True)
    g["geometry"] = shapely.set_precision(geom.to_numpy(), grid_deg)
    g = g[~g.geometry.is_empty & g.geometry.notna()]
    return g


def interactive_map(scored: gpd.GeoDataFrame, deposits: gpd.GeoDataFrame | None = None, demand: gpd.GeoDataFrame | None = None, known: gpd.GeoDataFrame | None = None, roads: gpd.GeoDataFrame | None = None, min_score: float = 20.0, min_area_km2: float = 1.0, tol_deg: float = 0.003, path: str | Path | None = None, route: gpd.GeoDataFrame | None = None, waypoints: gpd.GeoDataFrame | None = None) -> folium.Map:
    """Mapa folium con los polígonos por puntaje, depósitos, demanda y lugares conocidos."""
    sel = scored[scored["score"] >= min_score].to_crs(CRS_GEO)
    if min_area_km2 > 0:
        sel = sel[sel.geometry.to_crs("EPSG:5344").area / 1e6 >= min_area_km2]
    g = simplify(sel, tol_deg)
    g["score"] = g["score"].round(0)
    for c in ("d_consumo_km", "d_ruta_km"):
        if c in g.columns:
            g[c] = g[c].round(0)
    m = folium.Map(location=[-38.6, -68.5], zoom_start=7, tiles="OpenStreetMap", control_scale=True)
    cmap = matplotlib.colormaps["YlOrRd"]

    def style(feat):
        s = feat["properties"].get("score", 0) or 0
        r, gg, b, _ = cmap(min(1.0, s / 100.0))
        return {"fillColor": matplotlib.colors.to_hex((r, gg, b)), "color": "#555555", "weight": 0.3, "fillOpacity": 0.65}

    keep = [c for c in ("nombre", "clase", "descrip_litologica", "edad_inf", "score", "d_consumo_km", "d_ruta_km") if c in g.columns]
    folium.GeoJson(
        g[keep + ["geometry"]].to_json(),
        name=f"blancos con puntaje ≥ {min_score:g}",
        style_function=style,
        tooltip=folium.GeoJsonTooltip(fields=keep, aliases=["unidad", "clase", "litología", "edad", "puntaje", "km a Añelo", "km a ruta"][: len(keep)], localize=True),
    ).add_to(m)
    if roads is not None and len(roads):
        folium.GeoJson(simplify(roads.to_crs(CRS_GEO), 0.005)[["geometry"]].to_json(), name="rutas nacionales", style_function=lambda f: {"color": "#333333", "weight": 1.2, "opacity": 0.6}).add_to(m)
    if deposits is not None and len(deposits):
        fg = folium.FeatureGroup(name="depósitos de arena y sílice (SEGEMAR)")
        for _, r in deposits.to_crs(CRS_GEO).iterrows():
            folium.CircleMarker([r.geometry.y, r.geometry.x], radius=4, color="#2a78d6", fill=True, fill_opacity=0.9, tooltip=f"{r.get('nombre', '')} · {r.get('commodity', '')}").add_to(fg)
        fg.add_to(m)
    if demand is not None and len(demand):
        fg = folium.FeatureGroup(name="arena bombeada por área desde 2021")
        mx = float(demand["sand_t"].max())
        for _, r in demand.iterrows():
            folium.CircleMarker([r["lat"], r["lon"]], radius=4 + 26 * (r["sand_t"] / mx) ** 0.5, color="#111111", weight=1, fill=True, fill_color="#f2b134", fill_opacity=0.5, tooltip=f"{r['area']}: {r['sand_t']/1e3:,.0f} kt de arena, {r['wells']} pozos").add_to(fg)
        fg.add_to(m)
    if known is not None and len(known):
        fg = folium.FeatureGroup(name="lugares con arena conocida")
        for _, r in known.iterrows():
            color = "#2e8b57" if r.estado.startswith("favorable") else ("#c0504d" if "cuestionada" in r.estado else "#555555")
            folium.Marker([r.lat, r.lon], icon=folium.Icon(color="green" if color == "#2e8b57" else ("red" if color == "#c0504d" else "gray"), icon="info-sign"), tooltip=f"{r.lugar}: {r.estado}").add_to(fg)
        fg.add_to(m)
    if route is not None and len(route):
        r = route.iloc[0]
        fg = folium.FeatureGroup(name=f"ruta de la arena, Ibicuy a Añelo ({r['km']:,.0f} km)".replace(",", "."))
        coords = [(y, x) for x, y in simplify(route.to_crs(CRS_GEO), 0.001).geometry.iloc[0].coords]
        folium.PolyLine(coords, color="#111111", weight=5, opacity=0.9, tooltip=f"{r['nombre']}: {r['km']:,.0f} km".replace(",", ".")).add_to(fg)
        folium.PolyLine(coords, color="#f2b134", weight=2.5, opacity=1.0).add_to(fg)
        if waypoints is not None and len(waypoints):
            for _, w in waypoints.iterrows():
                folium.CircleMarker([w["lat"], w["lon"]], radius=5, color="#111111", weight=1.5, fill=True, fill_color="#ffffff", fill_opacity=1.0, tooltip=f"{w['lugar']}: {w['nota']}").add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    if path is not None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        m.save(str(path))
    return m


def route_figure(route: gpd.GeoDataFrame, waypoints: gpd.GeoDataFrame, roads_all: gpd.GeoDataFrame, scored: gpd.GeoDataFrame | None, path: str | Path, min_score: float = 40.0) -> Path:
    """PNG de la ruta completa sobre la red de rutas nacionales, con los blancos de mayor puntaje."""
    fig, ax = plt.subplots(figsize=(10, 8))
    roads_all.to_crs(CRS_GEO).plot(ax=ax, color="#cccccc", linewidth=0.5)
    if scored is not None:
        top = scored[scored["score"] >= min_score].to_crs(CRS_GEO)
        top.plot(ax=ax, color="#f2b134", linewidth=0, alpha=0.8, label=f"blancos con puntaje ≥ {min_score:g}")
    route.to_crs(CRS_GEO).plot(ax=ax, color="#111111", linewidth=2.2)
    for _, w in waypoints.iterrows():
        ax.plot(w["lon"], w["lat"], marker="o", color="white", markeredgecolor="black", markersize=6)
        ax.annotate(w["lugar"].split(",")[0], (w["lon"], w["lat"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    r = route.iloc[0]
    ax.set_xlim(-71.5, -57.5); ax.set_ylim(-41.5, -32.5); ax.set_aspect(1 / 0.78)
    ax.set_title(f"La ruta de la arena: Ibicuy a Añelo, {r['km']:,.0f} km por caminos reales".replace(",", "."), fontsize=12, loc="left")
    ax.plot([], [], color="#111111", linewidth=2.2, label="ruta de la arena (ruteo OSRM sobre OpenStreetMap)")
    ax.plot([], [], color="#cccccc", linewidth=1, label="rutas nacionales")
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.set_xlabel("longitud"); ax.set_ylabel("latitud")
    fig.text(0.99, 0.01, "datos: OSRM y OpenStreetMap, IDE Transporte, SEGEMAR · arena-lab", ha="right", fontsize=7, color="gray")
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return Path(path)


def static_map(scored: gpd.GeoDataFrame, deposits: gpd.GeoDataFrame | None, known: gpd.GeoDataFrame | None, path: str | Path, min_score: float = 20.0, title: str = "Dónde buscar arena de fractura: puntaje de prospectividad") -> Path:
    """PNG para el README: polígonos por puntaje, depósitos y lugares conocidos."""
    fig, ax = plt.subplots(figsize=(10, 9))
    bg = scored.to_crs(CRS_GEO)
    bg[bg["base"] > 0].plot(ax=ax, color="#e8e8e8", linewidth=0)
    top = bg[bg["score"] >= min_score]
    top.plot(ax=ax, column="score", cmap="YlOrRd", vmin=0, vmax=100, linewidth=0, legend=True, legend_kwds={"label": "puntaje (0 a 100)", "shrink": 0.6})
    if deposits is not None and len(deposits):
        deposits.to_crs(CRS_GEO).plot(ax=ax, color="#2a78d6", markersize=14, label="depósitos de arena y sílice (SEGEMAR)")
    if known is not None and len(known):
        for _, r in known.iterrows():
            c = "#2e8b57" if r.estado.startswith("favorable") else ("#c0504d" if "cuestionada" in r.estado else "#555555")
            ax.plot(r.lon, r.lat, marker="^", color=c, markersize=10, markeredgecolor="black")
            ax.annotate(r.lugar.split(",")[0], (r.lon, r.lat), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.plot([], [], marker="^", color="#2e8b57", linestyle="", label="favorable según Cormine 2026")
    ax.plot([], [], marker="^", color="#c0504d", linestyle="", label="explotada, calidad cuestionada")
    ax.set_title(title, fontsize=12, loc="left"); ax.set_xlabel("longitud"); ax.set_ylabel("latitud")
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    ax.set_aspect(1 / 0.78)
    fig.text(0.99, 0.01, "datos: SEGEMAR SIGAM (CC-BY 4.0), Secretaría de Energía, IDE Transporte · arena-lab", ha="right", fontsize=7, color="gray")
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return Path(path)


def class_bar(scored: gpd.GeoDataFrame, path: str | Path) -> Path:
    """Superficie por clase de blanco, en km²."""
    g = scored.copy()
    g["area_km2"] = g.geometry.to_crs("EPSG:5344").area / 1e6
    s = g.groupby("clase")["area_km2"].sum().reindex([c for c in CLASS_COLORS] + ["sin interés"]).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.barh(s.index, s.values / 1e3, color=[CLASS_COLORS.get(c, "#dddddd") for c in s.index])
    for i, v in enumerate(s.values / 1e3):
        ax.text(v + 1, i, f"{v:,.0f}".replace(",", "."), va="center", fontsize=9)
    ax.set_xlabel("miles de km² en la ventana"); ax.invert_yaxis(); ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Cuánta superficie cae en cada clase de blanco", loc="left", fontsize=11)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)
    return Path(path)


__all__ = ["CLASS_COLORS", "simplify", "interactive_map", "static_map", "class_bar", "route_figure"]
