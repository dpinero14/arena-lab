"""Baja los datos crudos a data/raw. Nada de esto se versiona.

- SEGEMAR (SIGAM, CC-BY 4.0): mapa geológico 1:250.000 recortado a la ventana de
  trabajo, depósitos de minerales industriales de todo el país, muestras
  geoquímicas de la ventana. Por WFS, paginado.
- IDE Transporte: tramos de rutas nacionales con TMDA 2017 (se usan como red vial).
- Secretaría de Energía (CC-BY 4.0): registro de fractura (Adjunto IV) y
  producción no convencional (Capítulo IV, por las coordenadas de los pozos).

Uso: python scripts/download_data.py [--skip-energia]
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alab import BBOX, DATA_RAW  # noqa: E402
from alab.segemar import fetch_layer, save_layer  # noqa: E402

TMDA = ("https://ide.transporte.gob.ar/geoserver/observ/ows?service=WFS&version=1.0.0&request=GetFeature"
        "&typeName=observ:_3.4.1.4.1.tmda_17_18_view&maxFeatures=1550&outputFormat=application%2Fjson")
PORTAL = "http://datos.energia.gob.ar/dataset"
ENERGIA = {
    "fractura_adjunto_iv.csv": (f"{PORTAL}/71fa2e84-0316-4a1b-af68-7f35e41f58d7/resource/2280ad92-6ed3-403e-a095-50139863ab0d"
                                "/download/datos-de-fractura-de-pozos-de-hidrocarburos-adjunto-iv-actualizacin-diaria.csv"),
    "produccion_no_convencional.csv": (f"{PORTAL}/c846e79c-026c-4040-897f-1ad3543b407c/resource/b5b58cdc-9e07-41f9-b392-fb9ec68b0725"
                                       "/download/produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv"),
}


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  ya existe: {dest.name}")
        return
    print(f"  bajando {dest.name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "arena-lab/0.1 (+https://github.com/dpinero14)"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    print(f"  listo: {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")


def main(skip_energia: bool = False) -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    print("SEGEMAR")
    for name, bbox in (("unidades", BBOX), ("depositos_industriales", None), ("geoquimica", BBOX)):
        dest = DATA_RAW / f"segemar_{name}.parquet"
        if dest.exists():
            print(f"  ya existe: {dest.name}")
            continue
        gdf = fetch_layer(name, bbox=bbox, page=2000)
        save_layer(gdf, dest)
        print(f"  guardado {dest.name}: {len(gdf)} features")
    print("IDE Transporte")
    download(TMDA, DATA_RAW / "tmda_rutas_nacionales.geojson")
    if not skip_energia:
        print("Secretaría de Energía")
        for name, url in ENERGIA.items():
            download(url, DATA_RAW / name)
    print("listo")


if __name__ == "__main__":
    main(skip_energia="--skip-energia" in sys.argv)
