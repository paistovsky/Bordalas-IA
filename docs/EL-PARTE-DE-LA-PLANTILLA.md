# EL PARTE DE LA PLANTILLA

Cada dia a las 18:37 de Madrid, un veredicto por jugador para la proxima
jornada. Lo pidio el dueno el 24/10, despues de que Jonny no jugara en la
J10 y nos dejara un 0 sin recambio: «This analysis should be done daily on
each player». El dia mas reciente arriba; se guardan 14 dias.

Veredictos: TITULAR / DUDA / SUPLENTE (perdio el puesto) / LESIONADO /
SANCIONADO / DESCARTADO. «Perdio el puesto» solo con pruebas: dos
suplencias seguidas estando sano, o lo dice el entrenador.

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
