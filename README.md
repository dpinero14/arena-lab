# arena-lab

Dónde buscar arena de fractura para Vaca Muerta, con datos abiertos. Séptimo
repo de la serie de Machine Learning aplicado a hidrocarburos y el primero de
minería: el mapa geológico 1:250.000 de SEGEMAR, clasificado con reglas
explícitas, ponderado por distancia al consumo y a las rutas, y controlado
contra los lugares donde la industria ya dijo que hay arena buena o mala.

> Vaca Muerta bombea más de cinco millones de toneladas de arena por año y las
> trae en camión desde Entre Ríos, a 1.400 km, porque la arena cercana de Río
> Negro no aguantó la presión. Neuquén explora la suya con 104 pedidos de
> cateo. Este repo hace lo que hace un geólogo antes de salir al campo: mirar
> el mapa y decidir dónde muestrear primero.

![Mapa de prospectividad](docs/figures/mapa_arena.png)

El mapa interactivo, para recorrer los blancos, los depósitos conocidos, las
rutas y las áreas donde se bombea: <https://dpinero14.github.io/arena-lab/mapa_arena.html>

## Qué hace

| Notebook | Qué hace |
|---|---|
| `01_donde_buscar_arena` | Baja y clasifica 21.546 polígonos del mapa geológico en cinco clases de blanco. Calcula un puntaje de 0 a 100 por polígono con la geología, la distancia al centro de la demanda, a la red vial y a los depósitos de arena conocidos. Lista los mejores blancos. Controla el puntaje en siete lugares con arena conocida. Dibuja el mapa. |

Las reglas y los pesos están en `src/alab/targets.py` y `src/alab/score.py`,
en un solo lugar cada uno, para que se puedan leer y discutir. Todo está
testeado con polígonos sintéticos; el notebook narra.

## Qué encontramos

**La ventana tiene 143.000 km² con algún interés, y casi toda la arena eólica
está en La Pampa.** De los 21.546 polígonos, 436 son arena eólica cuaternaria
y suman 68.800 km², pero el 90 % de esa superficie es el manto arenoso de La
Pampa, las hojas Victorica, Santa Rosa, Darregueira y General Acha, a 250 o
400 km del consumo. A menos de 150 km del centro de la demanda hay 13
polígonos eólicos que suman 433 km². La arena cercana es escasa en el mapa,
no solo en las canteras.

| Clase de blanco | Polígonos | km² |
|---|---|---|
| Arena eólica cuaternaria | 436 | 68.819 |
| Arena fluvial cuaternaria | 3.142 | 52.990 |
| Arenisca antigua | 2.405 | 22.911 |
| Otra con arena | 4.359 | 98.147 |
| Sin interés | 11.204 | 161.392 |

**El puntaje encuentra la arena que ya se conoce, incluida la mala.** En los
lugares donde la industria habló, el mejor polígono a 15 km queda arriba del
percentil 85 en todos los casos con cobertura: Senillosa, que Cormine dio por
favorable, en el 99; la cantera de Vista en Bajada del Palo, en el 98; Dolavon,
en el 88. Y Allen, la arena de Río Negro que las operadoras dejaron por rotura
y arcillas, sale con el puntaje máximo, 100. El mapa geológico dice dónde hay
médanos, no si sus granos aguantan la presión de confinamiento. Ese es el
límite del método y acá está medido, no anunciado.

| Lugar | Qué se sabe | Mejor puntaje a 15 km | Clase | Percentil |
|---|---|---|---|---|
| Senillosa | favorable, Cormine 2026 | 70 | fluvial cuaternaria | 99 |
| Bajada del Palo | cantera de Vista | 60 | eólica cuaternaria | 98 |
| Dolavon | planta pionera | 43 | fluvial cuaternaria | 88 |
| Bajo de Añelo | en estudio | 41 | fluvial cuaternaria | 86 |
| Allen | explotada, calidad cuestionada | 100 | eólica cuaternaria | 100 |
| Cutral Có | favorable, Cormine 2026 | sin cobertura | | |
| Zapala | favorable, Cormine 2026 | sin cobertura | | |

**Hay un hueco de 39.000 km² en la cartografía, y es el que más importa.** El
SIGAM no tiene publicadas las hojas 1:250.000 entre Zapala y Piedra del
Águila: un rectángulo de 130 por 330 km con cobertura cero. El corredor Cutral
Có a Zapala, donde Cormine obtuvo resultados positivos, cae adentro. Con datos
públicos no se puede decir nada de esa zona, y eso también es un resultado.

**Cerca del consumo, los blancos son los médanos del Bajo de Añelo y las
terrazas de los ríos.** A menos de 150 km, los mejores puntajes son los
"depósitos de médanos longitudinales" del Bajo de Añelo, 89 km² a 28 km del
centro de la demanda, y las terrazas fluviales antiguas de los ríos Neuquén,
Limay y Negro, entre Senillosa y General Roca. El Bajo de Añelo es una de las
tres zonas que Neuquén explora. Su puntaje pierde por la distancia a rutas
nacionales, 68 km, porque la red vial usada no tiene las rutas provinciales.

