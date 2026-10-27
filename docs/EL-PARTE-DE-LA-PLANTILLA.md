# EL PARTE DE LA PLANTILLA

Cada dia a las 18:37 de Madrid, un veredicto por jugador para la proxima
jornada. Lo pidio el dueno el 24/10, despues de que Jonny no jugara en la
J10 y nos dejara un 0 sin recambio: «This analysis should be done daily on
each player». El dia mas reciente arriba; se guardan 14 dias.

Veredictos: TITULAR / DUDA / SUPLENTE (perdio el puesto) / LESIONADO /
SANCIONADO / DESCARTADO. «Perdio el puesto» solo con pruebas: dos
suplencias seguidas estando sano, o lo dice el entrenador.

## LA LISTA DE OBJETIVOS (25/10, del «mejor equipo posible»)

Libres que suben el once si el Computer los saca. Se miran CADA MANANA en
la supervision de las 08:22 (mercado del Computer del dia). Si sale uno: se
compara con el peor de su puesto, se escribe `fichar` + `vender_si_ficha`
(el que sale, con su propio `si_esta`, y solo cuando el nuevo ya es
nuestro), con un esceptico antes, y nunca una J que empiece en rojo. NO se
deja una orden esperando a un jugador que no esta en el mercado: la mejora
resta la puja entera si un dia lee el mercado vacio (la_mejora_del_once.py,
caja de la jornada) y puede entrar en modo deficit.

| Objetivo | Puesto | Precio 25/10 | Por quien | Puja | Nota |
|---|---|---|---|---|---|
| Adrian Nino (Malaga) | DEL | 2,93 M, +340 k/dia | Roberto Fernandez | +25-35 % (sube mucho; rivales +7/+41 %), tope 4,8 M | 2 titularidades, 4 goles en 6; el hueco entre los dos baja ~0,4 M al dia: es de esta semana |
| Juan Iglesias (Sevilla) | DEF | 3,62 M | Sergi Cardona | +8-10 % | 9 de 9 titular, FF 90 |
| Ndukwe (Levante) | DEF | 1,07 M | Sergi Cardona | +12 % | gano el puesto a Mandi |
| Remiro (Real Sociedad) | POR | 3,72 M | Gulacsi | +5-8 % | 6,0 pts/partido, 8 de 9 |
| Exposito (Espanyol) | MED | 4,47 M | el peor medio | +5-8 % | lo vendimos el 23/10 por Boye |
| Agoume (Sevilla) | MED | 3,36 M | el peor medio | +5-8 % | 9 de 9 titular |
| Ivan Martin (Racing) | MED | 2,76 M | el peor medio | +5-8 % | FF 90 |
| Zabiri (Racing) | DEL | 7,54 M | Roberto Fernandez | +10-20 % | solo en el parón (09-19/11), si no esta apercibido (4 amarillas) y la caja lo paga |

Ventanas de la J11 (vie 30/10 21:00): la mejora y la orden con venta
emparejada pujan hasta la vuelta del jue 04:50 (40 h). Despues, solo lo que
pague la caja entera.

## 27/10/2026, 19:15 de Madrid (J11: vie 30/10 21:00; cierre 20:45)

(La Copa no puntua para nosotros: solo se mira como pista de rotacion.)

