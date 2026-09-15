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

5. **La ruta de la arena pasa por médanos.** Los depósitos eólicos holocenos
   de Santa Isabel, La Pampa, 1.700 km², quedan a 190 a 290 km del consumo y a
   9 km de una ruta nacional. Los camiones que vienen de Entre Ríos pasan al
   lado. Que sirvan o no, lo dice el laboratorio.

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
