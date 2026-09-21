import numpy as np

from alab.logistics import CHAINS
from alab.service import (CAMPANA, EQUIPO_PARADO_USD_DIA, cycle_stock_t, dia_parado_en_toneladas, lead_time_days,
                          lead_time_stats, ranking, safety_stock_t, service_table)

CAMION = next(c for c in CHAINS if c.nombre == "camión directo, hoy")
TREN = next(c for c in CHAINS if "Tren Norpatagónico" in c.nombre)


def test_el_camion_simulado_tarda_lo_que_dice_la_prensa():
    """Mediana de 3 días: las 70 a 75 horas que reportan los choferes, contra 48 ideales."""
    d = lead_time_days(CAMION, n=4000, seed=1)
    assert 2.7 < np.median(d) < 3.3
    assert np.percentile(d, 95) > np.median(d)       # la cola está a la derecha, como los viajes malos


def test_cada_transbordo_suma_varianza():
    s = lead_time_stats(n=4000).set_index("cadena")
    assert s.loc[TREN.nombre, "transbordos"] == 3 and s.loc[CAMION.nombre, "transbordos"] == 0
    assert s.loc[TREN.nombre, "dias_desvio"] > s.loc[CAMION.nombre, "dias_desvio"]
    assert s.loc[TREN.nombre, "dias_p50"] > s.loc[CAMION.nombre, "dias_p50"]


def test_stock_de_ciclo_por_tamano_de_lote():
    assert cycle_stock_t(CAMION) == 15.0              # media camionada
    assert cycle_stock_t(TREN) == 7500.0              # media barcaza de mar: el lote manda
    cercana = next(c for c in CHAINS if c.nombre == "arena cercana de Neuquén")
    assert cycle_stock_t(cercana) == 15.0


def test_mas_nivel_de_servicio_pide_mas_stock_y_cuesta_menos():
    """La asimetría que planteó Carlos Scanio: el stock es barato y la parada es cara."""
    t = service_table(chains=[CAMION, TREN], n=4000).set_index(["cadena", "servicio"])
    for c in (CAMION.nombre, TREN.nombre):
        assert t.loc[(c, 0.99), "stock_seguridad_t"] > t.loc[(c, 0.95), "stock_seguridad_t"]
        assert t.loc[(c, 0.99), "falta_usd_t"] < t.loc[(c, 0.95), "falta_usd_t"]
        assert t.loc[(c, 0.99), "total_usd_t"] < t.loc[(c, 0.95), "total_usd_t"]   # conviene subir el servicio


def test_el_stock_no_da_vuelta_el_ranking():
    """Con arena barata, el costo del stock es centavos contra decenas de dólares de flete."""
    r = ranking(0.99, n=4000)
    assert not r.cambia.any()
    assert r.stock_usd_t.max() < 2.0
    assert r.iloc[0].cadena == "arena cercana de Neuquén" and r.iloc[-1].cadena == "camión directo, hoy"


def test_safety_stock_crece_con_el_consumo():
    campana = {**CAMPANA, "t_por_dia": 4000.0}
    assert safety_stock_t(CAMION, 0.99, n=4000, campana=campana) > safety_stock_t(CAMION, 0.99, n=4000)


def test_un_dia_parado_en_toneladas():
    t = dia_parado_en_toneladas()
    assert abs(t - EQUIPO_PARADO_USD_DIA / 22.0) < 1e-6 and 6000 < t < 8000
