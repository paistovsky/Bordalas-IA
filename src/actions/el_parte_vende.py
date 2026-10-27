"""
EL PARTE VENDE (17/10/2026; arreglado el 21/10/2026, dos veces, y el
27/10/2026)

POR QUE EXISTE

    Paso 4 del laboratorio (verificado el 17/10): cuando Biwenger pasa a
    un jugador de 'ok' a 'doubt' o 'injured', su precio cae. Rentabilidad
    anormal a 3 dias (AR3) -3,4 % (n = 105 cambios de estado en 11 dias,
    lo mismo en las dos mitades); a 7 dias (AR7) -4,7 % (n = 54). Muestra
    pequeña: confianza MEDIA.

    Hasta hoy nadie vende por el parte: el de la plantilla que cae en
    duda o lesionado y no juega se queda en el banquillo perdiendo
    valor, salvo que el cierre de la jornada lo necesite para la caja.

    Ojo con lo que compra el suelo: aceptar al 95 % de su valor es ceder
    hoy lo que de media se pierde en una semana (-4,7 %). Lo que se gana
    es cualquier oferta por encima del suelo, no esperar a que caiga, y
    la caja libre para la ronda y la mejora.

LA REGLA

    1. A QUIEN. De la plantilla de la foto (`my_team`), los que el
       catalogo de la foto (`la_orden_del_gestor.leer_los_estados`) da
       en 'doubt' o 'injured' (`MALOS`). Nunca:
         - a uno del ONCE ESCRITO: el del panel (`status.lineup.players`,
           la misma fuente que `el_cierre_de_la_jornada`) y la alineacion
           vigente en Biwenger de la foto (`user_lineup.data.lineup
           .players`). Hacen falta LOS DOS: sin el del panel no se sabe
           quien es titular (`SIN_ONCE_ESCRITO`), sin el de Biwenger no
           se sabe quien sigue puesto (`SIN_ONCE_DE_BIWENGER`), y en los
           dos casos NO SE HACE NADA y la salida lo dice;
         - a un sancionado ('sanctioned'): se mira y no se toca
           (`SANCION`);
         - a un FICHAJE que todavia no ha jugado una ronda con
           nosotros: hasta que ACABA la primera ronda que EMPEZO
           despues de su llegada, y nunca antes de `DIAS_DE_FICHAJE`
           (7) dias (`RECIEN_FICHADO` los 7 dias,
           `SIN_JUGAR_CON_NOSOTROS` despues); ni a uno del que no se
           sepa desde cuando es nuestro (`SIN_FECHA_DE_FICHAJE`) o
           cuando juega su primera ronda (`SIN_RONDA_TRAS_EL_FICHAJE`);
         - a Yamal, por su nombre, siempre (este como este la orden).
           Sin nombre no se vende: no se sabria si es el;
         - a un protegido del gestor (`la_orden_del_gestor.protegidos`:
           `proteger` y `fichar`) ni a uno de `conservar`
           (`la_orden_del_gestor.conservados`);
         - a uno que vende LA ORDEN (`vender_si_ficha.jugadores` y
           `viajes.candidatos`): lo vende ella, cuando su relevo y su
           suelo (o el del viaje) lo digan (`LA_ORDEN`, desde el
           27/10/2026: ver F1 y LOS VIAJES);
         - a lo que aguanta LA CARTERA de la ronda
           (`la_ronda_de_la_manana.los_que_aguanta`): tiene su propia
           salida;
         - a lo que esta vuelta ya vendio (el estado de v10, la vuelta
           de la mejora y el plan del cierre, solo si son de ESTA
           vuelta, como los cuenta el cierre).
    2. QUE. Si la oferta viva del Computer llega al `SUELO` (95 %) de su
       valor de hoy (el `price` de la foto), ACEPTAR_OFERTA_DEL_COMPUTER.
       Si no, y no esta publicado (ni en la foto ni en esta vuelta),
       PONER_A_LA_VENTA a su valor: no saca a nadie del once y hace
       nacer la oferta del proximo reset. Publicado y sin oferta que
       llegue, NADA (con el motivo). Una escritura por jugador y vuelta.
    3. CUANDO. Nunca con una ronda jugandose
       (`la_proxima_jornada.jornada_en_curso`, como la ronda de la
       mañana): en esta liga el once no se cambia empezada la ronda, y
       vender a uno del once cerrado pierde sus puntos. Ni en la zona de
       silencio, ni sin calendario (`SIN_CALENDARIO`), ni sin la orden
       del gestor encendida y valida (`ORDEN_APAGADA`, `ORDEN_NO_VALIDA`,
       desde el 27/10/2026: ver F2). En esos casos no se escribe nada,
       tampoco se publica.

LOS TRES ARREGLOS (21/10/2026)

    La revision del laboratorio del 21/10 reprodujo tres fallos.

    1. EL FICHAJE NO SE REVENDE ANTES DE JUGAR. Regla de la casa (E14,
       02/10): «un fichaje para el once no se revende antes de jugar con
       nosotros, salvo lesion larga» (cuatro vendidos en el paron sin
       jugar: -3,3 M y cero puntos; la ida y vuelta cuesta un 10-20 %).
       Nada protegia al recien llegado: la puja del dueño por Gaya (1844)
       se resuelve el 22/10 a las 05:00 UTC; si llega en duda y los once
       sanos lo dejan fuera del once, el parte lo publicaba el jueves y
       lo vendia el viernes, antes de la J10, deshaciendo la compra.
       Ahora no se toca a quien es nuestro desde hace menos de 7 dias
       (y, desde la segunda revision, hasta que juega una ronda: ver
       H1 mas abajo). La salvedad de la lesion larga NO se aplica: el
       catalogo no dice cuanto dura; si hace falta, lo vende el dueño
       a mano.

       DE DONDE SALE LA FECHA: del tablon de la liga (`TABLON`,
       `data/rival_intelligence/board_events.json`), que el paso V10
       del workflow pide en cada vuelta ANTES del parte
       (`collect_board_history`) y que se guarda como libro. Es lo que
       publica Biwenger: una subasta ganada es un evento 'market' con
       `content[].to.id` = nosotros; una compra a un manager, un
       'transfer' con `to.id` = nosotros. Medido el 21/10 sobre el
       tablon de verdad: Sergi Cardona (30493), 'market' del 17/10 a
       las 05:05:38 UTC por 919.000; Luismi Cruz (25777), 'market' del
       14/10 a las 05:03:03 UTC por 3.252.000; estan los diez fichajes
       que siguen en la plantilla. El libro de posiciones
       (`data/trading/position_ledger.json`) tambien trae a los dos,
       pero con la hora a la que los VIO (14 minutos despues), no trae
       a Yamal (26271) y da por perdido a 19862, que sigue siendo
       nuestro: no sirve de fuente.

       QUIEN NO TIENE COMPRA EN EL TABLON es del reparto del dia 1 (el
       `leagueReset` del 09/08)... o un fichaje que el fichero todavia
       no trae (si la peticion de esta vuelta fallo, es el de la
       anterior). Se le da por nuestro DESDE EL RESET solo si (a) el
       tablon empieza en el reset, (b) el jugador no se ha movido nunca
       desde entonces y (c) el tablon esta AL DIA: trae el evento
       'market' (las subastas) del ultimo reset del Computer, que se
       lee de la foto (`el_ultimo_reset`: el `until` de sus ventas
       menos 24 h, `market_clock`), o, desde la segunda revision, un
       movimiento de 2 h despues de ese reset (H2). Si lo ultimo que
       dice el tablon de un jugador nuestro es que se fue o que lo
       compro otro, el tablon va por detras. En todos esos casos, y si
       el tablon no se puede leer: sin fecha, y no se vende
       (`SIN_FECHA_DE_FICHAJE`). Y si el tablon no esta al dia, desde
       la segunda revision no tiene fecha NADIE (H2). Se falla del
       lado seguro. Lo que queda sin cubrir: una compra a un manager
       hecha despues de la ultima peticion buena, de uno que ese
       manager tenia del reparto, pasaria por nuestra desde el reset
       (tiene que fallar la peticion de esta vuelta, y compras entre
       managers hemos hecho una en 73 dias).

    2. LOS DOS ONCES. El once del panel ya deja fuera a los titulares
       lesionados y sancionados (es el once que se quiere poner); el de
       Biwenger es el que esta puesto. Antes bastaba el del panel, y
       `league_collector` deja `user_lineup` en None si `GET /user`
       falla: sin la mitad de Biwenger, el titular en duda que el panel
       ya habia quitado se podia vender. Ahora sin uno de los dos no se
       hace nada (`SIN_ONCE_DE_BIWENGER`).

    3. EL SANCIONADO NO SE VENDE. La regla del dueño lo nombraba
       ('sanctioned' estaba en `MALOS`), pero una sancion suele ser de
       un partido y el laboratorio solo midio 'doubt' e 'injured' (AR3
       -3,4 %, AR7 -4,7 %): al titular que se pierde una jornada por
       tarjetas se le vendia para siempre por una caida que nadie ha
       medido. Sale en `malos` (se miro) y en `no_se_tocan` (`SANCION`).

LA SEGUNDA REVISION (21/10/2026)

    La revision de esos arreglos reprodujo dos fallos mas, con el
    calendario y el tablon de verdad.

    H1. SIETE DIAS NO SON JUGAR. E14 dice «antes de jugar con
        nosotros», no «antes de una semana», y los cuatro de -3,3 M se
        vendieron EN UN PARON. Con el reloj de 7 dias, un fichaje del
        10/11 (la J12 acaba el 08/11 y la J13 no se juega hasta el
        22/11) en duda y fuera del once se vendia el 17/11 sin haber
        jugado; uno del 22/12 (la J17 acaba el 20/12, la J18 es el
        03/01), el 29/12. Ahora no se toca a un fichaje hasta que
        ACABA (su `fin` mas `MARGEN_FINAL`, las 3 h de
        `la_proxima_jornada.jornada_en_curso`) la primera ronda de
        `las_rondas` que EMPEZO despues de su llegada: la primera en la
        que pudo estar en nuestro once (en esta liga el once se cierra
        al empezar la ronda). Y nunca antes de los 7 dias. `correr` le
        pasa a `decidir` las rondas del mismo calendario con el que
        mira si hay una ronda jugandose; la cuenta la hace
        `hasta_cuando_no_se_toca`, pura.

        - Cuenta una ronda de verdad: la ventana principal de su
          jornada (`aparte` False) con al menos `PARTIDOS_DE_RONDA` (5)
          partidos. Un adelantado o un aplazado suelto no: en el
          adelantado de la J6 (Real Sociedad-Celta, jueves 03/09)
          jugaban dos equipos de veinte, y el calendario de hoy guarda
          de la J6 solo el Levante-Athletic del 21/10 (sale como su
          ventana principal, con un partido). Con ellos se daria por
          jugada una ronda en la que su equipo, casi seguro, no jugo; y
          si cae en un paron, es venderlo sin jugar.
        - Sin ninguna ronda que empiece despues de su llegada (el
          calendario no la trae, o no llegan las rondas), no se sabe
          cuando juega: no se vende (`SIN_RONDA_TRAS_EL_FICHAJE`). Sin
          calendario el parte ya no hacia nada (`SIN_CALENDARIO`).
        - Al del reparto y al que llego antes de una ronda que ya acabo
          no les cambia nada, si el calendario guarda esa ronda: el de
          produccion guarda las ultimas jugadas (el del 19/10 traia la
          J8 y la J9, no la J7). Si algun dia solo trajera las por
          jugar, esperarian a que acabe la proxima: del lado seguro.

        LO QUE EL CALENDARIO NO VE. Quien jugo de verdad. Al fichaje que
        llego antes del cierre de una ronda y se quedo fuera de nuestro
        once se le da por jugada: Gaya, si llega el 22/10 a las 05:00
        UTC en duda y no entra en el once de la J10 (23-26/10), se
        puede vender desde el 29/10 a las 05:00 UTC (los 7 dias). Para
        no darsela haria falta el once de cada ronda, y el libro que lo
        guarda (`data/intelligence/onces_de_la_jornada.jsonl`) tiene
        una (la J9). El que llega CON la ronda empezada (una subasta
        del sabado) si espera a la siguiente. Tampoco ve si su equipo
        juega esa ronda (un aplazado suyo) ni la hora de verdad de las
        jornadas que LaLiga no ha fijado: hasta que la fija, el
        calendario trae todos sus partidos el domingo a las 17:00, como
        para `jornada_en_curso`.

    H2. EL TABLON ATRASADO NO DA FECHAS. Con el tablon sin las subastas
        del ultimo reset (`TABLON_ATRASADO`) solo esperaban los del
        reparto: al que tenia un movimiento se le fechaba con el ultimo
        que traia el fichero... que puede no ser el ultimo. Historia de
        verdad: Jonny (1599), nuestro desde el 10/08, se vendio el
        20/08 a las 09:59 y se recompro en la subasta del 23/08 a las
        05:03; con el tablon parado el 20/08 a las 09:00 (peticiones
        fallando), el parte lo daba por nuestro desde el 10/08 y
        aceptaba la oferta el 23/08, el dia que volvio. Ahora, si no se
        sabe que el tablon esta al dia, no tiene fecha NADIE y en esa
        vuelta no se vende a nadie (`SIN_FECHA_DE_FICHAJE`).

        AL DIA SIN SUBASTA. Para que los dias en que nadie gana una
        subasta (5 de 73) no paren el parte entero, el tablon tambien
        esta al dia si trae un movimiento ('market' o 'transfer') de
        `MARGEN_DEL_TABLON` (2 h) o mas despues del ultimo reset: si lo
        trae, se pidio despues, y para entonces las subastas de ese
        reset ya estaban. Medido el 21/10 con las 159 versiones del
        tablon que hay en git (23/09-21/10, cada una como se pidio):
          - ningun 'market' ni 'transfer' aparecio en una version
            posterior a otra que ya traia uno mas nuevo, ni con fecha
            posterior a su version. Los que si llegan tarde son
            'bettingPool', 'poll' y 'adminText' (2.545 veces): no
            cuentan;
          - las 71 subastas llegaron entre 2 y 11,5 minutos despues de
            las 05:00 UTC;
          - cada version usada cada hora hasta 48 h despues (el tablon
            de una vuelta cuya peticion fallo): 7.510 casos, NINGUNO
            dado por al dia sin las subastas de su dia, ni con la
            prueba de antes ni con esta. Esta da por al dia 318 mas y
            desatasca los cuatro dias sin subasta que caen en esas
            versiones (03, 09, 11 y 20/10) desde su primer movimiento
            (entre las 07:43 y las 16:06 UTC); hasta entonces, ese
            dia no se vende.
        Las 2 h cubren tambien el cambio de hora: si el reset sigue la
        hora de Madrid, en primavera `el_ultimo_reset` (el `until`
        menos 24 h) sale una hora antes que el de verdad, y 2 h
        despues de el sigue siendo una hora despues del reset.

LA REVISION FINAL (27/10/2026): EL PARTE Y LA ORDEN

    La revision final del 27/10 encontro dos agujeros (gravedad media)
    entre el parte y la orden del gestor (`la_orden_del_gestor`).

    F1. LO QUE VENDE LA ORDEN ES DE LA ORDEN. El parte no leia
        `vender_si_ficha`. La orden empareja cada venta con su relevo
        (`si_esta`, el suyo o el general) y le pone el suelo del gestor
        (`suelo`), y aguanta el cobro mientras el relevo no llega, si
        llega y no esta sano (EL_PARTE_DEL_RELEVO: 'doubt', 'injured',
        sin estado) o si la oferta no llega a ese suelo. El parte no
        sabia nada de eso: a un `vender_si_ficha` en duda o lesionado,
        fuera del once y que no estuviera tambien en `conservar`, le
        aceptaba la oferta del Computer en SU 95 %, justo la venta que la
        orden estaba aguantando. Tres formas de romperlo, reproducidas
        en la guardia: (a) el relevo llega en duda y la orden no cobra
        (si el que entra no juega, el que sale es quien tapa el hueco),
        y el parte si; (b) la oferta llega al 95 % del valor y no al
        suelo del gestor, y el parte vendia por debajo de lo que el
        gestor escribio; (c) el relevo todavia no es nuestro (la puja
        sigue viva o se perdio), y el parte vendia al que sale sin tener
        con quien cambiarlo. De verdad: Jonny (1599) estuvo del 24 al
        27/10 en `vender_si_ficha` por Kike Salas (`si_esta` 28115, suelo
        1.450.000), y lo que lo guardaba del parte era estar TAMBIEN en
        `conservar`; la orden no lo pide, y el gestor ya habia avisado de
        que si Kike caia lesionado el lunes habria que decidir a mano.

        Ahora a los `vender_si_ficha.jugadores` de una orden VALIDA el
        parte no los toca (`LA_ORDEN`), se cumpla o no su condicion
        (relevo, `desde`, `si_saldo_negativo`): los vende la orden,
        cuando ella diga y por lo que ella diga. Se lee el `player_id`
        (`los_que_vende_la_orden`).

        SIN `player_id` (27/10/2026, la revision del arreglo). Uno de
        `vender_si_ficha` con solo el nombre (`{"nombre": "Cardona",
        "si_esta": ..., "suelo": ...}`) o con un `player_id` que no es
        un numero: la orden lo busca en la plantilla por su id, no lo
        encuentra y no lo vende, pero el gestor lo escribio para
        venderlo con su relevo y su suelo; el unico que lo venderia
        seria el parte, en su 95 %, sin relevo ni suelo. Esa orden no
        vale para el parte (`NO_SE_ENTIENDE`, F2), como un `proteger`,
        un `conservar` o un `fichar` sin `player_id`: se falla del lado
        seguro y el gestor la arregla.

        LOS VIAJES (27/10/2026, la revision del arreglo). La orden
        tambien vende los `viajes.candidatos` que estan en la
        plantilla, con el suelo del viaje: lo pagado (`puja`) mas un
        1 % hasta `hasta`, y hasta un 5 % por debajo despues. Un viaje
        comprado hace mas de 7 dias, con su primera ronda jugada, en
        duda y fuera del once, el parte lo vendia al 95 % de su valor de
        hoy, por debajo de lo que pide la orden. Ahora tambien es de la
        orden (`LA_ORDEN`), se cumplan o no sus topes, y sin `player_id`
        la orden no vale (`NO_SE_ENTIENDE`). La de hoy no trae ninguno
        (`candidatos` vacio, `hasta` el 07/10).

        LO QUE NO CUBRE: el relevo. Si ya es nuestro es un fichaje, y no
        se toca hasta que juega una ronda con nosotros (E14, H1); el
        gestor, ademas, lo pasa a `conservar` al ganarlo (Kike Salas,
        25/10). Despues de eso, en duda y fuera del once, es uno mas.

    F2. SIN LA ORDEN, A NADIE. `la_orden_del_gestor.protegidos` y
        `conservados` dan VACIO si la orden esta apagada, caducada o no
        vale (`validar`), y el parte lo leia como «el gestor no guarda a
        nadie»: fallaba del lado ABIERTO. Con la orden caducada sin
        renovar (la de hoy caduca el 30/11), sin fichero o con un JSON
        roto, los diez de `conservar` de hoy (Cardona, Gaya, Boye, Kike
        Salas...) y los de `proteger` quedaban a la venta al 95 % en
        cuanto cayeran en duda fuera del once (Yamal no: va por su
        nombre). Ahora `correr` lee la orden UNA vez, despues del reloj
        y antes de la foto (`la_orden_no_vale`), y:
          - con su interruptor (`BORDALAS_LA_ORDEN_DEL_GESTOR`) apagado
            no escribe nada (`ORDEN_APAGADA`). Se decidio fallar del lado
            seguro: apagada, la orden no se lee, no se sabe a quien
            guarda el gestor y el parte no vende a nadie. El parte
            encendido NECESITA la orden encendida (en el workflow de
            produccion lo esta);
          - encendida, si `validar` no la da por buena (no hay fichero o
            no se lee: `SIN_ORDEN`; `SIN_CADUCIDAD`, `CADUCADA`,
            `NOMBRA_A_UN_INTOCABLE`, `FICHAJE_MAL_ESCRITO`), o no se
            sabe leer a quien guarda o que vende ella (`NO_SE_ENTIENDE`:
            un jugador de `conservar` que no es un dict deja vacio a
            `conservados` ENTERO, y `validar` no mira `conservar`; uno
            sin `player_id` no se guarda; un jugador de
            `vender_si_ficha` que no es un dict hace reventar a
            `validar`; uno de `vender_si_ficha` o de `viajes.candidatos`
            sin `player_id` solo lo venderia el parte), tampoco
            (`ORDEN_NO_VALIDA`; el motivo queda en `la_orden` y en el
            detalle).
        Lo del reloj (zona de silencio, ronda jugandose, sin calendario)
        se dice antes: no depende de la orden.

QUE NO HACE

    No compra, no pone el once, no toca a nadie 'ok', 'warned' o sin
    estado, no acepta ofertas de managers y no quita de la venta (el
    cliente de escritura no sabe). No mira la caja: eso es del cierre.

    Corre como paso propio del workflow, DESPUES del cierre de la jornada
    (necesita el once escrito del panel y lo que el cierre ya cobro y
    publico en esta vuelta): `python -m src.actions.el_parte_vende`.
    Nace APAGADO: `BORDALAS_EL_PARTE_VENDE`. Nunca lanza. Encendido,
    sin la orden del gestor encendida y valida no vende a nadie (F2).

LO QUE DEJA PARA LA ROTACION (17/10/2026)

    La rotacion corre DESPUES y lee la foto de antes: sin esto no veia
    lo que el parte acababa de vender o publicar (emparejaba al que ya
    no estaba, o vendia al que salia con el que entro ya vendido).
    Encendido, `main` deja lo que mando en `VUELTA_PARTE`, con la forma
    del fichero de la vuelta de la mejora ({run_id, generated_at,
    hechas}: `la_mejora_del_once.escribir_la_vuelta`). `correr` no
    escribe nada (las guardias no tocan produccion).
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timedelta, timezone
from pathlib import Path


ENV = "BORDALAS_EL_PARTE_VENDE"
RAIZ = Path(__file__).parents[2]

# Lo que mando en esta vuelta, para la rotacion (que corre despues).
VUELTA_PARTE = RAIZ / "data" / "trading" / "el_parte_vuelta.json"

# El tablon de la liga: de donde sale desde cuando es nuestro cada uno.
TABLON = RAIZ / "data" / "rival_intelligence" / "board_events.json"

# Lo que dice el parte del catalogo de Biwenger para vender. Sin
# 'sanctioned' desde el 21/10/2026: ver `SANCIONADO`.
MALOS = frozenset({"doubt", "injured"})

# El sancionado se mira y no se vende (`SANCION`): una sancion suele ser
# de un partido y su caida no esta medida.
SANCIONADO = "sanctioned"

# Un fichaje no se toca hasta que lleva estos dias con nosotros (E14)...
DIAS_DE_FICHAJE = 7

# ... ni hasta que acaba la primera ronda que empezo despues de su
# llegada (21/10/2026, H1): su ultimo partido mas este margen
# (= `la_proxima_jornada.MARGEN_FINAL`, el de `jornada_en_curso`).
MARGEN_FINAL = timedelta(hours=3)

# Lo que hace falta para que una ronda cuente como jugada: la ventana
# principal de su jornada con al menos media jornada de partidos. Un
# aplazado o un adelantado suelto no (ver H1).
PARTIDOS_DE_RONDA = 5

# El tablon esta al dia sin subasta si trae un movimiento de esto o mas
# despues del ultimo reset del Computer (21/10/2026, H2): las subastas
# llegan entre 2 y 11,5 min despues, y 1 h es la del cambio de hora.
MARGEN_DEL_TABLON = timedelta(hours=2)

# Lo minimo que se acepta del Computer, sobre el valor de hoy.
SUELO = 0.95

# Nunca se vende. Regla de la casa (= `la_orden_del_gestor.INTOCABLES`);
# aqui se mira si el nombre CONTIENE "yamal", por si el catalogo lo
# escribe de otra forma.
INTOCABLE = "yamal"


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# AYUDAS QUE NUNCA LANZAN
# ============================================================

def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError, OverflowError):
        return defecto


def _dict(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    try:
        if isinstance(x, dict):
            x = list(x.values())
        return [f for f in (x or []) if isinstance(f, dict)]
    except Exception:                               # noqa: BLE001
        return []


def _ids(x) -> set:
    try:
        if isinstance(x, (str, bytes)):
            return set()
        return {i for i in (_int(v) for v in (x or [])) if i is not None}
    except Exception:                               # noqa: BLE001
        return set()


def _por_id(x) -> dict:
    """`{player_id: valor}` con las claves en entero. Nunca lanza."""
    try:
        return {_int(k): v for k, v in _dict(x).items() if _int(k) is not None}
    except Exception:                               # noqa: BLE001
        return {}


def _nombres(x) -> list:
    """Los nombres de un jugador (uno o varios), sin blancos."""
    try:
        if isinstance(x, str):
            x = [x]
        return [str(n).strip() for n in (x or []) if str(n or "").strip()]
    except Exception:                               # noqa: BLE001
        return []


def _fecha(x) -> datetime | None:
    """Un instante en UTC: un `datetime` (sin zona, UTC), un epoch en
    segundos (el `date` del tablon) o un texto ISO. None si no es nada de
    eso. Nunca lanza."""
    try:
        if isinstance(x, datetime):
            cuando = x
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            if x <= 0:
                return None
            cuando = datetime.fromtimestamp(x, timezone.utc)
        elif isinstance(x, str) and x.strip():
            cuando = datetime.fromisoformat(x.strip().replace("Z", "+00:00"))
        else:
            return None
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        return cuando.astimezone(timezone.utc)
    except Exception:                               # noqa: BLE001
        return None


def el_suelo(valor) -> int | None:
    """El `SUELO` de `valor`, redondeado hacia arriba (al menos el 95 %).
    None si no hay valor. Pura."""
    valor = _int(valor)
    if valor is None or valor <= 0:
        return None
    return -(-valor * int(SUELO * 100) // 100)


def ids_del_once(alineacion) -> set:
    """Los ids de `{"players": [...]}` (el once del panel o el de
    Biwenger). Vacio si no se sabe. Nunca lanza."""
    try:
        return _ids(p.get("id") for p in _lista(_dict(alineacion).get("players")))
    except Exception:                               # noqa: BLE001
        return set()


# ============================================================
# DESDE CUANDO ES NUESTRO (21/10/2026)
# ============================================================

def el_ultimo_reset(snapshot) -> datetime | None:
    """
    El ultimo reset del Computer que ve la foto: el `until` comun de sus
    ventas es el PROXIMO (`market_clock.computer_reset_epoch`), y el
    ultimo fue 24 h antes. None si la foto no trae ventas del Computer:
    entonces no se puede saber si el tablon esta al dia. Nunca lanza.
    """
    try:
        from src.analysis.market_clock import computer_reset_epoch

        proximo, _ = computer_reset_epoch(_dict(snapshot))
        proximo = _int(proximo)
        if proximo is None or proximo <= 24 * 3600:
            return None
        return datetime.fromtimestamp(proximo - 24 * 3600, timezone.utc)
    except Exception:                               # noqa: BLE001
        return None


AVISOS = {
    "SIN_TABLON": ("el tablon no se pudo leer: no se sabe cuando llego nadie y no "
                   "se vende a nadie (SIN_FECHA_DE_FICHAJE)"),
    "SIN_RESET_EN_EL_TABLON": ("el tablon no empieza en el reset de la liga: a los "
                               "del reparto no se les puede dar fecha y no se venden"),
    "TABLON_ATRASADO": ("no se sabe si el tablon esta al dia: no trae las subastas "
                        "del ultimo reset del Computer ni ningun movimiento de 2 h "
                        "despues (o la foto no dice cuando fue el reset). Lo ultimo "
                        "que trae de cada uno puede no ser lo ultimo que paso: no se "
                        "da fecha a NADIE y en esta vuelta no se vende a nadie "
                        "(SIN_FECHA_DE_FICHAJE)"),
}


def las_fechas_de_fichaje(eventos, yo, plantilla, ultimo_reset=None) -> dict:
    """
    Desde cuando es nuestro cada jugador de `plantilla`, del tablon de
    la liga (la lista de `board_events.json`). Pura. Nunca lanza.

        {"fechas": {player_id: datetime UTC}, "aviso": None o un AVISOS}

    Primero, si el tablon esta AL DIA: trae un 'market' (las subastas)
    desde `ultimo_reset`, o un movimiento ('market' o 'transfer') de
    `MARGEN_DEL_TABLON` o mas despues (21/10/2026, H2). Si no lo esta,
    o no se sabe `ultimo_reset`: NADIE tiene fecha (`TABLON_ATRASADO`).

    Al dia, con compra en el tablon (lo ultimo que lo movio fue un
    'market' o un 'transfer' con `to.id` = `yo`), la fecha de ese
    evento. Sin ningun movimiento desde el reset, la del reset, si el
    tablon empieza en el. Si lo ultimo que lo movio no es hacia
    nosotros, el tablon va por detras: sin fecha. Quien no tiene fecha
    no esta en `fechas`.
    """

    salida = {"fechas": {}, "aviso": None}
    try:
        yo = _int(yo)
        if isinstance(eventos, dict):
            eventos = eventos.get("events")
        eventos = _lista(eventos) if isinstance(eventos, list) else []
        if yo is None or not eventos:
            salida["aviso"] = "SIN_TABLON"
            return salida

        # El reset vigente: lo de antes es de otra temporada.
        reset = None
        for e in eventos:
            cuando = _fecha(_int(e.get("date")))
            if e.get("type") == "leagueReset" and cuando is not None:
                reset = cuando if reset is None or cuando > reset else reset

        tope = _fecha(ultimo_reset)
        al_dia = False
        ultimo_movimiento = None
        movidos: dict = {}                  # {player_id: (cuando, hacia nosotros)}
        for e in eventos:
            if e.get("type") not in ("market", "transfer"):
                continue
            cuando = _fecha(_int(e.get("date")))
            if cuando is None or (reset is not None and cuando < reset):
                continue
            if e.get("type") == "market" and tope is not None and cuando >= tope:
                al_dia = True
            if ultimo_movimiento is None or cuando > ultimo_movimiento:
                ultimo_movimiento = cuando
            for op in _lista(e.get("content")):
                jugador = op.get("player")
                pid = _int(_dict(jugador).get("id") if isinstance(jugador, dict) else jugador)
                if pid is None:
                    continue
                a_nosotros = _int(_dict(op.get("to")).get("id")) == yo
                antes = movidos.get(pid)
                if antes is None or cuando > antes[0]:
                    movidos[pid] = (cuando, a_nosotros)
                elif cuando == antes[0]:
                    # Dos movimientos en el mismo segundo: hacia nosotros
                    # solo si lo son los dos.
                    movidos[pid] = (cuando, antes[1] and a_nosotros)

        # Sin subasta desde el reset (5 dias de 73): al dia si trae un
        # movimiento de 2 h despues. Solo 'market' y 'transfer': las
        # porras y las encuestas llegan con fecha de atras (H2).
        if (not al_dia and tope is not None and ultimo_movimiento is not None
                and ultimo_movimiento >= tope + MARGEN_DEL_TABLON):
            al_dia = True
        if not al_dia:
            # H2: lo ultimo que trae de cada uno puede no ser lo ultimo
            # que paso (vendido y recomprado despues): nadie tiene fecha.
            salida["aviso"] = "TABLON_ATRASADO"
            return salida

        fechas = {}
        for pid in _ids(plantilla):
            if pid in movidos:
                cuando, a_nosotros = movidos[pid]
                if a_nosotros:
                    fechas[pid] = cuando
            elif reset is not None:
                fechas[pid] = reset

        salida["fechas"] = fechas
        if reset is None:
            salida["aviso"] = "SIN_RESET_EN_EL_TABLON"
        return salida
    except Exception:                               # noqa: BLE001
        return {"fechas": {}, "aviso": "SIN_TABLON"}


# ============================================================
# HASTA CUANDO NO SE TOCA UN FICHAJE (21/10/2026, H1)
# ============================================================

def hasta_cuando_no_se_toca(fichado, rondas) -> datetime | None:
    """
    Hasta cuando no se vende a uno que es nuestro desde `fichado` (E14:
    no se revende antes de jugar con nosotros): hasta que acaba (`fin`
    mas `MARGEN_FINAL`) la primera ronda de `rondas` que EMPEZO despues
    de su llegada, y nunca antes de `DIAS_DE_FICHAJE` dias desde que
    llego. Las de `la_proxima_jornada.las_rondas`: `[{inicio, fin,
    partidos, aparte}]`. Solo cuentan las de verdad: `aparte` False y
    `PARTIDOS_DE_RONDA` partidos o mas.

    None si no se sabe: sin `fichado`, sin rondas o sin ninguna que
    empiece despues de su llegada. Pura. Nunca lanza.
    """
    try:
        fichado = _fecha(fichado)
        if fichado is None:
            return None
        finales = []
        for r in _lista(rondas):
            if r.get("aparte") or (_int(r.get("partidos")) or 0) < PARTIDOS_DE_RONDA:
                continue
            inicio, fin = _fecha(r.get("inicio")), _fecha(r.get("fin"))
            if inicio is None or fin is None or inicio <= fichado:
                continue
            finales.append(max(inicio, fin) + MARGEN_FINAL)
        if not finales:
            return None
        return max(fichado + timedelta(days=DIAS_DE_FICHAJE), min(finales))
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# LA ORDEN DEL GESTOR (27/10/2026)
# ============================================================

def los_que_vende_la_orden(orden) -> set:
    """
    Los `vender_si_ficha.jugadores` de la orden del gestor (27/10/2026,
    F1) y sus `viajes.candidatos` (27/10/2026, la revision del arreglo:
    LOS VIAJES), por su `player_id`: esten o no en la plantilla y se
    cumpla o no su condicion (su relevo `si_esta` o el general, `desde`,
    `si_saldo_negativo`; los topes y `hasta` del viaje). Esos los vende
    la orden, con su relevo y su suelo (o el del viaje), y el parte no
    los toca (`LA_ORDEN`). Uno sin `player_id` no se puede guardar, y la
    orden tampoco lo vende (lo busca en la plantilla por el): solo lo
    venderia el parte, asi que con uno asi la orden no vale
    (`la_orden_no_vale`: `NO_SE_ENTIENDE`). Vacio si no hay orden o no
    se entiende. Solo vale con la orden VALIDA: eso lo mira `correr`
    antes (`la_orden_no_vale`). Pura. Nunca lanza.
    """
    try:
        orden = _dict(orden)
        venta = _dict(orden.get("vender_si_ficha"))
        viajes = _dict(orden.get("viajes"))
        return (_ids(j.get("player_id") for j in _lista(venta.get("jugadores")))
                | _ids(v.get("player_id") for v in _lista(viajes.get("candidatos"))))
    except Exception:                               # noqa: BLE001
        return set()


def la_orden_no_vale(orden, ahora, encendida=True) -> str | None:
    """
    None si el parte se puede fiar de la orden del gestor (27/10/2026,
    F2): su interruptor esta encendido (`encendida`, el de
    `la_orden_del_gestor.activa`) y `la_orden_del_gestor.validar` la da
    por buena a la hora `ahora`. Si no, por que:

        "APAGADA"         el interruptor de la orden esta apagado
        lo de `validar`   "SIN_ORDEN" (no hay fichero o no se lee),
                          "SIN_CADUCIDAD", "CADUCADA",
                          "NOMBRA_A_UN_INTOCABLE", "FICHAJE_MAL_ESCRITO"
        "NO_SE_ENTIENDE"  `validar` revienta al mirarla (un jugador de
                          `vender_si_ficha` que no es un dict, una hora
                          sin zona), o la da por buena pero `protegidos`
                          y `conservados` no la saben leer: un
                          `proteger`, `conservar` o `fichar` que no es
                          una lista de jugadores, cada uno con su
                          `player_id` (uno que no es un dict los deja
                          vacios ENTEROS; uno sin `player_id` no se
                          guarda), o un `vender_si_ficha` o sus
                          `jugadores` que no son un dict y una lista de
                          dicts. Desde la revision del arreglo
                          (27/10/2026), tambien lo que vende ella
                          (`los_que_vende_la_orden`): un jugador de
                          `vender_si_ficha` sin `player_id` (la orden no
                          lo encuentra y solo lo venderia el parte, sin
                          su relevo ni su suelo), o unos `viajes` y sus
                          `candidatos` que no son un dict y una lista de
                          jugadores, cada uno con su `player_id`

    Con cualquiera de ellos `protegidos` y `conservados` dan vacio, o no
    se sabe a quien guarda el gestor o que vende la orden: el parte no
    vende a nadie. `ahora` se pasa tal cual, como a `protegidos` y
    `conservados`, para que los tres digan lo mismo. Nunca lanza.
    """
    try:
        if not encendida:
            return "APAGADA"
        from src.actions.la_orden_del_gestor import validar

        invalida = validar(orden, ahora)
        if invalida:
            return invalida
        # Lo que `validar` no mira y `protegidos` / `conservados` no saben
        # leer: lo dan por vacio, y eso tambien es no saber a quien guarda.
        for clave in ("proteger", "conservar", "fichar"):
            lista = orden.get(clave)
            if not lista:
                continue
            if not isinstance(lista, list) or not all(
                    isinstance(x, dict) and _int(x.get("player_id")) is not None
                    for x in lista):
                return "NO_SE_ENTIENDE"
        venta = orden.get("vender_si_ficha")
        if venta and not isinstance(venta, dict):
            return "NO_SE_ENTIENDE"
        viajes = orden.get("viajes")
        if viajes and not isinstance(viajes, dict):
            return "NO_SE_ENTIENDE"
        # Lo que vende ella (F1, LOS VIAJES), cada uno con su `player_id`:
        # sin el, la orden no lo encuentra y solo lo venderia el parte, en
        # su 95 % (27/10/2026, la revision del arreglo).
        for jugadores in ((venta or {}).get("jugadores"), (viajes or {}).get("candidatos")):
            if jugadores and (not isinstance(jugadores, list) or not all(
                    isinstance(j, dict) and _int(j.get("player_id")) is not None
                    for j in jugadores)):
                return "NO_SE_ENTIENDE"
        return None
    except Exception:                               # noqa: BLE001
        return "NO_SE_ENTIENDE"


# ============================================================
# LA DECISION (pura)
# ============================================================

def por_que_no(*, puede_escribir=True, sin_calendario=False, en_curso=False,
               once_escrito=None, once_de_biwenger=None):
    """None si toca mirar el parte en esta vuelta. Si no, el motivo.
    `en_curso` None es no saberlo: no se hace nada. `once_escrito` (el
    del panel) y `once_de_biwenger` None es no mirarlos todavia (el reloj
    va antes que leer el panel); vacios, no saber quien es titular: no
    se hace nada. Nunca lanza."""
    try:
        if not puede_escribir:
            return "ZONA_DE_SILENCIO"
        if sin_calendario:
            return "SIN_CALENDARIO"
        if en_curso or en_curso is None:
            return "JORNADA_EN_CURSO"
        if once_escrito is not None and not _ids(once_escrito):
            return "SIN_ONCE_ESCRITO"
        if once_de_biwenger is not None and not _ids(once_de_biwenger):
            return "SIN_ONCE_DE_BIWENGER"
        return None
    except Exception:                               # noqa: BLE001
        return "SIN_ONCE_ESCRITO"


MOTIVOS = {
    "ZONA_DE_SILENCIO": "zona de silencio: no se escribe",
    "SIN_CALENDARIO": "sin calendario no se sabe si hay una ronda jugandose: no se vende",
    "JORNADA_EN_CURSO": ("hay una ronda jugandose (el once no se cambia empezada la "
                         "ronda): no se vende ni se publica"),
    "SIN_ONCE_ESCRITO": ("sin el once escrito del panel (status.lineup.players) no se "
                         "sabe quien es titular: no se vende ni se publica a nadie"),
    "SIN_ONCE_DE_BIWENGER": ("sin la alineacion vigente en Biwenger "
                             "(user_lineup.data.lineup.players: la foto la deja en None "
                             "si GET /user falla) no se sabe quien sigue puesto, y el "
                             "once del panel ya deja fuera a los lesionados y "
                             "sancionados: no se vende ni se publica a nadie"),
    "ORDEN_APAGADA": ("la orden del gestor esta apagada (BORDALAS_LA_ORDEN_DEL_GESTOR): "
                      "no se sabe a quien guarda (proteger, conservar) ni que vende "
                      "ella (vender_si_ficha, viajes): no se vende ni se publica a nadie"),
    "ORDEN_NO_VALIDA": ("la orden del gestor no vale (no hay, no se lee, caducada o mal "
                        "escrita): sin ella no se sabe a quien guarda (proteger, "
                        "conservar) ni que vende ella (vender_si_ficha, viajes): no se "
                        "vende ni se publica a nadie"),
}


def decidir(
    *, plantilla, estados, nombres=None, precios=None, ofertas_del_computer=None,
    en_venta=frozenset(), once_escrito=frozenset(), once_de_biwenger=frozenset(),
    protegidos=frozenset(), conservados=frozenset(), aguanta=frozenset(),
    vendidos=frozenset(), fichajes=None, ahora=None, rondas=None,
    en_curso=False, puede_escribir=True, sin_calendario=False,
    de_la_orden=frozenset(),
) -> dict:
    """
    Que vende el parte en esta vuelta. Pura: ni red, ni disco, ni reloj.

        plantilla             {player_id} nuestros (la foto)
        estados               {player_id: status del catalogo}
        nombres               {player_id: nombre o [nombres]} (Yamal)
        precios               {player_id: valor de hoy}
        ofertas_del_computer  {player_id: {"offer_id", "amount"}}
        en_venta              {player_id} publicados (foto y esta vuelta)
        once_escrito          {player_id} titulares del panel; vacio = no
                              se sabe y no se hace nada
        once_de_biwenger      {player_id} la alineacion vigente en
                              Biwenger; vacio = no se sabe y no se hace
                              nada
        protegidos            `proteger` y `fichar` de la orden
        conservados           `conservar` de la orden
        de_la_orden           `vender_si_ficha.jugadores` y
                              `viajes.candidatos` de la orden valida
                              (27/10/2026, F1 y LOS VIAJES): los vende
                              ella (`los_que_vende_la_orden`)
        aguanta               lo de LA CARTERA de la ronda
        vendidos              {player_id} vendidos en esta vuelta
        fichajes              {player_id: datetime} desde cuando es
                              nuestro (`las_fechas_de_fichaje`); quien
                              no esta, o None, no se vende
        ahora                 la hora de la vuelta (sin ella, no se
                              cuentan los dias y no se vende a nadie)
        rondas                las de `la_proxima_jornada.las_rondas`
                              (21/10/2026, H1): con ellas se sabe si un
                              fichaje ya jugo una ronda con nosotros
                              (`hasta_cuando_no_se_toca`); None o
                              vacias, no se sabe y no se vende a nadie
        en_curso              hay una ronda jugandose (None: no se sabe)
        puede_escribir        fuera de la zona de silencio
        sin_calendario        no hay rondas que mirar

    `{"activo", "motivo", "acciones", "malos", "no_se_tocan"}`: `malos`
    son los del parte que se miraron (tambien los sancionados);
    `no_se_tocan`, los que no se venden y por que.
    """

    salida = {"activo": False, "motivo": None, "acciones": [], "malos": [],
              "no_se_tocan": []}
    try:
        once_escrito, once_de_biwenger = _ids(once_escrito), _ids(once_de_biwenger)
        motivo = por_que_no(puede_escribir=puede_escribir, sin_calendario=sin_calendario,
                            en_curso=en_curso, once_escrito=once_escrito,
                            once_de_biwenger=once_de_biwenger)
        if motivo:
            salida["motivo"] = motivo
            return salida

        once = once_escrito | once_de_biwenger
        estados, nombres = _por_id(estados), _por_id(nombres)
        precios, ofertas = _por_id(precios), _por_id(ofertas_del_computer)
        en_venta, vendidos = _ids(en_venta), _ids(vendidos)
        protegidos, conservados, aguanta = _ids(protegidos), _ids(conservados), _ids(aguanta)
        de_la_orden = _ids(de_la_orden)
        fichajes = {pid: f for pid, f in ((p, _fecha(v)) for p, v in _por_id(fichajes).items())
                    if f is not None}
        ahora = _fecha(ahora)
        rondas = _lista(rondas)

        acciones, malos, no_se_tocan = [], [], []
        for pid in sorted(_ids(plantilla)):
            estado = str(estados.get(pid) or "").strip().lower()
            if estado not in MALOS and estado != SANCIONADO:
                continue
            malos.append(pid)
            suyos = _nombres(nombres.get(pid))
            nombre = suyos[0] if suyos else None
            fichado = fichajes.get(pid)
            hasta = None

            if pid in vendidos:
                por = "VENDIDO_EN_ESTA_VUELTA"
            elif pid in once:
                por = "ONCE_ESCRITO"
            elif any(INTOCABLE in n.lower() for n in suyos):
                por = "YAMAL"
            elif not suyos:
                por = "SIN_NOMBRE"
            elif pid in protegidos:
                por = "PROTEGIDO"
            elif pid in conservados:
                por = "CONSERVAR"
            elif pid in de_la_orden:
                # F1 (27/10/2026): lo vende la orden, con su relevo y su
                # suelo (o el del viaje); si ella lo aguanta, el parte no
                # se lo salta.
                por = "LA_ORDEN"
            elif pid in aguanta:
                por = "LA_CARTERA"
            elif estado == SANCIONADO:
                por = "SANCION"
            elif fichado is None or ahora is None:
                por = "SIN_FECHA_DE_FICHAJE"
            else:
                # E14 (H1): los 7 dias, y hasta que acaba su primera ronda.
                hasta = hasta_cuando_no_se_toca(fichado, rondas)
                if ahora - fichado < timedelta(days=DIAS_DE_FICHAJE):
                    por = "RECIEN_FICHADO"
                elif hasta is None:
                    por = "SIN_RONDA_TRAS_EL_FICHAJE"
                elif ahora < hasta:
                    por = "SIN_JUGAR_CON_NOSOTROS"
                else:
                    por = None
            valor = _int(precios.get(pid))
            suelo = el_suelo(valor)
            if por is None and suelo is None:
                por = "SIN_VALOR"
            if por:
                fila = {"player_id": pid, "nombre": nombre, "estado": estado, "por": por}
                if por in ("RECIEN_FICHADO", "SIN_JUGAR_CON_NOSOTROS",
                           "SIN_RONDA_TRAS_EL_FICHAJE"):
                    fila["fichado"] = fichado.isoformat()
                    if hasta is not None:
                        fila["hasta"] = hasta.isoformat()
                no_se_tocan.append(fila)
                continue

            oferta = _dict(ofertas.get(pid))
            importe = _int(oferta.get("amount"), 0) or 0
            offer_id = _int(oferta.get("offer_id"))
            if offer_id and importe >= suelo:
                acciones.append({
                    "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": pid,
                    "nombre": nombre, "offer_id": offer_id, "importe": importe,
                    "valor": valor, "suelo": suelo, "estado": estado, "parte": True,
                })
            elif pid not in en_venta:
                acciones.append({
                    "accion": "PONER_A_LA_VENTA", "player_id": pid, "nombre": nombre,
                    "precio": valor, "estado": estado, "parte": True,
                })
            else:
                acciones.append({
                    "accion": "NADA", "player_id": pid, "nombre": nombre,
                    "estado": estado, "parte": True,
                    "motivo": (
                        f"publicado; la oferta del Computer ({importe}) no llega al "
                        f"{int(SUELO * 100)} % de su valor ({suelo})" if offer_id else
                        "publicado; esperando la oferta del Computer"
                    ),
                })

        salida.update({"activo": True, "acciones": acciones, "malos": malos,
                       "no_se_tocan": no_se_tocan})
        return salida
    except Exception as error:                      # noqa: BLE001
        return {"activo": False, "motivo": f"ERROR: {type(error).__name__}: {error}",
                "acciones": [], "malos": [], "no_se_tocan": []}


# ============================================================
# EL PASO DEL WORKFLOW
# ============================================================

def _leer(ruta, defecto):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return defecto


def lo_vendido_y_publicado(v10, vuelta_mejora, plan_cierre, ahora, run_id=None) -> dict:
    """
    Lo que ESTA vuelta ya cobro y publico antes del parte (la foto es de
    antes): las `hechas` de v10 (si su estado es de esta vuelta), las de
    la mejora (su fichero de la vuelta) y las del cierre (su plan), con
    las mismas pruebas de vuelta que usa el cierre (`run_id`; si no, la
    hora). `{"vendidos", "listados", "descartados"}`. Nunca lanza.
    """
    salida = {"vendidos": set(), "listados": set(), "descartados": []}
    try:
        from src.actions.el_cierre_de_la_jornada import (
            la_vuelta_de_la_mejora, lo_de_esta_vuelta,
        )
        from src.actions.la_mejora_del_once import es_de_esta_vuelta

        descartado = es_de_esta_vuelta(v10, ahora, run_id)
        de_la_vuelta = {} if descartado else dict(_dict(v10))
        if descartado:
            salida["descartados"].append(f"v10: {descartado}")
        hechas_mejora, d_mejora = la_vuelta_de_la_mejora(vuelta_mejora, ahora, run_id)
        hechas_cierre, d_cierre = la_vuelta_de_la_mejora(plan_cierre, ahora, run_id)
        if d_mejora:
            salida["descartados"].append(f"mejora: {d_mejora}")
        if d_cierre:
            salida["descartados"].append(f"cierre: {d_cierre}")
        de_la_vuelta["la_mejora_del_once"] = {"hechas": hechas_mejora}
        de_la_vuelta["el_cierre_de_la_jornada"] = {"hechas": hechas_cierre}
        vuelta = lo_de_esta_vuelta(de_la_vuelta)
        salida["vendidos"] = _ids(vuelta.get("vendidos"))
        salida["listados"] = _ids(vuelta.get("listados"))
    except Exception as error:                      # noqa: BLE001
        salida["descartados"].append(f"lo de esta vuelta: {type(error).__name__}")
    return salida


def correr(cycle=None, escritor_factory=None, ahora: datetime | None = None, *,
           status=None, calendario=None, orden_ruta=None, libro_ronda_ruta=None,
           v10=None, vuelta_mejora=None, plan_cierre=None, tablon=None) -> dict:
    """
    El parte, en esta vuelta. Nunca lanza.

    Lo que no se pasa se lee de produccion: la foto de `cycle["snapshot"]`
    (sin `cycle`, la ultima `snapshot_*.json`, como el cierre), `status`
    del panel, el calendario de los chollos, la orden del gestor
    (`orden_ruta`), el libro de la ronda (`libro_ronda_ruta`), lo que
    esta vuelta ya hizo (`v10`, `vuelta_mejora`, `plan_cierre`) y los
    eventos del tablon (`tablon`, la lista de `TABLON`).
    Apagado, no lee ni escribe nada. Sin la orden del gestor encendida y
    valida (27/10/2026, F2), tampoco escribe nada (`ORDEN_APAGADA`,
    `ORDEN_NO_VALIDA`).
    """

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": [],
              "decision": None}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.la_orden_del_gestor import (
            _pid, conservados, ejecutar, leer_la_foto, leer_la_orden, leer_los_estados,
            protegidos,
        )
        from src.actions.la_orden_del_gestor import activa as la_orden_activa
        from src.actions.la_ronda_de_la_manana import los_que_aguanta
        from src.actions.los_chollos import CALENDARIO, _puede_escribir
        from src.analysis.la_proxima_jornada import jornada_en_curso, las_rondas

        ahora = ahora or datetime.now(timezone.utc)

        # 3. CUANDO: con una ronda jugandose, en la zona de silencio o sin
        # calendario, nada (y sin leer nada mas).
        cal = CALENDARIO if calendario is None else calendario
        # Las rondas tambien dicen cuando ha jugado un fichaje (H1).
        rondas = las_rondas(cal)
        sin_calendario = not rondas
        en_curso = bool(jornada_en_curso(ahora, cal))
        puede_escribir = bool(_puede_escribir(ahora))
        salida["en_curso"] = en_curso
        motivo = por_que_no(puede_escribir=puede_escribir, sin_calendario=sin_calendario,
                            en_curso=en_curso)
        if motivo:
            salida["motivo"] = motivo
            salida["detalle"] = MOTIVOS.get(motivo)
            return salida

        # LA ORDEN DEL GESTOR (27/10/2026, F2): apagada o sin valer,
        # `protegidos` y `conservados` dan vacio y no se sabe a quien
        # guarda el gestor: no se vende a nadie. Se lee UNA vez (apagada,
        # ni eso); lo que vende ella (F1) sale de esta misma lectura.
        encendida = la_orden_activa()
        orden = leer_la_orden(orden_ruta) if encendida else None
        no_vale = la_orden_no_vale(orden, ahora, encendida=encendida)
        if no_vale:
            motivo = "ORDEN_APAGADA" if no_vale == "APAGADA" else "ORDEN_NO_VALIDA"
            salida["motivo"] = motivo
            salida["la_orden"] = no_vale
            salida["detalle"] = (MOTIVOS.get(motivo) if motivo == "ORDEN_APAGADA"
                                 else f"{MOTIVOS.get(motivo)} (la orden: {no_vale})")
            return salida
        de_la_orden = los_que_vende_la_orden(orden)

        if cycle is None:
            from src.actions.la_mejora_del_once import _la_ultima_foto

            snapshot = _la_ultima_foto()
        else:
            snapshot = _dict(cycle).get("snapshot")
        snapshot = _dict(snapshot)

        yo = _pid(_dict(snapshot.get("league")).get("user"))
        if yo is None:
            salida["motivo"] = "SIN_SABER_QUIEN_SOY"
            return salida
        foto = leer_la_foto(snapshot, yo)

        # EL ONCE ESCRITO: el del panel (la fuente del cierre) Y la
        # alineacion vigente en Biwenger de la foto (21/10/2026: hacen
        # falta los dos; el del panel ya deja fuera a los lesionados y
        # sancionados). Sin uno de los dos, no se hace nada. Con los dos,
        # no se toca a ninguno de ninguno.
        if status is None:
            from src.actions.la_mejora_del_once import STATUS

            status = _leer(STATUS, {})
        del_panel = ids_del_once(_dict(status).get("lineup"))
        de_biwenger = ids_del_once(_dict(_dict(snapshot.get("user_lineup")).get("data"))
                                   .get("lineup"))
        once_escrito = (del_panel | de_biwenger) if (del_panel and de_biwenger) else set()
        salida["once_escrito"] = sorted(once_escrito)

        motivo = por_que_no(puede_escribir=puede_escribir, sin_calendario=sin_calendario,
                            en_curso=en_curso, once_escrito=del_panel,
                            once_de_biwenger=de_biwenger)
        if motivo:
            salida["motivo"] = motivo
            salida["detalle"] = MOTIVOS.get(motivo)
            return salida

        # Lo que esta vuelta ya cobro y publico (la foto es de antes).
        if v10 is None or vuelta_mejora is None or plan_cierre is None:
            from src.actions.el_cierre_de_la_jornada import PLAN, VUELTA_MEJORA
            from src.actions.la_mejora_del_once import V10

            v10 = _leer(V10, {}) if v10 is None else v10
            vuelta_mejora = _leer(VUELTA_MEJORA, {}) if vuelta_mejora is None else vuelta_mejora
            plan_cierre = _leer(PLAN, {}) if plan_cierre is None else plan_cierre
        vuelta = lo_vendido_y_publicado(v10, vuelta_mejora, plan_cierre, ahora,
                                        os.environ.get("GITHUB_RUN_ID"))
        salida["vuelta_descartada"] = vuelta["descartados"]

        # DESDE CUANDO ES NUESTRO CADA UNO (21/10/2026): del tablon que el
        # paso V10 acaba de pedir. Sin tablon, o sin saber que esta al
        # dia (H2), nadie tiene fecha y no se vende a nadie.
        if tablon is None:
            tablon = _leer(TABLON, None)
        fichajes = las_fechas_de_fichaje(tablon, yo, foto["plantilla"],
                                         el_ultimo_reset(snapshot))
        if fichajes["aviso"]:
            salida["aviso_del_tablon"] = fichajes["aviso"]
            salida["detalle_del_tablon"] = AVISOS.get(fichajes["aviso"])

        # Nombres y valor: la foto (plantilla y catalogo) y el panel.
        catalogo = _dict(_dict(_dict(snapshot.get("catalog")).get("data")).get("players"))
        nombres: dict = {}

        def _apuntar(pid, nombre):
            pid = _int(pid)
            if pid is not None and str(nombre or "").strip():
                nombres.setdefault(pid, []).append(str(nombre))

        for k, ficha in catalogo.items():
            _apuntar(k, _dict(ficha).get("name"))
        for j in _lista(snapshot.get("my_team")):
            _apuntar(j.get("id"), j.get("name"))
        for j in _lista(_dict(_dict(status).get("roster")).get("players")):
            _apuntar(j.get("id"), j.get("name"))
        precios = {}
        for k, ficha in catalogo.items():
            if _int(k) is not None and _int(_dict(ficha).get("price")):
                precios[_int(k)] = _int(_dict(ficha).get("price"))
        precios.update(_por_id(foto.get("precios")))

        d = decidir(
            plantilla=foto["plantilla"], estados=leer_los_estados(snapshot),
            nombres=nombres, precios=precios,
            ofertas_del_computer=foto["ofertas_del_computer"],
            en_venta=set(foto["en_venta"]) | vuelta["listados"],
            once_escrito=del_panel, once_de_biwenger=de_biwenger,
            protegidos=protegidos(orden_ruta, ahora),
            conservados=conservados(orden_ruta, ahora),
            aguanta=los_que_aguanta(libro_ronda_ruta),
            vendidos=vuelta["vendidos"], fichajes=fichajes["fechas"], ahora=ahora,
            rondas=rondas, en_curso=en_curso, puede_escribir=puede_escribir,
            sin_calendario=sin_calendario, de_la_orden=de_la_orden,
        )
        salida["decision"] = d
        salida["acciones"] = d["acciones"]

        escrituras = [a for a in d["acciones"] if a.get("accion") != "NADA"]
        if not d.get("activo"):
            salida["motivo"] = d.get("motivo")
            return salida
        if not escrituras:
            salida["motivo"] = "NADA_QUE_HACER"
            return salida

        if escritor_factory is None:
            from src.biwenger.write_client import BiwengerWriteClient

            escritor_factory = BiwengerWriteClient

        salida["hechas"] = ejecutar(escrituras, escritor_factory())
        salida["motivo"] = "EJECUTADA"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida


def el_parte(r) -> list:
    """Las lineas de la vuelta, para leerlas en el log. Nunca lanza."""
    lineas = []
    try:
        r = _dict(r)
        lineas.append(f"  {r.get('motivo')}"
                      + (f": {r.get('detalle')}" if r.get("detalle") else ""))
        if r.get("once_escrito"):
            lineas.append(f"  Once escrito (no se toca): {r.get('once_escrito')}")
        for v in r.get("vuelta_descartada") or []:
            lineas.append(f"  Sin contar lo de esta vuelta de {v}")
        if r.get("aviso_del_tablon"):
            lineas.append(f"  Fechas de fichaje: {r.get('aviso_del_tablon')}"
                          + (f": {r.get('detalle_del_tablon')}"
                             if r.get("detalle_del_tablon") else ""))
        d = _dict(r.get("decision"))
        if d.get("malos"):
            lineas.append(f"  Con parte malo en la plantilla: {d.get('malos')}")
        for n in _lista(d.get("no_se_tocan")):
            desde = ""
            if n.get("fichado"):
                desde = (f" (nuestro desde {n.get('fichado')}"
                         + (f"; no se toca hasta {n.get('hasta')}" if n.get("hasta") else "")
                         + ")")
            lineas.append(f"      no se toca {n.get('player_id')} {n.get('nombre') or ''} "
                          f"({n.get('estado')}): {n.get('por')}{desde}")
        for a in _lista(r.get("acciones")):
            importe = a.get("importe") or a.get("precio")
            lineas.append(f"  -> {a.get('accion')} {a.get('player_id')} {a.get('nombre') or ''} "
                          f"({a.get('estado')}) {importe if importe else ''}"
                          f"{(' suelo ' + str(a.get('suelo'))) if a.get('suelo') else ''}"
                          f"{(' (' + str(a.get('motivo')) + ')') if a.get('motivo') else ''}")
        for h in _lista(r.get("hechas")):
            lineas.append(f"  hecha {h.get('accion')} {h.get('player_id')} exito={h.get('exito')} "
                          f"http={h.get('http_status')} {h.get('error') or ''}")
    except Exception as error:                      # noqa: BLE001
        lineas.append(f"  (el parte no se pudo escribir: {type(error).__name__})")
    return lineas


def main() -> int:
    r = correr()
    # Encendido, SIEMPRE (tambien sin nada hecho): lo de esta vuelta, para
    # la rotacion. Apagado no se escribe (la rotacion no lo echa de menos).
    try:
        if r.get("activa"):
            from src.actions.la_mejora_del_once import escribir_la_vuelta

            escribir_la_vuelta(r.get("hechas") or [], VUELTA_PARTE)
    except Exception:                               # noqa: BLE001
        pass
    print("=" * 100)
    print("EL PARTE VENDE")
    print("=" * 100)
    for linea in el_parte(r):
        print(linea)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