| Jugador | Veredicto | J11 % | Copa (pista) | Cambio |
|---|---|---|---|---|
| Gulacsi (POR) | TITULAR | 88 | Manacor hoy 21:00, se espera a Luiz Junior | = |
| Kike Salas (DEF) | TITULAR | 86 | jue 29, FF le deja fuera | 80 -> 86 (FF J11 90) |
| Chust (DEF) | TITULAR | 92 | NO titular en Pinatar (confirmado): descansa | 90 -> 92 |
| Gaya (DEF) | TITULAR | 82 | mie 28, FF le deja fuera | 78 -> 82: FF le da por recuperado del golpe en la nariz; entrena normal |
| **Sergi Cardona (DEF)** | **DUDA** | **45** | **unico lateral izquierdo convocado para Manacor (21:00): casi seguro titular** | 55 -> 45 |
| Olasagasti (MED) | TITULAR | 85 | fuera de la convocatoria de Copa (descansa) | 80 -> 85 |
| Pablo Ibanez (MED) | TITULAR | 84 | mie 28, FF le deja fuera | = |
| Unai Lopez (MED) | TITULAR | 82 | Huelva hoy 21:00, convocado | = (Ciss sancionado en la J11) |
| Yamal (DEL) | TITULAR | 95 | exento | 92 -> 95 |
| Roberto Fernandez (DEL) | TITULAR | 89 | NO titular en Sestao (confirmado) | 87 -> 89 |
| Boye (DEL) | TITULAR | 87 | mie 28, FF le deja fuera | «pequena molestia» de un golpe, ya recuperado |

**Caja:** +1.418.975 (premio J10 cobrado: 39 pts), 0 pujas vivas; ningun motor
ha pujado.

**Hecho hoy:** nada (en el mercado de hoy no hay ningun defensa que pase el
liston: Lejeune deja la caja en rojo por +0,5 xP; De Haas FF 70).

**Plan:** 20:10, once de Manacor. Si Cardona es titular: J11 35-40 % y
mie 08:22-23:00 se busca relevo en el mercado de ese dia (TODOS los
defensas de la lista, no solo los nombrados: los candidatos con nombre casi
nunca salen): ok, 3+ partidos, FF J11 >= 80 en pagina «Posible alineacion
J11», sin jugar la Copa del mie, +1 pt sobre Cardona y caja >= 0 (puja
maxima ~2,82 M con el suelo de Cardona en 1,40 M). Ultimo recurso De Haas
(FF 70) si sigue. Si es suplente o no juega: 65-70 % y Cardona se queda.
Antes de escribir, mirar que la mejora no haya pujado ya por un defensa.
Jue 08:22: limpieza de la orden.

## 26/10/2026, 19:30 de Madrid (J11: vie 30/10 21:00; cierre 20:45)

| Jugador | Veredicto | J11 % | J11 (Madrid) | Copa | Cambio |
|---|---|---|---|---|---|
| Gulacsi (POR, Villarreal) | TITULAR | 88 | Villarreal-Espanyol, vie 30/10 21:00 | descansa (Luiz Junior en Manacor) | = |
| Kike Salas (DEF, Sevilla) | TITULAR | 80 | Getafe-Sevilla, dom 01/11 14:00 | jue 29 (Hortaleza), FF le deja fuera | J10 hoy 21:00 |
| Chust (DEF, Elche) | TITULAR | 90 | Elche-Valencia, dom 01/11 18:30 | descansa | = |
| Gaya (DEF, Valencia) | TITULAR | 78 | Elche-Valencia, dom 01/11 18:30 | descansa (mie 28) | golpe en la nariz (codazo de Gueye), pruebas por posible fractura; entreno sin limites; como mucho, mascara |
| **Sergi Cardona (DEF, Villarreal)** | **DUDA** | **55** | Villarreal-Espanyol, vie 30/10 21:00 | **FF le pone titular en Manacor (mar 27, 21:00)** | 60 -> 55. Romero no viaja a la Copa y vuelve «con cautela»; Akhomach tocado |
| Jonny (DEF, Alaves) | DUDA | 40 | Barcelona-Alaves, sab 31/10 21:00 | | se vende esta noche (00:07) |
| Olasagasti (MED, Levante) | TITULAR | 80 | Levante-Atletico, sab 31/10 14:00 | descansa (mie 28) | 78 -> 80 |
| Pablo Ibanez (MED, Alaves) | TITULAR | 84 | Barcelona-Alaves, sab 31/10 21:00 | descansa | 82 -> 84 |
| Unai Lopez (MED, Rayo) | TITULAR | 82 | Rayo-Celta, sab 31/10 16:15 | descansa (mar 27, Huelva) | 78 -> 82 (Ciss sancionado) |
| Yamal (DEL, Barcelona) | TITULAR | 92 | Barcelona-Alaves, sab 31/10 21:00 | exento | J10: 3 pts, sin golpes |
| Roberto Fernandez (DEL, Espanyol) | TITULAR | 87 | Villarreal-Espanyol, vie 30/10 21:00 | FF le hace descansar (mar 27, Sestao) | riesgo de cambio de entrenador |
| Boye (DEL, Alaves) | TITULAR | 88 | Barcelona-Alaves, sab 31/10 21:00 | descansa | = |

