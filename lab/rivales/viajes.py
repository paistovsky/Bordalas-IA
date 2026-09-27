"""
Laboratorio, experimento 1: como ganan Pollo17 y Luismi_Haz.

Solo lee dos libros de data/ (el tablon y el historial de precios).
No importa nada de src/, no sale a la red, no escribe en data/.

Reconstruye, para cada manager, sus VIAJES: una compra al Computer
emparejada (FIFO por jugador) con su venta posterior. De cada viaje
saca lo que se sabia el dia de la compra (prima pagada sobre el precio,
tendencia del precio los dias antes, cuantos pujaron) y lo que paso
(dias aguantado, precio al vender, a quien vendio).

Uso:  python3 lab/rivales/viajes.py            (tabla en pantalla)
      python3 lab/rivales/viajes.py --json F   (los viajes a un fichero)
"""
import bisect
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"
PRECIOS = RAIZ / "data/autopilot/price_history.json"

PEPE, POLLO, LUISMI = 14175949, 14145555, 14156489
NOMBRES = {PEPE: "Pepe", POLLO: "Pollo17", LUISMI: "Luismi_Haz"}
COMPUTER = 0

# Biwenger cambia los precios una vez al dia, con el reset de las 05:00 UTC.
# «Dia de mercado» D = de las 05:00 UTC de D a las 05:00 UTC de D+1.
RESET_UTC_H = 5


def dia_de_mercado(ts):
    d = dt.datetime.utcfromtimestamp(ts)
    if d.hour < RESET_UTC_H:
        d -= dt.timedelta(days=1)
    return d.date()


class Precios:
    """Precio de cada jugador por dia de mercado (el ultimo visto ese dia)."""

    def __init__(self, ruta=PRECIOS):
        crudo = json.load(open(ruta))["players"]
        self.por_jugador = {}
        for pid, v in crudo.items():
            dias = {}
            for t, p in zip(v["t"], v["p"]):
                dias[dia_de_mercado(t)] = p
            orden = sorted(dias)
            self.por_jugador[int(pid)] = (orden, [dias[d] for d in orden])
        self.primer_dia = min(o[0][0] for o in self.por_jugador.values() if o[0])
        self.ultimo_dia = max(o[0][-1] for o in self.por_jugador.values() if o[0])

    def en(self, pid, dia):
        """Precio vigente el dia de mercado `dia` (o el ultimo anterior)."""
        s = self.por_jugador.get(pid)
        if not s:
            return None
        i = bisect.bisect_right(s[0], dia) - 1
        if i < 0:
            return None
        # un precio de hace mas de 3 dias no es «el de hoy»
        if (dia - s[0][i]).days > 3:
            return None
        return s[1][i]

    def serie(self, pid):
        return self.por_jugador.get(pid, ([], []))


def eventos():
    """Compras y ventas del tablon, en orden: (ts, jugador, comprador, vendedor, importe, pujas)."""
    out = []
    for e in json.load(open(TABLON)):
        if e["type"] == "market":
            for x in e["content"]:
                pujas = len(x.get("bids") or []) + 1  # las perdedoras + la ganadora
                out.append((x.get("date", e["date"]), x["player"], x["to"]["id"],
                            COMPUTER, x["amount"], pujas))
        elif e["type"] == "transfer":
            for x in e["content"]:
                to = x.get("to", {}).get("id", COMPUTER)
                out.append((e["date"], x["player"], to, x["from"]["id"], x["amount"], None))
    out.sort(key=lambda r: r[0])
    return out


def pct(a, b):
    return None if (a is None or not b) else a / b - 1


