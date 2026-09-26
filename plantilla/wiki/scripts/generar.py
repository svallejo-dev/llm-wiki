#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sebastian Vallejo — https://github.com/svallejo-dev/llm-wiki
# Copiado en tu wiki, es tuyo: no hace falta conservar este aviso (LICENSE-WIKIS.md).
"""Genera los índices derivados de la wiki y reporta el lint mecánico.

Una sola pasada sobre el frontmatter y los enlaces produce:
  wiki/<seccion>/_indice.md   tabla por sección (agrupada si la sección lo pide)
  wiki/_alias.tsv             alias -> página, para "busca antes de crear"
  wiki/_grafo.tsv             adyacencia por página: grado, entrantes, salientes, tipadas

Todo lo que depende del dominio —secciones, topología, umbrales— vive en
wiki/_config.json. Este script no sabe nada de ninguna wiki concreta, y por eso
es el mismo en todas: se actualiza con `andamiar.py actualizar`.

Sin dependencias: solo stdlib. Uso:
  python3 wiki/scripts/generar.py            genera y reporta
  python3 wiki/scripts/generar.py --check    solo reporta, no escribe
"""
import collections
import json
import pathlib
import re
import sys

W = pathlib.Path(__file__).resolve().parent.parent
RE_ENLACE = re.compile(r"\[\[([^\]|#]+)")
RE_TIPADA = re.compile(r"^\s*-\s*([a-záéíóúñ ]+?)::\s*\[\[([^\]|#]+)", re.M)
ENCABEZADO = "| Página | TL;DR | Conf. | Actualizado |\n|---|---|---|---|"


def config():
    f = W / "_config.json"
    if not f.exists():
        sys.exit(f"ERROR: falta {f.relative_to(W.parent)}. "
                 "Ahí se declaran las secciones y la topología de la wiki.")
    return json.loads(f.read_text(encoding="utf-8"))


def frontmatter(texto):
    """Parser mínimo del frontmatter que define el esquema: escalares y listas [a, b]."""
    if not texto.startswith("---"):
        return {}
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}
    datos = {}
    for linea in texto[3:fin].splitlines():
        if not linea.strip() or linea.lstrip().startswith("#") or ":" not in linea:
            continue
        clave, _, valor = linea.partition(":")
        clave, valor = clave.strip(), valor.strip()
        if valor.startswith("[") and valor.endswith("]"):
            datos[clave] = [v.strip().strip('"').strip("'")
                            for v in valor[1:-1].split(",") if v.strip()]
        else:
            datos[clave] = valor.strip('"').strip("'")
    return datos


def cargar(cfg):
    pags = {}
    for s in cfg["secciones"]:
        sec = s["carpeta"]
        for p in sorted((W / sec).glob("*.md")):
            if p.name.startswith("_"):
                continue
            texto = p.read_text(encoding="utf-8")
            clave = f"{sec}/{p.stem}"
            pags[clave] = {
                "sec": sec, "ruta": p, "fm": frontmatter(texto),
                "out": {e.strip() for e in RE_ENLACE.findall(texto)} - {clave},
                "tip": [(v.strip(), d.strip()) for v, d in RE_TIPADA.findall(texto)],
            }
    return pags


def fila(k, pags):
    fm = pags[k]["fm"]
    marca = {"obsoleto": " ⚠︎ obsoleto",
             "disputado": " ⚠︎ disputado"}.get(fm.get("estado", ""), "")
    return (f"| [[{k}]] | {fm.get('tldr', '')}{marca} | "
            f"{fm.get('confianza', '')} | {fm.get('actualizado', '')} |")


def escribir_indices(cfg, pags):
    for s in cfg["secciones"]:
        sec = s["carpeta"]
        (W / sec).mkdir(exist_ok=True)
        claves = sorted(k for k, v in pags.items() if v["sec"] == sec)
        if claves and s.get("agrupar_por"):
            campo, orden = s["agrupar_por"], s.get("ordenar_por", "")
            grupos = collections.defaultdict(list)
            for k in claves:
                grupos[pags[k]["fm"].get(campo, f"sin-{campo}")].append(k)
            bloques = []
            for g in sorted(grupos):
                filas = "\n".join(fila(k, pags) for k in sorted(
                    grupos[g], key=lambda x: pags[x]["fm"].get(orden, "")))
                bloques.append(f"### {g}\n\n{ENCABEZADO}\n{filas}")
            cuerpo = "\n\n".join(bloques)
        elif claves:
            cuerpo = ENCABEZADO + "\n" + "\n".join(fila(k, pags) for k in claves)
        else:
            cuerpo = ENCABEZADO + "\n\n_Vacío._"
        (W / sec / "_indice.md").write_text(
            f"# Índice · {s['titulo']}\n\n> {len(claves)} páginas · generado por "
            f"`wiki/scripts/generar.py`, no editar a mano\n\n{s['desc']}\n\n{cuerpo}\n",
            encoding="utf-8")


