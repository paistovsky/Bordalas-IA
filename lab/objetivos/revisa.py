"""
E26: revisar una lista de objetivos contra la foto del dia.

E25 (08/10) dejo una lista de fichajes para el gestor. Una lista vale lo
que vale el dia en que se hizo: aqui se mira, para cada nombre, el estado
de Biwenger, el ultimo cambio de precio, de quien es (libre, rival,
nuestro) y su total de puntos, con la foto de un ciclo (status.json).
Ademas, lo que dijo FutbolFantasy de ellos (archivo de E4/E6).

Reglas que aplica (del laboratorio):
  - estado distinto de ok -> FUERA (E6, E24: un lesionado de verdad pierde
    1,5-2 % al dia y no puntua);
  - precio bajando -> esperar (E1/E3: comprar lo que sube);
  - vara = puntos totales (E7/E17), no la media de pocos partidos.

Uso:  python3 lab/objetivos/revisa.py status.json "Nombre 1" "Nombre 2" ...
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    f = json.load(open(sys.argv[1]))
    cat = {p["name"]: p for p in f["todaLaLiga"]["players"]}
    noticias = [json.loads(l) for l in open(RAIZ / "lab/noticias/eventos_hasta_29_09.jsonl")]
    print(f"Foto: {f['meta']['generated_at']}\n")
    for n in sys.argv[2:]:
        p = cat.get(n)
        if not p:
            print(f"   {n:<16} NO ESTA en el catalogo de hoy")
            continue
        inc = p.get("price_increment") or 0
        if p["status"] != "ok":
            veredicto = f"FUERA ({p['status']})"
        elif inc < 0:
            veredicto = "esperar (su precio baja)"
        else:
            veredicto = "vale"
        ult = [e for e in noticias if e["pid"] == p["id"]][-1:]
        nota = f"  | FF {ult[0]['publicada'][:10]} {ult[0]['tipo']}: {ult[0]['titulo'][:50]}" if ult else ""
        print(f"   {n:<16} {veredicto:<26} {p['points']:3d} pts en {p['played']} · {p['price']/1e6:5.2f} M"
              f" ({inc:+,}) · {p.get('de_quien')}{nota}")
