# Material para el post

No es el texto del post: son los hallazgos en crudo, con los números del
notebook, para que el texto salga de lo que a vos te haga sentido contar.

## Lo que el repo hace

Toma el mapa geológico 1:250.000 de SEGEMAR, 21.546 polígonos de Neuquén, Río
Negro, La Pampa y el norte de Chubut, y hace lo que hace un geólogo antes de
salir a buscar arena de fractura: lee la génesis, la litología y la edad de
cada unidad, separa lo eólico cuaternario, lo fluvial y las areniscas, lo
pondera por distancia al consumo, a las rutas y a las canteras conocidas, y
devuelve un mapa de blancos con puntaje de 0 a 100. Todo con datos abiertos y
código a la vista.

## Cinco hallazgos

1. **La arena cercana es escasa en el mapa, no solo en las canteras.** A
   menos de 150 km del centro de la demanda hay 13 polígonos de arena eólica
   cuaternaria, 433 km². La arena eólica de la ventana, 68.800 km², está en un
   90 % en La Pampa, a 250 o 400 km.

2. **El puntaje encuentra la arena que ya se conoce, incluida la mala.**
   Senillosa, favorable según Cormine, percentil 99. Bajada del Palo, la
   cantera de Vista, 98. Y Allen, la arena que la industria descartó por
   calidad, puntaje 100. El mapa geológico dice dónde hay médanos, no si sus
   granos aguantan la presión. Ese límite del método ahora está medido.

3. **Hay un hueco de 39.000 km² en la cartografía pública, y es el que más
   importa.** El SIGAM no tiene las hojas entre Zapala y Piedra del Águila.
   El corredor Cutral Có a Zapala, donde Neuquén tuvo resultados positivos,
   cae adentro. Con datos públicos, de esa zona no se puede decir nada.

4. **Cerca del consumo, los blancos son los médanos del Bajo de Añelo y las
   terrazas de los ríos.** El Bajo de Añelo, una de las tres zonas que
   explora Neuquén, tiene 89 km² de médanos longitudinales a 28 km del centro
   de la demanda.

5. **La ruta de la arena cruza un mar de arena.** El recorrido real de los
   camiones, Ibicuy a Añelo, ruteado sobre OpenStreetMap: 1.461 km y 20
   horas de manejo continuo. Entre Santa Rosa y Puelches atraviesa el manto
   arenoso de La Pampa: 83 polígonos de arena eólica, 19.800 km², a menos de
   15 km de la traza, con puntajes de hasta 75. Los camiones que traen arena
   desde 1.400 km pasan por encima de arena durante 300 km. Que sirva, lo
   dice el laboratorio. Que nadie la ensayó en público, lo dice el mapa.

## La logística, medida (notebook 2)

6. **El camión de hoy cuesta 97 dólares por tonelada hasta el pozo y emite
   200 kg de CO₂e.** Barcaza y tren costarían 35 y emitirían 38. Con 5
   millones de toneladas, la diferencia son 309 millones de dólares por año:
   el tren pagaría sus 500 millones en menos de dos años si pudiera llevarlo
   todo, en cinco y medio con la capacidad que se le atribuye al primer año.
   A 8 millones de toneladas, el camión directo cuesta 776 millones y pone
   5.300 camiones en la ruta.

7. **Cada alternativa tiene un "pero" verificable.** El tren: menos de
   100.000 toneladas hoy, 37 % de la vía en buen estado, 83 km que faltan,
   sin licitación. El río: dragado, terminales, cabotaje, y San Antonio a 180
   km del río. La arena cercana: 20.000 toneladas por mes y la calidad sin
   ensayos públicos.

8. **Argentina está en la etapa que Estados Unidos dejó en 2017, con el modo
   equivocado.** Allá la arena de calidad viajaba 2.000 km en tren con la
   logística en tres cuartos del precio, hasta que apareció la arena regional.
   Acá la logística pesa lo mismo, pero en camión, y la arena regional se
   descartó por calidad.

## Lo que hay que decir sí o sí

- El mapa señala dónde buscar, no si la arena sirve. No hay un solo ensayo de
  laboratorio argentino publicado como dato.
- Los pesos son una opinión declarada y están en un solo archivo.
- La red vial son rutas nacionales; las provinciales no están.

## Ángulos posibles

- El hueco del mapa: el Estado explora arena en una zona que su propio
  servicio geológico no tiene cartografiada en línea.
- El método que encuentra la arena mala: un mapa que "acierta" en Allen
  demuestra por qué el laboratorio es insustituible.
- La ruta de la arena y los médanos de La Pampa.

## Links

- Repo: https://github.com/dpinero14/arena-lab
- Mapa interactivo: https://dpinero14.github.io/arena-lab/mapa_arena.html
