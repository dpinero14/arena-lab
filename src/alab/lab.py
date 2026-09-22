"""El laboratorio de la arena: una página con perillas para probar demanda, carga por camión y reparto por cadena.

Genera un HTML autónomo, sin mapa, que recalcula en el navegador con las
mismas reglas de `logistics.py` y `roads.py`: costo anual, ahorro contra el
camión, camiones en circulación, pasadas por día sobre cada corredor, autos
equivalentes en desgaste, emisiones y repago del tren. Abajo dibuja la ruta
tramo por tramo con el tránsito de 2017 de cada uno. Los datos van embebidos;
la lógica está en JavaScript porque tiene que correr al mover una perilla.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from .animation import SUPUESTOS
from .logistics import CHAINS, INVERSION_TREN_MUSD, Chain
from .roads import AUTOS_POR_PASADA

# Corredor de rutas nacionales que carga el tramo largo en camión de cada cadena; las demás no tocan la ruta larga.
CORREDOR = {"camión directo, hoy": "Ibicuy", "barcaza a Bahía Blanca y camión": "Bahía Blanca"}

# Cargas por camión que se pueden elegir: lo que se ve hoy y lo que permite la ley. Diario Neuquino 11/9/2026 (26 a 53 t, máximo 55 t brutas);
# Río Negro 30/7/2026 (bitrenes de 75 t). El Decreto 689/2026 (BO 31/7/2026) fija los bitrenes B2 y B3 en 75 t brutas con 500 kg de
# tolerancia; lo señaló Luis Alberto Troncoso en los comentarios del post del 17/9/2026.
CARGAS = [
    {"t": 30, "nombre": "30 t, lo que carga hoy un semirremolque según los choferes"},
    {"t": 40, "nombre": "40 t, un semirremolque al máximo legal de 55 t brutas"},
    {"t": 50, "nombre": "50 t, un bitrén de 75 t brutas"},
]


def chains_for_lab(chains: list[Chain] = CHAINS, min_km: float = 200.0) -> list[dict]:
    """Lo que el laboratorio necesita de cada cadena, en un dict plano."""
    out = []
    for c in chains:
        largo = sum(l.km for l in c.legs if l.modo == "camion" and l.km >= min_km)
        out.append({"nombre": c.nombre, "usd_t": round(c.usd_t_pozo, 1), "kg_co2e_t": round(c.kg_co2e_t(), 1), "km_camion": round(c.km_camion),
                    "km_camion_largo": round(largo), "corredor": CORREDOR.get(c.nombre), "capacidad_mt": c.capacidad_mt, "estado": c.estado, "limite": c.limite,
                    "capex_musd": c.capex_musd, "vida_anios": c.vida_anios, "usd_t_variable": round(c.usd_t_variable, 1), "agua_t_t": c.agua_t_t})
    return out


def sand_lab_html(tramos: gpd.GeoDataFrame, yearly: pd.DataFrame, path: str | Path, chains: list[Chain] = CHAINS, s: dict = SUPUESTOS, inversion_tren_musd: float = INVERSION_TREN_MUSD) -> Path:
    """Escribe la página del laboratorio. `tramos` son los de `roads.route_segments`, de uno o más corredores."""
    ultimo = yearly[yearly["nat_t"] == yearly["nat_t"].max()].iloc[0]
    data = {
        "chains": chains_for_lab(chains), "cargas": CARGAS, "supuestos": s, "inversion_tren_musd": inversion_tren_musd, "autos_por_pasada": AUTOS_POR_PASADA,
        "tramos": [{"ruta": r["ruta"], "corredor": r["corredor"], "km": float(r["km"]), "km_desde": float(r["km_desde"]), "tmda17": int(r["tmda17"])} for _, r in tramos.sort_values(["corredor", "km_desde"]).iterrows()],
        "medido": {"anio": int(ultimo["anio"]), "mt": round(float(ultimo["nat_t"]) / 1e6, 2)},
    }
    html = TEMPLATE_LAB.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


TEMPLATE_LAB = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laboratorio de la arena</title>
<style>
:root{--bg:#0e1b25;--ink:#e9eff3;--muted:#8ea2af;--accent:#f2b134;--rule:#22384a;--card:#132633;--ok:#4caf50;--warn:#fc8d59;--bad:#d7301f}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI",system-ui,sans-serif;font-size:14px;line-height:1.45}
.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 40px}
.eyebrow{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:600}
h1{margin:4px 0 4px;font-size:26px;font-weight:600;text-wrap:balance}
.sub{color:var(--muted);max-width:70ch;margin:0 0 18px}
.grid{display:grid;grid-template-columns:minmax(280px,380px) 1fr;gap:18px}
@media (max-width:820px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:14px 16px}
h2{margin:0 0 10px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.k{margin:10px 0 12px}
.k label{display:flex;justify-content:space-between;align-items:baseline;font-size:13px;margin-bottom:3px}
.k label .v{font-family:Consolas,monospace;color:var(--accent);font-size:14px}
.k input[type=range]{width:100%;accent-color:var(--accent);margin:0}
.presets{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.presets button,.radio label{background:var(--bg);color:var(--ink);border:1px solid var(--rule);border-radius:4px;padding:4px 8px;font-size:11.5px;cursor:pointer}
.presets button:hover{border-color:var(--accent)}
.radio{display:flex;flex-direction:column;gap:4px}
.radio label{display:flex;gap:8px;align-items:center}
.radio input{accent-color:var(--accent);margin:0}
.chk{display:flex;gap:8px;align-items:flex-start;font-size:12.5px;color:var(--muted);margin-top:10px}
.chk input{accent-color:var(--accent);margin-top:3px}
.share{font-size:11.5px;color:var(--muted);margin-top:2px}
.big{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:10px}
.big div{background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:10px 12px}
.big .l{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.big .v{font-family:Consolas,monospace;font-size:26px;color:var(--accent);font-weight:600;font-variant-numeric:tabular-nums}
.big .u{font-size:11.5px;color:var(--muted)}
.row{display:flex;justify-content:space-between;gap:12px;padding:5px 0;border-bottom:1px dashed var(--rule);font-size:13px}
.row .l{color:var(--muted)}.row .v{font-family:Consolas,monospace;font-size:14px;text-align:right;font-variant-numeric:tabular-nums}
.warn{color:var(--warn);font-size:12px;margin-top:8px;line-height:1.4}
.strip{display:flex;height:34px;margin:8px 0 2px;border-radius:3px;overflow:hidden;background:var(--bg)}
.strip div{height:100%;border-right:1px solid rgba(0,0,0,.35);transition:background .2s}
.strip div:hover{outline:2px solid #fff;outline-offset:-2px}
.lbl{display:flex;font-size:10.5px;color:var(--muted);margin-bottom:8px}
.lbl div{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;padding-right:4px}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:6px}
th,td{padding:5px 6px;border-bottom:1px dashed var(--rule);text-align:right;font-variant-numeric:tabular-nums}
th{color:var(--muted);font-weight:500}td:first-child,th:first-child{text-align:left}
td.v{font-family:Consolas,monospace}
.legend{font-size:11.5px;color:var(--muted);margin:6px 0}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 4px 0 2px;vertical-align:middle}
.note{color:var(--muted);font-size:11.5px;line-height:1.5;border-left:3px solid var(--accent);padding-left:10px;margin-top:14px}
.foot{font-size:11px;color:var(--muted);margin-top:16px;border-top:1px solid var(--rule);padding-top:10px}.foot a{color:var(--accent);text-decoration:none}
.corr{margin-top:14px}
.corr h3{margin:0 0 2px;font-size:13px;font-weight:600}
.corr .sub2{font-size:12px;color:var(--muted);margin:0}
</style></head><body><div class="wrap">
<div class="eyebrow">arena-lab · laboratorio</div>
<h1>La arena, la ruta y el pozo: mové las perillas</h1>
<p class="sub">Cuánta arena se bombea por año, cuánto carga cada camión y por dónde viaja. Abajo, cada tramo de ruta nacional con su tránsito de 2017 y las pasadas de camiones de arena que le tocan.</p>
<div class="grid">
<div class="card">
  <h2>Perillas</h2>
  <div class="k"><label><span>arena por año</span><span class="v" id="mtV"></span></label><input type="range" id="mt" min="1" max="15" step="0.5" value="5.5">
    <div class="presets" id="presets"></div></div>
  <div class="k"><label><span>carga por camión</span></label><div class="radio" id="cargas"></div></div>
  <div class="k"><label><span>reparto por cadena</span><span class="v" id="camV"></span></label><div class="share" id="camL"></div></div>
  <div id="shares"></div>
  <label class="chk"><input type="checkbox" id="cap" checked><span>respetar las capacidades conocidas: el tren 1,5 Mt el primer año, la arena cercana 0,24 Mt; lo que sobra vuelve al camión directo</span></label>
</div>
<div class="card">
  <h2>Resultados del año</h2>
  <div class="big">
    <div><div class="l">costo de transporte al pozo</div><div class="v" id="costo"></div><div class="u">millones de USD por año</div></div>
    <div><div class="l">contra todo en camión</div><div class="v" id="ahorro"></div><div class="u">millones de USD que se ahorran</div></div>
    <div><div class="l">pasadas por día, ruta de Entre Ríos</div><div class="v" id="pasIb"></div><div class="u">camiones cargados más vacíos</div></div>
  </div>
  <div class="row"><span class="l">camiones de larga distancia en circulación</span><span class="v" id="camiones"></span></div>
  <div class="row"><span class="l">pasadas por día en la RN 22, Bahía Blanca a Añelo</span><span class="v" id="pasBB"></span></div>
  <div class="row"><span class="l">desgaste equivalente por día, en autos</span><span class="v" id="autos"></span></div>
  <div class="row"><span class="l">tramos donde la arena supera todo el tránsito de 2017</span><span class="v" id="sup"></span></div>
  <div class="row"><span class="l">emisiones</span><span class="v" id="co2"></span></div>
  <div class="row"><span class="l">el tren paga sus 500 MUSD en</span><span class="v" id="repago"></span></div>
  <div class="row"><span class="l">el arenoducto paga sus 2.000 MUSD en</span><span class="v" id="repagoDucto"></span></div>
  <div class="warn" id="warn"></div>
</div>
</div>
<div class="card corr" id="corrIb"><h3>La ruta de Entre Ríos, tramo por tramo</h3><p class="sub2">Ibicuy a Añelo por RN 12, RN 5, RN 35, RN 152 y RN 151. El ancho es el largo del tramo; el color, cuánto pesan los camiones de arena contra todo el tránsito que tenía en 2017.</p>
  <div class="strip" id="stripIb"></div><div class="lbl" id="lblIb"></div><table id="tabIb"></table></div>
<div class="card corr" id="corrBB"><h3>La RN 22 de Bahía Blanca a Añelo, tramo por tramo</h3><p class="sub2">El tramo en camión de la cadena por barcaza. Cerca de Neuquén el tránsito de 2017 ya era alto; en el medio, no.</p>
  <div class="strip" id="stripBB"></div><div class="lbl" id="lblBB"></div><table id="tabBB"></table></div>
<div class="legend">Pasadas de arena contra el tránsito total de 2017 del tramo: <span class="dot" style="background:#4caf50"></span>menos del 20 % · <span class="dot" style="background:#fee08b"></span>20 a 50 · <span class="dot" style="background:#fc8d59"></span>50 a 100 · <span class="dot" style="background:#d7301f"></span>la arena sola supera el tránsito de 2017</div>
<div class="note" id="note"></div>
<div class="foot">Datos: Secretaría de Energía (registro de fractura), IDE Transporte (tránsito medio diario 2017 por tramo), OSRM sobre OpenStreetMap; costos por tonelada de prensa 2026, emisiones EU-27 2018 (CE Delft para la EEA), desgaste según la Guía AASHTO 1993. Código y método: <a href="https://github.com/dpinero14/arena-lab">github.com/dpinero14/arena-lab</a> · la ruta animada: <a href="ruta_animada.html">ruta_animada.html</a></div>
</div>
<script>
const D = __DATA__; const S = D.supuestos, C = D.chains;
const fmt = (x, d=0) => x == null || !isFinite(x) ? "–" : x.toLocaleString("es-AR", {maximumFractionDigits: d, minimumFractionDigits: d});
const colorPct = pct => pct >= 100 ? "#d7301f" : pct >= 50 ? "#fc8d59" : pct >= 20 ? "#fee08b" : "#4caf50";
const iCam = C.findIndex(c => c.corredor === "Ibicuy"), iBB = C.findIndex(c => c.corredor === "Bahía Blanca"), iTren = C.findIndex(c => c.nombre.includes("Tren")), iDucto = C.findIndex(c => c.nombre.includes("arenoducto"));
// costo por tonelada a un volumen: fijo si hay tarifa; con capex, la inversión se reparte en lo que se mueve
const usdT = (c, tons) => c.capex_musd == null ? c.usd_t : (tons > 0 ? c.usd_t_variable + c.capex_musd * 1e6 / (c.vida_anios * tons) : Infinity);
// perillas
const mt = document.getElementById("mt");
const presets = [[D.medido.mt, `${D.medido.anio}: ${fmt(D.medido.mt, 1)} Mt, registro de fractura`], [7, "2026: 7 Mt, proyección"], [8, "2027: 8 Mt, proyección"], [15, "15 Mt, el techo que se menciona"]];
presets.forEach(([v, t]) => { const b = document.createElement("button"); b.textContent = t; b.onclick = () => { mt.value = v; calc(); }; document.getElementById("presets").appendChild(b); });
const cargas = document.getElementById("cargas");
D.cargas.forEach((c, i) => { const l = document.createElement("label"); l.innerHTML = `<input type="radio" name="carga" value="${c.t}" ${i === 0 ? "checked" : ""}> ${c.nombre}`; cargas.appendChild(l); });
const shares = document.getElementById("shares"); const sliders = [];
C.forEach((c, i) => { if (i === iCam) return; const d = document.createElement("div"); d.className = "k";
  d.innerHTML = `<label><span>${c.nombre}</span><span class="v" id="sh${i}"></span></label><input type="range" min="0" max="100" step="5" value="0" data-i="${i}"><div class="share" id="shl${i}">${c.usd_t} USD/t al pozo · ${c.km_camion} km en camión · ${c.kg_co2e_t} kg CO₂e/t</div>`;
  shares.appendChild(d); sliders.push(d.querySelector("input")); });
function pct(){ // reparto en fracciones; el que se mueve se recorta si el total pasa de 100
  let tot = 0; sliders.forEach(s => tot += +s.value);
  if (tot > 100 && lastMoved) { lastMoved.value = Math.max(0, +lastMoved.value - (tot - 100)); tot = 0; sliders.forEach(s => tot += +s.value); }
  const f = C.map(() => 0); sliders.forEach(s => f[+s.dataset.i] = +s.value / 100); f[iCam] = Math.max(0, 1 - tot / 100); return f;
}
let lastMoved = null;
document.querySelectorAll("input").forEach(el => el.addEventListener("input", e => { if (e.target.type === "range" && e.target.id !== "mt") lastMoved = e.target; calc(); }));
// tramos
function buildStrip(corredor, stripId, lblId){
  const rows = D.tramos.filter(t => t.corredor === corredor); const tot = rows.reduce((a, t) => a + t.km, 0);
  const strip = document.getElementById(stripId), lbl = document.getElementById(lblId); strip.innerHTML = ""; lbl.innerHTML = "";
  rows.forEach(t => { const d = document.createElement("div"); d.style.width = (100 * t.km / tot) + "%"; d.dataset.tmda = t.tmda17; d.dataset.ruta = t.ruta; d.dataset.km = t.km; strip.appendChild(d); });
  let cur = null, acc = 0; rows.forEach(t => { if (t.ruta !== cur) { if (cur) { const d = document.createElement("div"); d.style.width = (100 * acc / tot) + "%"; d.textContent = cur; lbl.appendChild(d); } cur = t.ruta; acc = 0; } acc += t.km; });
  const d = document.createElement("div"); d.style.width = (100 * acc / tot) + "%"; d.textContent = cur; lbl.appendChild(d);
  return rows;
}
const rowsIb = buildStrip("Ibicuy", "stripIb", "lblIb"), rowsBB = buildStrip("Bahía Blanca", "stripBB", "lblBB");
function paint(rows, stripId, tabId, pasadas){
  const strip = document.getElementById(stripId); let sup = 0, kmSup = 0;
  [...strip.children].forEach(d => { const p = 100 * pasadas / +d.dataset.tmda; d.style.background = colorPct(p); d.title = `${d.dataset.ruta}, ${fmt(+d.dataset.km)} km: ${fmt(+d.dataset.tmda)} vehículos por día en 2017; ${fmt(pasadas)} pasadas de arena por día (${fmt(p)} %)`; if (p >= 100) { sup++; kmSup += +d.dataset.km; } });
  const by = {}; rows.forEach(t => { const b = by[t.ruta] = by[t.ruta] || {km: 0, min: 1e9, max: 0}; b.km += t.km; b.min = Math.min(b.min, t.tmda17); b.max = Math.max(b.max, t.tmda17); });
  let h = "<tr><th>ruta</th><th>km</th><th>tránsito 2017, veh/día</th><th>pasadas de arena/día</th><th>% del tránsito 2017</th></tr>";
  const rng = (a, b) => a === b ? fmt(a) : `${fmt(a)} a ${fmt(b)}`;
  Object.entries(by).forEach(([r, b]) => { h += `<tr><td>${r}</td><td class="v">${fmt(b.km)}</td><td class="v">${rng(b.min, b.max)}</td><td class="v">${fmt(pasadas)}</td><td class="v">${rng(Math.round(100 * pasadas / b.max), Math.round(100 * pasadas / b.min))}</td></tr>`; });
  document.getElementById(tabId).innerHTML = h;
  return {sup, kmSup, n: strip.children.length};
}
function calc(){
  const t = +mt.value * 1e6, tcam = +document.querySelector("input[name=carga]:checked").value, cap = document.getElementById("cap").checked;
  const f = pct(); const tons = f.map(x => x * t); const warn = [];
  if (cap) C.forEach((c, i) => { if (c.capacidad_mt && tons[i] > c.capacidad_mt * 1e6) { const ex = tons[i] - c.capacidad_mt * 1e6; tons[i] = c.capacidad_mt * 1e6; tons[iCam] += ex; warn.push(`${c.nombre}: la capacidad conocida es ${fmt(c.capacidad_mt, 2)} Mt; ${fmt(ex / 1e6, 2)} Mt vuelven al camión directo.`); } });
  document.getElementById("mtV").textContent = fmt(+mt.value, 1) + " Mt";
  document.getElementById("camV").textContent = fmt(100 * tons[iCam] / t) + " % camión directo";
  document.getElementById("camL").textContent = `${C[iCam].usd_t} USD/t al pozo · ${C[iCam].km_camion} km en camión · ${C[iCam].kg_co2e_t} kg CO₂e/t. Lo que no va por otra cadena, va por acá.`;
  sliders.forEach(s => { const i = +s.dataset.i; document.getElementById("sh" + i).textContent = fmt(100 * tons[i] / t) + " %";
    if (C[i].capex_musd != null) document.getElementById("shl" + i).textContent = `${tons[i] > 0 ? fmt(usdT(C[i], tons[i])) : "–"} USD/t al pozo con ${fmt(tons[i] / 1e6, 1)} Mt (capex ${fmt(C[i].capex_musd)} MUSD a ${fmt(C[i].vida_anios)} años) · ${C[i].km_camion} km en camión · ${C[i].kg_co2e_t} kg CO₂e/t`; });
  const costo = tons.reduce((a, x, i) => a + (x > 0 ? x * usdT(C[i], x) : 0), 0) / 1e6, base = t * C[iCam].usd_t / 1e6;
  const co2 = tons.reduce((a, x, i) => a + x * C[i].kg_co2e_t, 0) / 1e6;
  if (iDucto >= 0 && tons[iDucto] > 0) warn.push(`arenoducto: ${fmt(tons[iDucto] * C[iDucto].agua_t_t / 1e6, 1)} hm³ de agua por año en la pulpa; con el capex por km del gasoducto (4.400 MUSD) costaría ${fmt(C[iDucto].usd_t_variable + 4400e6 / (C[iDucto].vida_anios * tons[iDucto]))} USD/t.`);
  const pasIb = 2 * tons[iCam] / tcam / S.dias_operativos, pasBB = iBB >= 0 ? 2 * tons[iBB] / tcam / S.dias_operativos : 0;
  const camiones = (pasIb / 2) * S.dias_ciclo + (pasBB / 2) * S.dias_ciclo * (iBB >= 0 ? C[iBB].km_camion_largo / C[iCam].km_camion_largo : 0);
  const ahorroTren = iTren >= 0 ? tons[iTren] * (C[iCam].usd_t - C[iTren].usd_t) / 1e6 : 0;
  const ahorroDucto = iDucto >= 0 && tons[iDucto] > 0 ? tons[iDucto] * (C[iCam].usd_t - usdT(C[iDucto], tons[iDucto])) / 1e6 : 0;
  document.getElementById("repagoDucto").textContent = iDucto < 0 || tons[iDucto] <= 0 ? "no va nada por el caño" : (ahorroDucto > 0 ? fmt(C[iDucto].capex_musd / ahorroDucto, 1) + " años" : "nunca: a este volumen cuesta más que el camión");
  document.getElementById("costo").textContent = fmt(costo); document.getElementById("ahorro").textContent = fmt(base - costo);
  document.getElementById("pasIb").textContent = fmt(pasIb); document.getElementById("pasBB").textContent = fmt(pasBB);
  document.getElementById("camiones").textContent = fmt(camiones);
  document.getElementById("autos").textContent = fmt((pasIb + pasBB) * D.autos_por_pasada / 1e6, 1) + " millones";
  document.getElementById("co2").textContent = fmt(co2) + " kt CO₂e";
  document.getElementById("repago").textContent = ahorroTren > 0 ? fmt(D.inversion_tren_musd / ahorroTren, 1) + " años" : "no va nada por tren";
  const a = paint(rowsIb, "stripIb", "tabIb", pasIb), b = paint(rowsBB, "stripBB", "tabBB", pasBB);
  document.getElementById("sup").textContent = `${fmt(a.sup)} de ${fmt(a.n)} en Entre Ríos, ${fmt(a.kmSup)} km · ${fmt(b.sup)} de ${fmt(b.n)} en la RN 22`;
  document.getElementById("warn").innerHTML = warn.join("<br>");
}
document.getElementById("note").innerHTML = `Reglas: el costo por tonelada de cada cadena no cambia con la carga del camión, porque no hay una fuente que lo mida; la carga solo cambia cuántos camiones y cuántas pasadas hacen falta. Pasadas = viajes cargados más vueltas vacías, con ${S.dias_operativos} días operativos y un ciclo de ${S.dias_ciclo} días para los camiones de larga distancia. El tránsito de 2017 es el último publicado por tramo e incluye a todos los vehículos; la comparación es contra ese total, no contra los camiones de entonces. Una pasada de un semirremolque de cinco ejes desgasta el pavimento como ${fmt(D.autos_por_pasada)} autos (ley de la cuarta potencia, AASHTO 1993). Los repagos del tren y del arenoducto usan solo el ahorro de las toneladas que van por cada uno contra el camión directo. El arenoducto no existe: 1.100 km por el corredor de la RN 5 y del gasoducto Perito Moreno, 2.000 MUSD de capex al costo por km del mineraloducto de OCP en Marruecos, amortizados a 20 años sin interés en lo que se bombea, más 0,02 USD/tkm de operación y media tonelada de agua por tonelada de arena; las emisiones de la pulpa toman el factor del tren como cota.`;
calc();
</script></body></html>
"""

__all__ = ["CORREDOR", "CARGAS", "chains_for_lab", "sand_lab_html"]