**La ruta de la arena pasa por médanos.** Los polígonos con mejor puntaje
absoluto después de Allen son los depósitos eólicos holocenos de la hoja Santa
Isabel, en La Pampa: 38 polígonos, 1.700 km², a 190 a 290 km del consumo y a
9 km de una ruta nacional en la mediana. Los camiones que vienen de Entre Ríos
pasan al lado. Que sirvan o no, lo dice el laboratorio.

## Cómo se explora arena de fractura, en dos párrafos

La arena que sirve es cuarzosa, redonda y resistente. La norma API 19C pide
esfericidad y redondez de 0,6 o más, menos del 10 % de finos al comprimir a la
presión de ensayo, solubilidad en ácido menor al 2 o 3 %, turbidez menor a 250
FTU y sílice alta. Eso lo dan, sobre todo, las arenas eólicas: el viento
selecciona el tamaño y redondea los granos. Después las fluviales, con más
gravas y finos que separar. Y algunas areniscas poco cementadas, que hay que
moler.

Por eso las reglas de `targets.py` leen la génesis, la litología y la edad de
cada unidad: eólico y cuaternario puntúa más que fluvial, que puntúa más que
arenisca antigua; mencionar cuarzo suma, mencionar limos o gravas resta, lo
volcánico queda afuera. El resto es geografía: cuán lejos del consumo, cuán
lejos de un camino, cuán cerca de una cantera que ya existe.

## Cómo correrlo

Requiere Python 3.11 o superior.

```bash
git clone https://github.com/dpinero14/arena-lab.git
cd arena-lab
make setup                          # venv, geopandas, folium, kernel de Jupyter
make test                           # pytest, con polígonos sintéticos
make data                           # ~320 MB: SEGEMAR por WFS, rutas, registro de fractura y producción
make notebooks                      # unos 7 minutos
```

En Windows sin GNU make: `scripts\setup.ps1`, `scripts\test.ps1`,
`python scripts\download_data.py`, `scripts\notebooks.ps1`.

## Estructura

```
src/alab/
  segemar.py     descarga por WFS con paginado, GeoParquet
  targets.py     reglas geológicas: clase de blanco y banderas por polígono
  score.py       puntaje de prospectividad con pesos declarados
  validate.py    control contra lugares con arena conocida
  demand.py      arena bombeada por área, con coordenadas de pozo
  maps.py        mapa interactivo (folium) y figuras
notebooks/       01_donde_buscar_arena
tests/           pytest con polígonos sintéticos
docs/            mapa_arena.html y figuras
data/raw/        vacío y en .gitignore; ver data/README.md
```

## Limitaciones

- El mapa señala dónde buscar, no si la arena sirve. Esfericidad, redondez,
  rotura y turbidez salen del laboratorio, y no hay un solo ensayo argentino
  publicado como dato.
- Escala 1:250.000: un médano chico no aparece. La descripción de cada hoja
  la escribió un geólogo distinto con palabras distintas, y las reglas son de
  palabras clave.
- Faltan hojas en el SIGAM, y una de ellas es la que más importa.
- La red vial son rutas nacionales; las provinciales, como la RP 7 y la RP 17
  que llegan a Añelo, no están.
- Los pesos son una opinión declarada. Cambiarlos cambia el mapa.

## Próximos pasos

1. La geoquímica de SEGEMAR, 13.946 muestras en la ventana, como proxy de
   pureza: aluminio, hierro y calcio bajos donde la arena es cuarzosa.
2. Los cateos de Neuquén, cuando se publiquen como datos, como segunda
   validación.
3. Un laboratorio casero de forma de grano: microscopio USB, arena de Ibicuy y
   de Río Negro, esfericidad y redondez por visión, contra la tabla de Krumbein.

## Datos y licencias

- SEGEMAR, SIGAM, mapa geológico 1:250.000, depósitos de minerales
  industriales y geoquímica: <https://sigam.segemar.gov.ar>, CC-BY 4.0, por WFS.
- IDE Transporte, tránsito medio diario de rutas nacionales: datos.gob.ar.
- Secretaría de Energía, registro de fractura y producción no convencional:
  <https://datos.energia.gob.ar>, CC-BY 4.0.
- Lugares con arena conocida: prensa citada en `src/alab/validate.py`.
- Código: MIT.

## Autor

Diego Piñero. Data science en producción en logística, aprendiendo hidrocarburos
en público. Serie **Sur Analytics** de ML aplicado a Oil & Gas:
[well-log-lab](https://github.com/dpinero14/well-log-lab),
[well-pay-lab](https://github.com/dpinero14/well-pay-lab),
[vaca-muerta-lab](https://github.com/dpinero14/vaca-muerta-lab),
[oilgas-predictive-maintenance](https://github.com/dpinero14/oilgas-predictive-maintenance),
[reservoir-lab](https://github.com/dpinero14/reservoir-lab) y este.
