import pandas as pd

from alab.demand import demand_by_area, demand_centroid


def test_demand_by_area_y_centroide():
    frac = pd.DataFrame({
        "well_id": [1, 2, 3, 4], "area": ["A", "A", "B", "C"], "sand_domestic_t": [1000, 2000, 500, 100], "sand_imported_t": [0, 0, 100, 0],
        "frac_start": pd.to_datetime(["2022-01-01", "2023-01-01", "2024-01-01", "2019-01-01"]), "basin": ["NEUQUINA"] * 4, "reservoir_type": ["NO CONVENCIONAL"] * 4,
    })
    coords = pd.DataFrame({"well_id": [1, 2, 3, 4], "lon": [-68.8, -68.7, -69.5, -70.0], "lat": [-38.3, -38.4, -38.9, -39.0]})
    d = demand_by_area(frac, coords, since=2021)
    assert list(d["area"]) == ["A", "B"] and d.loc[d["area"] == "A", "sand_t"].iloc[0] == 3000 and d.loc[d["area"] == "B", "sand_t"].iloc[0] == 600
    c = demand_centroid(d).iloc[0]
    assert -69.5 < c.x < -68.7 and -38.9 < c.y < -38.3