def viajes(precios=None):
    precios = precios or Precios()
    abiertos = defaultdict(list)  # (manager, jugador) -> compras sin vender
    cerrados, compras = [], []
    for ts, pid, comprador, vendedor, importe, pujas in eventos():
        dia = dia_de_mercado(ts)
        if vendedor != COMPUTER and abiertos[(vendedor, pid)]:
            c = abiertos[(vendedor, pid)].pop(0)
            v_dia = dia
            p_venta = precios.en(pid, v_dia)
            c.update(
                venta_ts=ts, venta_dia=str(v_dia), venta=importe,
                a_quien="COMPUTER" if comprador == COMPUTER else "MANAGER",
                dias=(v_dia - dt.date.fromisoformat(c["dia"])).days,
                precio_venta_mercado=p_venta,
                prima_venta=pct(importe, p_venta),
                pl=importe - c["compra"],
                mov_mercado=(None if p_venta is None or c["precio_ayer"] is None
                             else p_venta - c["precio_ayer"]),
                tend_1d_venta=pct(p_venta, precios.en(pid, v_dia - dt.timedelta(days=1))),
                tend_2d_venta=pct(p_venta, precios.en(pid, v_dia - dt.timedelta(days=2))),
            )
            # pico entre compra y venta: vendio en el maximo o despues de que girara?
            dias_s, ps = precios.serie(pid)
            tramo = [(d, p) for d, p in zip(dias_s, ps)
                     if dt.date.fromisoformat(c["dia"]) <= d <= v_dia]
            if tramo:
                pico = max(tramo, key=lambda r: r[1])
                c["pico"] = pico[1]
                c["dias_desde_pico"] = (v_dia - pico[0]).days
            cerrados.append(c)
        if comprador in NOMBRES and vendedor == COMPUTER:
            ayer = dia - dt.timedelta(days=1)
            p_ayer = precios.en(pid, ayer)  # el precio mientras se pujaba
            c = dict(
                manager=NOMBRES[comprador], jugador=pid, compra_ts=ts, dia=str(dia),
                compra=importe, pujas=pujas, precio_ayer=p_ayer,
                prima_compra=pct(importe, p_ayer),
                tend_1d=pct(p_ayer, precios.en(pid, ayer - dt.timedelta(days=1))),
                tend_3d=pct(p_ayer, precios.en(pid, ayer - dt.timedelta(days=3))),
                tend_7d=pct(p_ayer, precios.en(pid, ayer - dt.timedelta(days=7))),
                sube_hoy=pct(precios.en(pid, dia), p_ayer),
            )
            abiertos[(comprador, pid)].append(c)
            compras.append(c)
    return compras, cerrados


def _med(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _f(x, pct_=True):
    if x is None:
        return "   -  "
    return f"{x*100:+6.1f}%" if pct_ else f"{x:>6.1f}"


def resumen(compras, cerrados):
    lineas = []
    for m in ("Pollo17", "Luismi_Haz", "Pepe"):
        cs = [c for c in compras if c["manager"] == m]
        vs = [c for c in cerrados if c["manager"] == m]
        con_p = [c for c in vs if c["precio_ayer"] is not None]
        lineas.append(f"== {m}: {len(cs)} compras, {len(vs)} viajes cerrados "
                      f"({len(con_p)} con precio de mercado)")
        lineas.append(f"   P&L total cerrado          {sum(c['pl'] for c in vs):>+14,}")
        lineas.append(f"   verde                      {sum(c['pl']>0 for c in vs)}/{len(vs)}")
        lineas.append(f"   prima de compra (mediana)  {_f(_med(c['prima_compra'] for c in cs))}")
        lineas.append(f"   tendencia 1d antes (med)   {_f(_med(c['tend_1d'] for c in cs))}")
        lineas.append(f"   tendencia 3d antes (med)   {_f(_med(c['tend_3d'] for c in cs))}")
        lineas.append(f"   subio el dia de compra     "
                      f"{sum((c['tend_1d'] or 0)>0 for c in cs)}/{sum(c['tend_1d'] is not None for c in cs)}")
        lineas.append(f"   pujas en su subasta (med)  {_f(_med(c['pujas'] for c in cs), False)}")
        lineas.append(f"   precio de compra (med)     {_med(c['compra'] for c in cs):>14,.0f}")
        lineas.append(f"   dias aguantado (mediana)   {_f(_med(c['dias'] for c in vs), False)}")
        lineas.append(f"   prima de venta (mediana)   {_f(_med(c['prima_venta'] for c in vs))}")
        lineas.append(f"   vende a Computer           {sum(c['a_quien']=='COMPUTER' for c in vs)}/{len(vs)}")
        lineas.append(f"   dias desde el pico (med)   {_f(_med(c.get('dias_desde_pico') for c in vs), False)}")
        lineas.append(f"   bajo el dia de venta       "
                      f"{sum((c['tend_1d_venta'] or 0)<0 for c in vs)}/{sum(c['tend_1d_venta'] is not None for c in vs)}")
        lineas.append(f"   mov. mercado (suma)        {sum(c['mov_mercado'] or 0 for c in vs):>+14,}")
        lineas.append("")
    return "\n".join(lineas)


if __name__ == "__main__":
    compras, cerrados = viajes()
    print(resumen(compras, cerrados))
    if "--json" in sys.argv:
        f = sys.argv[sys.argv.index("--json") + 1]
        json.dump({"compras": compras, "cerrados": cerrados}, open(f, "w"), indent=1, default=str)