**J10:** 39 puntos (Yamal 3).

**En riesgo para la J11:** Sergi Cardona (55 %). La senal decisiva es el
once de Copa del mar 27 a las ~20:00: si es titular en Manacor, baja a
35-40 % y se aplica la regla del mie; si no juega o sale suplente, sube a
65-70 %.

**Hecho hoy:** nada (en el mercado del Computer no hay ningun defensa mejor
que Cardona para la J11; Pablo Ramon apercibido, Zaid Romero en duda).

**Correcciones del esceptico (importantes):**
- **Contingencia de Kike (lun 23:05):** si se lesiona o le expulsan, NO
  vaciar `vender_si_ficha.jugadores` (la mejora perderia de golpe 1,53 M de
  caja pendiente y podria entrar en deficit). En su lugar, frenar la venta
  con `"desde": "2026-10-28T18:00:00+01:00"` en la fila de Jonny y decidir
  el mie.
- **Mar 08:22:** comprobar que Jonny se vendio (~+248.975) y que el once
  guardado en Biwenger tiene 11 con Cardona (el de ahora tiene a Jonny y no
  a Cardona: tras la venta quedaria con 10 si nadie lo reescribe).
- **Mar tarde, al cobrar el premio de la J10 (~1,17 M):** vigilar que el
  motor viejo (TABLERO) o el carril no se gasten la caja que hace falta para
  el cambio de Cardona.
- **Mie 18:00-23:00:** si Cardona <= 40 % y ningun motor ha pujado ya por
  su relevo: fichar un defensa del mercado de ese dia (ok, FF J11 >= 80 en
  una pagina «Posible alineacion J11», sin jugar la Copa del mie), puja
  +10-15 %, con Cardona en vender_si_ficha con su propio si_esta (quitando
  antes la fila de Jonny y el si_esta 28115). Candidatos: Sangare, Tarrega,
  Marcos Alonso, Sergio Gomez. Si no hay ninguno, Cardona se queda.

## 25/10/2026, 19:30 de Madrid (J11: vie 30/10 21:00; cierre 20:45)

