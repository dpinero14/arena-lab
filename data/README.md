# Datos

Nada de esta carpeta se versiona. `python scripts/download_data.py` baja todo a
`data/raw/` (unos 320 MB) y el notebook deja intermedios en `data/processed/`.

| Archivo | Fuente | Licencia | Qué es |
|---|---|---|---|
| `segemar_unidades.parquet` | SEGEMAR, SIGAM, capa `e250K_UnidadGeologica` por WFS | CC-BY 4.0 | Mapa geológico 1:250.000 recortado a la ventana de trabajo: 21.546 polígonos con nombre, litología, edad, génesis y morfología |
| `segemar_depositos_industriales.parquet` | SEGEMAR, capa `e250K.DepositMinIndust` | CC-BY 4.0 | 1.546 depósitos de minerales industriales del país, con commodity y modelo |
| `segemar_geoquimica.parquet` | SEGEMAR, capa `e250K.MuestraGeoqMu` | CC-BY 4.0 | 13.946 muestras geoquímicas de la ventana, 57 elementos |
| `tmda_rutas_nacionales.geojson` | IDE Transporte, capa `tmda_17_18_view` | datos.gob.ar | Tramos de rutas nacionales con tránsito medio diario 2017; se usan como red vial |
| `fractura_adjunto_iv.csv` | Secretaría de Energía, datos.energia.gob.ar | CC-BY 4.0 | Registro de fractura por pozo: arena nacional e importada, agua, etapas, fechas |
| `produccion_no_convencional.csv` | Secretaría de Energía, datos.energia.gob.ar | CC-BY 4.0 | Producción mensual por pozo; se usa por las coordenadas de cada pozo |
| `ruta_arena_osrm.json` | OSRM público sobre OpenStreetMap | ODbL | Traza de la ruta de la arena entre los puntos de paso; el notebook la baja si falta |

Descarga verificada el 15 de septiembre de 2026. El WFS de SEGEMAR está en
`https://sigam.segemar.gov.ar/geoserver217/ows`; la licencia CC-BY 4.0 está
declarada en el sitio del SIGAM.
