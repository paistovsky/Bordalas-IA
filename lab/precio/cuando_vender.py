"""
Laboratorio, experimento 3: CUANDO vender lo que se compro subiendo.

E1 dejo la regla «compra lo que sube, vende el primer dia que baja». La
mitad de compra ya esta en Pepe (BORDALAS_COMPRA_SOLO_SI_SUBE). Aqui se
mide la mitad de venta contra otras salidas, y como paga el Computer.

1) Como paga el Computer (ventas de los 8 managers al Computer en el
   tablon): oferta / precio del dia, segun el precio haya subido, quedado
   quieto o bajado ese dia.
2) Salidas: cada jugador-dia en que el precio SUBIO en el ultimo cambio es
   una entrada (se paga precio * 1,022: la puja ganadora mediana de E1).
   Se prueban varias salidas con el mismo conjunto de entradas. La venta
   se cobra a precio del dia * (1 + oferta medida en 1) segun el estado
   del precio ese dia. Lo que sigue abierto al final se valora a precio
   de hoy sin prima.

Uso:  python3 lab/precio/cuando_vender.py
"""
import datetime as dt
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import COMPUTER, Precios, dia_de_mercado, eventos  # noqa: E402

D = dt.timedelta(days=1)
PRIMA_COMPRA = 0.022


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def estado(P, pid, d):
    a, b = P.en(pid, d), P.en(pid, d - D)
    if a is None or b is None:
        return None
    return (a > b) - (a < b)


def como_paga(P):
    filas = []
    for ts, pid, comp, vend, imp, _ in eventos():
        if comp == COMPUTER and vend != COMPUTER:
            d = dia_de_mercado(ts)
            e, a = estado(P, pid, d), P.en(pid, d)
            if e is not None:
                man = P.en(pid, d + D)
                filas.append((e, imp / a - 1, None if man is None else man / a - 1))
    print("1) Como paga el Computer (ventas reales de la liga):")
    prima = {}
    for e, nom in ((1, "el precio subio ese dia"), (0, "quieto"), (-1, "el precio BAJO ese dia")):
        r = [f for f in filas if f[0] == e]
        prima[e] = med([f[1] for f in r])
        print(f"   {nom:<24} n={len(r):3d}  oferta sobre el precio del dia {prima[e]*100:+5.1f}%"
              f"   y al dia siguiente el precio {med([f[2] for f in r if f[2] is not None])*100:+5.1f}%")
    return prima


def salir(P, pid, dias, precios, i, regla, prima):
    """Desde la entrada i, devuelve (indice de venta, cerrado?) segun la regla."""
    bajadas = 0
    for j in range(i + 1, len(precios)):
        if (dias[j] - dias[j - 1]).days > 2:
            return j - 1, False  # hueco largo: se corta sin vender (falta el 07/09 entero: 2 dias se aceptan)
        baja = precios[j] < precios[j - 1]
        bajadas = bajadas + 1 if baja else 0
        tiempo = (dias[j] - dias[i]).days
        if regla[0] == "bajadas" and bajadas >= regla[1]:
            return j, True
        if regla[0] == "dias" and tiempo >= regla[1]:
            return j, True
        if regla[0] == "caida" and precios[j] < max(precios[i:j + 1]) * (1 - regla[1]):
            return j, True
        if regla[0] == "frena" and j >= i + 2 and precios[j] - precios[j - 1] < precios[j - 1] - precios[j - 2]:
            return j, True
    return len(precios) - 1, False


def simular(P, regla, prima, desde=None, hasta=None):
    pl = []
    for pid, (dias, precios) in P.por_jugador.items():
        for i in range(1, len(precios) - 1):
            if (dias[i] - dias[i - 1]).days > 2 or precios[i] <= precios[i - 1]:
                continue
            if (desde and dias[i] < desde) or (hasta and dias[i] > hasta):
                continue
            coste = precios[i] * (1 + PRIMA_COMPRA)
            j, cerrado = salir(P, pid, dias, precios, i, regla, prima)
            if cerrado:
                e = (precios[j] > precios[j - 1]) - (precios[j] < precios[j - 1])
                venta = precios[j] * (1 + prima[e])
            else:
                venta = precios[j]
            pl.append((venta / coste - 1, cerrado, (dias[j] - dias[i]).days))
    return pl


def linea(nombre, pl):
    """Sobre TODAS las entradas (lo abierto a precio de hoy): comparar solo los
    cerrados premia a la regla que cierra los buenos y deja abiertos los malos.
    ROI/dia cuenta un dia muerto por viaje (se cobra hoy, se puja para manana)."""
    roi = [p[0] for p in pl]
    cer = [p for p in pl if p[1]]
    dias = sum(p[2] + 1 for p in pl)
    return (f"   {nombre:<30} n={len(pl):5d} cerrados={len(cer)/len(pl):4.0%}"
            f"  verde {sum(r > 0 for r in roi)/len(roi):5.1%}"
            f"  ROI med {med(roi)*100:+5.1f}%  medio {sum(roi)/len(roi)*100:+5.1f}%"
            f"  dias med {med([p[2] for p in pl]):2d}  ROI/dia {sum(roi)/dias*100:+.2f}%")


REGLAS = [
    ("vende tras 1 bajada (E1)", ("bajadas", 1)),
    ("vende tras 2 bajadas", ("bajadas", 2)),
    ("vende cuando frena la subida", ("frena", 0)),
    ("vende si cae 3 % del pico", ("caida", 0.03)),
    ("vende a los 3 dias", ("dias", 3)),
    ("vende a los 5 dias", ("dias", 5)),
    ("vende a los 7 dias", ("dias", 7)),
]

if __name__ == "__main__":
    P = Precios()
    print(f"Precios del {P.primer_dia} al {P.ultimo_dia}, {len(P.por_jugador)} jugadores.\n")
    prima = como_paga(P)
    print("\n2) Salidas, mismas entradas (cada dia en que el precio subio), 42 dias:")
    for nom, r in REGLAS:
        print(linea(nom, simular(P, r, prima)))
    mitad = P.primer_dia + (P.ultimo_dia - P.primer_dia) / 2
    for etiqueta, kw in ((f"entradas hasta el {mitad}", dict(hasta=mitad)),
                         (f"entradas desde el {mitad + D}", dict(desde=mitad + D))):
        print(f"\n   Por mitades: {etiqueta}")
        for nom, r in REGLAS[:4]:
            print(linea(nom, simular(P, r, prima, **kw)))
