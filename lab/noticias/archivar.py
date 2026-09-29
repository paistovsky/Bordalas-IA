"""Archivo de noticias de FutbolFantasy (LaLiga) por rango de IDs.

El listado /laliga/noticias/pagina/N esta cacheado (se queda en el 24/09), asi
que se recorre cada ID de articulo: /laliga/noticias/<id> redirige al slug.
De cada articulo se guarda: id, url, titulo, descripcion, fecha de
publicacion (con hora), icono de tipo y equipo (el enlace /laliga/equipos/<slug>
mas repetido en la pagina, descontando el menu).

Uso: python3 lab/noticias/archivar.py 148600 151990 > lab/noticias/archivo.jsonl
"""
import json
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
BASE = "https://www.futbolfantasy.com/laliga/noticias/"


def get(url):
    r = subprocess.run(["curl", "-sL", "--compressed", "--max-time", "30", "-A", UA,
                        "-w", "\n%{url_effective} %{http_code}", url],
                       capture_output=True, text=True, errors="replace")
    body, _, tail = r.stdout.rpartition("\n")
    eff, _, code = tail.rpartition(" ")
    return body, eff, code


MENU = None


def team_of(html):
    c = Counter(re.findall(r'laliga/equipos/([a-z0-9-]+)', html))
    if MENU:
        for k, v in MENU.items():
            c[k] -= v
    c = +c
    if not c:
        return None
    (t1, n1), *rest = c.most_common(2)
    if rest and rest[0][1] == n1:
        return None
    return t1


def one(i):
    html, eff, code = get(f"{BASE}{i}")
    if code != "200" or "/laliga/noticias/" not in eff:
        return None
    def m(p):
        x = re.search(p, html)
        return x.group(1) if x else None
    return {
        "id": i, "url": eff,
        "titulo": m(r'<meta property="og:title" content="([^"]*)"'),
        "descripcion": m(r'<meta name="description" content="([^"]*)"'),
        "publicada": m(r'"datePublished":\s*"([^"]+)"'),
        "equipo": team_of(html),
    }


def main():
    global MENU
    a, b = int(sys.argv[1]), int(sys.argv[2])
    # menu: enlaces a equipos de una pagina neutra (el listado)
    html, _, _ = get("https://www.futbolfantasy.com/laliga/noticias/pagina/40")
    MENU = Counter(re.findall(r'laliga/equipos/([a-z0-9-]+)', html))
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(one, range(a, b + 1)):
            if r:
                print(json.dumps(r, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
