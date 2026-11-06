"""
E85: ¿que hace el mercado en un paron sin jornadas? Viene uno (J12 el
06-09/11, J13 el 20/11). El anterior: tras la J7 (ultimo partido 20/09)
hasta la J8 (09/10).

Con price_history: por cada dia, la fraccion de jugadores que suben, el
cambio medio de precio y la inercia (si subio ayer, ¿sube hoy?); en el
paron frente a las semanas con jornada (del 22/08 al 20/09 y del 09/10 al
05/11). Y el valor de mercado total de la liga dia a dia.

Uso:  python3 lab/precio/en_el_paron.py
"""
import datetime as dt
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios  # noqa: E402

D = dt.timedelta(days=1)
PARON = (dt.date(2026, 9, 22), dt.date(2026, 10, 8))
CON_JORNADA = [(dt.date(2026, 8, 22), dt.date(2026, 9, 20)), (dt.date(2026, 10, 9), dt.date(2026, 11, 5))]

if __name__ == "__main__":
    P = Precios()
    por_dia = {}
    for pid, (ds, ps) in P.por_jugador.items():
        for i in range(1, len(ds)):
            if (ds[i] - ds[i - 1]).days != 1:
                continue
            c = ps[i] / ps[i - 1] - 1
            por_dia.setdefault(ds[i], []).append((pid, c, ps[i]))

    def resumen(desde, hasta):
        sub, med, inercia, total = [], [], [0, 0], []
        d = desde
        while d <= hasta:
            hoy = por_dia.get(d, [])
            if hoy:
                sub.append(sum(c > 0 for _, c, _ in hoy) / len(hoy))
                med.append(st.mean(c for _, c, _ in hoy))
                total.append(sum(p for *_, p in hoy))
                ayer = {pid: c for pid, c, _ in por_dia.get(d - D, [])}
                for pid, c, _ in hoy:
                    if ayer.get(pid, 0) > 0:
                        inercia[1] += 1
                        inercia[0] += c > 0
            d += D
        return dict(dias=len(sub), suben=st.mean(sub), cambio=st.mean(med),
                    inercia=inercia[0] / inercia[1] if inercia[1] else None,
                    total=(total[-1] / total[0] - 1) if len(total) > 1 else None)

    for nombre, (a, b) in [("paron 22/09-08/10", PARON)] + [(f"con jornada {a:%d/%m}-{b:%d/%m}", (a, b)) for a, b in CON_JORNADA]:
        r = resumen(a, b)
        print(f"   {nombre:28} dias {r['dias']:>2}  suben {r['suben']:4.0%}/dia  cambio medio {r['cambio']:+.2%}/dia"
              f"  inercia {r['inercia']:.0%}  valor de la liga {r['total']:+.1%}")
