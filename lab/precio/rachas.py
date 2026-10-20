"""
E51: ¿cuanto dura una racha de subidas? Si un jugador lleva n dias
seguidos subiendo, ¿con que probabilidad sube manana, y cuanto le queda
de racha? Sirve para la cartera y la rotacion (compran al que sube y
venden el primer dia que no sube): ¿compensa entrar en el dia 1 de la
racha igual que en el dia 8?

Datos: data/autopilot/price_history.json (todos los jugadores, por dia de
mercado; un hueco de mas de 2 dias corta la serie).

Uso:  python3 lab/precio/rachas.py
"""
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios  # noqa: E402

if __name__ == "__main__":
    P = Precios()
    sigue = defaultdict(lambda: [0, 0])   # n -> [sube manana, casos]
    queda = defaultdict(list)             # n -> ganancia hasta el primer dia que no sube
    for pid, (dias, precios) in P.por_jugador.items():
        n = 0
        for i in range(1, len(dias)):
            if (dias[i] - dias[i - 1]).days > 2:
                n = 0
                continue
            n = n + 1 if precios[i] > precios[i - 1] else 0
            if n == 0 or i + 1 >= len(dias):
                continue
            k = min(n, 10)
            sigue[k][1] += 1
            sigue[k][0] += precios[i + 1] > precios[i]
            # ganancia comprando hoy al precio de hoy, vendiendo el primer dia que no sube
            j = i + 1
            while j < len(dias) and precios[j] > precios[j - 1]:
                j += 1
            if j < len(dias):
                queda[k].append(precios[j] / precios[i] - 1)
    print("dias seguidos subiendo   casos   sube manana   ganancia hasta el primer dia sin subir (mediana / media)")
    for k in sorted(sigue):
        s, c = sigue[k]
        q = queda[k]
        print(f"   {k if k < 10 else '10+':>4}                {c:>6}      {s/c:5.1%}        {st.median(q):+6.1%} / {st.mean(q):+6.1%}")
