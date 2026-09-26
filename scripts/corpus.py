#!/usr/bin/env python3
"""Inventario y sellado de un corpus de documentación reunida.

  corpus.py inventario <origen>
      Qué hay: formatos, tamaños, duplicados exactos, duplicados entre ficheros
      sueltos y contenido de zips, colecciones de registros con plantilla fija,
      PDFs sin capa de texto, nombres problemáticos y una estimación gruesa del
      tamaño que tendrá la wiki.

  corpus.py sellar <origen> <repo>/wiki [--aplicar]
      Sin --aplicar imprime el plan: qué se sella y con qué nombre, qué se
      descarta por duplicado, qué paquetes se extraen. Con --aplicar lo ejecuta
      usando wiki/scripts/capturar.py de la wiki destino, y deja lista la
      entrada de bitácora del sellado.

Nunca borra ni sobrescribe: los originales se quedan en <origen>.
Sin dependencias: solo stdlib. pdftotext y pdfinfo (poppler) son opcionales
para el inventario y obligatorios para sellar PDFs.
"""
import collections
import datetime as dt
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile

HOY = dt.date.today().isoformat()
TEXTO = {".md", ".markdown", ".txt"}
SOPORTADOS = TEXTO | {".pdf"}
BASURA = re.compile(r"(^|/)(__pycache__|\.pytest_cache|__MACOSX|\.git|\.venv|node_modules)(/|$)"
                    r"|(^|/)\.DS_Store$|\.pyc$")


# ---------------------------------------------------------------- utilidades

def slug(texto, limite=80):
    """Mismo algoritmo que wiki/scripts/capturar.py: minúsculas, sin tildes, kebab."""
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return re.sub(r"-{2,}", "-", t)[:limite].strip("-")


def md5(datos):
    return hashlib.md5(datos).hexdigest()


RUIDO_NOMBRE = re.compile(r"(^|-)(copia|copy|final|backup|bak|old|viejo|nuevo|new|"
                          r"duplicado|dup|tmp|temp|v\d+)(-|$)|-\d$")


def preferencia(nombre):
    """Entre duplicados exactos, el nombre que mejor describe el contenido.

    Al sellar, el nombre se normaliza igual, así que su forma (espacios, tildes)
    no importa: importa lo que dice. Pierde el que lleva ruido de copia o de
    versión ("copia", "final", "v2", "(1)"); entre los demás, el más descriptivo.
    """
    s = slug(pathlib.Path(nombre).stem)
    return (bool(RUIDO_NOMBRE.search(s)), -len(s), nombre)


def recorrer(origen):
    for p in sorted(origen.rglob("*")):
        rel = p.relative_to(origen).as_posix()
        if p.is_file() and not BASURA.search(rel) and not any(
                parte.startswith(".") for parte in p.relative_to(origen).parts):
            yield p


def titulo(texto):
    m = re.search(r"^# (.+)$", texto, re.M)
    return m.group(1).strip() if m else ""


def firma_h2(texto):
    """Los H2 de un documento, sin numeración. Si muchos ficheros comparten la
    misma secuencia de H2, son registros con plantilla fija (fichas, casos...)."""
    hs = [re.sub(r"^[\d.\s]+", "", h).strip().lower()
          for h in re.findall(r"^## (.+)$", texto, re.M)]
    return tuple(hs[:8]) if len(hs) >= 3 else None


def capa_de_texto(pdf):
    """Caracteres de texto en las dos primeras páginas; None si no hay pdftotext."""
    if not shutil.which("pdftotext"):
        return None
    r = subprocess.run(["pdftotext", "-l", "2", str(pdf), "-"], capture_output=True, text=True)
    return len(r.stdout.strip())


def paginas_pdf(pdf):
    if not shutil.which("pdfinfo"):
        return None
    r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
    return int(m.group(1)) if m else None


def miembros_zip(z):
    """(nombre, md5, texto-o-None) de cada miembro útil de un zip."""
    out, basura = [], []
    with zipfile.ZipFile(z) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if BASURA.search(info.filename):
                basura.append(info.filename)
                continue
            datos = zf.read(info)
            texto = None
            if pathlib.PurePosixPath(info.filename).suffix.lower() in TEXTO:
                texto = datos.decode("utf-8", errors="replace")
            out.append((info.filename, md5(datos), texto))
    return out, basura


def problemas_de_nombre(nombre):
    p = []
    if " " in nombre:
        p.append("espacios")
    if not nombre.isascii():
        p.append("caracteres no ASCII")
    if nombre != nombre.lower():
        p.append("mayúsculas")
    return p