| Jugador | Veredicto | J11 % | J11 (Madrid) | J10 | Cambio |
|---|---|---|---|---|---|
| Gulacsi (POR, Villarreal) | TITULAR | 88 | Villarreal-Espanyol, vie 30/10 21:00 | 90', 3 pts | 85 -> 88 (FF J11 90) |
| Kike Salas (DEF, Sevilla) | TITULAR | 80 | Getafe-Sevilla, dom 01/11 14:00 | lun 26/10 21:00 vs Osasuna | nuestro desde el 25/10; FF aun en la J10 |
| Chust (DEF, Elche) | TITULAR | 90 | Elche-Valencia, dom 01/11 18:30 | 90', 4 pts | = (FF J11 90) |
| Gaya (DEF, Valencia) | TITULAR | 78 | Elche-Valencia, dom 01/11 18:30 | 90', 4 pts (codazo de Gueye, sano) | 75 -> 78 |
| **Sergi Cardona (DEF, Villarreal)** | **DUDA** | **60** | Villarreal-Espanyol, vie 30/10 21:00 | **entro 65', asistencia, 8 pts** | 35 -> 60: FF J11 50 (con Carlos Romero, en duda por el aductor), JP titular; el entrenador: «gestionar» la carga, no perdio el puesto |
| Jonny (DEF, Alaves) | DUDA | 40 | Barcelona-Alaves, sab 31/10 21:00 | suplente sin jugar, 0 | se vende el mar 00:07 |
| Olasagasti (MED, Levante) | TITULAR | 78 | Levante-Atletico, sab 31/10 14:00 | titular hoy en Anoeta (en juego) | 75 -> 78 |
| Pablo Ibanez (MED, Alaves) | TITULAR | 82 | Barcelona-Alaves, sab 31/10 21:00 | 90', 4 pts | 85 -> 82 |
| Unai Lopez (MED, Rayo) | TITULAR | 78 | Rayo-Celta, sab 31/10 16:15 | 90', 5 pts | 82 -> 78 (FF 70, JP fijo) |
| Yamal (DEL, Barcelona) | TITULAR | 90 | Barcelona-Alaves, sab 31/10 21:00 | Clasico hoy 21:00 | = |
| Roberto Fernandez (DEL, Espanyol) | TITULAR | 88 | Villarreal-Espanyol, vie 30/10 21:00 | 90', 2 pts | = (riesgo de cambio de entrenador) |
| Boye (DEL, Alaves) | TITULAR | 88 | Barcelona-Alaves, sab 31/10 21:00 | 90', 3 pts, amarilla | = |

**J10:** 33 puntos con 9 de 11 jugados (Olasagasti y Yamal, hoy).

**En riesgo para la J11:** Sergi Cardona (60 %). Ayer el 0 % era la
alineacion CONFIRMADA de la J10, no un pronostico (el fallo que corrige
BORDALAS_LA_JORNADA_DE_CADA_PAGINA, que se enciende el lun 26/10).

**Hecho hoy:** nada. Opcion vista y descartada: Drkusic (Espanyol, 0,70 M,
FF J11 70 %, juega el MISMO partido que Cardona, el primero de la J11, cuyos
onces salen antes de nuestro cierre) como 12.o a 735.000. Gana ~+0,5 pts en
la J11 solo si alguien cambia a mano el once el vie entre las 20:00 y las
20:40; la caja del vie quedaria en ~+0,5 M (justo en la regla del 24/10) y
la orden se complicaria (si_esta, limpiezas). Con el beneficio tan pequeno,
no se hace.

**Plan:** lun 23:05, Kike Salas tras Sevilla-Osasuna (antes de vender a
Jonny a las 00:07). Mar: Jonny vendido y su fila fuera de la orden; onces de
Copa (Manacor-Villarreal 21:00: si Cardona es titular, baja para la J11).
**Mie 28, 18:00-23:00:** si Cardona <= 40 % y la mejora no ha pujado ya por
un defensa, fichar uno titular seguro del mercado de ese dia con venta
emparejada de Cardona (con su propio si_esta).

## 24/10/2026, 19:30 de Madrid (J11: vie 30/10 21:00; cierre 20:45)

