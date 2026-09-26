#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sebastian Vallejo — https://github.com/svallejo-dev/llm-wiki
# Copiado en tu wiki, es tuyo: no hace falta conservar este aviso (LICENSE-WIKIS.md).
"""Estado de repaso de la wiki, con repetición espaciada (cajas de Leitner).

Recordar lo que se ha leído no es lo mismo que haberlo leído: esto lleva la
cuenta de qué páginas se han repasado, cómo fue y cuándo toca volver.

  repaso.py pendientes [N]                    qué repasar ahora (por defecto 5)
  repaso.py registrar <pagina> <resultado>    resultado: acierto | parcial | fallo
  repaso.py estado                            resumen: por caja, flojas, próximas

Cinco cajas. Un acierto sube una caja; un parcial la mantiene; un fallo vuelve
a la 1. Cuanto más alta la caja, más tarda en volver: 1, 2, 4, 8 y 16 días.

El estado vive en wiki/_repaso.tsv. Lo escribe este script y nadie más; es
estado personal de estudio, no contenido de la wiki. Sin dependencias.
"""
import datetime as dt
import json
import pathlib
import re
import sys

W = pathlib.Path(__file__).resolve().parent.parent
ESTADO = W / "_repaso.tsv"
INTERVALO = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
CABECERA = ("# pagina\tcaja\tultima\tproxima\taciertos\tfallos\n"
            "# escrito por wiki/scripts/repaso.py — estado personal de repaso, no contenido\n")


def hoy():
    return dt.date.today()


def secciones():
    f = W / "_config.json"
    if not f.exists():
        sys.exit(f"ERROR: falta {f.relative_to(W.parent)}.")
    cfg = json.loads(f.read_text(encoding="utf-8"))
    # Las síntesis son la opinión del propio usuario: no tiene sentido examinarse de ella.
    return [s["carpeta"] for s in cfg["secciones"] if not s.get("hoja")]


def paginas():
    """pagina -> tldr, para las páginas repasables (vigentes, fuera de las secciones hoja)."""
    out = {}
    for sec in secciones():
        for p in sorted((W / sec).glob("*.md")):
            if p.name.startswith("_"):
                continue
            t = p.read_text(encoding="utf-8")[:1200]
            if re.search(r"^estado: obsoleto", t, re.M):
                continue
            m = re.search(r"^tldr: (.*)$", t, re.M)
            out[f"{sec}/{p.stem}"] = m.group(1).strip() if m else ""
    return out


def entrantes():
    """Grado entrante desde _grafo.tsv: las páginas más enlazadas son los conceptos centrales."""
    f, g = W / "_grafo.tsv", {}
    if f.exists():
        for l in f.read_text(encoding="utf-8").splitlines():
            c = l.split("\t")
            if l.startswith("#") or len(c) < 2:
                continue
            g[c[0]] = int(c[1]) if c[1].isdigit() else 0
    return g


def leer():
    est = {}
    if ESTADO.exists():
        for l in ESTADO.read_text(encoding="utf-8").splitlines():
            c = l.split("\t")
            if l.startswith("#") or len(c) < 6:
                continue
            est[c[0]] = {"caja": int(c[1]), "ultima": c[2], "proxima": c[3],
                         "aciertos": int(c[4]), "fallos": int(c[5])}
    return est


def escribir(est):
    filas = [f"{k}\t{v['caja']}\t{v['ultima']}\t{v['proxima']}\t{v['aciertos']}\t{v['fallos']}"
             for k, v in sorted(est.items())]
    ESTADO.write_text(CABECERA + "\n".join(filas) + ("\n" if filas else ""), encoding="utf-8")


def pendientes(n):
    pags, est, g, h = paginas(), leer(), entrantes(), hoy().isoformat()
    vencidas = sorted((k for k in pags if k in est and est[k]["proxima"] <= h),
                      key=lambda k: (est[k]["proxima"], est[k]["caja"]))
    # Lo nunca repasado, empezando por lo más central del grafo.
    nuevas = sorted((k for k in pags if k not in est), key=lambda k: (-g.get(k, 0), k))
    lista = [(k, "vencida") for k in vencidas] + [(k, "nueva") for k in nuevas]
    if not lista:
        # Todo al día: adelantar lo más flojo.
        lista = [(k, "adelantada") for k in sorted(
            (k for k in pags if k in est), key=lambda k: (est[k]["caja"], est[k]["proxima"]))]
    if not lista:
        print("No hay páginas que repasar todavía.")
        return
    for k, motivo in lista[:n]:
        caja = f"caja {est[k]['caja']}" if k in est else "sin repasar"
        print(f"{k}  ·  {pags[k]}  ({caja}, {motivo})")
    resto = len(lista) - n
    if resto > 0:
        print(f"\n… y {resto} más.")


def registrar(pagina, resultado):
    pagina = pagina.removesuffix(".md")
    if resultado not in ("acierto", "parcial", "fallo"):
        sys.exit("El resultado es acierto, parcial o fallo.")
    if not (W / f"{pagina}.md").exists():
        sys.exit(f"No existe wiki/{pagina}.md")
    est = leer()
    e = est.get(pagina, {"caja": 1, "ultima": "", "proxima": "", "aciertos": 0, "fallos": 0})
    if resultado == "acierto":
        e["caja"], e["aciertos"] = min(e["caja"] + 1, 5), e["aciertos"] + 1
    elif resultado == "fallo":
        e["caja"], e["fallos"] = 1, e["fallos"] + 1
    e["ultima"] = hoy().isoformat()
    e["proxima"] = (hoy() + dt.timedelta(days=INTERVALO[e["caja"]])).isoformat()
    est[pagina] = e
    escribir(est)
    print(f"{pagina}: {resultado} → caja {e['caja']}, vuelve el {e['proxima']}")


def estado():
    pags, est, h = paginas(), leer(), hoy().isoformat()
    repasadas = [k for k in est if k in pags]
    print(f"{len(repasadas)} de {len(pags)} páginas repasadas alguna vez.")
    if not repasadas:
        return
    cajas = {c: sum(1 for k in repasadas if est[k]["caja"] == c) for c in range(1, 6)}
    print("Por caja: " + " · ".join(f"{c}: {cajas[c]}" for c in range(1, 6)))
    vencidas = [k for k in repasadas if est[k]["proxima"] <= h]
    print(f"Vencidas hoy: {len(vencidas)}")
    flojas = sorted((k for k in repasadas if est[k]["fallos"]),
                    key=lambda k: (-est[k]["fallos"] + est[k]["aciertos"], est[k]["caja"]))[:5]
    if flojas:
        print("\nLo que más cuesta:")
        for k in flojas:
            print(f"  {k}  ({est[k]['aciertos']} aciertos, {est[k]['fallos']} fallos, caja {est[k]['caja']})")
    proxima = min((est[k]["proxima"] for k in repasadas), default=None)
    if proxima and proxima > h:
        print(f"\nPróximo repaso: {proxima}")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__.strip())
        return 1
    if a[0] == "pendientes":
        pendientes(int(a[1]) if len(a) > 1 and a[1].isdigit() else 5)
    elif a[0] == "registrar" and len(a) == 3:
        registrar(a[1], a[2])
    elif a[0] == "estado":
        estado()
    else:
        print(__doc__.strip())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
