"""arena-lab: dónde buscar arena de fractura para Vaca Muerta, con datos abiertos.

Rutas del repo y constantes geográficas. Todo lo demás vive en módulos con
funciones puras: `segemar` (descarga), `targets` (reglas geológicas), `score`
(prospectividad), `validate` (control contra lo conocido), `maps` (figuras).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
DOCS = REPO_ROOT / "docs"
FIGURES = DOCS / "figures"

# Ventana de trabajo (oeste, sur, este, norte) en grados: Neuquén, Río Negro,
# La Pampa y el norte de Chubut. Cubre las tres zonas que explora Neuquén, las
# canteras de Río Negro y Dolavon en Chubut. Ibicuy queda afuera a propósito.
BBOX = (-71.8, -43.5, -64.0, -35.5)

# Añelo, el centro operativo de Vaca Muerta: lon, lat.
ANELO = (-68.79, -38.35)

# Sistema proyectado para medir distancias en metros: POSGAR 2007 faja 2,
# que cubre Neuquén y Río Negro con distorsión mínima.
CRS_METRIC = "EPSG:5344"
CRS_GEO = "EPSG:4326"

__all__ = ["REPO_ROOT", "DATA_RAW", "DATA_PROC", "DOCS", "FIGURES", "BBOX", "ANELO", "CRS_METRIC", "CRS_GEO"]
