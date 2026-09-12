# ¿Está enchufado? Sí. ¿Pujará mañana? No — y ya sé por qué

**12/09/2026** · verja 112/112 · sin push

---

## La respuesta directa

**SÍ, está enchufado.** Camino verificado de punta a punta:

```
bordalas-live.yml            python -m src.v10_full_autonomous_live
  __main__  ->  main()  ->  run_full_autonomous_cycle()     (línea 849)
                              _correr_el_carril(cycle, action_taken)   (1031)
                                carril_executor.correr(...)
                                  la_rendija.permiso(disparo=...)
                                    write_client.place_bid
```

**Y el disparo de las 04:50 pasa la zona de silencio.** Comprobado contra los runs
reales, no deducido:

```
#1507  12/09 04:45 Madrid   event=workflow_dispatch
#1508  12/09 04:50 Madrid   event=workflow_dispatch
#1510  12/09 07:44 Madrid   event=schedule
```

`workflow_dispatch` está en `DISPAROS_DELIBERADOS`, así que la zona lo deja pasar.
El `schedule` de las 07:44 no pasaría, y así debe ser.

## Pero NO pujará, y esta vez no es un cable suelto

Seguí el hilo hasta el final en vez de dar por bueno el enchufe, y hay dos puertas
más abajo:

### Tercera: el tablero da importe cero

```
objetivos: 59 · con importe de puja: 0
Fermín   14.510.000   bid 0   RENDIMIENTO_INSUFICIENTE
Cancelo   6.260.000   bid 0   RENDIMIENTO_INSUFICIENTE
```

`RENDIMIENTO_MINIMO_DEL_CAPITAL` — la compuerta que exige que la operación rinda un
mínimo **sobre el capital inmovilizado**. El carril le pedía el importe a una pieza
que decide con el criterio que el carril **no usa**: su negocio es el *spread*, no
el rendimiento.

Arreglado: el carril calcula su propio importe, `precio × curva`, que es literalmente
«el importe que dice la curva».

### Cuarta, y es estructural: los topes se contradicen

```
presupuesto de especulación     2.080.300
MAX_SINGLE_SPECULATION_PERCENT        40 %
tope por operación                832.120

suelo del carril                1.000.000   (por debajo no paga la ficha)
```

**El carril mira jugadores de 1 M para arriba y nunca puede pujar más de 832.120.**
Las dos condiciones son incompatibles: **tal como está configurado, no puede comprar
nada, nunca.**

Para que entrara el más barato de hoy (Pablo Martínez, 1.230.000) el presupuesto de
especulación tendría que ser **≥ 3.083.610**.

**No lo he tocado.** Dijiste «ningún umbral se mueve» y éste es uno de los que
nombraste expresamente. Son tres caminos y los tres son decisión tuya: subir el
presupuesto de especulación, subir `MAX_SINGLE_SPECULATION_PERCENT`, o bajar el
suelo de 1 M aceptando que esas operaciones no pagan la ficha.

---

## Las dos guardias

### `test_el_carril_esta_enchufado` — y las demás piezas

Recorre el **árbol de importaciones**, no un `grep` (que diría que sí por un
comentario). Resultado sobre las seis piezas armadas:

| | |
|---|---|
| la rendija · el carril | ✓ ahora sí |
| la renovación | ✓ |
| la salida del viaje | ✓ |
| el escaparate | ✓ |
| la subasta | ✓ |

**Ninguna otra estaba desenchufada.** Era sólo el carril.

Lleva su propia red: `test_el_buscador_de_caminos_no_miente` le pregunta por algo
que sí está y por algo que no existe, porque un buscador que dice «sí» a todo no
comprueba nada.

### El indicador lo enciende el hecho

`ran_at` viaja en **todas** las salidas del carril —incluida la de bloqueado y la de
error—, y el panel lee eso, no la bandera:

```
CERRADA            se apagó sola
NUNCA HA CORRIDO   armado y publicado, y ningún ciclo lo ha ejecutado
EN VIVO            corrió · con la hora de la última vuelta y qué decidió
```

Y cuando no ha corrido nunca sale un aviso amarillo que lo dice con esas palabras.
**Doctrina 37**, con el reverso escrito: *lo que se arma, se enchufa; armar algo y
no conectarlo es peor que no armarlo, porque la pantalla dice que funciona.*

---

## Fortuño y Diego Conde: no fue la barandilla de portero

Lo comprobé y me equivoqué ayer al suponerlo. La barandilla de portero **no estaba
disparada**: el suelo son 2 porteros y ya teníamos 2 antes de comprar. Fueron
**dos compras de la vía de especular**, que no tiene suelo de 1 M — ese suelo es
**sólo del carril**.

O sea: la vía vieja compró exactamente lo que el carril tiene prohibido comprar,
por la razón que medimos (+1,52 % sobre 150.000 son 2.250 €, que no pagan la
ficha). Dos rutas con dos criterios distintos sobre el mismo mercado.

**No lo he cambiado** —la vía de especular es otra cosa y tiene sus propias
guardias— pero queda dicho, porque si el carril no puede comprar y la vía vieja
compra a 150 k, el experimento que estamos corriendo no es el que creemos.

---

## Estado

- Verja: **112/112**
- El carril: **enchufado**, correrá a las 04:50, y **no pujará** hasta que decidas
  sobre los topes
- Rama `main`, **sin push**
