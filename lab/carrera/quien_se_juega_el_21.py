"""
E50: el Levante-Athletic del 21/10 (aplazado de la J6) para cada manager:
cuantos jugadores de esos dos equipos tiene, cuantos puntos se esperan de
ellos (puntos por partido x titularidad FF, la vara de E20) y su caja hoy.
Si el aplazado es ronda propia (E45), quien la empiece en rojo pierde esos
puntos; ademas es la prueba que zanja E45.

Uso:  python3 -I lab/carrera/quien_se_juega_el_21.py status.json
"""
import json
import sys

LEVANTE, ATHLETIC = 10, 1  # E45

if __name__ == "__main__":
    f = json.load(open(sys.argv[1]))
    cat = {p["id"]: p for p in f["todaLaLiga"]["players"]}
    caja = {s["name"]: s.get("balance") for s in f["league_center"]["fantasy_standings"]}
    print(f"Foto: {f['meta']['generated_at']}\n")
    print(f"   {'manager':<16} {'caja':>12}   jugadores del Levante / Athletic (esperado)")
    for m in f["rival_squads"]["managers"]:
        suyos = []
        for p in m["players"]:
            c = cat.get(p["id"], {})
            if c.get("team_id") in (LEVANTE, ATHLETIC):
                pj = c.get("played") or 0
                media = (c.get("points") or 0) / pj if pj else 0
                tit = p.get("starter_probability") or 50
                suyos.append((p["name"], media * tit / 100, c.get("status")))
        esp = sum(e for _, e, s in suyos if s == "ok")
        cj = caja.get(m["name"])
        print(f"   {m['name'][:16]:<16} {cj:>12,}   {esp:4.1f}  " + ", ".join(f"{n} {e:.1f}" for n, e, _ in suyos)
              + ("   <- EN ROJO" if cj is not None and cj < 0 and suyos else ""))
