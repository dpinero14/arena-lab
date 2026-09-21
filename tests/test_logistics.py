from alab.logistics import ARENA_CHUBUT, ARENA_RIO_NEGRO, BARCAZA, BENCHMARKS, CHAINS, EMISIONES_G_TKM, TREN_MENDOZA, Chain, Leg, chains_table, scenarios


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


def test_arenoducto_reparte_el_capex_en_el_volumen():
    from alab.logistics import ARENODUCTO, REFERENCIA_MT
    d = next(c for c in CHAINS if "arenoducto" in c.nombre)
    assert d.capex_musd == ARENODUCTO["capex_musd"] and d.km_camion == 50 and d.agua_t_t == 0.5
    assert abs(d.usd_t_at(REFERENCIA_MT * 1e6) - d.usd_t_pozo) < 1e-9          # el costo declarado es el de referencia
    assert d.usd_t_at(8e6) < d.usd_t_at(5e6) < d.usd_t_at(2e6)                    # más volumen, menos capex por tonelada
    assert d.usd_t_at(0) == float("inf")
    cam = CHAINS[0]
    assert cam.usd_t_at(1e6) == cam.usd_t_pozo                                     # sin capex, el costo no cambia
    s = scenarios(tons_mt=(5.0, 8.0))
    ducto = s[s.cadena.str.contains("arenoducto")].set_index("demanda_mt")
    assert ducto.loc[8.0, "usd_t"] < ducto.loc[5.0, "usd_t"] and ducto.loc[5.0, "agua_hm3"] == 2.5
    assert ducto.loc[5.0, "repago_inversion_anios"] > 0 and ducto.loc[5.0, "pasadas_dia_rutas_nacionales"] == 0


def test_rutas_que_salieron_de_los_comentarios():
    """Tren a Mendoza, Río Negro y Chubut: existen, cuestan menos que el camión largo y no son gratis."""
    t = chains_table().set_index("cadena")
    cam = t.loc["camión directo, hoy"]
    mza, rn, ch = t.loc["tren a Mendoza y camión"], t.loc["arena de Río Negro, desde Allen"], t.loc["arena de Chubut, desde Dolavon"]
    assert mza.usd_t_pozo < cam.usd_t_pozo and mza.km_camion == TREN_MENDOZA["km_camion"]
    assert mza.kg_co2e_t < cam.kg_co2e_t          # el tren evita la mitad del camino, no todo
    assert rn.usd_t_pozo < ch.usd_t_pozo < cam.usd_t_pozo    # Allen está a 120 km; Dolavon, a 855
    assert rn.km_camion == ARENA_RIO_NEGRO["km_camion"] and ch.km_camion == ARENA_CHUBUT["km_camion"]
    mza_chain = next(c for c in CHAINS if c.nombre == "tren a Mendoza y camión")
    assert abs(mza_chain.capacidad_mt - 0.12) < 1e-9         # 10.000 t por mes es el 2 % de la demanda de 2025
    s = scenarios(tons_mt=(5.0,)).set_index("cadena")
    assert s.loc["tren a Mendoza y camión", "cubre_pct"] == 2 and s.loc["arena de Río Negro, desde Allen", "cubre_pct"] == 16
    assert s.loc["tren a Mendoza y camión", "pasadas_dia_rutas_nacionales"] > 0   # los 748 km de Palmira a Añelo siguen siendo camión


def test_barcaza_de_rio_y_de_mar_no_son_el_mismo_equipo():
    assert BARCAZA["atb_t"] >= 10 * BARCAZA["fluvial_t"] and "García Arguijo" in BARCAZA["fuente"]
