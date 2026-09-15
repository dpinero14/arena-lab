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

Y la ruta de la arena animada, año a año desde 2012: los camiones aparecen
sobre la traza en proporción a la arena bombeada, con el flete del año y los
dólares por kilómetro: <https://dpinero14.github.io/arena-lab/ruta_animada.html>

## Qué hace

| Notebook | Qué hace |
|---|---|
| `01_donde_buscar_arena` | Baja y clasifica 21.546 polígonos del mapa geológico en cinco clases de blanco. Calcula un puntaje de 0 a 100 por polígono con la geología, la distancia al centro de la demanda, a la red vial y a los depósitos de arena conocidos. Lista los mejores blancos. Controla el puntaje en siete lugares con arena conocida. Traza la ruta real de los camiones de Ibicuy a Añelo y mide qué blancos quedan al costado. Dibuja el mapa. |
| `02_la_logistica_de_la_arena` | Mide la cadena de hoy año a año: viajes, camiones, flete y dólares por kilómetro. Compara cinco cadenas con las mismas reglas: costo por tonelada, kilómetros en camión y emisiones. Corre escenarios de 5, 8 y 15 millones de toneladas con ahorro y repago del tren. Compara con Estados Unidos, Canadá y Rusia. Genera la ruta animada con capas y selector de cadena. |

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

**La ruta de la arena cruza un mar de arena.** El recorrido real de los
camiones, de Ibicuy a Añelo por la RN 12, la RN 5, la RN 35, la RN 152, la RP
20 y la RN 151, calculado con un ruteador abierto sobre OpenStreetMap, mide
1.461 km, contra los 1.474 que cita la prensa, y 20 horas de manejo continuo.
Entre Santa Rosa y Puelches atraviesa el manto arenoso de La Pampa: a menos de
15 km de la traza hay 83 polígonos de arena eólica cuaternaria, 19.800 km², en
las hojas Santa Rosa y General Acha, con puntajes de hasta 75. Los camiones
que traen arena desde 1.400 km pasan por encima de arena durante 300 km. Que
esa arena sirva o no, lo dice el laboratorio; que nadie la haya ensayado en
público, lo dice este mapa.

![La ruta de la arena](docs/figures/ruta_arena.png)

**En camiones y en dólares, año a año.** Con 30 toneladas por viaje, 300 días
operativos y un ciclo de seis días, la arena nacional de 2025 son 168.000
viajes cargados, 561 por día y unos 3.400 camiones en circulación, contra los
4.300 que cuenta la prensa contando los parados. A 70 dólares la tonelada de
flete, a precios de 2026, son 354 millones de dólares en el año: 242.000
dólares por cada kilómetro de ruta. Desde 2012, 1.460 millones. Cada viaje
cargado cuesta 2.100 dólares de flete, 1,44 por kilómetro. Los supuestos están
en `animation.py` y en la página animada, que además supone toda la arena
nacional por la ruta de Entre Ríos: hasta 2020 una parte venía de Río Negro y
Chubut, con viajes más cortos.

## La logística de la arena: cinco caminos con las mismas reglas

Cada cadena es una lista de tramos con su modo y sus kilómetros, más un costo
por tonelada puesta en el pozo tomado de fuentes de 2026, y las emisiones con
los factores europeos de 2018 pozo a rueda, los únicos con método comparable
para camión, tren, río y mar. Todo declarado en `src/alab/logistics.py`.

| Cadena | USD por tonelada al pozo | km en camión | kg CO₂e por tonelada | Estado |
|---|---|---|---|---|
| Camión directo, hoy | 97 | 1.461 | 200 | existe: 4.300 camiones, 70 a 75 h por tramo |
| Barcaza a Bahía Blanca y camión | 63 | 620 | 100 | en construcción: terminal de PTP en Ibicuy, 12 MUSD |
| Barcaza, Tren Norpatagónico y camión | 35 | 50 | 38 | no existe: el tren mueve menos de 100.000 t, 37 % de la vía en buen estado, faltan 83 km |
| Hidrovía patagónica por el río Negro | 48 | 50 | 48 | en estudio: dragado, terminales y cabotaje pendientes |
| Arena cercana de Neuquén | 30 | 60 | 8 | en prueba: 20.000 t por mes, calidad por confirmar |

**Con 5 millones de toneladas, la diferencia entre el camión y el tren son
309 millones de dólares por año.** El tren pagaría sus 500 millones en menos
de dos años si pudiera llevarlo todo; con la capacidad de 1,5 millones que se
le atribuye al primer año, el ahorro baja a 93 millones y el repago a cinco
años y medio. A 8 millones de toneladas, la cifra que se proyecta para 2027,
el camión directo cuesta 776 millones por año y pone 5.300 camiones en la
ruta. Las emisiones del camión son 1.000 kilotoneladas de CO₂e por año a 5
millones; el tren las baja a 190.

**Cómo lo resolvieron otros.** Estados Unidos pasó por dos etapas en diez
años: arena de calidad a 2.000 km en tren, con la logística en tres cuartos
del precio, y después arena regional a 50 km y una cinta transportadora de 68
km. Canadá mezcla arena importada por tren con local sin tren. Rusia no tiene
arena apta, usa cerámica y la lleva en tren a depósitos que carga antes del
invierno. Argentina está en la primera etapa con el modo equivocado: la misma
proporción de logística en el precio que tenía Estados Unidos, pero en camión.

La ruta animada, versión 2, con los blancos de arena debajo de la traza, el
ferrocarril y su estado, los ríos, los puertos y un selector de cadena que
cambia las unidades que circulan, el costo y las emisiones de cada año:
<https://dpinero14.github.io/arena-lab/ruta_animada.html>

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
  route.py       la ruta de la arena de Ibicuy a Añelo, por OSRM, con puntos de paso de la prensa
  animation.py   la ruta animada v1: camiones por año y flete por kilómetro, con supuestos declarados
  logistics.py   cadenas alternativas: tramos, costos por tonelada, emisiones, escenarios y benchmarks
  animation2.py  la ruta animada v2: capas, selector de cadena, contexto por año y cierre
  maps.py        mapa interactivo (folium) y figuras
notebooks/       01_donde_buscar_arena, 02_la_logistica_de_la_arena
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
- Los costos por tonelada de las cadenas vienen de tres fuentes con bases no
  idénticas, y las cadenas por agua todavía no tienen inversión estimada. Los
  factores de emisión son europeos de 2018; la flota argentina probablemente
  emite más. Las trazas de barcaza y tren son puntos de paso, no rutas exactas.

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
- Ruta de la arena: traza calculada con OSRM sobre OpenStreetMap (ODbL), con
  los puntos de paso que describen Diario Neuquino y LM Neuquén en septiembre
  de 2026.
- Ferrocarril, estaciones y puertos: IDE Transporte, por WFS. Ríos: IGN,
  capa de aguas continentales perennes, por WFS.
- Costos de las cadenas: Infobae 15/8/2026, El Cronista 4/9/2026, GlobalPorts
  15/7/2026, Bloomberg Línea 11/9/2026. Emisiones: CE Delft y Fraunhofer ISI
  para la Agencia Europea de Medio Ambiente, 2021, datos 2018.
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
