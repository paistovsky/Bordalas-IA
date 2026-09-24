from src.telemetry.dashboard_state import (
    build_dashboard_state,
    save_dashboard_state,
)

from src.telemetry.el_cronometro import Cronometro


def main() -> None:
    print()
    print("=" * 78)
    print("BORDALAS IA - SALA DE OPERACIONES - TELEMETRIA V2.0")
    print("=" * 78)

    # EL RELOJ DEL PANEL (21/09/2026)
    #
    #     La vuelta #1737 gasto 6 m 19 s en este paso y el
    #     registro no decia en que. Con esto queda partido en las
    #     dos mitades que hay aqui -montar el estado y
    #     guardarlo-, que es hasta donde llega este fichero.
    #
    #     Lo de dentro de `build_dashboard_state` no se parte
    #     aqui: medido el 21/09 con perfilador en el portatil,
    #     montarlo entero son 97,5 s y el reparto esta en el
    #     informe del encargo. Partirlo por dentro seria tocar
    #     1.300 lineas para medir, y este bloque mide sin tocar.
    cronometro = Cronometro("EL PANEL")

    with cronometro.etapa("build_dashboard_state"):
        state = build_dashboard_state()

    with cronometro.etapa("save_dashboard_state"):
        path = save_dashboard_state(state)

    rivals = (
        state.get("rival_intelligence", {})
        .get("managers", [])
        or []
    )

    lineup = state.get("lineup", {}) or {}

    print(f"Archivo:       {path}")
    print(f"Rivales:       {len(rivals)} managers")
    print(f"XI:            {lineup.get('playable', 0)}/11")
    print(
        "Ledger rival: "
        f"{state.get('rival_intelligence', {}).get('ledger_status')}"
    )
    print(
        "Decision:      "
        f"{state.get('decision', {}).get('label')}"
    )
    print(
        "Ultima accion: "
        f"{state.get('last_execution', {}).get('label') or 'Sin escritura'}"
    )
    print(
        "Verificada:    "
        f"{'SI' if state.get('last_execution', {}).get('verified_post_action') else 'NO'}"
    )
    print()

    for linea in cronometro.cuadro():
        print(linea)

    # EL ONCE SE BUSCA UNA VEZ (24/09/2026). Solo con su
    # interruptor puesto; apagado no imprime nada.
    from src.analysis.el_once_se_busca_una_vez import (
        linea as linea_del_once,
    )

    if linea_del_once():
        print(linea_del_once())

    print()
    print("# DASHBOARD TELEMETRY V2.0: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()