| Jugador | Veredicto | J11 % | J11 (Madrid) | J10 | Nota |
|---|---|---|---|---|---|
| Gulacsi (POR, Villarreal) | TITULAR | 85 | Villarreal-Espanyol, vie 30/10 21:00 | titular en Mestalla (en juego) | Copa (mar 27, Manacor) la juega el suplente |
| Chust (DEF, Elche) | TITULAR | 90 | Elche-Valencia, dom 01/11 18:30 | 90', 4 pts | Copa mar 27 ante un Preferente |
| Gaya (DEF, Valencia) | TITULAR | 75 | Elche-Valencia, dom 01/11 18:30 | titular (en juego) | riesgo de lesion «elevado» (FF); Copa mie 28 |
| Jonny (DEF, Alaves) | DUDA | 40 | Barcelona-Alaves, sab 31/10 21:00 | suplente sin jugar, 0 | decision tecnica; Valentini 5 titularidades. Cubierto por la orden de Kike Salas |
| **Sergi Cardona (DEF, Villarreal)** | **DUDA** | **35** | Villarreal-Espanyol, vie 30/10 21:00 | **suplente en Mestalla** (FF 0 %, Buchanan 100 %) | sano; carga de partidos (4 seguidos) y vuelta de Carlos Romero a final de mes. Una suplencia: no es «perdio el puesto» |
| Olasagasti (MED, Levante) | TITULAR | 75 | Levante-Atletico, sab 31/10 14:00 | dom 25/10 18:30 | Copa mie 28 (Tarancon); ya fue suplente en la J9 |
| Pablo Ibanez (MED, Alaves) | TITULAR | 85 | Barcelona-Alaves, sab 31/10 21:00 | 90', 4 pts | |
| Unai Lopez (MED, Rayo) | TITULAR | 82 | Rayo-Celta, sab 31/10 16:15 | 90', 5 pts | Copa en Huelva (mar 27 o mie 28) |
| Yamal (DEL, Barcelona) | TITULAR | 90 | Barcelona-Alaves, sab 31/10 21:00 | dom 25/10 21:00 (Clasico) | sin Copa (exento) |
| Roberto Fernandez (DEL, Espanyol) | TITULAR | 87 | Villarreal-Espanyol, vie 30/10 21:00 | 90', 2 pts (Racing 2-1) | Copa mar 27 (Sestao) |
| Boye (DEL, Alaves) | TITULAR | 88 | Barcelona-Alaves, sab 31/10 21:00 | 90', 3 pts, amarilla | |
| Kike Salas (DEF, Sevilla; puja viva) | TITULAR | 80 | Getafe-Sevilla, dom 01/11 14:00 | lun 26/10 21:00 | Copa jue 29 (Hortaleza): tres partidos en siete dias |

**En riesgo para la J11:** Jonny (cubierto por la orden de Kike Salas) y
Sergi Cardona. Para Cardona, hoy no hay recambio en el mercado del Computer
(solo Lago, con 4 amarillas y por jugar la J10, y dos que no juegan).

**Hecho hoy:** nada en la orden ni en las correcciones (el esceptico tumbo
todas las lineas: bajar de escalon a Cardona o a Jonny, vetar a Lago, un
fichar sin candidato y un vender_si_ficha de Cardona que repetiria el error
del 20/10).

**Plan:**
- Dom 25 desde las 07:15: mirar si la mejora puja sola por un defensa para
  tapar a Cardona (FF ya le da 0 %: lo lee como hueco). Si el objetivo es
  titular seguro en la J11 (FF >= 70 %, ok), dejarla; si no, `no_pujar`.
- Dom 25 si se pierde a Kike: cambiar de objetivo; el relevo vende al peor
  de Jonny y Cardona (sin el si_esta 28115 arriba).
- Mar 27 tarde (premio de la J10): caja menos pujas vivas >= 0.
- **Mie 28, 18:00-23:00 (decision):** con el once de la Copa (mar 27,
  Manacor) y las noticias de Carlos Romero, si Cardona sigue <= 40 % y ni la
  mejora ni la rotacion han actuado: fichar un defensa titular seguro
  (Sangare, Ndukwe, Javi Rodriguez, Puga, De Haas, Sarr) con vender_si_ficha
  de Cardona con su propio si_esta. Ultima vuelta que puja: jue 04:50.
- Vie 30, 20:00-20:40: el once del Villarreal sale antes de nuestro cierre.

**Fallo de Pepe visto:** el tablero de FF no comprueba la jornada de cada
pagina de equipo: hoy mezcla porcentajes de la J10 confirmada (Cardona 0 %,
Chust 100 %) con previsiones de la J11 (Jonny 50 %).
