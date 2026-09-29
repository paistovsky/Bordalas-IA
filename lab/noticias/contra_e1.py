"""BAJA: vender al leer la noticia frente a la salida de E1 (vender al Computer
el primer dia que baja, que paga +3,2 % sobre el precio nuevo; en dia quieto
+1,0 %, en dia de subida +2,1 %: tabla de E3).

Uso: python3 lab/noticias/contra_e1.py   (tras analizar.py)
"""
import json
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analizar import AQUI, FUERTE, norm  # noqa: E402

PRIMA = {1: 1.021, 0: 1.010, -1: 1.032}
filas = json.load(open(AQUI / "episodios.json"))
for nom, g in (("BAJA no venia bajando", lambda f: True),
               ("BAJA fuerte no venia bajando", lambda f: FUERTE.search(norm(f["titulo"])))):
    difs = []
    for f in filas:
        if f["tipo"] != "BAJA" or f["base"] < 1e6 or f["prev"] not in (0, 1) or not g(f):
            continue
        ch = {int(k): v for k, v in f["ch"].items()}
        noticia = f["base"] * PRIMA[f["prev"]]
        p, e1 = f["base"], None
        for k in range(0, 8):
            if ch.get(k) is None:
                break
            p = p * (1 + ch[k])
            if ch[k] < -0.0005:
                e1 = p * PRIMA[-1]
                break
        if e1 is None:
            e1 = p  # sigue sin bajar: se valora a precio del ultimo dia
        difs.append(noticia / e1 - 1)
    difs.sort()
    print(f"{nom}: n={len(difs)}  vender al leer gana a E1 en media {100*st.mean(difs):+.1f} %, "
          f"mediana {100*st.median(difs):+.1f} %, gana en {sum(d > 0 for d in difs)}/{len(difs)}")
