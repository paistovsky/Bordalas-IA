"""
La puerta de validacion: las 66 guardias, en un solo sitio.

POR QUE LA LISTA VIVE AQUI Y NO EN EL WORKFLOW

    Hasta el 07/09/2026 era al reves: las 66 lineas estaban
    escritas a mano en `.github/workflows/bordalas-live.yml` y
    este script las leia de ahi con una expresion regular. La
    idea era buena -una sola fuente de verdad- pero el sitio era
    el equivocado.

    Con la lista en el YAML, cada guardia nueva habia que
    acordarse de ponerla en DOS sitios: el fichero del test y el
    workflow. Y el dia que se olvidara, CI habria corrido menos
    guardias que el dueño en local SIN AVISAR DE NADA: el paso
    habria salido verde por no haber ejecutado lo que faltaba.

    Un fallo silencioso, que es la clase mas cara.

    Ahora la lista esta aqui, el workflow llama a este script, y
    añadir una guardia es tocar una sola linea.

COMO SE AÑADE UNA GUARDIA

    Una linea en `TESTS`. Nada mas.

CODIGO DE SALIDA

    0 si pasan todas, 1 si falla cualquiera. De eso depende que
    el workflow pare el ciclo, asi que hay una guardia que lo
    comprueba: `test_puerta_una_sola_lista_v1`.

DOCTRINA 52: LA VERJA SE CORRE A FICHERO, NUNCA A `tail`
(14/09/2026)

    En una tuberia el codigo de salida es el del ULTIMO mandato.
    Corriendo esto asi:

        python scripts/run_validation_gate.py | tail -25

    `tail` devuelve 0 SIEMPRE. Tres vueltas seguidas dieron
    "exit 0" con una guardia en rojo, y el rojo estaba impreso
    mas arriba de las veinticinco lineas que se miraban.

    Es el mismo fallo silencioso que esta cabecera cuenta del
    workflow, pero en la mano de quien la corre: verde por no
    haber mirado, no por haber pasado.

    Asi que:

        python scripts/run_validation_gate.py > salida.txt 2>&1
        echo $?

    La salida a fichero y el codigo mirado. Si no, no se ha
    corrido.

USO

    python scripts/run_validation_gate.py

    Parar en el primer fallo:

    python scripts/run_validation_gate.py --parar
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

# LA RAIZ, EN EL CAMINO (13/09/2026)
#
#     `python scripts/run_validation_gate.py` pone `scripts/` en
#     `sys.path`, NO la raiz. Asi que el import del censo de mas
#     abajo fallaba —ModuleNotFoundError— y caia a su `except`,
#     dejando la lista VACIA: no se perdonaba ninguna y la verja
#     fallaba por las 30.
#
#     No se vio antes porque yo lo corria con `PYTHONPATH=.` y
#     con `python -c`, que si mete el directorio actual. Dos
#     formas de arrancar lo mismo y solo una reproduce CI.
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# ============================================================
# LAS GUARDIAS
# ============================================================
#
#     El orden es el que tenian en el workflow: primero las del
#     ciclo, despues los candados de la auditoria del 15/08/2026
#     y al final lo que se ha ido añadiendo por noches.

# ============================================================
# LAS QUE NO ESTAN, Y POR QUE
# ============================================================
#
# Una guardia comentada dentro de una lista de 200 lineas se
# vuelve invisible en dos dias. Aqui arriba, con su motivo y su
# fecha, no.
#
# Esta lista SOLO deberia encoger, y cada entrada es una promesa
# a plazo: mientras algo este aqui, eso NO se comprueba.
RETIRADAS = {
    "src.analysis.test_la_pantalla_pinta_v1": (
        "10/09/2026. Monta los componentes de Inicio con "
        "`renderToString`. Se puso en rojo en CI dos intentos "
        "seguidos y la verja corre ANTES del ciclo: dejarla "
        "habria costado la manana en que la ventana del reset se "
        "abre por primera vez. En local pasa 3/3 con y sin la "
        "foto real, asi que lo que revienta es el runner, no la "
        "guardia. El log solo dejo el pie 'Node.js v24.20.0' y "
        "las lineas del error quedaron por encima. Primera "
        "sospecha para manana: que `node_modules` no llegue "
        "entero al runner. MIENTRAS ESTE AQUI, LA PANTALLA NO SE "
        "COMPRUEBA EN CI."
    ),
}


TESTS = [
    "src.analysis.test_jp_profile_scope_v114",
    "src.analysis.test_multisource_starter_v1124",
    "src.analysis.test_v10_full_autonomous_live",
    "src.analysis.test_live_solvency_authority_v115",
    "src.telemetry.test_dashboard_execution_v121",
    "src.analysis.test_solvency_deadlock_v1",
    "src.analysis.test_write_path_guards_v1",
    "src.analysis.test_negotiation_persistence_v1",
    "src.analysis.test_bid_deduplication_v1",
    "src.analysis.test_source_accuracy_v1",
    "src.analysis.test_write_verification_v1",
    "src.analysis.test_protection_gate_v1",
    "src.analysis.test_reroll_memory_v1",
    "src.analysis.test_ledger_dedup_v1",
    "src.analysis.test_market_clock_v1",
    "src.analysis.test_position_guardrail_v1",
    "src.analysis.test_speculation_budget_v1",
    "src.analysis.test_bid_exposure_v1",
    "src.analysis.test_bid_targets_v1",
    "src.analysis.test_external_name_safety_v1",
    "src.analysis.test_portfolio_budget_v1",
    "src.analysis.test_roster_plan_guardrail_v1",
    "src.analysis.test_rival_bid_model_v1",
    "src.analysis.test_player_value_v1",
    "src.analysis.test_acquisition_wiring_v1",
    "src.analysis.test_bid_visibility_v1",
    "src.analysis.test_dashboard_truth_v1",
    # LOS INTOCABLES, DEROGADOS (dueño, 21/09/2026)
    #
    #     Aqui corria `src.analysis.test_intocables_v1`, que
    #     vigilaba la lista de jugadores que Pepe no podia vender
    #     -de Clave para arriba- ordenada por el dueño el 18/08.
    #     Protegia a cinco de catorce: Yamal, Exposito,
    #     Olasagasti, Djene y el portero titular.
    #
    #     El dueño la retira el 21/09/2026. Se quita de aqui a
    #     proposito y no se silencia: la lista ya no existe, asi
    #     que su guardia tampoco tiene que existir.
    #
    #     Lo que la sustituye NO es otra lista, es una cuenta:
    #     `test_calidad_y_porteria_v1`, que exige que lo que entra
    #     CABE EN EL ONCE antes de soltar a un grande, y que
    #     ademas conserva las cuatro comprobaciones de aquella
    #     guardia que nunca fueron una lista -el accidente del
    #     12/09 con `in_lineup`/`is_starter`, el portero titular,
    #     el "sin escalon no se vende" y que los vetados se vean-.
    "src.analysis.test_calidad_y_porteria_v1",
    "src.analysis.test_encender_calidad_v1",
    "src.analysis.test_balon_parado_v1",
    "src.analysis.test_rueda_v1",
    "src.analysis.test_que_gire_v1",
    "src.analysis.test_calibracion_larga_v1",
    "src.analysis.test_mercado_rivales_v1",
    "src.analysis.test_peticiones_v1",
    "src.analysis.test_la_subasta_v1",
    "src.analysis.test_prima_de_puja_v1",

    # Las puertas del dia que se encendieron las pujas: el
    # interruptor, el reloj de solvencia por encima de todo, el
    # tope de tres del primer dia, el peor caso contando la
    # plantilla, y que la compra a rivales siga cerrada.
    "src.analysis.test_encender_las_pujas_v1",

    # La regla que salio de emparejar las compras con sus ventas
    # en el tablon de los ocho: no se compra para revender a
    # quien no consta que vaya a jugar. Apagada.
    "src.analysis.test_la_regla_de_compra_v1",

    # El dia despues de las seis compras del 21/09: cerrar la
    # reventa sin cerrar la compra para quedarse, y que el tope
    # de tres sea por VENTANA y no por vuelta.
    "src.analysis.test_el_corte_y_el_cupo_v1",

    # Cada via cobra en su moneda: al que se queda le paga la
    # liga a 30.000 el punto, no el mercado a 18.300. Apagado.
    "src.analysis.test_la_moneda_del_fichaje_v1",

    # El que publica: que salga la cola de venta que ya esta
    # calculada, en su orden, y sin el once. Apagado.
    "src.analysis.test_el_que_publica_v1",

    # La prioridad de pujar por el reloj: dentro de la ventana la
    # puja no pierde contra un tramite, fuera pierde. Apagada.
    "src.analysis.test_la_hora_de_pujar_v1",

    # Que la vuelta se apunte entera —las candidatas que pierden y
    # lo que costo en peticiones— para dejar de reconstruirla.
    "src.analysis.test_la_vuelta_se_apunta_v1",
    "src.analysis.test_intel_v1",
    "src.analysis.test_calendario_v1",
    "src.analysis.test_cobrar_ofertas_v1",

    # El dia que Pepe empezo a escribir: renovar en la ventana,
    # la zona de silencio y que renovar no pueda vender.
    "src.analysis.test_renovar_en_la_ventana_v1",

    # La primera ruta que VENDE sola: las cinco prohibiciones,
    # cada una con su nombre, y la marca VIAJE como unico
    # permiso.
    "src.analysis.test_la_salida_del_viaje_v1",

    # El dia que se vio que la ventana no se habia abierto nunca
    # y que `FUERA_DE_VENTANA` no se distinguia de una noche
    # normal.
    "src.analysis.test_una_ventana_que_no_se_abre_v1",
    "src.analysis.test_ciclo_una_sola_vez_v1",
    "src.analysis.test_escrituras_con_cuerpo_v1",
    "src.analysis.test_cambiar_titular_v1",
    "src.analysis.test_suelo_de_titulares_v1",
    "src.analysis.test_marcador_v1",
    "src.analysis.test_plantillas_rivales_v1",

    # El dia que una puja del dueno dejo a la liga entera en
    # bancarrota: la linea de credito es un numero medido, no se
    # deduce de un maximumBid contaminado.
    "src.analysis.test_linea_de_credito_v1",
    "src.analysis.test_abono_jornada_v1",
    "src.analysis.test_mercado_completo_v1",
    "src.analysis.test_pujar_por_el_xi_v1",
    "src.analysis.test_once_real_v1",
    "src.analysis.test_presupuesto_de_fichar_v1",
    "src.analysis.test_reventa_al_computer_v1",
    "src.analysis.test_once_de_verdad_v1",
    "src.analysis.test_correccion_jerarquia_v1",
    "src.analysis.test_contraoferta_v1",
    "src.analysis.test_escritura_contada_v1",
    "src.analysis.test_nombre_corto_v1",
    "src.analysis.test_action_starvation_v1",
    "src.analysis.test_price_history_store_v1",
    "src.analysis.test_futbolfantasy_source_v12",
    "src.analysis.test_starter_aware_xi_v1",
    "src.analysis.test_bid_outcome_ledger_v1",
    "src.analysis.test_etiqueta_vigilar_v1",
    "src.analysis.test_jornada_del_tablero_v1",
    "src.analysis.test_plantillas_rivales_llenas_v1",
    "src.analysis.test_penaltis_apagados_v1",
    "src.analysis.test_tope_por_operacion_v1",
    "src.analysis.test_jornada_en_la_valoracion_v1",
    "src.analysis.test_estado_de_carrera_v1",
    "src.analysis.test_valor_temporada_sombra_v1",
    "src.analysis.test_ampliar_plantilla_sombra_v1",
    "src.analysis.test_dashboard_orden_de_variables_v1",
    "src.analysis.test_pantalla_lee_lo_publicado_v1",
    "src.analysis.test_posibles_cambios_v1",
    "src.analysis.test_lo_desconocido_v1",
    "src.analysis.test_el_ciclo_publica_v1",
    # RETIRADA LA NOCHE DEL 10/09/2026. No borrada: retirada.
    #
    #     Se puso en rojo en CI dos intentos seguidos y la verja
    #     corre ANTES del ciclo, asi que la manana en que la
    #     ventana del reset se abre por primera vez Pepe no
    #     habria pujado ni renovado. Vale mas una guardia menos
    #     que el bot parado esa noche.
    #
    #     Sigue estando entera y pasa en local (3/3, con y sin la
    #     foto real). Lo que no sabemos es por que revienta en el
    #     runner: el log solo enseña el pie "Node.js v24.20.0" y
    #     las lineas que importan quedaron por encima.
    #
    #     Se recupera manana, con el diagnostico delante. Esta
    #     apuntada en DEUDA para que no se quede aqui de adorno.
    # "src.analysis.test_la_pantalla_pinta_v1",
    "src.analysis.test_la_caja_de_la_liga_v1",
    "src.analysis.test_el_dinero_cuadra_v1",
    "src.analysis.test_la_prima_de_compra_v1",
    "src.analysis.test_el_ojeador_conectado_v1",
    "src.analysis.test_la_etiqueta_dice_lo_que_mide_v1",
    "src.analysis.test_la_rendija_v1",
    "src.analysis.test_esta_enchufado_v1",
    "src.analysis.test_el_escaparate_publica_v1",
    "src.analysis.test_el_cuadro_de_objetivos_v1",
    "src.analysis.test_toda_la_liga_v1",
    "src.analysis.test_lo_nuestro_a_la_venta_v1",
    "src.analysis.test_la_columna_que_miente_v1",
    "src.analysis.test_la_pantalla_de_mercado_v1",
    "src.analysis.test_la_hoja_de_estilos_v1",
    "src.analysis.test_la_lista_blanca_v1",
    "src.analysis.test_cada_compra_sabe_de_que_via_vino_v1",
    "src.analysis.test_el_orden_distingue_tamano_v1",
    "src.analysis.test_la_prima_va_por_tramo_v1",
    "src.analysis.test_el_bucle_de_la_vara_v1",
    "src.analysis.test_la_cesta_solo_el_suelo_v1",
    "src.analysis.test_la_lista_de_objetivos_v1",
    "src.analysis.test_el_liston_del_manager_v1",
    "src.analysis.test_el_marcador_por_su_fecha_v1",
    "src.analysis.test_una_jornada_sin_once_no_cuadra_v1",
    # LA CARA SALE DE LA VERJA Y SE VUELVE EL PASO 0
    # (21/09/2026, dueño)
    #
    #     Aqui corria
    #     `test_ninguna_guardia_depende_del_entorno_v1`. No se
    #     borra: se muda a `EL_PASO_0`, ahi abajo.
    #
    #     EL NUMERO QUE LA DEFENDIA ERA DE OTRA MAQUINA
    #     (doctrina 90)
    #
    #         Su cabecera decia "esta guardia, ella sola: 275 s"
    #         y "la verja CON ella: 480 s". Los dos son del
    #         portatil del dueño. En el runner de GitHub la
    #         verja entera tarda 21 m 52 s, y esta guardia
    #         —que corre la verja OTRA VEZ por dentro— se lleva
    #         1.312 de esos segundos.
    #
    #         Un numero medido en una maquina aplicado a otra es
    #         un numero que se recibe, no uno que se mide.
    #
    #     Y LO QUE COMPRABA POR HORA ERA CERO
    #
    #         La verja corre DENTRO del job, con el `env` de
    #         produccion puesto. Un interruptor que ya esta
    #         encendido en el YAML y que rompe guardias las
    #         rompe en la corrida de verdad: eso es exactamente
    #         lo que paso el 20/09 —«102/167 FALLA
    #         test_la_lista_de_objetivos_v1»— y lo cazo la verja
    #         normal, no esta.
    #
    #         Lo unico que esta añade es el aviso ANTICIPADO
    #         sobre los interruptores que TODAVIA NO estan en el
    #         YAML. Eso es una comprobacion previa al despegue,
    #         y una comprobacion previa no se corre 24 veces al
    #         dia para un despegue que hay una vez por semana.
    #
    #     LO QUE LA SUSTITUYE, para que no dependa de que
    #     alguien se acuerde: `test_el_paso_0_no_se_olvida_v1`,
    #     aqui debajo. Lee el YAML —versionado— y el registro de
    #     lo que ya paso el paso 0, y se pone roja si el YAML
    #     enciende algo que nadie probo.
    "src.analysis.test_el_paso_0_no_se_olvida_v1",
    "src.analysis.test_solo_un_interruptor_por_vuelta_v1",
    "src.analysis.test_ninguna_pasa_con_las_manos_vacias_v1",
    "src.analysis.test_los_sentidos_v1",
    "src.analysis.test_la_alarma_de_los_sentidos_v1",
    "src.analysis.test_el_calendario_v1",
    "src.analysis.test_los_rivales_v1",
    "src.analysis.test_la_puerta_de_los_managers_v1",
    "src.analysis.test_el_reloj_de_las_guardias_v1",
    "src.analysis.test_el_once_que_jugo_v1",
    "src.analysis.test_el_orden_del_tiempo_v1",
    "src.analysis.test_el_vestuario_libre_v1",
    "src.analysis.test_los_libros_v1",
    "src.analysis.test_el_empujon_que_no_mata_v1",
    "src.analysis.test_el_plato_del_carril_v1",
    "src.analysis.test_la_puja_del_carril_v1",
    "src.analysis.test_los_dos_techos_v1",
    "src.analysis.test_el_libro_sabe_perder_v1",
    "src.analysis.test_el_libro_recoge_v1",
    "src.analysis.test_el_reloj_de_48h_v1",
    "src.analysis.test_los_relojes_v1",
    "src.analysis.test_ojeador_fuentes_v1",
    "src.analysis.test_ojeador_emparejamiento_v1",
    "src.analysis.test_ojeador_informe_v1",
    "src.analysis.test_divergencia_v1",
    "src.analysis.test_puerta_una_sola_lista_v1",
    "src.analysis.test_freno_acelerador_v1",
    "src.analysis.test_freno_de_mano_v1",
    "src.analysis.test_confianza_por_via_v1",
    "src.analysis.test_despliegue_v1",
    "src.analysis.test_orden_de_venta_v1",
    "src.analysis.test_reloj_solvencia_v1",

    # El dia que el dueno pujo a mano y Pepe no se entero: las
    # tres vias para ver una puja, la linea de credito medida y
    # la deuda contingente.
    "src.analysis.test_pujas_del_dueno_v1",
    "src.analysis.test_venta_ejecutable_v1",
    "src.analysis.test_ojeador_prensa_v1",
    "src.analysis.test_motivo_del_tablero_v1",
    "src.analysis.test_puja_impredecible_v1",
    "src.analysis.test_retrotest_rampa_v1",
    "src.analysis.test_no_contar_dos_veces_v1",
    "src.analysis.test_fuera_de_muestra_v1",
    "src.analysis.test_tope_deducido_v1",
    "src.analysis.test_arbitro_v1",
    "src.analysis.test_verja_determinista_v1",
    "src.analysis.test_once_v1",
    "src.analysis.test_interruptor_tener_v1",
    "src.analysis.test_vara_v1",
    "src.analysis.test_forma_estable_v1",

    # El dia que el 0,1443 % resulto ser el valor de reventa al
    # Computer con otro nombre: el plazo de cada par, los dias
    # planos en el denominador y la masa de verdad de la curva.
    "src.analysis.test_los_tres_denominadores_v1",

    # El `intent` prestado, el denominador del libro de acierto y
    # los pesos de la curva: los tres arreglos que no tocan
    # ningun umbral.
    "src.analysis.test_los_tres_arreglos_v1",

    # Comprar un jugador y vendérselo al Computer: una sola
    # definicion, y las dos primas sobre los mismos viajes.
    "src.analysis.test_el_viaje_al_computer_v1",

    # La regla del carril del Computer: sale de la medicion, no
    # de una constante, y sigue apagada.
    "src.analysis.test_el_carril_de_un_dia_v1",

    # El cable entre la cola de venta y el presupuesto de fichar,
    # el techo de Biwenger medido, el motivo que no se corta y la
    # prima del Computer partida por tramo.
    "src.analysis.test_la_plaza_y_el_cable_v1",

    # El cable tendido: las dos cajas separadas, ninguna puja
    # contra dinero no cobrado, la cola por consecuencia y las
    # fichas libres contra el maximo historico.
    "src.analysis.test_el_cable_v1",

    # De quien es cada jugador de la lista, el orden de las
    # operaciones y el guardarrail mirando titularidad.
    "src.analysis.test_la_lista_de_la_compra_v1",

    # Como rota el escaparate y si estabamos alli: la rotacion
    # sale de censos guardados, no de la foto de hoy.
    "src.analysis.test_el_escaparate_v1",

    # El libro del escaparate -una linea por reset, sin duplicar-
    # y el mapa de que freno cuelga de cada `intent`.
    "src.analysis.test_el_proposito_v1",

    # Lo que cuesta de verdad tener a un jugador, y que la verja
    # deje de escribir en los libros.
    "src.analysis.test_el_carry_v1",
    "src.analysis.test_la_direccion_v1",
    "src.analysis.test_empezar_a_anotar_v1",
    "src.analysis.test_la_escala_v1",

    # Un jugador sin pronostico no desplaza del XI a uno con
    # pronostico en su puesto. El 18/09/2026 el tercer portero del
    # Atletico, sin una sola fuente, sentaba a Dituro.
    "src.analysis.test_sin_pronostico_v1",

    # Si la caja no cuadra, se publica el evento sospechoso y su
    # tipo, no solo el numero. El 18/09/2026 el descuadre de
    # 420.200 EUR era una venta nuestra contada dos veces.
    "src.analysis.test_la_caja_cuadra_o_dice_por_que_v1",

    # La reja de duplicados sin la fecha dentro: colapsa la
    # reemision del tablon y NO se come dos operaciones reales.
    "src.analysis.test_la_reja_no_se_come_dos_operaciones_reales_v1",
    "src.analysis.test_la_caja_cuadra_con_la_real_v1",

    # Doctrina 85: el suelo del que no tiene pronostico se deriva
    # de los pesos que lo sostienen, no se escribe a mano.
    "src.analysis.test_el_suelo_sigue_a_su_escalera_v1",

    "src.analysis.test_doctrina_v1",

    # El plazo de la solvencia sale del calendario, con su fecha,
    # o dice "no lo se". El 23/09 frenaba "el viernes" con la
    # jornada a 16 dias.
    "src.analysis.test_el_plazo_sale_del_calendario_v1",

    # El que vuelve de lesion no es un malo: la marca de «su pasado
    # se queda corto», con sus dos frenos, y la lista del dia.
    "src.analysis.test_el_que_va_a_despegar_v1",

    # La sombra de la puja: a quien pujaria Pepe con los candados
    # levantados, sin una sola escritura.
    "src.analysis.test_la_sombra_de_la_puja_v1",

    # El libro de aciertos de la valoracion y la foto de cada
    # jornada: sin ellos no se toca ninguna formula de valoracion.
    "src.analysis.test_el_libro_de_la_valoracion_v1",
]


# ============================================================
# EL PASO 0: LO QUE SE CORRE A MANO, ANTES DE TOCAR EL YAML
# ============================================================
#
#     NO ES UNA LISTA DE GUARDIAS RETIRADAS. `RETIRADAS` es eso,
#     y significa "esto NO se comprueba". Esto significa otra
#     cosa: se comprueba, pero no cada hora — se comprueba antes
#     de encender un interruptor, que es el unico momento en que
#     la respuesta puede cambiar.
#
#         python scripts/run_validation_gate.py --paso-0
#
#     Ese mandato la corre y, si pasa, apunta en
#     `config/paso_0.json` que interruptores quedan probados. Ese
#     fichero va a git junto con el cambio del YAML.
#
#     LO QUE VIAJA DE UNA MAQUINA A OTRA ES EL VEREDICTO, NO LOS
#     SEGUNDOS. Que la verja salga verde con un interruptor
#     puesto no depende del runner —para eso esta
#     `test_verja_determinista_v1`—; lo que si depende, y mucho,
#     es lo que tarda.
EL_PASO_0 = [
    "src.analysis.test_ninguna_guardia_depende_del_entorno_v1",
]


# Donde el paso 0 apunta lo que ha probado. Versionado a
# proposito: es lo que `test_el_paso_0_no_se_olvida_v1` lee para
# saber si el YAML enciende algo sin probar.
REGISTRO_DEL_PASO_0 = RAIZ / "config" / "paso_0.json"


WORKFLOW = None   # ya no se lee de ningun sitio: la lista es esta.


def modulos_del_workflow() -> list[str]:
    """
    Se conserva el nombre por compatibilidad con quien lo llame.

    Devuelve la lista de este fichero, que es la unica que hay.
    """

    return list(TESTS)


# ============================================================
# EL VEREDICTO, A FICHERO (20/09/2026)
# ============================================================
#
#     Los tres commits del 19/09 por la noche no dicen si la
#     verja paso. Dos de ellos la rompieron —cinco rojas a la
#     mañana siguiente— y la cazamos de casualidad, porque
#     tocaba mirar otra cosa.
#
#     "Acordarse de ponerlo en el mensaje" no es un mecanismo.
#     Asi que la verja deja aqui lo que hizo, y el hook
#     `prepare-commit-msg` lo pega en el mensaje solo.
#
#     LO QUE SE GUARDA ES LA HUELLA DEL ARBOL, NO LA HORA
#
#         Una hora no dice si la verja se corrio sobre ESTE
#         codigo. Se guarda el SHA-256 de todos los `.py` de
#         `src/` y `scripts/` mas los ficheros del panel: si
#         luego se toca una linea, la huella cambia y el hook
#         escribe "el arbol cambio despues", que es la verdad.
#
#     No es un libro y no va a git: vive en `.verja/`, ignorado.
VEREDICTO = RAIZ / ".verja" / "ultima.json"


def _sin_finales_de_linea(ruta) -> bytes:
    """El contenido con CRLF y CR pasados a LF."""

    crudo = ruta.read_bytes()

    return crudo.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def huella_del_arbol() -> str:
    """
    SHA-256 de lo que la verja vigila. Nunca lanza.

    Si no se puede calcular, devuelve "?" — y el hook lee eso
    como "no se sabe", que no es "esta bien" (doctrina 24).
    """

    try:
        import hashlib

        digest = hashlib.sha256()

        rutas = []

        for patron in ("src/**/*.py", "scripts/**/*.py",
                       "dashboard-v8/src/**/*.js"):
            rutas.extend(RAIZ.glob(patron))

        for ruta in sorted(rutas):

            if "__pycache__" in ruta.parts:
                continue

            digest.update(
                str(ruta.relative_to(RAIZ)).encode("utf-8")
            )

            # LOS FINALES DE LINEA SE NORMALIZAN (20/09/2026)
            #
            #     `git checkout -- fichero` lo reescribe con CRLF
            #     en Windows. Los bytes cambian, el codigo no, y
            #     la huella decia "el arbol cambio despues" por
            #     una restauracion que no movio una instruccion.
            #     Paso en el primer commit que uso esto.
            #
            #     Es la misma falsa alarma que este mismo dia
            #     hemos quitado de dos guardias. Se compara el
            #     CONTENIDO, no el fichero.
            digest.update(_sin_finales_de_linea(ruta))

        return digest.hexdigest()

    except Exception:                               # noqa: BLE001
        return "?"


# UNA VERJA DENTRO DE OTRA NO APUNTA EL VEREDICTO (20/09/2026)
#
#     `test_ninguna_guardia_depende_del_entorno_v1` corre esta
#     verja otra vez, con todos los interruptores puestos, para
#     comprobar que el veredicto no cambia. Si esa corrida de
#     dentro escribiese `.verja/ultima.json`, el mensaje del
#     commit contaria la de dentro —parcial y con el entorno
#     retorcido— en vez de la de verdad.
#
#     No es un `BORDALAS_*` a proposito: no es un interruptor de
#     comportamiento, es como se llama a si misma.
ANIDADA = "VERJA_ANIDADA"


def _apuntar_el_veredicto(
    verdes: int, total: int, fallos: list, parcial: bool
) -> None:
    """Lo que hizo la verja, para el mensaje del commit. Nunca lanza."""

    if str(os.environ.get(ANIDADA, "")).strip() == "1":
        return

    try:
        from datetime import datetime, timezone

        VEREDICTO.parent.mkdir(parents=True, exist_ok=True)

        VEREDICTO.write_text(
            json.dumps(
                {
                    "cuando": datetime.now(
                        timezone.utc
                    ).isoformat(timespec="seconds"),
                    "verdes": verdes,
                    "total": total,
                    "fallos": sorted(fallos),
                    # Una corrida con `--solo` o `--extra` no es
                    # la verja: se marca para que el mensaje no
                    # pueda presumir de un verde que no es.
                    "parcial": parcial,
                    "huella": huella_del_arbol(),
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )

    except Exception as error:                      # noqa: BLE001
        print(
            f"AVISO: no se pudo apuntar el veredicto de la verja "
            f"({type(error).__name__}): el commit dira que no se "
            f"sabe."
        )


# ============================================================
# EL PASO 0, A MANO
# ============================================================


def _correr_el_paso_0(parar: bool = False) -> int:
    """
    La comprobacion cara, a mano, y su registro.

    Devuelve 0 si pasa. Si pasa, apunta en
    `config/paso_0.json` QUE interruptores quedan probados: los
    del inventario entero, porque eso es lo que la guardia pone
    -todos a la vez- y por tanto lo que prueba.
    """

    import time

    print("EL PASO 0")
    print("=" * 66)
    print(
        "  La verja entera, otra vez, con TODOS los "
        "interruptores puestos."
    )
    # SIN NOMBRAR EL FICHERO DEL WORKFLOW
    #
    #     `test_la_puerta_no_lee_el_workflow` mira los literales
    #     de este script -no sus docstrings- y se pone roja si
    #     alguno nombra el YAML: esa es la señal de que la lista
    #     ha vuelto al sitio equivocado. La frase dice lo mismo
    #     sin dar pie al falso positivo.
    print(
        "  Va antes de tocar el `env` del workflow de CI."
    )
    print()

    arranco = time.perf_counter()

    fallos = []

    for indice, modulo in enumerate(EL_PASO_0, start=1):

        proceso = subprocess.run(
            [sys.executable, "-m", modulo],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(RAIZ),
        )

        corto = modulo.rsplit(".", 1)[-1]

        salida = (
            (proceso.stdout or "") + (proceso.stderr or "")
        ).strip().splitlines()

        # LA REGLA DE LA VERJA TAMBIEN AQUI: una que no imprime
        # nada no ha probado nada (doctrina 24).
        if proceso.returncode == 0 and not salida:
            print(f"  {indice}/{len(EL_PASO_0)}  MUDA  {corto}")
            fallos.append(modulo)
            continue

        if proceso.returncode == 0:
            print(f"  {indice}/{len(EL_PASO_0)}  OK    {corto}")

        else:
            print(f"  {indice}/{len(EL_PASO_0)}  FALLA {corto}")

            for linea in salida:
                if linea.lstrip().startswith("FALLA"):
                    # LA CONSOLA DE WINDOWS NO ES UTF-8
                    #
                    #     El motivo de una guardia trae guiones
                    #     largos y tildes. Con `cp1252` de salida,
                    #     `print` revienta con UnicodeEncodeError
                    #     y el paso 0 se cae ENSEÑANDO UN
                    #     TRACEBACK EN VEZ DEL MOTIVO, que es
                    #     justo lo contrario de lo que hace falta
                    #     en ese momento. Paso el 21/09/2026.
                    print(
                        "        -> "
                        + linea.strip()[:400].encode(
                            sys.stdout.encoding or "utf-8",
                            errors="replace",
                        ).decode(
                            sys.stdout.encoding or "utf-8",
                            errors="replace",
                        )
                    )

            fallos.append(modulo)

            if parar:
                break

    tardo = time.perf_counter() - arranco

    print("=" * 66)
    print(f"EL PASO 0 HA TARDADO {tardo:.0f} s ({tardo / 60:.1f} min).")

    if fallos:
        print()
        print(
            "NO SE ENCIENDE NADA. Con los interruptores puestos "
            "la verja no da el mismo verde que sin ellos."
        )
        return 1

    probados = _apuntar_el_paso_0(tardo)

    print()
    print(
        f"PASADO. Quedan probados {len(probados)} interruptores, "
        f"apuntados en "
        f"{REGISTRO_DEL_PASO_0.relative_to(RAIZ).as_posix()}."
    )
    print(
        "  Ese fichero va a git EN EL MISMO COMMIT que el cambio "
        "del YAML. Si no va, la verja se pondra roja en la "
        "primera vuelta y el ciclo no correra."
    )

    return 0


def _apuntar_el_paso_0(segundos: float) -> list:
    """
    Lo que acaba de quedar probado. Nunca lanza.

    Se apunta el INVENTARIO ENTERO porque eso es lo que la
    guardia pone: los 21 a la vez. Apuntar solo el que el dueño
    tenia en la cabeza seria apuntar menos de lo comprobado.
    """

    try:
        from datetime import datetime, timezone

        sys.path.insert(0, str(RAIZ))

        from scripts.los_interruptores import inventario

        probados = sorted(inventario())

        REGISTRO_DEL_PASO_0.parent.mkdir(
            parents=True, exist_ok=True
        )

        REGISTRO_DEL_PASO_0.write_text(
            json.dumps(
                {
                    "version": 1,

                    # LO QUE VIAJA ES EL VEREDICTO, NO EL RELOJ.
                    # Los segundos se apuntan para poder verlos,
                    # y se dice de que maquina salen: un numero
                    # sin su maquina es un numero que engaña
                    # (doctrina 90).
                    "cuando": datetime.now(
                        timezone.utc
                    ).isoformat(timespec="seconds"),
                    "segundos": round(segundos, 1),
                    "maquina": (
                        f"{platform.system()} "
                        f"{platform.machine()}"
                    ),

                    "probados": probados,

                    # El arbol sobre el que se probo. No decide
                    # nada -si decidiera, cada linea tocada
                    # pondria el ciclo en rojo-, pero deja ver
                    # de cuando es la prueba.
                    "huella": huella_del_arbol(),
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )

        return probados

    except Exception as error:                      # noqa: BLE001
        print(
            f"AVISO: no se pudo apuntar el paso 0 "
            f"({type(error).__name__}): el registro no ha "
            f"cambiado, asi que la guardia seguira diciendo que "
            f"falta."
        )
        return []


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--parar",
        action="store_true",
        help="detenerse en el primer fallo",
    )

    parser.add_argument(
        "--extra",
        nargs="*",
        default=[],
        help="guardias adicionales, sueltas, para probar a mano",
    )

    parser.add_argument(
        "--solo",
        nargs="*",
        default=None,
        help=(
            "correr SOLO estas guardias, en vez de la lista entera. "
            "Para probar una a mano sin esperar a las 68."
        ),
    )

    parser.add_argument(
        "--paso-0",
        dest="paso_0",
        action="store_true",
        help=(
            "correr EL PASO 0 en vez de la verja: la "
            "comprobacion cara que se hace ANTES de encender un "
            "interruptor en el YAML. Si pasa, apunta en "
            "config/paso_0.json que interruptores quedan "
            "probados."
        ),
    )

    args = parser.parse_args()

    if args.paso_0:
        return _correr_el_paso_0(parar=args.parar)

    modulos = list(args.solo) if args.solo else list(TESTS)

    for extra in (args.extra or []):
        if extra not in modulos:
            modulos.append(extra)

    # Sin lista no se puede dar verde: seria decir "todo bien"
    # por no haber mirado nada, que es justo el fallo que este
    # cambio viene a cerrar.
    if not modulos:
        print("La lista de guardias esta vacia: eso no es un exito.")
        return 1

    print(f"Puerta de validacion: {len(modulos)} tests")
    print("=" * 66)

    # EL RELOJ DE LA VERJA SE ENSEÑA, NO DECIDE (21/09/2026)
    #
    #     El dueño pregunto por una guardia que fallase al
    #     pasarse de un tope declarado. No se ha hecho, y el
    #     motivo esta en el encargo mismo: un tope seria un
    #     numero medido en una maquina y aplicado a otra
    #     —doctrina 90—, y aqui la diferencia es de 2,9 veces
    #     (medido el 21/09: 7 m 30 s en el portatil, 21 m 52 s
    #     en el runner, las mismas 171 guardias).
    #
    #     Ademas una guardia que mide tiempo MIRA EL RELOJ DEL
    #     SISTEMA, que es justo lo que esta casa le prohibe a una
    #     guardia.
    #
    #     Lo que si hace falta es que el numero ESTE en cada
    #     registro de CI, para poder verlo crecer. Eso es este
    #     reloj: lo imprime el corredor, que no es una guardia, y
    #     no decide nada.
    import time

    arranco = time.perf_counter()

    fallos = []

    # Lo que ha abierto cada guardia. Se imprime SIEMPRE.
    censadas = {}

    # EL VIGILANTE DE `data/` (13/09/2026)
    #
    #     Viaja DENTRO de la ejecucion que ya se hace: Python
    #     importa `sitecustomize` solo al arrancar, y cada
    #     guardia ya corre en su propio proceso. Coste cero.
    #
    #     Una guardia que corriera las otras 119 para vigilarlas
    #     duplicaria la verja entera —medido: no termina en diez
    #     minutos— y una verja lenta se acaba saltando.
    entorno = dict(os.environ)

    entorno["BORDALAS_VIGILA_DATA"] = "1"

    entorno["PYTHONPATH"] = os.pathsep.join(
        x
        for x in (
            str(RAIZ / "scripts" / "vigila_data"),
            entorno.get("PYTHONPATH") or "",
        )
        if x
    )

    # LAS QUE TIENEN PERMISO, Y POR ESCRITO. Una definicion.
    #
    #     `LEEN_DATA_HOY` es el censo del 13/09: 28 guardias que
    #     abren `data/` al correrse. No se perdonan, se cuentan —
    #     y el vigilante falla por CUALQUIERA QUE NO ESTE, que es
    #     lo que evita la proxima. La lista solo puede encoger.
    try:
        from src.analysis.test_verja_determinista_v1 import (
            CENSADAS_EL,
            DEUDA,
            LEEN_DATA_HOY,
            PUEDEN_ENCERRARLO,
        )

    except Exception as error:                      # noqa: BLE001
        # SIN CENSO NO SE PERDONA NADA, Y SE DICE. El 13/09 este
        # `except` se comio un ModuleNotFoundError en silencio y
        # la verja fallo por las 30.
        print(
            f"AVISO: no se pudo leer el censo de lecturas "
            f"({type(error).__name__}): no se perdonara ninguna."
        )

        DEUDA, LEEN_DATA_HOY = {}, frozenset()

        CENSADAS_EL, PUEDEN_ENCERRARLO = "?", {}

    for indice, modulo in enumerate(modulos, start=1):

        proceso = subprocess.run(
            [sys.executable, "-m", modulo],
            capture_output=True,
            text=True,
            env=entorno,
        )

        # LO QUE HA ABIERTO DE VERDAD.
        #
        #     Una guardia que lee `data/` no falla hoy: falla el
        #     dia que el bot trabaje. Asi que se trata como un
        #     fallo AHORA, con su nombre y su fichero.
        abiertos = sorted(
            {
                linea.split("VIGILANTE-DATA:", 1)[1].strip()
                for linea in (proceso.stderr or "").splitlines()
                if "VIGILANTE-DATA:" in linea
            }
        )

        # EL VIGILANTE AVISA Y NO TUMBA (13/09/2026)
        #
        #     Decision del dueño, y con el motivo escrito porque
        #     importa mas que la decision:
        #
        #     EL VIGILANTE MIDE DEUDA NUESTRA, no si el codigo
        #     funciona. Y llevaba cuatro horas siendo lo unico
        #     que tenia a Pepe parado, con ofertas sin cobrar y
        #     publicaciones sin renovar.
        #
        #     Un detector que apaga el bot el primer dia se acaba
        #     apagando el, y entonces no queda nada.
        #
        #     Y HAY UNA RAZON ESTRUCTURAL, ademas: el censo se
        #     construye en la maquina del dueño, donde esos
        #     ficheros no existen; en CI la cache los restaura y
        #     aparecen lecturas que aqui no se ven. Alguna —el
        #     archivo de prensa por fecha— trae un fichero nuevo
        #     cada dia, asi que el censo caducaria solo. EL CENSO
        #     NO SE PUEDE CONSTRUIR DESDE LOCAL.
        #
        #     Lo que SI tumba es una guardia rota. Eso no cambia.
        #
        #     Y lo que salva a este aviso de volverse ruido: el
        #     numero sale SIEMPRE, el censo solo puede ENCOGER, y
        #     las que pueden encerrar a Pepe —las que leen un
        #     fichero que el ciclo escribe— se arreglan una a
        #     una, cada una con su guardia propia y esa si roja.
        if abiertos:
            censadas[modulo] = abiertos

        corto = modulo.rsplit(".", 1)[-1]

        # UNA GUARDIA MUDA NO HA PROBADO NADA (14/09/2026)
        #
        #     La verja corre cada guardia como `python -m
        #     <modulo>`. Un fichero registrado que define sus
        #     `test_*` pero NO tiene un `if __name__ ==
        #     "__main__"` se importa, no ejecuta nada y devuelve
        #     0. La verja lo cuenta como OK.
        #
        #     Paso de verdad: `test_el_orden_del_tiempo_v1` se
        #     registro asi y salio "OK" durante un commit entero
        #     sin haberse ejecutado ni una vez. Pasaba al
        #     correrla a mano, asi que no se vio por ningun lado.
        #
        #     Es la tercera vez que aparece esta familia: el
        #     workflow con la lista a mano (07/09), el `tail` que
        #     devuelve 0 (doctrina 52) y esta. Siempre lo mismo
        #     —verde por no haber ejecutado, no por haber
        #     pasado— y siempre callada.
        #
        # LA REGLA, QUE ES HERMANA DE LA 24
        #
        #     Ninguna guardia pasa con las manos vacias, y
        #     ninguna pasa sin decir que ha probado. Si no
        #     imprime una sola linea, no cuenta como verde.
        #
        #     Medido sobre las 134 del 14/09: todas dicen algo.
        #     Tres de ellas corren al importar y sin `main`, y
        #     tambien imprimen — asi que la regla no obliga a una
        #     forma concreta de escribir la guardia, solo a que
        #     deje constancia.
        mudo = (
            proceso.returncode == 0
            and not (proceso.stdout or "").strip()
        )

        if mudo:
            print(
                f"  {indice:>2}/{len(modulos)}  MUDA  {corto}"
            )

            fallos.append(modulo)

            print(
                "             no imprimio nada: probablemente "
                "le falta `if __name__ == \"__main__\": main()` "
                "y no se ha ejecutado ninguna prueba"
            )

            continue

        if proceso.returncode == 0:
            print(f"  {indice:>2}/{len(modulos)}  OK    {corto}")

        else:
            print(f"  {indice:>2}/{len(modulos)}  FALLA {corto}")

            salida = (
                (proceso.stderr or "")
                + (proceso.stdout or "")
            ).strip().splitlines()

            # EL NOMBRE DE LA QUE FALLA, NO SOLO CUANTAS
            # (14/09/2026, madrugada)
            #
            #     El registro de CI decia "46/47" y nada mas: las
            #     seis ultimas lineas de un modulo son su propio
            #     banner de resumen, asi que el nombre de la
            #     subprueba se quedaba justo fuera de la ventana.
            #
            #     Hubo que correr el modulo suelto a mano para
            #     saber cual era. Veinte minutos, de madrugada, y
            #     con el reset encima.
            #
            #     UNA VERJA QUE DICE CUANTAS FALLAN Y NO CUAL NO
            #     ES UNA VERJA: ES UN AVISO.
            #
            #     Cada modulo de esta casa imprime "FALLA <nombre>:
            #     <motivo>" por subprueba. Se sacan TODAS, enteras
            #     y las primeras: el motivo de la primera suele
            #     explicar las demas.
            por_su_nombre = [
                linea
                for linea in salida
                if linea.lstrip().startswith("FALLA")
            ]

            for linea in por_su_nombre:
                print(f"        -> {linea.strip()[:400]}")

            # Y el final de la salida, para lo que no siga ese
            # formato: una excepcion, un import roto, un
            # `SystemExit` sin mensaje.
            if not por_su_nombre:
                for linea in salida[-8:]:
                    print(f"           {linea[:120]}")

            fallos.append(modulo)

            if args.parar:
                break

    print("=" * 66)

    # EL NUMERO, SIEMPRE, CON LAS RUTAS.
    #
    #     Un detector que el primer dia bloquea todo se acaba
    #     desactivando, y entonces no queda nada. Este no bloquea
    #     por las censadas — pero NO se calla: la deuda se ve en
    #     cada vuelta, con nombre y fichero, o deja de existir.
    if censadas:
        print()
        print(
            f"LEEN LA CARPETA DE ESTADO AL CORRERSE: "
            f"{len(censadas)} de {len(modulos)}"
        )
        print(
            "  (censadas el "
            + str(CENSADAS_EL)
            + "; la lista solo puede encoger)."
        )
        print(
            "  ESTO NO TUMBA LA VERJA: mide deuda nuestra, no "
            "si el codigo funciona."
        )

        for modulo in sorted(censadas):
            corto = modulo.rsplit(".", 1)[-1]

            # Las no censadas se marcan, que es lo que hace
            # util el aviso: la deuda vieja se conoce, la nueva
            # hay que verla el dia que aparece.
            nuevas = (
                ""
                if modulo in LEEN_DATA_HOY or modulo in DEUDA
                else "   <- NUEVA, no censada"
            )

            peligro = (
                "   <- LEE UN FICHERO QUE EL CICLO ESCRIBE"
                if modulo in PUEDEN_ENCERRARLO
                else ""
            )

            print(f"  {corto}{nuevas}{peligro}")

            for ruta in censadas[modulo]:
                print(f"      {ruta}")

        print()

    tardo = time.perf_counter() - arranco

    print(
        f"LA VERJA HA TARDADO {tardo:.0f} s "
        f"({tardo / 60:.1f} min) en {len(modulos)} guardias, "
        f"{tardo / max(1, len(modulos)):.2f} s de media."
    )

    # Y lo que NO se ha corrido aqui, dicho en voz alta cada
    # vuelta: si el paso 0 se vuelve invisible, vuelve a
    # depender de que alguien se acuerde.
    if not (args.solo or args.extra):
        print(
            f"EL PASO 0 NO SE CORRE AQUI: {len(EL_PASO_0)} "
            f"comprobacion(es) que van ANTES de tocar el `env` "
            f"del workflow, a mano, con "
            f"`--paso-0`. Quien vigila que no se olvide es "
            f"`test_el_paso_0_no_se_olvida_v1`, que si esta "
            f"arriba."
        )

    print()

    _apuntar_el_veredicto(
        verdes=len(modulos) - len(fallos),
        total=len(modulos),
        fallos=fallos,
        parcial=bool(args.solo or args.extra),
    )

    if fallos:
        print(f"FALLAN {len(fallos)} de {len(modulos)}:")
        for modulo in fallos:
            print(f"  - {modulo}")
        print()
        print("NO subas hasta arreglarlos: CI parara el ciclo.")
        return 1

    print(f"Los {len(modulos)} en verde. Se puede subir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
