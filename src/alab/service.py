"""La cadena que no se corta: nivel de servicio, stock de seguridad y qué cuesta cada uno.

El resto del repo compara cadenas por costo promedio. Esto agrega lo que falta:
los tiempos no son fijos. El camión que debería tardar 48 horas tarda 70 a 75;
cada transbordo suma espera con cola a la derecha. Con demanda por campaña, no
por promedio diario, se calcula cuánto stock hay que tener en la locación para
no frenar la fractura con 95, 98 o 99 % de probabilidad, cuánto cuesta ese
stock y cuánto costaría el equipo parado.

El planteo es de Carlos Scanio, gerente de operaciones y supply chain, en los
comentarios del post del 17/9/2026: el nivel de servicio se mide como
probabilidad de no faltar durante una campaña; el costo de una flota parada
supera por mucho el de inmovilizar arena, que es barata de acopiar; y cada
transbordo suma su propia varianza.

Todos los supuestos están en las constantes de arriba, declarados, y varios
son eso: supuestos, no mediciones.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .logistics import CHAINS, KM_DIA, TASA_CAPITAL_ANUAL, VALOR_ARENA_USD_T, Chain

# Nivel de servicio y su z de la normal estándar: probabilidad de no quedarse sin arena en la campaña.
SERVICIO_Z = {0.95: 1.645, 0.98: 2.054, 0.99: 2.326}

# La campaña, no el promedio diario. Un pozo de Vaca Muerta lleva 10.000 a 15.000 t de arena
# (Infobae 15/8/2026) y se fractura en unos seis días: el ritmo de consumo sale de ahí.
CAMPANA = {
    "t_por_dia": 2000.0,      # lo que bombea una flota de fractura en un día de campaña
    "dias": 30.0,             # largo de la campaña: varios pozos seguidos en el mismo pad
    "fuente": "10.000 a 15.000 t por pozo y ~6 días de fractura; pendiente de confirmar con operación real",
}

# Velocidad sin demoras, km por día. El camión ideal hace Ibicuy-Añelo en 48 horas: 730 km por día.
# `KM_DIA` de logistics.py son 500, que ya incluyen las demoras reales; acá el retraso se simula aparte.
KM_DIA_IDEAL = {**KM_DIA, "camion": 730.0}

# Tamaño de lote por modo, toneladas: lo que llega junto en cada envío. De ahí sale el stock de
# ciclo, que es la diferencia grande entre el camión y las cadenas por agua.
LOTE_T = {"camion": 30.0, "tren": 2000.0, "fluvial": 1500.0, "maritimo": 15000.0, "pulpa": 10000.0}

# Variabilidad de los tiempos. El camión se modela como el tiempo ideal por un factor lognormal:
# la mediana lo lleva de 48 a 72 horas, que es lo que reporta la prensa de Neuquén, y la cola
# derecha cubre los viajes malos. Cada transbordo suma su propia demora, también lognormal.
DEMORA = {
    "camion_mediana": 1.5,        # 72 h sobre 48 ideales
    "camion_sigma_log": 0.25,     # dispersión del factor; P90 ≈ 1,4 veces la mediana
    "transbordo_dias": 0.5,       # mediana de espera y manipuleo por cambio de modo
    "transbordo_sigma_log": 0.6,  # cola derecha: el transbordo malo tarda varias veces más
    "otros_modos_sigma_log": 0.15,  # barcaza, tren y caño son más regulares que el camión
    "fuente": "camión 70 a 75 h contra 48 ideales (Diario Neuquino 11/9/2026); el resto, supuestos declarados",
}

# Qué cuesta tener arena parada en la locación y qué cuesta que se corte.
ACOPIO_USD_T = 3.0            # movimiento y acopio en locación por tonelada almacenada; supuesto
EQUIPO_PARADO_USD_DIA = 150000.0   # costo de un día de flota de fractura detenida; supuesto, orden de magnitud
DIAS_PARADA = 2.0             # cuánto dura una parada cuando falta arena; supuesto


def lead_time_days(chain: Chain, n: int = 20000, seed: int = 0, demora: dict = DEMORA, km_dia: dict = KM_DIA_IDEAL) -> np.ndarray:
    """Muestras del tiempo puerta a puerta de un envío por esta cadena, en días.

    Cada tramo tarda sus km sobre la velocidad comercial del modo, multiplicado por un
    factor lognormal; el camión arrastra el factor grande y el resto uno chico. Entre
    tramos consecutivos se suma una demora de transbordo, también lognormal.
    """
    rng = np.random.default_rng(seed)
    total = np.zeros(n)
    for i, leg in enumerate(chain.legs):
        base = leg.km / km_dia[leg.modo]
        if leg.modo == "camion":
            mediana, sigma = demora["camion_mediana"], demora["camion_sigma_log"]
        else:
            mediana, sigma = 1.0, demora["otros_modos_sigma_log"]
        total += base * mediana * rng.lognormal(0.0, sigma, n)
        if i > 0:
            total += demora["transbordo_dias"] * rng.lognormal(0.0, demora["transbordo_sigma_log"], n)
    return total


def lead_time_stats(chains: list[Chain] = CHAINS, n: int = 20000, seed: int = 0) -> pd.DataFrame:
    """Por cadena: mediana, desvío y percentil 95 del tiempo de entrega, en días."""
    rows = []
    for c in chains:
        d = lead_time_days(c, n=n, seed=seed)
        rows.append({"cadena": c.nombre, "transbordos": max(0, len(c.legs) - 1), "dias_p50": round(float(np.median(d)), 1),
                     "dias_desvio": round(float(d.std()), 2), "dias_p95": round(float(np.percentile(d, 95)), 1)})
    return pd.DataFrame(rows)


def safety_stock_t(chain: Chain, servicio: float, n: int = 20000, seed: int = 0, campana: dict = CAMPANA) -> float:
    """Toneladas de arena que hay que tener en la locación para cubrir la variabilidad del tránsito.

    Con consumo conocido durante la campaña, la incertidumbre es la del tiempo de
    entrega: el stock de seguridad es z por el consumo diario por el desvío del tránsito.
    """
    d = lead_time_days(chain, n=n, seed=seed)
    return SERVICIO_Z[servicio] * campana["t_por_dia"] * float(d.std())


def cycle_stock_t(chain: Chain, lote: dict = LOTE_T) -> float:
    """Stock de ciclo: la mitad del lote más grande de la cadena.

    Un camión trae 30 toneladas y una barcaza de mar 15.000: la arena que llega junta
    tiene que esperar en algún lado hasta que se consuma, y eso también es stock.
    """
    return max(lote[l.modo] for l in chain.legs) / 2.0


def service_table(chains: list[Chain] = CHAINS, servicios: tuple[float, ...] = (0.95, 0.98, 0.99), n: int = 20000, seed: int = 0,
                  campana: dict = CAMPANA, acopio_usd_t: float = ACOPIO_USD_T, valor_usd_t: float = VALOR_ARENA_USD_T,
                  tasa: float = TASA_CAPITAL_ANUAL, equipo_parado_usd_dia: float = EQUIPO_PARADO_USD_DIA, dias_parada: float = DIAS_PARADA) -> pd.DataFrame:
    """Por cadena y nivel de servicio: stock necesario, lo que cuesta tenerlo y el costo total por tonelada.

    El stock se paga dos veces: el capital inmovilizado mientras dura la campaña y el
    acopio de cada tonelada que pasa por la locación. La falta se paga con el equipo
    parado, ponderada por la probabilidad de que ocurra.
    """
    t_campana = campana["t_por_dia"] * campana["dias"]
    rows = []
    for c in chains:
        ciclo = cycle_stock_t(c)
        for s in servicios:
            ss = safety_stock_t(c, s, n=n, seed=seed, campana=campana)
            stock = ss + ciclo
            capital = stock * valor_usd_t * tasa * campana["dias"] / 365.0   # USD por campaña
            acopio = stock * acopio_usd_t                                    # USD por campaña
            falta = (1.0 - s) * dias_parada * equipo_parado_usd_dia          # USD esperados por campaña
            stock_usd_t = (capital + acopio) / t_campana
            falta_usd_t = falta / t_campana
            rows.append({"cadena": c.nombre, "servicio": s, "stock_seguridad_t": round(ss), "stock_ciclo_t": round(ciclo),
                         "stock_total_t": round(stock), "dias_de_consumo": round(stock / campana["t_por_dia"], 1),
                         "stock_usd_t": round(stock_usd_t, 2), "falta_usd_t": round(falta_usd_t, 2),
                         "flete_usd_t": round(c.usd_t_pozo, 1),
                         "total_usd_t": round(c.usd_t_pozo + c.capital_transito_usd_t() + stock_usd_t + falta_usd_t, 2)})
    return pd.DataFrame(rows)


def dia_parado_en_toneladas(equipo_parado_usd_dia: float = EQUIPO_PARADO_USD_DIA, valor_usd_t: float = VALOR_ARENA_USD_T) -> float:
    """Cuántas toneladas de arena en cantera compra un día de flota de fractura parada.

    Es la asimetría que plantea Carlos Scanio: la arena es barata de acopiar y la parada, cara.
    """
    return equipo_parado_usd_dia / valor_usd_t


def ranking(servicio: float = 0.99, chains: list[Chain] = CHAINS, **kw) -> pd.DataFrame:
    """Las cadenas ordenadas por costo total con nivel de servicio, y si cambian de puesto contra el flete solo."""
    t = service_table(chains=chains, servicios=(servicio,), **kw).sort_values("total_usd_t").reset_index(drop=True)
    t["puesto_total"] = t.index + 1
    t["puesto_flete"] = t.flete_usd_t.rank(method="first").astype(int)
    t["cambia"] = t.puesto_total != t.puesto_flete
    return t[["cadena", "flete_usd_t", "stock_seguridad_t", "stock_usd_t", "falta_usd_t", "total_usd_t", "puesto_flete", "puesto_total", "cambia"]]


def service_figure(tabla: pd.DataFrame, path, servicio: float = 0.99):
    """Barras del stock de seguridad por cadena al nivel de servicio pedido, con los días de consumo que representa."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bg, ink, muted, rule, acento, contexto = "#0e1b25", "#e9eff3", "#8ea2af", "#22384a", "#f2b134", "#6b8799"
    d = tabla[tabla.servicio == servicio].sort_values("stock_total_t")
    fig, ax = plt.subplots(figsize=(8.4, 5.4), dpi=200)
    fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
    fig.subplots_adjust(left=0.36, right=0.97, top=0.78, bottom=0.12)
    y = np.arange(len(d))
    colores = [acento if "camión directo" in c else contexto for c in d.cadena]
    ax.barh(y, d.stock_total_t, height=0.58, color=colores, zorder=3)
    for i, (t, dias) in enumerate(zip(d.stock_total_t, d.dias_de_consumo)):
        ax.text(t * 1.02, i, f"{t:,.0f} t · {dias:.1f} días".replace(",", "."), va="center", ha="left", color=ink, fontsize=11)
    ax.set_yticks(y); ax.set_yticklabels([c.replace(", ", ",\n") if len(c) > 28 else c for c in d.cadena], color=ink, fontsize=10.5)
    ax.tick_params(axis="x", colors=muted, labelsize=10, length=0)
    ax.set_xlim(0, float(d.stock_total_t.max()) * 1.38)
    ax.grid(axis="x", color=rule, linewidth=0.8, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.text(0.03, 0.93, "Cuánta arena queda parada en cada cadena", color=ink, fontsize=15.5, fontweight="bold")
    fig.text(0.03, 0.875, f"Stock de seguridad más stock de ciclo, para no frenar la fractura el {servicio:.0%} de las campañas.", color=muted, fontsize=10.5)
    fig.text(0.03, 0.825, f"Consumo de {CAMPANA['t_por_dia']:,.0f} t por día. El stock de ciclo manda: un camión trae 30 t y una barcaza de mar, 15.000.".replace(",", "."), color=muted, fontsize=10.5)
    fig.text(0.03, 0.03, "Fuente: arena-lab. Tiempos simulados sobre la variabilidad declarada en service.py; planteo de Carlos Scanio.", color=muted, fontsize=9)
    fig.savefig(path, facecolor=bg)
    plt.close(fig)
    return path


__all__ = ["SERVICIO_Z", "CAMPANA", "DEMORA", "ACOPIO_USD_T", "EQUIPO_PARADO_USD_DIA", "DIAS_PARADA",
           "lead_time_days", "lead_time_stats", "safety_stock_t", "service_table", "ranking", "service_figure"]
