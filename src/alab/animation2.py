"""La ruta de la arena animada, versión 2: cadenas alternativas, capas y contexto.

Sobre la versión 1 agrega: los blancos de arena debajo de la ruta, el
ferrocarril con su estado, los puertos y los ríos como capas; un selector de
cadena logística (camión, barcaza y camión, barcaza y tren, hidrovía, arena
cercana) que cambia las unidades que circulan, el costo del año y las
emisiones; una línea de contexto por año; y una pantalla de cierre. Los
recorridos de barcazas, trenes y camiones son trazas aproximadas por puntos
de paso, salvo las de camión, que salen de OSRM.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString

from . import CRS_GEO, CRS_METRIC
from .animation import SUPUESTOS
from .logistics import CHAINS, Chain

# Trazas aproximadas (lon, lat) para las unidades que no van por ruta: agua y tren.
AGUA_IBICUY_BB = [(-59.18, -33.76), (-58.90, -33.95), (-58.40, -34.30), (-57.30, -35.00), (-57.00, -36.30), (-57.55, -38.10), (-58.60, -38.75), (-60.20, -39.20), (-61.60, -39.25), (-62.30, -38.78)]
AGUA_BB_VIEDMA = [(-62.30, -38.78), (-62.10, -39.30), (-62.50, -40.30), (-62.85, -41.05)]
RIO_NEGRO_ARRIBA = [(-62.85, -41.05), (-62.99, -40.80), (-63.60, -40.35), (-64.45, -40.10), (-65.20, -39.70), (-65.65, -39.28), (-66.40, -39.20), (-67.07, -39.10), (-67.58, -39.03), (-68.06, -38.95)]
TREN_BB_ANELO = [(-62.30, -38.78), (-62.90, -38.85), (-64.00, -38.99), (-65.65, -39.28), (-66.40, -39.20), (-67.07, -39.10), (-67.58, -39.03), (-68.06, -38.95), (-68.16, -38.72), (-68.79, -38.35)]
TREN_NUEVO_DESDE = (-68.16, -38.72)   # Contraalmirante Cordero: desde acá los 83 km que faltan
CAMION_ULTIMA_MILLA = [(-68.79, -38.35), (-68.66, -38.30), (-68.60, -38.22)]
CAMION_CERCANA = [(-68.43, -39.02), (-68.55, -38.80), (-68.70, -38.55), (-68.79, -38.35)]
# arenoducto hipotético: cruce del Paraná en Zárate, corredor de la RN 5 hasta Salliqueló y la traza del gasoducto Perito Moreno hasta Tratayén
ARENODUCTO_TRAZA = [(-59.17, -33.74), (-59.03, -34.10), (-59.60, -34.60), (-60.49, -35.12), (-61.97, -35.81), (-62.96, -36.75), (-64.60, -37.05), (-66.30, -37.55), (-67.90, -38.10), (-68.73, -38.38), (-68.79, -38.35)]

# Contexto por año: solo hechos verificados o que salen de los propios datos.
CONTEXTO = {
    2013: "YPF y Chevron arrancan Loma Campana; casi toda la arena es importada",
    2014: "primeras 100.000 t nacionales; siguen dominando las importadas",
    2016: "la arena nacional supera a la importada por primera vez",
    2017: "las canteras patagónicas y Entre Ríos abastecen el crecimiento",
    2019: "1,5 millones de toneladas, récord hasta entonces",
    2020: "pandemia: la actividad cae a la mitad",
    2021: "el salto: 2,3 millones de toneladas, la importada ya no cuenta",
    2022: "3 millones de toneladas; 4.000 camiones en la ruta",
    2024: "Río Negro produce 2,6 Mt; las operadoras empiezan a dejar la arena patagónica",
    2025: "5 millones de toneladas; NRG en concurso; Río Negro cae 43 %",
    2026: "año parcial; PTP invierte 12 MUSD en la terminal fluvial de Ibicuy",
}

# unidades de transporte por modo: capacidad por unidad, km por día y cuántas unidades representa un punto
UNIDADES = {
    "camion": {"t": 30.0, "km_dia": 500.0, "por_punto": 25, "color": "#f2b134", "nombre": "camión"},
    "fluvial": {"t": 2400.0, "km_dia": 300.0, "por_punto": 1, "color": "#3b8ed0", "nombre": "barcaza (80 camiones)"},
    "maritimo": {"t": 2400.0, "km_dia": 400.0, "por_punto": 1, "color": "#3b8ed0", "nombre": "barcaza (80 camiones)"},
    "tren": {"t": 2000.0, "km_dia": 400.0, "por_punto": 1, "color": "#2e8b57", "nombre": "tren (2.000 t)"},
    "pulpa": {"t": 10000.0, "km_dia": 144.0, "por_punto": 1, "color": "#26c6da", "nombre": "pulpa en el arenoducto (10.000 t, a 6 km/h)"},
}


def _path(coords: list[tuple[float, float]]) -> dict:
    """Vértices [lat, lon, s] con s acumulado, y largo en km, para una traza de puntos."""
    line = LineString(coords)
    m = gpd.GeoSeries([line], crs=CRS_GEO).to_crs(CRS_METRIC).iloc[0]
    mxy = np.asarray(m.coords)
    seg = np.hypot(np.diff(mxy[:, 0]), np.diff(mxy[:, 1]))
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    s = cum / cum[-1]
    return {"coords": [[round(y, 4), round(x, 4), round(float(v), 5)] for (x, y), v in zip(coords, s)], "km": round(float(cum[-1] / 1000.0))}


def _osrm_path(cache: Path, tol: float = 0.003) -> list[tuple[float, float]]:
    d = json.loads(Path(cache).read_text(encoding="utf-8"))
    line = LineString(d["routes"][0]["geometry"]["coordinates"]).simplify(tol, preserve_topology=True)
    return [(round(x, 4), round(y, 4)) for x, y in line.coords]


def chain_paths(route_cache: Path, bb_cache: Path, chains: list[Chain] = CHAINS) -> list[dict]:
    """Para cada cadena: sus tramos animables, con modo, traza y km."""
    ibicuy = _osrm_path(route_cache)
    bb = _osrm_path(bb_cache)
    # (modo, traza, corredor): el corredor nombra las rutas nacionales que ese tramo en camión carga; None si no toca la ruta larga
    by_name = {
        "camión directo, hoy": [("camion", ibicuy, "Ibicuy")],
        "barcaza a Bahía Blanca y camión": [("maritimo", AGUA_IBICUY_BB, None), ("camion", bb, "Bahía Blanca")],
        "barcaza, Tren Norpatagónico y camión": [("maritimo", AGUA_IBICUY_BB, None), ("tren", TREN_BB_ANELO, None), ("camion", CAMION_ULTIMA_MILLA, None)],
        "hidrovía patagónica por el río Negro": [("maritimo", AGUA_IBICUY_BB + AGUA_BB_VIEDMA[1:], None), ("fluvial", RIO_NEGRO_ARRIBA, None), ("camion", CAMION_ULTIMA_MILLA, None)],
        "arena cercana de Neuquén": [("camion", CAMION_CERCANA, None)],
        "arenoducto, hipotético": [("pulpa", ARENODUCTO_TRAZA, None), ("camion", CAMION_ULTIMA_MILLA, None)],
    }
    out = []
    for c in chains:
        legs = [{"modo": modo, "corredor": corredor, **_path(coords)} for modo, coords, corredor in by_name[c.nombre]]
        out.append({"nombre": c.nombre, "usd_t": round(c.usd_t_pozo, 1), "kg_co2e_t": round(c.kg_co2e_t(), 1), "km_camion": round(c.km_camion), "km_total": round(c.km_total),
                    "estado": c.estado, "limite": c.limite, "capacidad_mt": c.capacidad_mt, "paths": legs,
                    "capex_musd": c.capex_musd, "vida_anios": c.vida_anios, "usd_t_variable": round(c.usd_t_variable, 1), "agua_t_t": c.agua_t_t})
    return out


def logistics_animation_html(yearly: pd.DataFrame, chains: list[dict], layers: dict, waypoints: gpd.GeoDataFrame, path: str | Path, partial_year: int | None = None, s: dict = SUPUESTOS) -> Path:
    """Escribe la página v2. `layers` trae GeoJSON ya simplificados: blancos, ferrocarril, rios, puertos y, si está, tramos con el tránsito de 2017."""
    layers = {"tramos": {"type": "FeatureCollection", "features": []}, **layers}
    data = {
        "years": [{k: (None if pd.isna(v) else (int(v) if float(v).is_integer() else float(v))) for k, v in row.items()} for row in yearly.to_dict("records")],
        "partial": partial_year, "supuestos": s, "unidades": UNIDADES, "contexto": {str(k): v for k, v in CONTEXTO.items()},
        "chains": chains, "layers": layers, "tren_nuevo_desde": TREN_NUEVO_DESDE,
        "waypoints": [{"lugar": r["lugar"], "lat": float(r["lat"]), "lon": float(r["lon"]), "nota": r["nota"]} for _, r in waypoints.iterrows()],
    }
    html = TEMPLATE2.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


TEMPLATE2 = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>La ruta de la arena, año a año</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--bg:#0e1b25;--ink:#e9eff3;--muted:#8ea2af;--accent:#f2b134;--rule:#22384a;--card:#132633;--ok:#2e8b57;--water:#3b8ed0}
html,body{margin:0;height:100%;font-family:"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink)}
#map{position:absolute;inset:0}
#panel{position:absolute;top:12px;right:12px;width:380px;max-height:calc(100% - 24px);overflow:auto;background:rgba(14,27,37,.95);border:1px solid var(--rule);border-radius:6px;padding:14px 18px;z-index:1000;box-sizing:border-box}
.eyebrow{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:600}
h1{margin:4px 0 2px;font-size:19px;font-weight:600}
.sub{color:var(--muted);font-size:12px;margin-bottom:8px}
.year{font-family:Consolas,monospace;font-size:50px;line-height:1;color:var(--accent);font-weight:700;margin:4px 0 0}
.ctx{color:var(--ink);font-size:12.5px;min-height:34px;margin:4px 0 6px;line-height:1.35}
.chains{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}
.chains button{background:var(--card);color:var(--ink);border:1px solid var(--rule);border-radius:4px;padding:4px 8px;font-size:11.5px;cursor:pointer;font-weight:500}
.chains button.on{background:var(--accent);color:#0e1b25;border-color:var(--accent);font-weight:600}
.row{display:flex;justify-content:space-between;align-items:baseline;padding:4px 0;border-bottom:1px dashed var(--rule);font-size:13px;gap:10px}
.row .l{color:var(--muted)}.row .v{font-family:Consolas,monospace;font-size:14.5px;text-align:right}
.big{margin:8px 0 2px}.big .l{color:var(--muted);font-size:11px;letter-spacing:.1em;text-transform:uppercase}
.big .v{font-family:Consolas,monospace;font-size:28px;color:var(--accent);font-weight:600}.big .u{font-size:12px;color:var(--muted);margin-left:6px;font-family:"Segoe UI",system-ui,sans-serif}
.estado{font-size:12px;color:var(--muted);line-height:1.4;margin:6px 0;border-left:3px solid var(--water);padding-left:10px}
.bars{display:flex;align-items:flex-end;gap:3px;height:46px;margin:8px 0 2px}
.bar{flex:1;background:var(--card);border-radius:2px 2px 0 0}.bar.on{background:var(--accent)}.bar.done{background:#6b5a2b}
.bars-lbl{display:flex;justify-content:space-between;font-size:10px;color:var(--muted)}
.ctl{display:flex;gap:8px;align-items:center;margin:8px 0 4px}
button.play{background:var(--accent);color:#0e1b25;border:0;border-radius:4px;padding:6px 12px;font-weight:600;cursor:pointer}
input[type=range]{flex:1;accent-color:var(--accent)}
.layers{display:flex;flex-wrap:wrap;gap:8px 12px;font-size:11.5px;color:var(--muted);margin:6px 0}
.layers label{cursor:pointer}
.legend{font-size:11.5px;color:var(--muted);margin-top:6px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 4px 0 2px;vertical-align:middle}
.note{color:var(--muted);font-size:11px;line-height:1.45;border-left:3px solid var(--accent);padding-left:10px;margin-top:8px}
.foot{font-size:11px;color:var(--muted);margin-top:8px;border-top:1px solid var(--rule);padding-top:8px}.foot a{color:var(--accent);text-decoration:none}
#end{position:absolute;inset:0;display:none;align-items:center;justify-content:center;background:rgba(14,27,37,.86);z-index:2000}
#end .box{background:var(--bg);border:1px solid var(--rule);border-radius:8px;padding:26px 30px;max-width:640px;width:90%}
#end h2{margin:0 0 8px;font-size:22px}#end p{color:var(--muted);font-size:14px;line-height:1.5}
#end table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}#end td,#end th{padding:5px 6px;border-bottom:1px dashed var(--rule);text-align:right}#end td:first-child,#end th:first-child{text-align:left}
#end .v{font-family:Consolas,monospace}
.cmp{width:100%;border-collapse:collapse;font-size:12px;margin:6px 0}.cmp td,.cmp th{padding:4px 5px;border-bottom:1px dashed var(--rule);text-align:right}.cmp td:first-child,.cmp th:first-child{text-align:left}.cmp th{color:var(--muted);font-weight:500}.cmp .v{font-family:Consolas,monospace}
@media (max-width:760px){#panel{left:8px;right:8px;top:auto;bottom:8px;width:auto;max-height:60%}}
</style></head><body>
<div id="map"></div>
<div id="panel">
  <div class="eyebrow">arena-lab · la logística de la arena</div>
  <h1>De Ibicuy a Añelo, año a año</h1>
  <div class="sub">Elegí por dónde viaja la arena. Los camiones, barcazas y trenes aparecen en proporción a lo que se bombea cada año.</div>
  <div class="year"><span id="year">2012</span></div>
  <div class="ctx" id="ctx"></div>
  <div class="chains" id="chains"></div>
  <div class="estado" id="estado"></div>
  <div class="row"><span class="l">arena nacional bombeada</span><span class="v" id="nat"></span></div>
  <div id="single">
  <div class="row"><span class="l">unidades en circulación</span><span class="v" id="units"></span></div>
  <div class="row"><span class="l">kilómetros en camión por tonelada</span><span class="v" id="kmcam"></span></div>
  <div class="big"><div class="l">costo de transporte del año, hasta el pozo</div><div class="v" id="costo"></div></div>
  <div class="row"><span class="l">contra el camión directo</span><span class="v" id="ahorro"></span></div>
  <div class="row"><span class="l">pasadas de camión por día en rutas nacionales</span><span class="v" id="pasadas"></span></div>
  <div class="row"><span class="l">tramos donde la arena supera todo el tránsito de 2017</span><span class="v" id="superados"></span></div>
  <div class="row"><span class="l">emisiones del año</span><span class="v" id="co2"></span></div>
  <div class="row"><span class="l">acumulado 2012 a hoy, esta cadena</span><span class="v" id="acum"></span></div>
  </div>
  <table id="cmp" class="cmp" style="display:none"></table>
  <div class="bars" id="bars"></div><div class="bars-lbl"><span id="y0"></span><span>arena nacional por año</span><span id="y1"></span></div>
  <div class="ctl"><button class="play" id="play">Pausa</button><input type="range" id="slider" min="0" max="0" value="0"></div>
  <div class="layers">
    <label><input type="checkbox" id="lyBlancos" checked> blancos de arena</label>
    <label><input type="checkbox" id="lyTren" checked> ferrocarril</label>
    <label><input type="checkbox" id="lyRios" checked> ríos</label>
    <label><input type="checkbox" id="lyPuertos" checked> puertos</label>
    <label><input type="checkbox" id="lyTramos" checked> presión sobre la ruta</label>
  </div>
  <div class="legend" id="legend"></div>
  <div class="note" id="note"></div>
  <div class="foot">Datos: Secretaría de Energía (Adjunto IV), SEGEMAR, IDE Transporte, IGN, OSRM sobre OpenStreetMap; costos de prensa 2026 y emisiones EU-27 2018 (CE Delft para la EEA). Código y método: <a href="https://github.com/dpinero14/arena-lab">github.com/dpinero14/arena-lab</a></div>
</div>
<div id="end"><div class="box"><h2 id="endTitle"></h2><p id="endText"></p><table id="endTable"></table><p><button class="play" id="again">Ver de nuevo</button></p></div></div>
<script>
const D = __DATA__;
const S = D.supuestos, Y = D.years, U = D.unidades, C = D.chains;
const fmt = (x, d=0) => x == null || !isFinite(x) ? "–" : x.toLocaleString("es-AR", {maximumFractionDigits: d, minimumFractionDigits: d});
// costo por tonelada de una cadena a un volumen: fijo si tiene tarifa; si tiene capex, la inversión se reparte en lo que se mueve ese año
const usdT = (c, tons) => c.capex_musd == null ? c.usd_t : (tons > 0 ? c.usd_t_variable + c.capex_musd * 1e6 / (c.vida_anios * tons) : Infinity);
const Q = new URLSearchParams(location.search);   // ?ys=segundos por año, ?chain=índice (-1 todas), ?video=1 esconde los controles
const map = L.map("map", {zoomControl: !Q.has("video")}).setView([-37.2, -64.0], 6);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom: 18, attribution: "&copy; OpenStreetMap"}).addTo(map);
// tramos de ruta nacional con su tránsito de 2017: se pintan cada año según cuánto pesan los camiones de arena
const lyTramos = L.geoJSON(D.layers.tramos, {style: {color: "#4caf50", weight: 16, opacity: .55, lineCap: "butt"}, onEachFeature: (f, l) => l.bindTooltip("", {sticky: true})}).addTo(map);
function pasadasEn(corredor, ci, y){
  // pasadas de camión de larga distancia por día sobre ese corredor: ida cargada y vuelta vacía; con "todas" se muestra la de hoy, el camión directo
  const per = 2 * (y.nat_t / U.camion.t) / S.dias_operativos; const c = C[ci < 0 ? 0 : ci]; let n = 0;
  c.paths.forEach(p => { if (p.modo === "camion" && p.corredor === corredor) n += per; });
  return n;
}
const colorPct = pct => pct >= 100 ? "#d7301f" : pct >= 50 ? "#fc8d59" : pct >= 20 ? "#fee08b" : "#4caf50";
function paintTramos(ci, y){
  let sup = 0, kmSup = 0, n = 0, pasadas = 0;
  lyTramos.eachLayer(l => { const f = l.feature.properties; const p = pasadasEn(f.corredor, ci, y); const pct = 100 * p / f.tmda17;
    l.setStyle({color: colorPct(pct)});
    l.setTooltipContent(`${f.ruta}, ${fmt(f.km)} km: ${fmt(f.tmda17)} vehículos por día en 2017; ${fmt(p)} pasadas de camiones de arena por día en ${y.anio} (${fmt(pct)} % del tránsito de 2017)`);
    if (f.corredor === "Ibicuy") { n++; if (pct >= 100) { sup++; kmSup += f.km; } }
    pasadas = Math.max(pasadas, p); });
  return {sup, kmSup, n, pasadas};
}
// capas de contexto
const lyBlancos = L.geoJSON(D.layers.blancos, {style: f => ({color: "#c98a1a", weight: .4, fillColor: "#f2b134", fillOpacity: .18 + .4 * Math.min(1, (f.properties.score || 0) / 100)}), onEachFeature: (f, l) => l.bindTooltip(`${f.properties.nombre}: puntaje ${f.properties.score}`)}).addTo(map);
const lyTren = L.geoJSON(D.layers.ferrocarril, {style: f => ({color: f.properties.estado === "Activo" ? "#2e8b57" : "#9aa5ad", weight: f.properties.estado === "Activo" ? 1.6 : 1, dashArray: f.properties.estado === "Activo" ? null : "4 4", opacity: .8}), onEachFeature: (f, l) => l.bindTooltip(`Ferrocarril ${f.properties.linea}, ${f.properties.operador}: ${f.properties.estado}`)}).addTo(map);
const lyRios = L.geoJSON(D.layers.rios, {style: {color: "#3b8ed0", weight: 1.4, opacity: .7}, interactive: false}).addTo(map);
const lyPuertos = L.layerGroup(D.layers.puertos.map(p => L.circleMarker([p.lat, p.lon], {radius: 6, color: "#111", weight: 1.5, fillColor: "#3b8ed0", fillOpacity: 1}).bindTooltip(`Puerto ${p.nombre}`))).addTo(map);
[["lyBlancos", lyBlancos], ["lyTren", lyTren], ["lyRios", lyRios], ["lyPuertos", lyPuertos], ["lyTramos", lyTramos]].forEach(([id, ly]) => document.getElementById(id).onchange = e => e.target.checked ? ly.addTo(map) : map.removeLayer(ly));
if (Q.has("video")) { ["ctl", "layers", "foot"].forEach(cls => document.querySelector("." + cls).style.display = "none"); }
D.waypoints.forEach(w => L.circleMarker([w.lat, w.lon], {radius: 4, color: "#111", weight: 1.2, fillColor: "#fff", fillOpacity: 1}).bindTooltip(`${w.lugar}: ${w.nota}`).addTo(map));
// trazas por cadena
const routeLayers = L.layerGroup().addTo(map);
function drawOne(k, thin){
  C[k].paths.forEach(p => {
    const ll = p.coords.map(c => [c[0], c[1]]);
    const col = U[p.modo].color;
    L.polyline(ll, {color: "#111", weight: thin ? 3.5 : 5, opacity: .9}).addTo(routeLayers);
    L.polyline(ll, {color: col, weight: thin ? 1.8 : 2.5, opacity: 1, dashArray: p.modo === "tren" ? "8 6" : (p.modo === "pulpa" ? "2 7" : null)}).bindTooltip(p.modo === "pulpa" ? C[k].nombre + ": traza hipotética por el corredor de la RN 5 y del gasoducto Perito Moreno" : C[k].nombre).addTo(routeLayers);
  });
  if (C[k].nombre.includes("Tren")) {
    const tn = D.tren_nuevo_desde; L.circleMarker([tn[1], tn[0]], {radius: 6, color: "#c0504d", weight: 2, fillColor: "#fff", fillOpacity: 1}).bindTooltip("Contraalmirante Cordero: desde acá faltan 83 km de vía nueva hasta Añelo").addTo(routeLayers);
  }
}
function drawChain(ci){
  routeLayers.clearLayers();
  if (ci < 0) { C.forEach((c, k) => drawOne(k, true)); } else { drawOne(ci, false); }
}
function at(path, s){ const R = path.coords; let lo = 0, hi = R.length - 1; while (hi - lo > 1){ const m = (lo + hi) >> 1; (R[m][2] <= s) ? lo = m : hi = m; }
  const a = R[lo], b = R[hi], f = (s - a[2]) / Math.max(1e-9, b[2] - a[2]); return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f]; }
// unidades animadas
let units = [];
function clearUnits(){ units.forEach(u => map.removeLayer(u.m)); units = []; }
function unitsForChain(c, y){
  // por tramo: unidades en circulación = viajes/día × días de ciclo (ida y vuelta), un punto cada `por_punto`
  const out = []; let total = 0;
  C[c].paths.forEach((p, pi) => {
    const u = U[p.modo]; const viajes = y.nat_t / u.t; const vdia = viajes / S.dias_operativos;
    const ciclo = Math.max(1, 2 * p.km / u.km_dia + 1); const enRuta = vdia * ciclo; total += enRuta;
    let n = Math.round(enRuta / u.por_punto); if (y.nat_t > 0 && n < 1) n = 1;
    for (let k = 0; k < n; k++) out.push({c, pi, s: Math.random(), dir: (p.modo === "camion" && k % 2) ? -1 : 1, modo: p.modo});
  });
  return {list: out, total};
}
function unitsFor(ci, y){
  if (ci >= 0) return unitsForChain(ci, y);
  const all = {list: [], total: 0};
  C.forEach((_, k) => { const r = unitsForChain(k, y); all.list.push(...r.list); all.total += r.total; });
  return all;
}
function setUnits(ci, y){
  const want = unitsFor(ci, y);
  clearUnits();
  want.list.forEach(w => { const col = w.dir < 0 ? "#9aa5ad" : U[w.modo].color; const r = w.modo === "camion" ? 4 : 6;
    const m = L.circleMarker([0, 0], {radius: r, color: "#111", weight: .8, fillColor: col, fillOpacity: .95, interactive: false}).addTo(map); units.push({...w, m}); });
  return want.total;
}
// panel
const natMax = Math.max(...Y.map(y => y.nat_t)); const bars = document.getElementById("bars");
Y.forEach(y => { const b = document.createElement("div"); b.className = "bar"; b.style.height = Math.max(2, 46 * y.nat_t / natMax) + "px"; b.title = `${y.anio}: ${fmt(y.nat_t / 1e3)} kt`; bars.appendChild(b); });
document.getElementById("y0").textContent = Y[0].anio; document.getElementById("y1").textContent = Y[Y.length - 1].anio;
const chainsDiv = document.getElementById("chains");
function pick(i){ ci = i; [...chainsDiv.children].forEach((x, k) => x.classList.toggle("on", (i < 0) ? (k === C.length) : (k === i))); drawChain(i); show(idx, true); }
C.forEach((c, i) => { const b = document.createElement("button"); b.textContent = c.nombre; b.onclick = () => pick(i); chainsDiv.appendChild(b); });
{ const b = document.createElement("button"); b.textContent = "todas a la vez"; b.onclick = () => pick(-1); chainsDiv.appendChild(b); }
document.getElementById("legend").innerHTML = Object.values(U).filter((u, i, a) => a.findIndex(x => x.nombre === u.nombre) === i).map(u => `<span class="dot" style="background:${u.color}"></span>${u.nombre}${u.por_punto > 1 ? ", un punto = " + u.por_punto : ""}`).join(" · ") + ` · <span class="dot" style="background:#9aa5ad"></span>vuelve vacío`
  + `<br>Presión sobre la ruta, pasadas de arena contra todo el tránsito de 2017 del tramo: <span class="dot" style="background:#4caf50"></span>menos del 20 % · <span class="dot" style="background:#fee08b"></span>20 a 50 · <span class="dot" style="background:#fc8d59"></span>50 a 100 · <span class="dot" style="background:#d7301f"></span>la arena sola supera el tránsito de 2017`;
document.getElementById("note").innerHTML = `Supuestos: ${fmt(S.t_por_camion)} t por camión, 2.400 t por barcaza, 2.000 t por tren, ${S.dias_operativos} días operativos. Costos por tonelada hasta el pozo: camión 97 (flete 70 y última milla 27, Infobae 8/2026); barcaza y camión 62,7; barcaza, tren y camión 35,2 (El Cronista 9/2026); hidrovía 48 (GlobalPorts 7/2026); arena cercana 30, calidad por confirmar. Arenoducto: no existe; 1.100 km por el corredor de la RN 5 y del gasoducto, 2.000 MUSD de capex (el costo por km de OCP en Marruecos) a 20 años sin interés más 0,02 USD/tkm, media tonelada de agua por tonelada de arena; con el capex por km del gasoducto Perito Moreno serían 4.400 MUSD. Emisiones pozo a rueda: camión 137, tren 24, río 33, mar 6,6 gCO₂e/tkm (EU-27 2018); la pulpa toma el factor del tren como cota. Toda la arena nacional se supone por la cadena elegida.`;
const slider = document.getElementById("slider"); slider.max = Y.length - 1;
let idx = 0, ci = Math.max(-1, Math.min(C.length - 1, parseInt(Q.get("chain") || "0"))), playing = true, last = performance.now(), yearClock = 0, ended = false;
const YEAR_SECONDS = Math.max(0.5, parseFloat(Q.get("ys") || "4"));
const acum = C.map(() => 0);
function acumHasta(cIdx, i){ let a = 0; for (let k = 0; k <= i; k++) a += Y[k].nat_t > 0 ? Y[k].nat_t * usdT(C[cIdx], Y[k].nat_t) / 1e6 : 0; return a; }
function show(i, keep){
  idx = i; const y = Y[i]; slider.value = i;
  document.getElementById("year").textContent = y.anio + (D.partial === y.anio ? " ·" : "");
  document.getElementById("ctx").textContent = D.contexto[String(y.anio)] || "";
  document.getElementById("nat").textContent = fmt(y.nat_t / 1e3) + " kt";
  const total = setUnits(ci, y);
  const pr = paintTramos(ci, y);
  const cmp = document.getElementById("cmp"), single = document.getElementById("single");
  if (ci < 0) {
    document.getElementById("estado").innerHTML = `<b>Las ${C.length === 6 ? "seis" : C.length} cadenas a la vez</b>, cada una con sus unidades. La tabla compara el mismo año por cada camino; la ruta se pinta con la presión del camión directo, la de hoy. El arenoducto reparte su capex en lo bombeado cada año: en los años de poca arena sale carísimo.`;
    single.style.display = "none"; cmp.style.display = "block";
    let h = "<tr><th>cadena</th><th>MUSD</th><th>unidades</th><th>pasadas/día</th><th>kt CO₂e</th></tr>";
    C.forEach((c, k) => { const r = unitsForChain(k, y); const largo = c.paths.some(p => p.modo === "camion" && p.corredor); const pas = largo ? 2 * (y.nat_t / U.camion.t) / S.dias_operativos : 0;
      h += `<tr><td>${c.nombre}</td><td class="v">${fmt(y.nat_t * usdT(c, y.nat_t) / 1e6, 1)}</td><td class="v">${fmt(r.total)}</td><td class="v">${fmt(pas)}</td><td class="v">${fmt(y.nat_t * c.kg_co2e_t / 1e6, 1)}</td></tr>`; });
    cmp.innerHTML = h;
  } else {
    const c = C[ci];
    single.style.display = "block"; cmp.style.display = "none";
    document.getElementById("estado").innerHTML = `<b>${c.estado}</b>. ${c.limite}`;
    document.getElementById("units").textContent = fmt(total);
    document.getElementById("pasadas").textContent = fmt(pr.pasadas);
    document.getElementById("superados").textContent = pr.n ? `${fmt(pr.sup)} de ${fmt(pr.n)}, ${fmt(pr.kmSup)} km` : "–";
    document.getElementById("kmcam").textContent = fmt(c.km_camion) + " de " + fmt(c.km_total) + " km";
    const ut = usdT(c, y.nat_t), costo = y.nat_t * ut / 1e6, base = y.nat_t * C[0].usd_t / 1e6;
    document.getElementById("costo").innerHTML = fmt(costo, 1) + '<span class="u">millones de USD' + (c.capex_musd != null ? `, ${fmt(ut)} USD/t con el capex repartido en lo bombeado este año` : "") + '</span>';
    document.getElementById("ahorro").textContent = (ci === 0) ? "es la referencia" : ((base - costo >= 0 ? "ahorra " : "cuesta de más ") + fmt(Math.abs(base - costo), 1) + " MUSD");
    document.getElementById("co2").textContent = fmt(y.nat_t * c.kg_co2e_t / 1e6, 1) + " kt CO₂e";
    document.getElementById("acum").textContent = fmt(acumHasta(ci, i)) + " MUSD";
  }
  [...bars.children].forEach((b, k) => { b.className = "bar" + (k === i ? " on" : (k < i ? " done" : "")); });
  if (!keep) yearClock = 0;
}
function finish(){
  ended = true; playing = false; document.getElementById("play").textContent = "Reproducir";
  const lastI = Y.length - 1;
  document.getElementById("endTitle").textContent = `${Y[0].anio} a ${Y[lastI].anio}: qué habría costado cada camino`;
  const totT = Y.reduce((a, y) => a + y.nat_t, 0);
  document.getElementById("endText").textContent = `${fmt(totT / 1e6, 1)} millones de toneladas de arena nacional en total. Con los costos de 2026 aplicados a todos los años, el mismo volumen por cada cadena habría costado:`;
  let h = "<tr><th>cadena</th><th>MUSD</th><th>km en camión</th><th>kt CO₂e</th></tr>";
  C.forEach((c, k) => { h += `<tr><td>${c.nombre}</td><td class="v">${fmt(acumHasta(k, lastI))}</td><td class="v">${fmt(c.km_camion)}</td><td class="v">${fmt(totT * c.kg_co2e_t / 1e6)}</td></tr>`; });
  document.getElementById("endTable").innerHTML = h;
  document.getElementById("end").style.display = "flex";
}
function frame(now){
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (playing && !ended){ yearClock += dt; if (yearClock >= YEAR_SECONDS){ yearClock = 0; if (idx + 1 < Y.length) show(idx + 1); else finish(); } }
  units.forEach(u => { const p = C[u.c].paths[u.pi]; const secs = 3 + 8 * p.km / 1500; u.s += u.dir * dt / secs; if (u.s > 1) u.s -= 1; if (u.s < 0) u.s += 1; u.m.setLatLng(at(p, u.s)); });
  requestAnimationFrame(frame);
}
document.getElementById("play").onclick = e => { if (ended) return; playing = !playing; e.target.textContent = playing ? "Pausa" : "Reproducir"; };
document.getElementById("again").onclick = () => { document.getElementById("end").style.display = "none"; ended = false; playing = true; document.getElementById("play").textContent = "Pausa"; show(0); };
slider.oninput = e => { playing = false; ended = false; document.getElementById("end").style.display = "none"; document.getElementById("play").textContent = "Reproducir"; show(+e.target.value); };
pick(ci); requestAnimationFrame(frame);
</script></body></html>
"""

__all__ = ["CONTEXTO", "UNIDADES", "chain_paths", "logistics_animation_html"]
