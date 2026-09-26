#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sebastian Vallejo — https://github.com/svallejo-dev/llm-wiki
# Copiado en tu wiki, es tuyo: no hace falta conservar este aviso (LICENSE-WIKIS.md).
"""Verifica el invariante de anclaje: toda cifra citable existe literal en el raw.

La ingesta establece el invariante; esto lo comprueba. Extrae los literales de
alta señal de una página y los busca **verbatim** en los raw de su campo `raw:`
(o de la página de la que deriva).

  verificar_anclaje.py                      todas las páginas con campo raw:
  verificar_anclaje.py conceptos/rag        una página
  verificar_anclaje.py --cifras             solo el inventario de _cifras.md
  verificar_anclaje.py --citas              las citas entre comillas de TODAS las
                                            páginas, contra todo el raw

Reporta, nunca arregla: un hecho mal anclado lo decide una persona (regla 11).

Por qué normaliza los saltos de línea antes de buscar: `pdftotext` conserva el
maquetado del PDF, así que una frase del original puede quedar partida en dos
líneas y un `grep -F` de la frase entera falla aunque el dato esté ahí. Pasó de
verdad con `41% of all new code` / `is AI-generated`.
"""
import json
import pathlib
import re
import sys
import unicodedata

W = pathlib.Path(__file__).resolve().parent.parent


def secciones():
    """Las secciones las declara wiki/_config.json: el script no conoce ninguna wiki."""
    f = W / "_config.json"
    if not f.exists():
        sys.exit(f"ERROR: falta {f.relative_to(W.parent)}.")
    return [s["carpeta"] for s in json.loads(f.read_text(encoding="utf-8"))["secciones"]]

# Literales que merecen anclaje. La idea es cazar lo que un lector citaría y
# dejar pasar la prosa: si no es una cifra, una fecha o una cita, no es un dato
# de carga y no hace falta verificarlo.
PATRONES = [
    (r"`([^`\n]*?\d[^`\n]*?)`", "código o cifra entre backticks"),
    (r"\b(\d{1,3}(?:[.,]\d{3})+)\b", "número con separador de millares"),
    (r"\b(\d+[.,]\d+\s*(?:×|x|%|min|ms|s|MB|GB|K|M)?)\b", "decimal"),
    (r"\b(\d+\s*(?:%|×|K\b|M\b))", "porcentaje o multiplicador"),
    (r"\b(\d{4}-\d{2}-\d{2})\b", "fecha ISO"),
    (r"\bn\s*=\s*(\d+)\b", "tamaño muestral"),
]
CITA_MIN = 40   # por debajo, las comillas suelen marcar un término, no una cita
RUIDO = re.compile(r"^(?:\d{4}|20\d\d|[01]?\d|\d{1,2}[.,]\d{1,2})$")
# Rutas de fichero y fechas de la propia página no son datos de carga: son
# metadatos que la wiki escribe sobre sí misma, no afirmaciones sobre el mundo.
ES_RUTA = re.compile(r"(?:^|/)(?:raw|wiki)/|\.(?:md|pdf|py|tsv|json|ya?ml)$")


