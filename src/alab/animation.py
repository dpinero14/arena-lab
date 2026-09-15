"""La ruta de la arena animada: camiones que aparecen año a año y dólares que corren por kilómetro.

Genera una página HTML autónoma (Leaflet desde CDN, datos embebidos) donde el
tiempo avanza de 2012 a hoy. Cada año, la cantidad de camiones que circulan
sobre la traza sale de las toneladas de arena nacional bombeadas ese año; el
flete, de un precio por tonelada declarado. Los supuestos están en `SUPUESTOS`
y se muestran en la página.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from . import CRS_GEO, CRS_METRIC

SUPUESTOS = {
    "t_por_camion": 30.0,        # toneladas de arena por viaje; los camiones pesan 53-55 t brutas
    "dias_operativos": 300,      # días de operación por año
    "dias_ciclo": 6.0,           # ida, descarga y vuelta: 70-75 h por tramo según la prensa
    "usd_flete_por_t": 70.0,     # flete de larga distancia por tonelada, a precios de 2026 (Infobae, 15/8/2026)
    "camiones_por_punto": 25,    # un punto en el mapa representa 25 camiones en circulación
}


def yearly_series(frac: pd.DataFrame, route_km: float, basin: str = "NEUQUINA", first_year: int = 2012, s: dict = SUPUESTOS) -> pd.DataFrame:
    """Por año: arena nacional e importada, viajes, camiones en circulación y flete."""
    f = frac[(frac["basin"].str.upper() == basin) & (frac["reservoir_type"].str.upper() == "NO CONVENCIONAL") & (frac["frac_start"].dt.year >= first_year)]
    g = f.groupby(f["frac_start"].dt.year).agg(nat_t=("sand_domestic_t", "sum"), imp_t=("sand_imported_t", "sum"), pozos=("well_id", "nunique"))
    g.index.name = "anio"
    g["viajes"] = (g["nat_t"] / s["t_por_camion"]).round()
    g["viajes_dia"] = (g["viajes"] / s["dias_operativos"]).round(1)
    g["camiones"] = (g["viajes_dia"] * s["dias_ciclo"]).round()
    g["flete_musd"] = (g["nat_t"] * s["usd_flete_por_t"] / 1e6).round(1)
    g["usd_km_anio"] = (g["nat_t"] * s["usd_flete_por_t"] / route_km).round()
    g["flete_acum_musd"] = g["flete_musd"].cumsum().round(1)
    g["usd_por_viaje"] = round(s["t_por_camion"] * s["usd_flete_por_t"])
    g["usd_por_km_viaje"] = round(s["t_por_camion"] * s["usd_flete_por_t"] / route_km, 2)
    return g.reset_index()


def route_vertices(route: gpd.GeoDataFrame, tol_deg: float = 0.002) -> list[list[float]]:
    """Vértices [lat, lon, s] con s = fracción de la longitud recorrida, para interpolar posiciones."""
    line = route.to_crs(CRS_GEO).geometry.iloc[0].simplify(tol_deg, preserve_topology=True)
    m = gpd.GeoSeries([line], crs=CRS_GEO).to_crs(CRS_METRIC).iloc[0]
    xy = np.asarray(line.coords)
    mxy = np.asarray(m.coords)
    seg = np.hypot(np.diff(mxy[:, 0]), np.diff(mxy[:, 1]))
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    s = cum / cum[-1]
    return [[round(float(y), 4), round(float(x), 4), round(float(v), 5)] for (x, y), v in zip(xy, s)]


def route_animation_html(route: gpd.GeoDataFrame, waypoints: gpd.GeoDataFrame, yearly: pd.DataFrame, path: str | Path, partial_year: int | None = None, s: dict = SUPUESTOS) -> Path:
    """Escribe la página animada. `partial_year` marca el año incompleto."""
    data = {
        "route": route_vertices(route),
        "km": float(route.iloc[0]["km"]),
        "waypoints": [{"lugar": r["lugar"], "lat": float(r["lat"]), "lon": float(r["lon"]), "nota": r["nota"]} for _, r in waypoints.iterrows()],
        "years": [{k: (None if pd.isna(v) else (int(v) if float(v).is_integer() else float(v))) for k, v in row.items()} for row in yearly.to_dict("records")],
        "partial": partial_year,
        "supuestos": s,
    }
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


TEMPLATE = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>La ruta de la arena, año a año</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--bg:#0e1b25;--ink:#e9eff3;--muted:#8ea2af;--accent:#f2b134;--rule:#22384a;--card:#132633}
html,body{margin:0;height:100%;font-family:"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink)}
#map{position:absolute;inset:0}
#panel{position:absolute;top:12px;right:12px;width:360px;max-height:calc(100% - 24px);overflow:auto;background:rgba(14,27,37,.94);border:1px solid var(--rule);border-radius:6px;padding:16px 18px;z-index:1000;box-sizing:border-box}
.eyebrow{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:600}
h1{margin:4px 0 2px;font-size:20px;font-weight:600}
.sub{color:var(--muted);font-size:12.5px;margin-bottom:10px}
.year{font-family:Consolas,monospace;font-size:54px;line-height:1;color:var(--accent);font-weight:700;margin:6px 0 2px}
.year small{font-size:13px;color:var(--muted);font-weight:400;margin-left:8px;font-family:"Segoe UI",system-ui,sans-serif}
.row{display:flex;justify-content:space-between;align-items:baseline;padding:5px 0;border-bottom:1px dashed var(--rule);font-size:13.5px}
.row .l{color:var(--muted)}.row .v{font-family:Consolas,monospace;font-size:15px}
.big{margin:8px 0 2px}.big .l{color:var(--muted);font-size:11px;letter-spacing:.1em;text-transform:uppercase}
.big .v{font-family:Consolas,monospace;font-size:30px;color:var(--accent);font-weight:600}.big .u{font-size:13px;color:var(--muted);margin-left:6px;font-family:"Segoe UI",system-ui,sans-serif}
.bars{display:flex;align-items:flex-end;gap:3px;height:56px;margin:10px 0 2px}
.bar{flex:1;background:var(--card);border-radius:2px 2px 0 0;position:relative}.bar.on{background:var(--accent)}.bar.done{background:#6b5a2b}
.bars-lbl{display:flex;justify-content:space-between;font-size:10px;color:var(--muted)}
.ctl{display:flex;gap:8px;align-items:center;margin:10px 0 4px}
button{background:var(--accent);color:#0e1b25;border:0;border-radius:4px;padding:6px 12px;font-weight:600;cursor:pointer}
input[type=range]{flex:1;accent-color:var(--accent)}
.note{color:var(--muted);font-size:11.5px;line-height:1.45;border-left:3px solid var(--accent);padding-left:10px;margin-top:10px}
.legend{font-size:11.5px;color:var(--muted);margin-top:8px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 4px 0 2px;vertical-align:middle}
.foot{font-size:11px;color:var(--muted);margin-top:10px;border-top:1px solid var(--rule);padding-top:8px}
.foot a{color:var(--accent);text-decoration:none}
@media (max-width:700px){#panel{left:8px;right:8px;top:auto;bottom:8px;width:auto;max-height:55%}}
</style></head><body>
<div id="map"></div>
<div id="panel">
  <div class="eyebrow">arena-lab · la ruta de la arena</div>
  <h1>De Ibicuy a Añelo, año a año</h1>
  <div class="sub">Cada punto ámbar son <span id="cpp"></span> camiones cargados en circulación; los grises vuelven vacíos. Un cruce de la ruta dura 8 segundos.</div>
  <div class="year"><span id="year">2012</span><small id="parcial"></small></div>
  <div class="row"><span class="l">arena nacional bombeada</span><span class="v" id="nat"></span></div>
  <div class="row"><span class="l">arena importada</span><span class="v" id="imp"></span></div>
  <div class="row"><span class="l">viajes de camión en el año</span><span class="v" id="viajes"></span></div>
  <div class="row"><span class="l">camiones cargados por día</span><span class="v" id="vdia"></span></div>
  <div class="row"><span class="l">camiones en circulación</span><span class="v" id="cam"></span></div>
  <div class="big"><div class="l">flete del año, a precios de 2026</div><div class="v" id="flete"></div></div>
  <div class="row"><span class="l">dólares por kilómetro de ruta, por año</span><span class="v" id="usdkm"></span></div>
  <div class="row"><span class="l">flete acumulado desde 2012</span><span class="v" id="acum"></span></div>
  <div class="bars" id="bars"></div><div class="bars-lbl"><span id="y0"></span><span>arena nacional por año</span><span id="y1"></span></div>
  <div class="ctl"><button id="play">Pausa</button><input type="range" id="slider" min="0" max="0" value="0"></div>
  <div class="legend"><span class="dot" style="background:#f2b134"></span>cargado, hacia Añelo <span class="dot" style="background:#9aa5ad"></span>vacío, de vuelta · ruta de <span id="km"></span> km</div>
  <div class="note" id="note"></div>
  <div class="foot">Datos: registro de fractura de la Secretaría de Energía (Adjunto IV, CC-BY 4.0); traza por OSRM sobre OpenStreetMap. Código y método: <a href="https://github.com/dpinero14/arena-lab">github.com/dpinero14/arena-lab</a></div>
</div>
<script>
const D = __DATA__;
const S = D.supuestos, Y = D.years, R = D.route;
const fmt = (x, d=0) => x == null ? "–" : x.toLocaleString("es-AR", {maximumFractionDigits: d, minimumFractionDigits: d});
document.getElementById("cpp").textContent = S.camiones_por_punto;
document.getElementById("km").textContent = fmt(D.km);
document.getElementById("note").innerHTML = `Supuestos: ${fmt(S.t_por_camion)} t por camión, ${S.dias_operativos} días operativos, ciclo de ${S.dias_ciclo} días por viaje, flete de ${fmt(S.usd_flete_por_t)} USD/t a precios de 2026 (Infobae, agosto 2026). Cada viaje cargado cuesta ${fmt(Y[0].usd_por_viaje)} USD de flete, ${fmt(Y[0].usd_por_km_viaje, 2)} USD por km. Se supone toda la arena nacional por la ruta de Entre Ríos: hasta 2020 una parte venía de Río Negro y Chubut, con viajes más cortos. La arena importada no viaja por esta ruta.`;
const map = L.map("map", {zoomControl: true}).setView([-36.6, -64.5], 6);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom: 18, attribution: "&copy; OpenStreetMap"}).addTo(map);
const latlngs = R.map(p => [p[0], p[1]]);
const base = L.polyline(latlngs, {color: "#111", weight: 4, opacity: .9}).addTo(map);
const glow = L.polyline(latlngs, {color: "#f2b134", weight: 2, opacity: 1}).addTo(map);
map.fitBounds(base.getBounds(), {paddingTopLeft: [20, 20], paddingBottomRight: [380, 20]});
D.waypoints.forEach(w => L.circleMarker([w.lat, w.lon], {radius: 5, color: "#111", weight: 1.5, fillColor: "#fff", fillOpacity: 1}).bindTooltip(`${w.lugar}: ${w.nota}`).addTo(map));
// posición sobre la traza para s en [0,1]
const svals = R.map(p => p[2]);
function at(s){ let lo = 0, hi = R.length - 1; while (hi - lo > 1){ const m = (lo + hi) >> 1; (svals[m] <= s) ? lo = m : hi = m; }
  const a = R[lo], b = R[hi], f = (s - a[2]) / Math.max(1e-9, b[2] - a[2]); return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f]; }
// camiones
const pool = []; let trucks = [];
function marker(color){ const m = L.circleMarker([0, 0], {radius: 4, color: "#111", weight: .8, fillColor: color, fillOpacity: .95, interactive: false}); m.addTo(map); return m; }
function setTrucks(n){
  const want = Math.max(0, Math.round(n / S.camiones_por_punto));
  while (trucks.length < want){ const loaded = trucks.length % 2 === 0; trucks.push({s: Math.random(), dir: loaded ? 1 : -1, m: marker(loaded ? "#f2b134" : "#9aa5ad")}); }
  while (trucks.length > want){ const t = trucks.pop(); map.removeLayer(t.m); }
}
// años
const natMax = Math.max(...Y.map(y => y.nat_t));
const bars = document.getElementById("bars");
Y.forEach((y, i) => { const b = document.createElement("div"); b.className = "bar"; b.style.height = Math.max(2, 56 * y.nat_t / natMax) + "px"; b.title = `${y.anio}: ${fmt(y.nat_t / 1e3)} kt`; bars.appendChild(b); });
document.getElementById("y0").textContent = Y[0].anio; document.getElementById("y1").textContent = Y[Y.length - 1].anio;
const slider = document.getElementById("slider"); slider.max = Y.length - 1;
let idx = 0, playing = true, last = performance.now(), yearClock = 0;
const YEAR_SECONDS = 4, CROSS_SECONDS = 8;
function show(i){
  idx = i; const y = Y[i]; slider.value = i;
  document.getElementById("year").textContent = y.anio;
  document.getElementById("parcial").textContent = (D.partial === y.anio) ? "año incompleto" : "";
  document.getElementById("nat").textContent = fmt(y.nat_t / 1e3) + " kt";
  document.getElementById("imp").textContent = fmt(y.imp_t / 1e3) + " kt";
  document.getElementById("viajes").textContent = fmt(y.viajes);
  document.getElementById("vdia").textContent = fmt(y.viajes_dia);
  document.getElementById("cam").textContent = fmt(y.camiones);
  document.getElementById("flete").innerHTML = fmt(y.flete_musd, 1) + '<span class="u">millones de USD</span>';
  document.getElementById("usdkm").textContent = fmt(y.usd_km_anio) + " USD/km";
  document.getElementById("acum").textContent = fmt(y.flete_acum_musd) + " MUSD";
  [...bars.children].forEach((b, k) => { b.className = "bar" + (k === i ? " on" : (k < i ? " done" : "")); });
  base.setStyle({weight: 3 + 9 * y.nat_t / natMax}); glow.setStyle({weight: 1 + 4 * y.nat_t / natMax});
  setTrucks(y.camiones);
}
function frame(now){
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (playing){ yearClock += dt; if (yearClock >= YEAR_SECONDS){ yearClock = 0; show((idx + 1) % Y.length); } }
  trucks.forEach(t => { t.s += t.dir * dt / CROSS_SECONDS; if (t.s > 1) t.s -= 1; if (t.s < 0) t.s += 1; t.m.setLatLng(at(t.s)); });
  requestAnimationFrame(frame);
}
document.getElementById("play").onclick = e => { playing = !playing; e.target.textContent = playing ? "Pausa" : "Reproducir"; };
slider.oninput = e => { playing = false; document.getElementById("play").textContent = "Reproducir"; yearClock = 0; show(+e.target.value); };
show(0); requestAnimationFrame(frame);
</script></body></html>
"""

__all__ = ["SUPUESTOS", "yearly_series", "route_vertices", "route_animation_html"]
