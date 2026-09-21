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

## La ruta paga el pozo (notebook 3)

9. **En la RN 152 pasan más camiones de arena que vehículos había en 2017.**
   El tránsito medio diario de 2017, el último publicado por tramo, era de
   197 y 290 vehículos por día en dos tramos entre General Acha y Casa de
   Piedra. En 2025 son 1.122 pasadas de camiones de arena por día: cuatro a
   seis veces todo el tránsito de entonces. Desde 2021, 198 km de la RN 152
   tienen más arena que tránsito tenían. En la RN 5, entre Luján y Santa
   Rosa, la arena es del 7 al 34 % del tránsito de 2017.

10. **Cada camión desgasta como 10.000 autos, y son 1.122 por día.** Ley de la
    cuarta potencia, AASHO Road Test, Guía AASHTO 1993: 4,26 ejes
    equivalentes por pasada de un semirremolque de 36 t contra 0,0004 de un
    auto. Los de la arena pesan 53 a 55 t; es un piso. Doce millones de
    autos por día, en desgaste, sobre una ruta que en 2017 veía 200.

11. **El modelo y la prensa coinciden sin haberse mirado.** El repo da 1.122
    pasadas diarias con el registro de fractura y 30 t por camión. La Pampa
    cuenta 1.200 camiones por día para justificar una tasa vial (Río Negro,
    30/7/2026); Puelches dice que pasó de 200 o 300 a entre 800 y 1.200 (La
    Arena, 9/5/2026); La Nación cuenta 4.300 camiones de flota (11/9/2026)
    contra los 3.400 en circulación del modelo.

12. **Lo anunciado contra lo que cuesta.** Obras y concesiones de 2026 para
    toda la ruta: del orden de 100 millones de dólares, una vez. El flete de
    2025: 354 millones, cada año. La RN 5 se concesionó en agosto de 2026 a
    20 años sin obras de ampliación, con calzada de 1961 de 3,30 a 3,65 m por
    mano para camiones de 2,60 m.

## El arenoducto (idea de Diego, 16/9/2026)

13. **Mover la arena por caño no es ciencia ficción, es un mineraloducto.**
    Minas-Rio, 529 km y 26,5 Mt por año; OCP en Marruecos, 187 km, 400 M€ y
    90 % menos de costo de transporte; Alumbrera, 316 km, 1997 a 2018; la
    URSS movió piedra en cápsulas por un tubo de 49 km en 1980; el Dune
    Express lleva 13 Mt de arena de fractura por una cinta cerrada de 68 km.
    Con el capex por km de OCP, un arenoducto Ibicuy–Añelo de 1.100 km costaría
    2.000 MUSD y daría 69 USD/t a 5 Mt, 62 a 8 Mt: repaga en 14 y 7 años.
    Con el capex por km del gasoducto, 4.400 MUSD y 93 USD/t, casi el camión.
    Pierde con el tren a 1.000 km; gana con arena a 100 km. Y la pulpa llega
    húmeda, que es lo que el Permian ya bombea sin secar y con menos polvo.

## Lo que hay que decir sí o sí

- El mapa señala dónde buscar, no si la arena sirve. No hay un solo ensayo de
  laboratorio argentino publicado como dato.
- Los pesos son una opinión declarada y están en un solo archivo.
- La red vial son rutas nacionales; las provinciales no están.
- El tránsito de 2017 incluye a todos los vehículos y ya tenía arena; la
  comparación es contra ese total. Toda la arena se supone por Entre Ríos,
  cuando es el 75 %: las pasadas reales por Puelches son algo menores.

## Lo que agregaron los comentarios (21/9/2026)

14. **El modelo cambió por los comentarios del post.** Tres cadenas nuevas:
    el tren a Palmira y camión a Neuquén, como el acuerdo de YPF con Trenes
    Argentinos Cargas de 2021 (84 USD/t, 124 kg CO2e/t, 10.000 t por mes);
    la arena de Río Negro desde Allen (33 USD/t, 120 km, la segunda más barata
    de las nueve); y la de Chubut desde Dolavon (68 USD/t, 855 km).
15. **La barcaza de río y la de mar no son el mismo equipo.** 1.500 toneladas
    contra 15.000 a 20.000 de una ATB: la animación ahora las distingue.
16. **El límite que más duele no es el costo, es la confiabilidad.** El modelo
    compara promedios; no tiene colas en los transbordos ni stock de
    seguridad. Declarado, con crédito a quien lo marcó.
17. **La física le da la razón al modelo en el arenoducto.** Con granos de 0,1
    a 0,6 mm hay que sostener de 3 a 5 m/s para que la pulpa no sedimente: la
    misma conclusión a la que el costo llegaba por otro lado.

18. **La confiabilidad no da vuelta el ranking, pero cambia dónde va la plata.**
    Con los tiempos simulados, las cadenas por agua necesitan unas 11.000
    toneladas de arena parada entre stock de seguridad y de ciclo, tres veces
    el camión directo, porque lo que llega junto es una barcaza de 15.000
    toneladas y no una camionada de 30. El costo de ese stock es de centavos
    por tonelada: el orden de las cadenas no se mueve porque la arena es
    barata.
19. **Conviene subir el nivel de servicio, no bajarlo.** De 95 a 99 % el costo
    total baja en todas las cadenas: el stock extra cuesta menos que las
    paradas que evita. Un día de flota de fractura parada equivale a 6.800
    toneladas de arena en cantera.

## Ángulos posibles

- El hueco del mapa: el Estado explora arena en una zona que su propio
  servicio geológico no tiene cartografiada en línea.
- El método que encuentra la arena mala: un mapa que "acierta" en Allen
  demuestra por qué el laboratorio es insustituible.
- La ruta de la arena y los médanos de La Pampa.
- La ruta paga el pozo: el costo que no está en los 97 dólares por tonelada.

## Links

- Repo: https://github.com/dpinero14/arena-lab
- Mapa interactivo: https://dpinero14.github.io/arena-lab/mapa_arena.html
- Ruta animada: https://dpinero14.github.io/arena-lab/ruta_animada.html
- Laboratorio: https://dpinero14.github.io/arena-lab/laboratorio_arena.html
