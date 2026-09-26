#!/usr/bin/env python3
"""Mete una fuente en wiki/raw/ con nombre normalizado y encabezado de procedencia.

Resuelve los cinco pasos que a mano se olvidan: normalizar el nombre, poner
procedencia, avisar de duplicados, extraer texto de un PDF a un `.md` hermano
y no pisar nunca un raw ya sellado.

  capturar.py <fichero.pdf> [--fuente URL] [--publicado FECHA] [--autor X]
  capturar.py <fichero.md|.txt> [--fuente ...]
  capturar.py <https://...>
  capturar.py <ruta> --slug nombre-a-mano

No escribe nada si el destino existe: `wiki/raw/` es inmutable. Sin dependencias.
"""
import argparse
import datetime as dt
import html.parser
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request

RAW = pathlib.Path(__file__).resolve().parent.parent / "raw"
HOY = dt.date.today().isoformat()


def slug(texto, limite=80):
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return re.sub(r"-{2,}", "-", t)[:limite].strip("-")


class ATexto(html.parser.HTMLParser):
    """Extractor mínimo: descarta script/style/nav y conserva saltos de bloque."""
    SALTAR = {"script", "style", "noscript", "nav", "footer", "header", "svg"}
    BLOQUE = {"p", "div", "br", "li", "tr", "section", "article",
              "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote"}

    def __init__(self):
        super().__init__()
        self.partes, self.mudo, self.titulo, self._en_titulo = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in self.SALTAR:
            self.mudo += 1
        if tag == "title":
            self._en_titulo = True
        if tag in self.BLOQUE:
            self.partes.append("\n")
        if tag in ("h1", "h2", "h3"):
            self.partes.append("\n## ")

    def handle_endtag(self, tag):
        if tag in self.SALTAR and self.mudo:
            self.mudo -= 1
        if tag == "title":
            self._en_titulo = False
        if tag in self.BLOQUE:
            self.partes.append("\n")

    def handle_data(self, d):
        if self._en_titulo:
            self.titulo += d
        elif not self.mudo and d.strip():
            self.partes.append(d.strip() + " ")

    def texto(self):
        t = "".join(self.partes)
        t = re.sub(r"[ \t]{2,}", " ", t)
        return re.sub(r"\n{3,}", "\n\n", t).strip()


def encabezado(titulo, fuente, publicado, autor, capturado_extra="", original=None):
    l = [f"# {titulo}", "", f"> Fuente: {fuente}"]
    if original:
        l.append(f"> Original: `{original}`")
    l.append(f"> Capturado: {HOY}" + (f" · {capturado_extra}" if capturado_extra else ""))
    l.append(f"> Publicado: {publicado or 'Desconocido'}")
    if autor:
        l.append(f"> Autor: {autor}")
    return "\n".join(l) + "\n\n---\n\n"


def avisar_duplicados(fuente, s):
    """La dedup por origen es la razón de ser del encabezado de procedencia."""
    hits = []
    for f in sorted(RAW.glob("*.md")):
        cab = f.read_text(encoding="utf-8", errors="replace")[:1200]
        if fuente and fuente != "no proporcionada" and fuente in cab:
            hits.append(f"{f.name}  (misma Fuente)")
        elif s and s[:40] in f.stem:
            hits.append(f"{f.name}  (nombre muy parecido)")
    if hits:
        print("\n  AVISO de posible duplicado — revisa antes de ingerir:")
        for h in hits:
            print(f"    {h}")