def escribir_alias(pags):
    filas = []
    for k, v in sorted(pags.items()):
        terminos = [k.split("/")[1], v["fm"].get("titulo", "")] + v["fm"].get("alias", [])
        for t in dict.fromkeys(x for x in terminos if x):
            filas.append(f"{t}\t{k}")
    (W / "_alias.tsv").write_text(
        "# alias\tpagina — generado por wiki/scripts/generar.py, no editar a mano\n"
        + "\n".join(filas) + "\n", encoding="utf-8")
    return len(filas)


def escribir_grafo(pags, entrantes):
    filas = []
    for k in sorted(pags):
        v = pags[k]
        salientes = sorted(x for x in v["out"] if x in pags)
        ent = sorted(entrantes[k])
        tip = ",".join(f"{verbo.replace(' ', '-')}>{dest}" for verbo, dest in v["tip"])
        filas.append(f"{k}\t{len(ent)}\t{len(salientes)}\t"
                     f"{','.join(ent)}\t{','.join(salientes)}\t{tip}")
    (W / "_grafo.tsv").write_text(
        "# pagina\tgrado_entrante\tgrado_saliente\tENTRANTES\tSALIENTES\tTIPADAS\n"
        "# generado por wiki/scripts/generar.py, no editar a mano\n"
        + "\n".join(filas) + "\n", encoding="utf-8")


def lint(cfg, pags, entrantes):
    inc = collections.defaultdict(list)
    por_sec = {s["carpeta"]: s for s in cfg["secciones"]}
    topologia = cfg.get("topologia", {})
    verbos = set(cfg.get("verbos_tipados", []))
    confianzas = set(cfg.get("confianza", ["alto", "medio", "bajo"]))
    tldr_max = cfg.get("tldr_max", 70)
    minimos = cfg.get("salientes_minimos", 2)

    for k, v in pags.items():
        fm, tipo, s = v["fm"], v["fm"].get("tipo", ""), por_sec[v["sec"]]
        for f in cfg.get("obligatorios", []):
            if not fm.get(f):
                inc["frontmatter incompleto"].append(f"{k}: falta `{f}`")
        if len(fm.get("tldr", "")) > tldr_max:
            inc[f"tldr de más de {tldr_max} caracteres"].append(f"{k}: {len(fm['tldr'])}")
        if fm.get("confianza") and fm["confianza"] not in confianzas:
            inc["confianza inválida"].append(f"{k}: {fm['confianza']}")

        for destino in sorted(v["out"]):
            if destino not in pags and not (W / f"{destino}.md").exists():
                inc["enlaces rotos"].append(f"{k} → {destino}")
            carpeta = destino.split("/")[0]
            permitidos = topologia.get(tipo)
            if permitidos and carpeta not in permitidos and not destino.endswith("_indice"):
                inc["violaciones de topología"].append(
                    f"{k} ({tipo}) → {destino}: un `{tipo}` no puede enlazar a `{carpeta}/`")

        for verbo, _ in v["tip"]:
            if verbos and verbo not in verbos:
                inc["verbo tipado desconocido"].append(f"{k}: `{verbo}::`")

        internos = [x for x in v["out"] if x in pags]
        salvo = s.get("exento_salientes_salvo")
        exento = salvo is not None and fm.get(salvo) != "true"
        if len(internos) < minimos and not exento:
            inc[f"menos de {minimos} enlaces salientes"].append(k)

        if s.get("cubre_minimo"):
            try:
                if int(fm.get("cubre", 0)) < s["cubre_minimo"]:
                    inc[f"cubre < {s['cubre_minimo']}"].append(k)
            except ValueError:
                inc["cubre inválido"].append(k)

    for k, v in pags.items():
        s, n = por_sec[v["sec"]], len(entrantes[k])
        if not n and not s.get("exenta_huerfanas"):
            inc["huérfanas"].append(k)
        if s.get("umbral_pozo") and n > s["umbral_pozo"]:
            inc[f"pozos gravitatorios (>{s['umbral_pozo']} entrantes)"].append(f"{k}: {n}")
        if n and s.get("hoja"):
            inc["nodo hoja con enlaces entrantes"].append(k)
    return inc


def main():
    check = "--check" in sys.argv
    cfg = config()
    pags = cargar(cfg)
    entrantes = collections.defaultdict(set)
    for k, v in pags.items():
        for d in v["out"]:
            if d in pags:
                entrantes[d].add(k)

    inc = lint(cfg, pags, entrantes)
    if not check:
        escribir_indices(cfg, pags)
        n_alias = escribir_alias(pags)
        escribir_grafo(pags, entrantes)
        aristas = sum(len([x for x in v["out"] if x in pags]) for v in pags.values())
        print(f"Generado: {len(cfg['secciones'])} índices de sección · _alias.tsv "
              f"({n_alias} alias) · _grafo.tsv ({len(pags)} nodos, {aristas} aristas)")

    if inc:
        print("\nLint mecánico — incidencias:")
        for cat in sorted(inc):
            print(f"\n  {cat} ({len(inc[cat])}):")
            for x in inc[cat]:
                print(f"    - {x}")
        print("\nLos arreglos de hechos, cifras y contradicciones NO se automatizan: "
              "repórtalos y espera confirmación.")
        return 1
    print("\nLint mecánico: sin incidencias.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
