from alab.logistics import BENCHMARKS, CHAINS, EMISIONES_G_TKM, Chain, Leg, chains_table, scenarios


def test_cadena_camion_es_la_mas_cara_y_la_que_mas_emite():
    t = chains_table()
    cam = t[t.cadena.str.startswith("camión")].iloc[0]
    assert cam.usd_t_pozo == t.usd_t_pozo.max()
    assert cam.kg_co2e_t == t.kg_co2e_t.max()
    tren = t[t.cadena.str.contains("Tren")].iloc[0]
    assert tren.usd_t_pozo < cam.usd_t_pozo / 2 and tren.km_camion == 50


def test_emisiones_por_tramo():
    c = Chain("x", [Leg("camion", 100), Leg("tren", 100)], 10.0, "", "")
    assert abs(c.kg_co2e_t() - (100 * EMISIONES_G_TKM["camion"] + 100 * EMISIONES_G_TKM["tren"]) / 1000) < 1e-9
    assert c.km_camion == 100 and c.km_total == 200


def test_escenarios():
    s = scenarios(tons_mt=(5.0, 8.0))
    assert set(s.demanda_mt) == {5.0, 8.0} and len(s) == 2 * len(CHAINS)
    cam5 = s[(s.demanda_mt == 5.0) & s.cadena.str.startswith("camión")].iloc[0]
    assert cam5.ahorro_musd == 0 and cam5.camiones_larga_distancia > 3000
    tren5 = s[(s.demanda_mt == 5.0) & s.cadena.str.contains("Tren")].iloc[0]
    assert tren5.ahorro_musd > 0 and tren5.repago_tren_anios is not None and tren5.repago_tren_anios > 0
    assert tren5.camiones_larga_distancia == 0 and tren5.cubre_pct == 30


def test_benchmarks_tienen_argentina():
    assert BENCHMARKS.pais.str.contains("Argentina").any() and "fuente" in BENCHMARKS.columns
