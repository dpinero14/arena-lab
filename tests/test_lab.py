import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from alab.lab import CARGAS, chains_for_lab, sand_lab_html
from alab.logistics import CHAINS


def test_chains_for_lab_marca_el_corredor_del_camion_largo():
    c = chains_for_lab()
    assert [x["nombre"] for x in c] == [x.nombre for x in CHAINS]
    cam = next(x for x in c if x["corredor"] == "Ibicuy"); bb = next(x for x in c if x["corredor"] == "Bahía Blanca")
    assert cam["km_camion_largo"] == 1461 and bb["km_camion_largo"] == 620
    assert all(x["corredor"] is None and x["km_camion_largo"] == 0 for x in c if "Tren" in x["nombre"] or "cercana" in x["nombre"] or "hidrovía" in x["nombre"])
    assert [k["t"] for k in CARGAS] == [30, 40, 50]


def test_html_del_laboratorio(tmp_path):
    tramos = gpd.GeoDataFrame({"ruta": ["RN 152", "RN 22"], "corredor": ["Ibicuy", "Bahía Blanca"], "km": [163.3, 80.0], "km_desde": [900.0, 100.0], "tmda17": [197, 1700]},
                              geometry=[LineString([(-65, -38), (-66, -38.5)]), LineString([(-63, -38.8), (-64, -38.9)])], crs="EPSG:4326")
    y = pd.DataFrame({"anio": [2024, 2025], "nat_t": [4.0e6, 5.05e6]})
    out = sand_lab_html(tramos, y, tmp_path / "lab.html")
    html = out.read_text(encoding="utf-8")
    assert "__DATA__" not in html and '"medido": {"anio": 2025, "mt": 5.05}' in html and "RN 152" in html and "bitrén" in html
