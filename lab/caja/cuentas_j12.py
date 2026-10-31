"""
E74: la caja de la J12 (vie 06/11, plazo 15:00) si mañana (dom 07:00) entra
Juan Iglesias (puja de la mejora, 3.769.900). Datos de la foto del ciclo
de las 17:11 del 31/10: saldo, ofertas del Computer, precios. Ingresos con
fecha: premio de la J11 (mar 03/11, E43/E52; minimo historico 29 pts) y
la racha (mie 05/11 ~00:10, E47). Ventas: Gaya (al que sustituye), y los de
inventario (Dani Lorenzo, Angel Ortiz, Ramon Enriquez) a su precio.

Uso:  python3 lab/caja/cuentas_j12.py
"""
SALDO, PUJA = -944_976, 3_769_900
VENTAS = {"Gaya": 1_770_000, "Dani Lorenzo": 2_020_000, "Angel Ortiz": 190_000, "Ramon Enriquez": 409_200}
RACHA = 250_000

if __name__ == "__main__":
    for premio, nombre in ((870_000, "premio minimo (29 pts)"), (1_200_000, "premio tipico (40 pts)")):
        base = SALDO - PUJA + premio + RACHA
        print(f"{nombre}: solo premio y racha {base:+,}")
        for combo in (("Gaya",), ("Gaya", "Angel Ortiz", "Ramon Enriquez"), ("Gaya", "Dani Lorenzo")):
            print(f"   + {' + '.join(combo):40} {base + sum(VENTAS[c] for c in combo):+,}")
