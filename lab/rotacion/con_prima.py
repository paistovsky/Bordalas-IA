"""
E46: la rotacion (BORDALAS_LA_ROTACION, apagada) con la prima de verdad.

La rotacion cambia al que lleva 2 dias sin subir por uno de su posicion,
del mercado, que sube. Su laboratorio da ~+30k/dia sin contar lo que
cuesta GANAR la subasta de uno que sube (E41: con pelea el 64-83 %, el
ganador paga +7 % a +16 %).

Aqui, con el escaparate real de cada dia (data/trading/libro_del_escaparate.jsonl,
los 20 del Computer) y el historial de precios:
  - compra: un jugador del escaparate que subio ayer, pujando precio x (1+k);
    se gana con la tasa de E41 segun cuanto subio (tablon);
  - viaje: se vende al Computer el primer dia que no sube (E3), a precio x 1,007
    (mediana de las ofertas, E38);
  - lo que se deja: un jugador cualquiera con 2 dias sin subir, guardado los
    mismos dias (deriva sin hacer nada).
Ganancia del cambio = viaje del que entra - deriva del que sale, en % del precio.

Uso:  python3 lab/rotacion/con_prima.py
"""
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios, pct  # noqa: E402

ESCAPARATE = RAIZ / "data/trading/libro_del_escaparate.jsonl"
D = dt.timedelta(days=1)
OFERTA = 1.007


def viaje(P, pid, dia, precio_compra):
    """Desde la compra (precio de `dia`), vender el primer dia que no sube."""
    p_prev, d = P.en(pid, dia), dia
    for _ in range(30):
        d += D
        p = P.en(pid, d)
        if p is None or d > P.ultimo_dia:
            return None
        if p <= p_prev:
            return p * OFERTA / precio_compra - 1, (d - dia).days
        p_prev = p
    return None


if __name__ == "__main__":
    P = Precios()
    # deriva de quien lleva 2 dias sin subir, a h dias (todo el universo)
    deriva = {}
    for pid, (dias, precios) in P.por_jugador.items():
        for i in range(2, len(dias)):
            if precios[i] <= precios[i - 1] <= precios[i - 2]:
                for h in range(1, 8):
                    p = P.en(pid, dias[i] + h * D)
                    if p:
                        deriva.setdefault(h, []).append(p / precios[i] - 1)
    der = {h: st.median(v) for h, v in deriva.items()}
    print("Deriva del que lleva 2 dias sin subir:", " ".join(f"{h}d {v:+.1%}" for h, v in sorted(der.items())))

    viajes = []
    for linea in open(ESCAPARATE):
        r = json.loads(linea)
        dia = dt.date.fromisoformat(r["dia_de_mercado"])
        for j in r["players"]:
            t1 = pct(P.en(j["id"], dia), P.en(j["id"], dia - D))
            if t1 is None or t1 <= 0:
                continue
            p0 = P.en(j["id"], dia)
            viajes.append((t1, j["id"], dia + D, p0))
    print(f"Candidatos que suben en el escaparate: {len(viajes)} (31 dias)\n")
    # tasa de victoria por prima y tramo de subida (E41, tablon)
    GANA = {"<2%": {0.01: 0.41, 0.03: 0.47, 0.05: 0.58, 0.08: 0.76, 0.12: 0.88},
            ">=2%": {0.01: 0.02, 0.03: 0.11, 0.05: 0.17, 0.08: 0.28, 0.12: 0.43}}
    print("  prima   tramo   viajes  gana%   viaje (mediana)  dias  - deriva  = cambio   por dia")
    for k in (0.01, 0.05, 0.08, 0.12):
        for tramo in ("<2%", ">=2%"):
            res = []
            for t1, pid, d1, p0 in viajes:
                if (t1 < 0.02) != (tramo == "<2%"):
                    continue
                v = viaje(P, pid, d1, p0 * (1 + k))
                if v:
                    res.append(v)
            if not res:
                continue
            r_med = st.median(x[0] for x in res)
            dias = st.median(x[1] for x in res)
            dr = der.get(min(7, max(1, round(dias))), 0)
            cambio = r_med - dr
            print(f"  +{k*100:3.0f} %  {tramo:5}  {len(res):>5}  {GANA[tramo][k]:4.0%}   {r_med:+7.1%}"
                  f"        {dias:4.1f}   {dr:+6.1%}   {cambio:+6.1%}   {cambio/dias:+.2%}")

    print("\nCon las primas de la cartera por precio (+12 % <1 M, +4 % 1-3 M, +1 % >3 M), por tramo de subida:")
    for tramo in ("<2%", ">=2%"):
        for lo, hi, k in ((0, 1e6, 0.12), (1e6, 3e6, 0.04), (3e6, 1e9, 0.01)):
            res = [viaje(P, pid, d1, p0 * (1 + k)) for t1, pid, d1, p0 in viajes
                   if lo <= p0 < hi and (t1 < 0.02) == (tramo == "<2%")]
            res = [x for x in res if x]
            if res:
                dias = st.median(x[1] for x in res)
                c = st.median(x[0] for x in res) - der.get(min(7, max(1, round(dias))), 0)
                print(f"   {tramo:5} {lo/1e6:.0f}-{min(hi,99e6)/1e6:.0f} M (+{k*100:.0f} %): n={len(res):>3}  cambio {c:+.1%}")