def norm(s):
    """Colapsa espacios y saltos, y quita acentos: la comparación es de cadena."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def frontmatter_raw(texto):
    if not texto.startswith("---"):
        return []
    fin = texto.find("\n---", 3)
    m = re.search(r"^raw: \[(.*?)\]", texto[3:fin if fin > 0 else None], re.M)
    if not m:
        return []
    return [v.strip().strip('"').strip("'") for v in m.group(1).split(",") if v.strip()]


def cuerpo(texto):
    if texto.startswith("---"):
        fin = texto.find("\n---", 3)
        if fin > 0:
            return texto[fin + 4:]
    return texto


def sin_rutas(texto):
    """Quita destinos de enlaces y rutas: una fecha dentro de
    `raw/2026-09-21-x.md` es parte de un nombre de fichero, no un dato."""
    texto = re.sub(r"\]\([^)]*\)", "]", texto)                      # destinos de [texto](destino)
    texto = re.sub(r"`[^`\n]*(?:raw|wiki)/[^`\n]*`", " ", texto)       # rutas entre backticks
    return re.sub(r"\b(?:raw|wiki)/\S+", " ", texto)                   # rutas sueltas


def citas(texto):
    """Pasajes entre comillas, emparejando en orden.

    Con comillas rectas un patrón no sabe cuál abre y cuál cierra, y empareja el
    cierre de una cita con la apertura de la siguiente. Aquí se recorre cada línea
    y se emparejan de dos en dos; las tipográficas (“ ”) ya distinguen apertura
    y cierre.
    """
    out = []
    for linea in texto.splitlines():
        out += re.findall(r"“([^”]+)”", linea)
        rectas = [m.start() for m in re.finditer(r'"', linea)]
        for a, b in zip(rectas[0::2], rectas[1::2]):
            out.append(linea[a + 1:b])
    return [c.strip() for c in out
            if len(c.strip()) >= CITA_MIN and "`" not in c and "[[" not in c]


def literales(texto, fechas_propias=()):
    texto = sin_rutas(texto)
    vistos, out = set(), []
    for c in citas(texto):
        if norm(c) not in vistos:
            vistos.add(norm(c))
            out.append((c, "cita textual"))
    for pat, clase in PATRONES:
        for m in re.finditer(pat, texto):
            lit = m.group(1).strip()
            if (len(lit) < 2 or RUIDO.match(lit) or ES_RUTA.search(lit)
                    or lit in fechas_propias or norm(lit) in vistos):
                continue
            vistos.add(norm(lit))
            # Una celda como `85% / 51% / 41%` agrupa tres cifras del original:
            # cada una ancla por separado, la cadena unida nunca.
            partes = [x.strip() for x in lit.split("/")] if (
                "/" in lit and clase != "cita textual") else [lit]
            for parte in partes:
                if parte and not RUIDO.match(parte):
                    out.append((parte, clase))
    # Una cifra suelta que ya va dentro de un literal más largo ("999K" dentro de
    # "999K estrellas") no añade información: si el largo ancla, ella también.
    largos = [norm(l) for l, _ in out]
    return [(l, c) for l, c in out
            if not any(norm(l) != o and norm(l) in o for o in largos)]


def resolver_raw(ref):
    p = W / ref
    if p.exists():
        return p
    for cand in (W / f"{ref}.md", W / "raw" / pathlib.Path(ref).name):
        if cand.exists():
            return cand
    return None


def verificar(pagina):
    texto = pagina.read_text(encoding="utf-8")
    refs = frontmatter_raw(texto)
    clave = f"{pagina.parent.name}/{pagina.stem}"
    if not refs:
        return clave, None, []

    corpus, faltan_raw = "", []
    for r in refs:
        f = resolver_raw(r)
        if f is None:
            faltan_raw.append(r)
        else:
            corpus += " " + norm(f.read_text(encoding="utf-8", errors="replace"))

    fallos = [("(raw inexistente)", r) for r in faltan_raw]
    propias = set(re.findall(r"^(?:creado|actualizado): (\S+)", texto, re.M))
    lits = literales(cuerpo(texto), propias)
    for lit, clase in lits:
        if norm(lit) not in corpus:
            fallos.append((lit, clase))
    return clave, len(lits), fallos


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    solo_cifras = "--cifras" in sys.argv

    if "--citas" in sys.argv:
        raws = " ".join(norm(f.read_text(encoding="utf-8", errors="replace"))
                        for f in (W / "raw").rglob("*.md"))
        malas = 0
        for s in secciones():
            for pag in sorted((W / s).glob("*.md")):
                if pag.name.startswith("_"):
                    continue
                for c in citas(sin_rutas(cuerpo(pag.read_text(encoding="utf-8")))):
                    if norm(c) not in raws:
                        malas += 1
                        corto = c if len(c) < 70 else c[:67] + "..."
                        print(f"  {s}/{pag.stem}  \u201c{corto}\u201d")
        if malas:
            print(f"\n{malas} citas entre comillas que no están literales en ningún raw. "
                  "Casi siempre son traducciones: quita las comillas y déjalas en cursiva "
                  "como paráfrasis, o cita en el idioma original.")
            return 1
        print("Todas las citas entre comillas están literales en el raw.")
        return 0

    if solo_cifras:
        t = (W / "_cifras.md").read_text(encoding="utf-8")
        raws = {f: norm(f.read_text(encoding="utf-8", errors="replace"))
                for f in (W / "raw").glob("*.md")}
        malos = 0
        for lit in re.findall(r"^\|\s*`([^`]+)`", t, re.M):
            for parte in [p.strip() for p in lit.split("/")]:
                if not any(norm(parte) in c for c in raws.values()):
                    print(f"  SIN ANCLAJE  {parte}")
                    malos += 1
        print(f"\n_cifras.md: {'todo anclado' if not malos else f'{malos} sin anclaje'}")
        return 1 if malos else 0

    if args:
        pags = [W / (a if a.endswith(".md") else a + ".md") for a in args]
    else:
        pags = [p for s in secciones() for p in sorted((W / s).glob("*.md"))
                if not p.name.startswith("_")]

    total_fallos = total_citas = con_raw = 0
    for p in pags:
        if not p.exists():
            print(f"  no existe: {p.relative_to(W)}")
            continue
        clave, n, fallos = verificar(p)
        if n is None:
            continue
        con_raw += 1
        if fallos:
            no_literales = [f for f in fallos if f[1] == "cita textual"]
            datos = [f for f in fallos if f[1] != "cita textual"]
            total_fallos += len(datos)
            total_citas += len(no_literales)
            print(f"\n  {clave}  ({n} literales)")
            for lit, clase in datos:
                print(f"    SIN ANCLAJE  {lit}   [{clase}]")
            for lit, _ in no_literales:
                corto = lit if len(lit) < 70 else lit[:67] + "..."
                print(f"    CITA NO LITERAL  \u201c{corto}\u201d")

    print(f"\n{con_raw} páginas con campo `raw:`")
    if total_citas:
        print(f"\n{total_citas} pasajes entre comillas que no aparecen literales en el raw.")
        print("Casi siempre es una traducción: el raw está en otro idioma. Las comillas "
              "afirman literalidad, así que la corrección es quitarlas y dejar el pasaje "
              "en cursiva como paráfrasis, o citar en el idioma original.")
    if total_fallos:
        print(f"\n{total_fallos} cifras o datos sin anclaje. Revisa a mano: puede ser un "
              "dato inventado, o una cifra derivada o reformateada. No se arregla solo.")
        return 1
    if not total_citas:
        print("Todos los literales anclados.")
    print("\nNota: solo se verifican las páginas con campo `raw:` — entidades y "
          "conceptos heredan el anclaje de su procedencia.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