def salir_si_existe(*rutas):
    for r in rutas:
        if r.exists():
            sys.exit(f"ERROR: `{r.relative_to(RAW.parent)}` ya existe. "
                     "raw/ es inmutable: si la fuente cambió, usa otra fecha o otro slug.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origen", help="ruta a un fichero, o una URL http(s)")
    ap.add_argument("--fuente", default="", help="URL o descripción del origen")
    ap.add_argument("--publicado", default="", help="fecha de publicación del original")
    ap.add_argument("--autor", default="")
    ap.add_argument("--titulo", default="", help="por defecto se deriva del origen")
    ap.add_argument("--slug", default="", help="fuerza el slug del nombre de fichero")
    a = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)

    # ---------- URL ----------
    if a.origen.startswith(("http://", "https://")):
        print(f"Descargando {a.origen}")
        req = urllib.request.Request(a.origen, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            crudo = r.read().decode(r.headers.get_content_charset() or "utf-8",
                                    errors="replace")
        p = ATexto()
        p.feed(crudo)
        cuerpo, titulo = p.texto(), (a.titulo or p.titulo.strip() or a.origen)
        s = a.slug or slug(titulo)
        destino = RAW / f"{HOY}-{s}.md"
        salir_si_existe(destino)
        destino.write_text(
            encabezado(titulo, a.fuente or a.origen, a.publicado, a.autor,
                       "extraído del HTML con capturar.py (texto derivado, no el original)")
            + cuerpo, encoding="utf-8")
        print(f"  -> {destino.relative_to(RAW.parent)}  ({len(cuerpo.split())} palabras)")
        avisar_duplicados(a.fuente or a.origen, s)
        return

    src = pathlib.Path(a.origen).expanduser().resolve()
    if not src.exists():
        sys.exit(f"ERROR: no existe {src}")
    titulo = a.titulo or src.stem.replace("_", " ").replace("-", " ").strip()
    s = a.slug or slug(src.stem)

    # ---------- PDF: binario inmutable + .md hermano greppable ----------
    if src.suffix.lower() == ".pdf":
        if not shutil.which("pdftotext"):
            sys.exit("ERROR: falta pdftotext. Instálalo con: brew install poppler")
        pdf_dest, md_dest = RAW / f"{HOY}-{s}.pdf", RAW / f"{HOY}-{s}.md"
        salir_si_existe(pdf_dest, md_dest)
        if src.parent != RAW or src.name != pdf_dest.name:
            shutil.move(str(src), str(pdf_dest)) if src.parent == RAW else shutil.copy2(str(src), str(pdf_dest))
        # -layout conserva cifras y tablas: sin él se rompe la verificación literal
        texto = subprocess.run(["pdftotext", "-layout", str(pdf_dest), "-"],
                               capture_output=True, text=True, check=True).stdout
        if len(texto.strip()) < 200:
            pdf_dest.unlink(missing_ok=True)
            sys.exit("ERROR: la extracción salió vacía — el PDF está escaneado y no "
                     "tiene capa de texto. Hace falta OCR (brew install tesseract), y "
                     "eso lo decide el usuario. No se ha sellado nada.")
        md_dest.write_text(
            encabezado(titulo, a.fuente or "no proporcionada", a.publicado, a.autor,
                       "extraído con `pdftotext -layout` (capa de texto nativa, sin OCR)",
                       original=pdf_dest.name) + texto, encoding="utf-8")
        print(f"  -> {pdf_dest.relative_to(RAW.parent)}  (original inmutable)")
        print(f"  -> {md_dest.relative_to(RAW.parent)}  ({len(texto.split())} palabras, greppable)")
        print("\n  El campo `raw:` de las páginas apunta al .md, nunca al .pdf.")
        avisar_duplicados(a.fuente, s)
        return

    # ---------- texto ----------
    if src.suffix.lower() not in (".md", ".txt", ".markdown"):
        sys.exit(f"ERROR: no sé capturar `{src.suffix}`. Admito .pdf, .md, .txt y URLs.")
    destino = RAW / f"{HOY}-{s}.md"
    cuerpo = src.read_text(encoding="utf-8", errors="replace")
    if destino != src:
        salir_si_existe(destino)
    ya = "> Fuente:" in cuerpo[:1500]
    h1 = re.match(r"\s*# (.+)\n", cuerpo)
    if ya:
        final = cuerpo
    elif h1 and not a.titulo:
        # Conserva el H1 del documento y pone la procedencia justo debajo,
        # en vez de apilar un título nuevo encima del original.
        final = encabezado(h1.group(1).strip(), a.fuente or "no proporcionada",
                           a.publicado, a.autor) + cuerpo[h1.end():].lstrip("\n")
    else:
        final = encabezado(titulo, a.fuente or "no proporcionada",
                           a.publicado, a.autor) + cuerpo
    destino.write_text(final, encoding="utf-8")
    if src != destino and src.parent == RAW:
        src.unlink()
    print(f"  -> {destino.relative_to(RAW.parent)}"
          f"  ({len(cuerpo.split())} palabras"
          f"{', ya traía encabezado' if ya else ', encabezado añadido'})")
    avisar_duplicados(a.fuente, s)


if __name__ == "__main__":
    main()
