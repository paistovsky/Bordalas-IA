# El carril con bolsillo propio: 3 M en euros, y por fin compra

**12/09/2026** · verja 112/112 · sin push

---

# VIAJES COMPLETADOS: 0

---

## Lo que queda puesto

| | |
|---|---|
| `CARRIL_TOPE_POR_OPERACION` | **3.000.000**, en euros, propio |
| Cupo por ciclo de reset | **1** (`PRUEBA_DE_HUMO`) |
| Suelo | **1.000.000** (`NORMAL`) — devuelto |
| Vía vieja de especular | **en pausa** |
| `MAX_SINGLE_SPECULATION_PERCENT` · `MAX_SAFE_DEBT` | **sin tocar** |

El 400.000 no se borra: queda escrito como `SUELO_RETIRADO_DE_LA_PRUEBA`, con el
porqué. El número se probó, se midió y se retiró por una razón, y la razón vale
más que el número.

**Y confirmo tu dato:** el +3,46 % del tramo 1–3 M ya estaba medido en la casa,
sobre las mismas 34 recompras, junto a `<1 M +1,52 %`, `3–6 M +3,20 %` y
`6 M+ +3,83 %`. No he inventado nada para justificar los 3 M.

---

## 1. ¿Rompe 3 M alguna barandilla? **No, y por construcción**

Medido contra el motor de solvencia con el saldo real de hoy:

| | saldo | riesgo | negativo | bloqueado |
|---|---|---|---|---|
| hoy | 4.333.406 | BAJO | no | no |
| tras pagar un viaje de 3.000.000 | **1.333.406** | **BAJO** | no | no |
| + la caída del 8 % en cuatro resets | **1.093.406** | **BAJO** | no | no |

El primer ámbar (`CONTROLAR`) está en **saldo 0**; el rojo, en negativo. Después
del peor caso quedan **1.093.406 € de margen** hasta el primer ámbar. Y la
jornada que viene sólo **entra** dinero (30.000 €/punto): no hay salida programada
que pueda cruzarse.

**Pero no te lo doy como «los números salen», sino como una propiedad:**
`bolsillo_del_carril()` devuelve `min(3.000.000, caja libre)`. El carril **no abre
deuda para especular**, así que no puede comprometer dinero que no hay — sea cual
sea la caja de ese día. Hay guardia que lo prueba para cinco cajas distintas.

### Un hueco que cerré por el camino

El motor de especular ya descuenta de **su** presupuesto las pujas vivas del
carril. **Al revés no pasaba.** El carril podía apartar 3 M sobre una caja de la
que la ruta normal ya hubiera reservado otro tanto — y las dos pujas se resuelven
en el **mismo reset**. Ahora `comprometido` se resta antes de nada: *tener
bolsillo propio no es tener dinero propio*.

---

## 2. El tope al elegir, probado con guardia

`test_el_bolsillo_propio_manda_al_elegir`, con los tres del mercado real:

```
sin filtrar   el orden elige a CANCELO, 5.970.000   -> tope 3.000.000, no cabe
con filtro    elige a TRENT, 2.760.000              -> se puede pagar
sin caja      no cabe nadie, aunque haya candidatos
```

### Y una corrección a lo que te dije esta mañana

Escribí que *«el orden prefiere a los caros»*. **No es cierto, y lo compruebo
ahora:** el orden **no mira el precio** — va por prima de posición, defensas
primero. Lo que pasó el 12/09 es que el primero de la lista, Cancelo, era defensa
**y** costaba 5,97 M. El fallo es el mismo —el orden no sabe nada del tope— pero
el mecanismo no era el que conté. Corregido en el código, en los comentarios y en
la guardia, que ahora usa a Cancelo y no a un delantero caro.

---

## 3. La tabla final, mercado de hoy

```
suelo 1.000.000 NORMAL · cupo 1 PRUEBA_DE_HUMO
bolsillo 3.000.000 (CARRIL_TOPE_POR_OPERACION) · comprometido 0
9 sobre el suelo -> 8 entran por margen -> 4 SE PUEDEN PAGAR
```

| | pos | precio | margen | pujaría | ritmo |
|---|---|---|---|---|---|
| **Trent** | DEF | 2.760.000 | **+3,67 %** | 2.760.000 | supuesto |
| **Rubén García** | MED | 2.680.000 | +2,85 % | 2.680.000 | supuesto |
| Isaac Romero | DEL | 2.350.000 | +1,80 % | 2.350.000 | supuesto |
| Maguette Gueye | MED | 1.730.000 | +1,35 % | 1.730.000 | **medido** |

**No caben:** Cancelo 5.970.000 · Parrott 6.450.000 · Larrubia 4.790.000 ·
Hjulmand 4.650.000.

```
ENTRA POR CUPO:  Trent (DEF, 2.760.000)
COMPROMETE:      2.760.000   de un tope de 3.000.000
```

**Dos avisos sobre esta tabla, que no me los callo:**

1. Mis márgenes salen **0,29 pp por encima** de los tuyos (Trent +3,67 vs +3,38).
   La diferencia es exacta y es la prima de puja: tú asumiste curva 1,0029 y **la
   curva calibrada en vivo hoy es 1,0000**. No es discrepancia de modelo.
2. **Tres de los cuatro usan el ritmo SUPUESTO** (+0,00 %/día, el mediano del
   mercado), no medido. El único con ritmo real es Maguette Gueye, que es el de
   peor margen. El margen de Trent descansa en suponer que su precio no se mueve;
   si cayera como Starfelt, su margen real sería del orden de +1,6 %.

Y una nota de modelo: el +3,46 % que citas es la prima del **tramo**; el modelo
publica la de la **posición** (+3,67 % para Trent). Son dos particiones de las
mismas 34 recompras y aquí coinciden de cerca, así que no he cambiado el
estimador — eso sería una decisión tuya, no un arreglo.

---

## Guardias

`test_la_rendija_v1` — **40/40** (eran 27 esta mañana). Las cuatro nuevas:

- el bolsillo es propio, en euros, y **mayor que el suelo** — si alguna vez
  volviera a ser menor, el carril no podría comprar nada y esto se pone rojo
- el bolsillo no puede gastar lo que no hay: acotado por la caja, por lo ya
  comprometido, y **sin caja no se puja** (dos casos, dos nombres:
  `CAJA_DESCONOCIDA` y `SIN_CAJA_LIBRE`)
- **el tope manda al elegir**, con el caso de Cancelo
- un viaje de 3 M no rompe la solvencia, y `tope <= caja` para cinco cajas

Y las que probaban el suelo de 400.000 están reescritas, no parcheadas.

---

## Estado

- Verja: **112/112**
- Suelo **1.000.000** · cupo **1** · bolsillo **3.000.000** · vía vieja **en pausa**
- Pantalla construida y desplegada: enseña el bolsillo, qué lo limita, y quién no
  cabe por el tope
- Rama `main`, **sin push**

---

# VIAJES COMPLETADOS: 0
