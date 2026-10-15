"""
E42: el reloj de las ofertas del Computer, con las fotos de los ciclos.

Lee los dashboard/data/status.json de varios artefactos
bordalas-live-diagnostics-* (bajados y descomprimidos a mano, uno por
carpeta) y saca, para cada oferta: jugador, importe, prima sobre el
precio y horas hasta caducar. Si todas las ofertas de un lote caducan
a la vez, ~48 h despues del reset de las 07:00, el lote nace con el reset.

Uso:  python3 -I lab/ofertas/reloj_de_ofertas.py CARPETA/status.json [...]
"""
import json
import sys

if __name__ == "__main__":
    for ruta in sys.argv[1:]:
        s = json.load(open(ruta))
        print(ruta)
        for o in s.get("offers") or []:
            print(f"   {', '.join(o['players']):20} {o['amount']:>10,}  {o.get('premium_percent'):+5.1f} %"
                  f"  {o['counterparty']:9} caduca en {o.get('hours_to_expiry')} h")