# ---------------------------------------------------------------- inventario

def inventario(origen):
    ficheros = list(recorrer(origen))
    if not ficheros:
        sys.exit(f"No hay ficheros en {origen}")

    por_ext = collections.Counter(f.suffix.lower() or "(sin extensión)" for f in ficheros)
    hashes = collections.defaultdict(list)          # md5 -> [descripciones]
    textos, pdfs, zips, otros = [], [], [], []
    firmas = collections.defaultdict(list)          # firma H2 -> [ficheros]

    for f in ficheros:
        ext, rel = f.suffix.lower(), f.relative_to(origen).as_posix()
        datos = f.read_bytes()
        if ext != ".zip":
            hashes[md5(datos)].append(("suelto", rel))
        if ext in TEXTO:
            t = datos.decode("utf-8", errors="replace")
            textos.append({"rel": rel, "lineas": t.count("\n") + 1,
                           "palabras": len(t.split()), "h1": titulo(t),
                           "fm": t.startswith("---"),
                           "urls": len(re.findall(r"https?://", t))})
            fh = firma_h2(t)
            if fh:
                firmas[fh].append(rel)
        elif ext == ".pdf":
            pdfs.append({"rel": rel, "mb": len(datos) / 1e6,
                         "paginas": paginas_pdf(f), "texto": capa_de_texto(f)})
        elif ext == ".zip":
            miembros, basura = miembros_zip(f)
            zips.append({"rel": rel, "n": len(miembros), "basura": basura})
            for nombre, h, t in miembros:
                hashes[h].append(("zip", f"{rel}:{nombre}"))
                if t:
                    fh = firma_h2(t)
                    if fh:
                        firmas[fh].append(f"{rel}:{nombre}")
        else:
            otros.append(rel)

    print(f"# Inventario de `{origen}`\n")
    print(f"{len(ficheros)} ficheros · " + " · ".join(f"{n} {e}" for e, n in por_ext.most_common()))

    if textos:
        print("\n## Documentos de texto\n")
        print("| Fichero | Líneas | Palabras | URLs | Frontmatter | Título |")
        print("|---|---|---|---|---|---|")
        for t in sorted(textos, key=lambda x: -x["palabras"]):
            print(f"| `{t['rel']}` | {t['lineas']} | {t['palabras']} | {t['urls']} | "
                  f"{'sí' if t['fm'] else 'no'} | {t['h1'][:60]} |")

    if pdfs:
        print("\n## PDF\n")
        for p in pdfs:
            if p["texto"] is None:
                estado = "¿capa de texto? instala poppler: brew install poppler"
            elif p["texto"] < 200:
                estado = "**SIN capa de texto: escaneado, hará falta OCR**"
            else:
                estado = "capa de texto nativa"
            pags = f"{p['paginas']} págs · " if p["paginas"] else ""
            print(f"- `{p['rel']}` — {pags}{p['mb']:.1f} MB · {estado}")

    if zips:
        print("\n## Paquetes\n")
        for z in zips:
            b = f" · basura a excluir: {len(z['basura'])} ({', '.join(sorted({x.split('/')[0] for x in z['basura']}))})" if z["basura"] else ""
            print(f"- `{z['rel']}` — {z['n']} ficheros útiles{b}")

    dup_sueltos = [v for v in hashes.values() if sum(1 for k, _ in v if k == "suelto") > 1]
    if dup_sueltos:
        print("\n## Duplicados exactos entre ficheros sueltos\n")
        print("Mismo contenido byte a byte. Se sella uno por grupo; el resto se descarta y queda registrado.\n")
        for grupo in dup_sueltos:
            nombres = [r for k, r in grupo if k == "suelto"]
            queda = min(nombres, key=lambda n: preferencia(pathlib.Path(n).name))
            print(f"- se conserva `{queda}`, se descarta " +
                  ", ".join(f"`{n}`" for n in nombres if n != queda))

    cruzados = [v for v in hashes.values()
                if any(k == "suelto" for k, _ in v) and any(k == "zip" for k, _ in v)]
    if cruzados:
        print("\n## Duplicados entre sueltos y contenido de paquetes\n")
        print("El paquete se conserva entero, pero al ingerir hay que tratarlos como **una sola fuente**.\n")
        for grupo in cruzados:
            print("- " + " ≡ ".join(f"`{r}`" for _, r in grupo))

    colecciones = {f: v for f, v in firmas.items() if len(v) >= 5}
    if colecciones:
        print("\n## Colecciones con plantilla fija\n")
        print("Muchos documentos con la misma secuencia de secciones: son registros, no fuentes "
              "sueltas. Candidatos a **tipo especializado** con carpeta propia y generación en lote.\n")
        for firma, docs in colecciones.items():
            print(f"- {len(docs)} documentos con secciones: {' · '.join(firma[:5])}…")
            print(f"  ej.: `{docs[0]}`")

    raros = [(f.relative_to(origen).as_posix(), problemas_de_nombre(f.name))
             for f in ficheros if problemas_de_nombre(f.name)]
    if raros:
        print("\n## Nombres que se normalizarán al sellar\n")
        for rel, p in raros[:25]:
            print(f"- `{rel}` — {', '.join(p)}")
        if len(raros) > 25:
            print(f"- … y {len(raros) - 25} más")

    if otros:
        print("\n## Sin soporte directo\n")
        print("No se sellan. Conviértelos a texto o PDF y captúralos aparte si importan.\n")
        for o in otros:
            print(f"- `{o}`")

    # Estimación: cada documento largo único da un resumen y alimenta varias
    # entidades y conceptos; los registros con plantilla dan una página cada uno.
    unicos_largos = len({md5((origen / t["rel"]).read_bytes()) for t in textos
                         if t["palabras"] >= 2500}) + sum(
        1 for p in pdfs if (p["paginas"] or 0) >= 10)
    registros = sum(len(v) for v in colecciones.values())
    bajo, alto = unicos_largos * 6 + registros, unicos_largos * 10 + registros
    print("\n## Estimación gruesa\n")
    print(f"{unicos_largos} documentos largos únicos · {registros} registros con plantilla "
          f"→ **~{bajo}-{alto} páginas** de wiki.")
    if alto > 150:
        print("\nPor encima de ~150 páginas un índice plano deja de ser fiable: la plantilla ya "
              "trae índice jerárquico, `q` y `_alias.tsv`, que es lo que lo resuelve.")


