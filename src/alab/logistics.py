"""Cadenas logísticas de la arena: cuánto cuesta cada tonelada por cada camino, y cuánto emite.

Cada cadena es una lista de tramos (modo, km) más un costo por tonelada hasta
el pozo. Donde la fuente da el costo de la cadena completa se usa ese número;
donde no, se deriva de los tramos con los costos unitarios de `MODES`. Las
emisiones salen de los factores europeos de 2018, pozo a rueda, que son los
únicos publicados con método comparable para los cuatro modos. Todo está a la
vista para discutirlo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# Factores de emisión pozo a rueda, EU-27 2018, gCO2e por tonelada-km.
# Fuente: CE Delft y Fraunhofer ISI para la Agencia Europea de Medio Ambiente,
# "Methodology for GHG Efficiency of Transport Modes" (2021), tablas 3.x, 5.x, 6.4 y 7.5.
EMISIONES_G_TKM = {"camion": 137.0, "tren": 24.0, "fluvial": 33.4, "maritimo": 6.6}

# Costos unitarios de referencia, USD por tonelada-km, derivados de cifras publicadas en 2026.
MODES = {
    "camion": {"usd_tkm": 70.0 / 1461.0, "fuente": "flete Ibicuy-Añelo 70 USD/t (Infobae, 15/8/2026) sobre 1.461 km"},
    "fluvial": {"usd_tkm": 16.9 / 1279.0, "fuente": "Ibicuy-Bahía Blanca por agua 16,9 USD/t sobre 1.279 km (El Cronista, 4/9/2026)"},
    "maritimo": {"usd_tkm": 16.9 / 1279.0, "fuente": "mismo tramo por agua; la fuente no separa río de mar"},
    "tren": {"usd_tkm": 15.9 / 665.0, "fuente": "derivado: 35,2 total de agua+tren+camión menos 16,9 de agua y 2,4 de última milla (El Cronista, 4/9/2026)"},
}

ULTIMA_MILLA_USD_T = 27.0     # de la planta cercana al pozo, Infobae 15/8/2026; igual en todas las cadenas
INVERSION_TREN_MUSD = 500.0   # Tren Norpatagónico, estimación original (Bloomberg Línea, 11/9/2026)


@dataclass
class Leg:
    modo: str
    km: float


@dataclass
class Chain:
    nombre: str
    legs: list[Leg]
    usd_t_pozo: float             # costo por tonelada puesta en el pozo, transporte incluido (a REFERENCIA_MT si tiene capex)
    estado: str                   # qué existe hoy
    fuente: str
    limite: str = ""
    capacidad_mt: float | None = None   # toneladas por año que podría mover hoy o al inicio, si se sabe
    capex_musd: float | None = None     # inversión que hay que amortizar con el volumen, si la cadena no tiene tarifa publicada
    vida_anios: float = 20.0            # plazo de amortización lineal, sin interés
    usd_t_variable: float = 0.0         # operación más última milla por tonelada, sin la inversión
    agua_t_t: float = 0.0               # toneladas de agua por tonelada de arena, para las pulpas

    @property
    def km_camion(self) -> float:
        return sum(l.km for l in self.legs if l.modo == "camion")

    @property
    def km_total(self) -> float:
        return sum(l.km for l in self.legs)

    def kg_co2e_t(self, f: dict = EMISIONES_G_TKM) -> float:
        return sum(l.km * f[l.modo] for l in self.legs) / 1000.0

    def usd_t_at(self, tons: float) -> float:
        """Costo por tonelada a un volumen anual: fijo si hay tarifa; si hay capex, la inversión se reparte en lo que se mueve."""
        if self.capex_musd is None:
            return self.usd_t_pozo
        if tons <= 0:
            return float("inf")
        return self.usd_t_variable + self.capex_musd * 1e6 / (self.vida_anios * tons)


REFERENCIA_MT = 5.0   # volumen al que se declara el costo por tonelada de las cadenas con capex: el de 2025

# El arenoducto: pulpa de arena y agua por caño, como los mineraloductos. No existe; los supuestos están acá.
ARENODUCTO = {
    "km": 1100.0,              # Ibicuy, cruce del Paraná en Zárate, corredor de la RN 5 a Salliqueló y la traza del gasoducto Perito Moreno a Tratayén
    "capex_musd": 2000.0,      # 1,85 MUSD/km: 400 M€ por 235 km de OCP en Marruecos (Energy Efficiency Magazine, 1/2022)
    "capex_alto_musd": 4400.0, # 4 MUSD/km: 2.300 MUSD por 573 km del gasoducto Perito Moreno (2023)
    "opex_usd_tkm": 0.02,      # 1 a 3 centavos por tonelada-km, rango de la literatura de mineraloductos
    "agua_t_t": 0.5,           # pulpas al 65-70 % de sólidos
    "vida_anios": 20.0,
    "precedentes": "Minas-Rio 529 km y 26,5 Mt/año; OCP 187 km, 400 M€, 90 % menos de costo; Alumbrera 316 km (1997-2018); LILO-2 49 km en cápsulas (1980); Dune Express 68 km, 13 Mt/año, 400 MUSD (2024)",
}
EMISIONES_G_TKM["pulpa"] = EMISIONES_G_TKM["tren"]   # bombeo eléctrico sin factor publicado: se toma el del tren como cota, declarado

# Equipos del tramo por agua. La distinción la marcó Alejandro Raúl García Arguijo, profesor de la
# Universidad de la Marina Mercante, en los comentarios del post del 17/9/2026: las barcazas de
# hidrovía son para ríos interiores; el tramo marítimo va con convoy de empuje o barcaza ATB.
BARCAZA = {
    "fluvial_t": 1500.0,      # barcaza de río tipo Mississippi, a granel
    "atb_t": 15000.0,         # barcaza ATB (articulated tug barge), 15.000 a 20.000 t; el convoy de empuje está definido en el REGINAVE
    "fuente": "Alejandro Raúl García Arguijo, en comentarios; Alberto Gianola Otamendi, Boletín del Centro Naval 851 (2019), para la barcaza de río con empujador",
}

# Rutas que aparecieron en los comentarios del post del 17/9/2026. Los km son de OSRM sobre
# OpenStreetMap, salvo el tramo ferroviario, aproximado por la distancia carretera.
TREN_MENDOZA = {
    "km_tren": 900.0,         # San Nicolás a Palmira por la línea San Martín, aproximado por ruta: la vía es más larga
    "km_camion": 748.0,       # Palmira a Añelo
    "capacidad_t_mes": 10000.0,
    "fuente": "acuerdo YPF y Trenes Argentinos Cargas, agosto de 2021 (Diario Río Negro); lo trajo Matías Derlich en comentarios",
}
ARENA_RIO_NEGRO = {"km_camion": 120.0, "capacidad_mt": 0.8,
                   "fuente": "canteras de Allen; producción 2025 de 1,5 Mt con caída del 42,6 % y proyección de ~0,8 Mt para 2026 (Diario Río Negro, 6/9/2026)"}
ARENA_CHUBUT = {"km_camion": 855.0,
                "fuente": "Dolavon, Chubut; sin producción publicada por año"}


CHAINS: list[Chain] = [
    Chain("camión directo, hoy", [Leg("camion", 1461)], 70.0 + ULTIMA_MILLA_USD_T,
          "existe: 4.300 camiones, 70 a 75 h por tramo", "Infobae 15/8/2026; Diario Neuquino 11/9/2026",
          "rutas al límite; 700 a 800 camiones más por año si la actividad se duplica"),
    Chain("barcaza a Bahía Blanca y camión", [Leg("fluvial", 250), Leg("maritimo", 1029), Leg("camion", 620)], 62.7,
          "en construcción: terminal de PTP en Ibicuy, 12 MUSD, permiso 2024", "El Cronista 4/9/2026; Diario Neuquino 29/8/2026",
          "falta terminal de arena en Bahía Blanca; 620 km de camión por la RN 22"),
    Chain("barcaza, Tren Norpatagónico y camión", [Leg("fluvial", 250), Leg("maritimo", 1029), Leg("tren", 665), Leg("camion", 50)], 35.2,
          "no existe: el tren mueve <100 kt/año, 37 % de la vía en buen estado, 10 km/h; faltan 83 km hasta Añelo", "El Cronista 4/9/2026; Bloomberg Línea 11/9/2026",
          "500 MUSD y una licitación que no está; 1,5 Mt el primer año, 6 Mt de potencial", capacidad_mt=1.5),
    Chain("hidrovía patagónica por el río Negro", [Leg("fluvial", 250), Leg("maritimo", 1330), Leg("fluvial", 720), Leg("camion", 50)], 48.0,
          "en estudio: dos informes técnicos, el tercero con inversiones pendiente", "GlobalPorts 15/7/2026",
          "dragado, terminales, reforma del cabotaje; el puerto de San Antonio queda a 180 km del río"),
    Chain("tren a Mendoza y camión", [Leg("tren", TREN_MENDOZA["km_tren"]), Leg("camion", TREN_MENDOZA["km_camion"])],
          TREN_MENDOZA["km_tren"] * MODES["tren"]["usd_tkm"] + TREN_MENDOZA["km_camion"] * MODES["camion"]["usd_tkm"] + ULTIMA_MILLA_USD_T,
          "existió: YPF y Trenes Argentinos Cargas, 10.000 t por mes desde agosto de 2021; sin datos públicos de hoy", TREN_MENDOZA["fuente"],
          "los km de vía son los de la ruta, la traza ferroviaria es más larga; 748 km siguen en camión por rutas que este modelo no mide",
          capacidad_mt=TREN_MENDOZA["capacidad_t_mes"] * 12 / 1e6),
    Chain("arena de Río Negro, desde Allen", [Leg("camion", ARENA_RIO_NEGRO["km_camion"])],
          ARENA_RIO_NEGRO["km_camion"] * MODES["camion"]["usd_tkm"] + ULTIMA_MILLA_USD_T,
          "existe y se recupera: 1,5 Mt en 2025 tras caer 42,6 %; ~110.000 t en agosto de 2026", ARENA_RIO_NEGRO["fuente"],
          "las operadoras se volcaron a Entre Ríos por calidad; el costo de acá no incluye esa diferencia en el pozo",
          capacidad_mt=ARENA_RIO_NEGRO["capacidad_mt"]),
    Chain("arena de Chubut, desde Dolavon", [Leg("camion", ARENA_CHUBUT["km_camion"])],
          ARENA_CHUBUT["km_camion"] * MODES["camion"]["usd_tkm"] + ULTIMA_MILLA_USD_T,
          "existe, chica: Arenas Patagónicas fue pionera", ARENA_CHUBUT["fuente"],
          "sin volumen publicado por año; 855 km de camión por rutas patagónicas que este modelo no mide"),
    Chain("arena cercana de Neuquén", [Leg("camion", 60)], 60 * MODES["camion"]["usd_tkm"] + ULTIMA_MILLA_USD_T,
          "en prueba: <20.000 t por mes, YPF y Vista", "Vaca Muerta News 2/5/2026; Mejor Energía 8/9/2026",
          "calidad por confirmar en pozo; volumen chico; sin ensayos públicos", capacidad_mt=0.24),
    Chain("arenoducto, hipotético", [Leg("pulpa", ARENODUCTO["km"]), Leg("camion", 50)],
          ARENODUCTO["opex_usd_tkm"] * ARENODUCTO["km"] + ULTIMA_MILLA_USD_T + ARENODUCTO["capex_musd"] * 1e6 / (ARENODUCTO["vida_anios"] * REFERENCIA_MT * 1e6),
          "no existe: pulpa de arena y agua por caño, como los mineraloductos de Minas-Rio, OCP y Alumbrera", "supuestos declarados en ARENODUCTO; precedentes: " + ARENODUCTO["precedentes"],
          "2.000 MUSD de capex a 20 años y 0,02 USD/tkm; con el capex por km del gasoducto serían 4.400 MUSD y 93 USD/t a 5 Mt; 2,5 hm³ de agua por año a 5 Mt",
          capex_musd=ARENODUCTO["capex_musd"], vida_anios=ARENODUCTO["vida_anios"], usd_t_variable=ARENODUCTO["opex_usd_tkm"] * ARENODUCTO["km"] + ULTIMA_MILLA_USD_T, agua_t_t=ARENODUCTO["agua_t_t"]),
]


def chains_table(chains: list[Chain] = CHAINS) -> pd.DataFrame:
    rows = []
    for c in chains:
        rows.append({"cadena": c.nombre, "usd_t_pozo": round(c.usd_t_pozo, 1), "km_total": round(c.km_total), "km_camion": round(c.km_camion),
                     "kg_co2e_t": round(c.kg_co2e_t(), 1), "capex_musd": c.capex_musd, "agua_t_t": c.agua_t_t, "estado": c.estado, "limite": c.limite, "fuente": c.fuente})
    return pd.DataFrame(rows)


def scenarios(tons_mt: tuple[float, ...] = (5.0, 8.0, 15.0), chains: list[Chain] = CHAINS, t_por_camion: float = 30.0, dias: int = 300, ciclo: float = 6.0, inversion_musd: float = INVERSION_TREN_MUSD) -> pd.DataFrame:
    """Por escenario de demanda y cadena: costo anual, ahorro contra el camión, camiones en circulación, CO2 y repago."""
    base = chains[0]
    rows = []
    for mt in tons_mt:
        t = mt * 1e6
        for c in chains:
            usd_t = c.usd_t_at(t)
            costo = t * usd_t / 1e6
            ahorro = t * (base.usd_t_pozo - usd_t) / 1e6
            # camiones de larga distancia: el ciclo se acorta en proporción a los km que quedan en camión
            viajes_largos = t / t_por_camion if c.km_camion > 200 else 0.0
            camiones = viajes_largos / dias * ciclo * (c.km_camion / base.km_camion)
            co2_kt = t * c.kg_co2e_t() / 1e6
            # ahorro alcanzable con la capacidad que la cadena tiene hoy o al inicio, si se conoce
            t_cap = min(t, c.capacidad_mt * 1e6) if c.capacidad_mt else t
            ahorro_cap = t_cap * (base.usd_t_pozo - c.usd_t_at(t_cap)) / 1e6
            # inversión a repagar con el ahorro: la del tren es un dato de prensa, la del arenoducto un supuesto declarado
            inversion = inversion_musd if "Tren" in c.nombre else c.capex_musd
            rows.append({"demanda_mt": mt, "cadena": c.nombre, "usd_t": round(usd_t, 1), "costo_musd": round(costo, 1), "ahorro_musd": round(ahorro, 1),
                         "ahorro_con_capacidad_musd": round(ahorro_cap, 1),
                         "camiones_larga_distancia": round(camiones), "pasadas_dia_rutas_nacionales": round(2 * viajes_largos / dias), "co2_kt": round(co2_kt, 1),
                         "agua_hm3": round(t * c.agua_t_t / 1e6, 1) if c.agua_t_t else None,
                         "repago_inversion_anios": round(inversion / ahorro, 1) if (inversion and ahorro > 0) else None,
                         "repago_tren_anios": round(inversion_musd / ahorro, 1) if ("Tren" in c.nombre and ahorro > 0) else None,
                         "repago_tren_con_capacidad_anios": round(inversion_musd / ahorro_cap, 1) if ("Tren" in c.nombre and ahorro_cap > 0) else None,
                         "cubre_pct": round(100 * min(1.0, c.capacidad_mt / mt), 0) if c.capacidad_mt else None})
    return pd.DataFrame(rows)


# Cómo lo resolvieron otros: distancia, modo y participación de la logística en el precio. Verificado 14/9/2026.
BENCHMARKS = pd.DataFrame([
    {"pais": "Estados Unidos, hasta 2017", "arena": "Northern White, Wisconsin", "distancia_km": 2000, "modo": "tren unitario y camión", "logistica_pct": "75 %", "que_cambio": "apareció arena regional en el Permian; el flete era la mitad del costo", "fuente": "PLG Consulting 2018; AOGR 12/2017"},
    {"pais": "Estados Unidos, hoy", "arena": "arena de duna del Permian", "distancia_km": 50, "modo": "camión, cajas y silos; cinta de 68 km", "logistica_pct": "la menor", "que_cambio": "60 % menos por tonelada; Dune Express de 400 MUSD mueve 13 Mt/año sin camiones", "fuente": "JPT 12/2018; JPT 2024"},
    {"pais": "Canadá", "arena": "Wisconsin y Peace River", "distancia_km": 1500, "modo": "tren a terminales y camión; arena local sin tren", "logistica_pct": "sin dato", "que_cambio": "mezcla de importada por tren y local cercana", "fuente": "Source Energy Services"},
    {"pais": "Rusia", "arena": "cerámica de los Urales", "distancia_km": 2000, "modo": "tren a depósitos en Siberia, camión y caminos de invierno", "logistica_pct": "sin dato", "que_cambio": "sin arena apta: 99 % cerámica; depósitos cargados antes del invierno", "fuente": "ROGTEC"},
    {"pais": "Argentina, hoy", "arena": "Ibicuy, Entre Ríos", "distancia_km": 1461, "modo": "camión", "logistica_pct": "más del 70 %", "que_cambio": "la arena cercana perdió por calidad; el tren no llega y el río está en estudio", "fuente": "Infobae 8/2026; este repo"},
])

__all__ = ["EMISIONES_G_TKM", "MODES", "ULTIMA_MILLA_USD_T", "INVERSION_TREN_MUSD", "REFERENCIA_MT", "ARENODUCTO", "BARCAZA",
           "TREN_MENDOZA", "ARENA_RIO_NEGRO", "ARENA_CHUBUT", "Leg", "Chain", "CHAINS", "chains_table", "scenarios", "BENCHMARKS"]