# ---------------------------------------------------------------- sellado

def sellar(origen, wiki, aplicar):
    capturar = wiki / "scripts" / "capturar.py"
    if not capturar.exists():
        sys.exit(f"ERROR: no existe {capturar}. Andamia la wiki primero (andamiar.py crear).")
    raw = wiki / "raw"
    raw.mkdir(exist_ok=True)

    ficheros = list(recorrer(origen))
    sueltos = [f for f in ficheros if f.suffix.lower() in SOPORTADOS]
    zips = [f for f in ficheros if f.suffix.lower() == ".zip"]
    sin_soporte = [f for f in ficheros if f.suffix.lower() not in SOPORTADOS | {".zip"}]

    grupos = collections.defaultdict(list)
    for f in sueltos:
        grupos[md5(f.read_bytes())].append(f)
    conservar, descartes = [], []
    for fs in grupos.values():
        queda = min(fs, key=lambda f: preferencia(f.name))
        conservar.append(queda)
        descartes += [(f, queda) for f in fs if f != queda]

    usados = set()
    plan = []
    for f in sorted(conservar, key=lambda f: f.name):
        base = slug(f.stem) or "documento"
        s, n = base, 2
        while s in usados or (raw / f"{HOY}-{s}.md").exists() or (raw / f"{HOY}-{s}.pdf").exists():
            s, n = f"{base}-{n}", n + 1
        usados.add(s)
        plan.append((f, s))

    paquetes = []
    for z in zips:
        destino, copia = raw / slug(z.stem), raw / "_paquetes" / z.name
        conflicto = destino.exists() or copia.exists()
        paquetes.append((z, destino, copia, conflicto))

    hashes_sueltos = {md5(f.read_bytes()): f for f in sueltos}
    cruzados = []
    for z in zips:
        miembros, _ = miembros_zip(z)
        for nombre, h, _t in miembros:
            if h in hashes_sueltos:
                cruzados.append((hashes_sueltos[h], z, nombre))

    print(f"# Plan de sellado · {origen} → {raw}\n")
    for f, s in plan:
        extra = "  (+ .md extraído)" if f.suffix.lower() == ".pdf" else ""
        print(f"  sellar     {f.relative_to(origen)}  →  {HOY}-{s}{f.suffix.lower()}{extra}")
    for f, queda in descartes:
        print(f"  descartar  {f.relative_to(origen)}  (idéntico a {queda.relative_to(origen)})")
    for z, destino, copia, conflicto in paquetes:
        estado = "  CONFLICTO: ya existe, se omite" if conflicto else ""
        print(f"  extraer    {z.relative_to(origen)}  →  raw/{destino.name}/  "
              f"(original en raw/_paquetes/){estado}")
    for f in sin_soporte:
        print(f"  omitir     {f.relative_to(origen)}  (formato sin soporte)")

    if not aplicar:
        print("\nNada aplicado. Revisa el plan y repite con --aplicar.")
        print("Para cambiar un nombre o qué duplicado se conserva, renombra el fichero en el "
              "corpus y vuelve a planificar: el corpus aún no es raw y se puede tocar.")
        return

    print("\nAplicando…")
    sellados, fallos, extraidos = [], [], []
    for f, s in plan:
        r = subprocess.run([sys.executable, str(capturar), str(f), "--slug", s],
                           capture_output=True, text=True)
        if r.returncode == 0:
            sellados.append((f, s))
        else:
            fallos.append((f, (r.stderr or r.stdout).strip().splitlines()[-1]))
    for z, destino, copia, conflicto in paquetes:
        if conflicto:
            fallos.append((z, "destino ya existe"))
            continue
        _, basura = miembros_zip(z)
        with zipfile.ZipFile(z) as zf:
            # Fuera la basura y cualquier entrada que intente salir del destino
            # (rutas absolutas o con ".."): un zip no debe escribir fuera de raw/.
            utiles = [m for m in zf.namelist()
                      if not m.endswith("/") and not BASURA.search(m)
                      and not m.startswith("/") and ".." not in pathlib.PurePosixPath(m).parts]
            for m in utiles:
                zf.extract(m, destino)
        copia.parent.mkdir(exist_ok=True)
        shutil.copy2(z, copia)
        extraidos.append((z, destino, len(utiles), basura))

    print(f"\n{len(sellados)} fuentes selladas · {len(descartes)} duplicados descartados · "
          f"{len(extraidos)} paquetes extraídos · {len(fallos)} fallos")
    for f, motivo in fallos:
        print(f"  FALLO  {f.name}: {motivo}")

    # Entrada de bitácora lista para añadir
    print("\n--- entrada de bitácora (añádela al final de wiki/bitacora.md) ---\n")
    print(f"## [{HOY}] sellado | raw inicial desde {origen.name}\n")
    print(f"> sellado · {len(sellados)} fuentes · {len(descartes)} duplicados descartados · "
          f"{len(extraidos)} paquetes extraídos\n")
    print(f"- **Origen**: `{origen}`")
    pdfs = sum(1 for f, _ in sellados if f.suffix.lower() == ".pdf")
    print(f"- **Sellados ({len(sellados)})**: nombres normalizados a `{HOY}-<slug>`, con "
          f"encabezado de procedencia" + (f"; {pdfs} PDF como `.pdf` + `.md` extraído con "
                                          "`pdftotext -layout`" if pdfs else "") + ".")
    if descartes:
        print(f"- **Descartados por duplicado byte a byte ({len(descartes)})**:")
        for f, queda in descartes:
            print(f"  - `{f.name}` ≡ `{queda.name}` (se conserva el segundo)")
    for z, destino, n, basura in extraidos:
        b = f"; excluida basura: {len(basura)} ficheros" if basura else ""
        print(f"- **Paquete** `{z.name}` → `raw/{destino.name}/` ({n} ficheros{b}); "
              f"original en `raw/_paquetes/`")
    for f, z, nombre in cruzados:
        print(f"- **Duplicado suelto/paquete**: `{f.name}` ≡ `{z.name}:{nombre}` — "
              "al ingerir, tratar como una sola fuente")
    for f in sin_soporte:
        print(f"- **Sin soporte, no sellado**: `{f.name}`")
    for f, motivo in fallos:
        print(f"- **Fallo**: `{f.name}` — {motivo}")
    print("- **A partir de aquí `wiki/raw/` es inmutable.**")
    print("\n--- fin ---")
    print(f"\nLos originales siguen en {origen}. Si esa carpeta está dentro del repo, bórrala "
          "tras verificar el sellado para no versionar el corpus dos veces.")


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "inventario":
        inventario(pathlib.Path(a[1]).expanduser().resolve())
    elif len(a) >= 3 and a[0] == "sellar":
        sellar(pathlib.Path(a[1]).expanduser().resolve(),
               pathlib.Path(a[2]).expanduser().resolve(), "--aplicar" in a)
    else:
        print(__doc__.strip())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
