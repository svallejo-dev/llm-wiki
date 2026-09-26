#!/usr/bin/env python3
"""Crea el andamiaje de una wiki LLM y mantiene sus scripts al día.

  andamiar.py crear <repo> --nombre N --dominio "frase" [--fecha YYYY-MM-DD]
      Copia la plantilla: núcleo CLAUDE.md y wiki/ con esquema, configuración,
      ficheros de sistema y scripts. Las skills de operación no se copian: las
      aporta el plugin llm-wiki. Nunca sobrescribe: si algo ya existe, se
      detiene y lo lista.

  andamiar.py actualizar <repo>
      Copia la versión actual de los scripts genéricos (wiki/scripts/) de la
      plantilla al repo. Solo scripts: el esquema y la configuración son
      propios de cada wiki y no se tocan.

  andamiar.py comprobar <repo>
      Dice qué scripts del repo difieren de la plantilla. Sale con código 1 si
      alguno está desactualizado.

Sin dependencias: solo stdlib.
"""
import argparse
import datetime as dt
import filecmp
import json
import pathlib
import shutil
import subprocess
import sys

PLUGIN = pathlib.Path(__file__).resolve().parent.parent
PLANTILLA = PLUGIN / "plantilla"
MARKETPLACE = "svallejo-dev/llm-wiki"


def destino_de(rel):
    """Ruta en el repo para un fichero de la plantilla."""
    if rel.suffix == ".tpl":
        rel = rel.with_suffix("")
    return rel


def tabla_secciones(cfg):
    filas = ["| Sección | Qué contiene | Índice |", "|---|---|---|"]
    for s in cfg["secciones"]:
        filas.append(f"| {s['titulo']} | {s['desc']} | [[{s['carpeta']}/_indice]] |")
    return "\n".join(filas)


def crear(repo, nombre, dominio, fecha):
    repo.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((PLANTILLA / "wiki" / "_config.json.tpl").read_text(encoding="utf-8")
                     .replace("{{NOMBRE}}", nombre))
    valores = {
        "{{NOMBRE}}": nombre, "{{DOMINIO}}": dominio, "{{FECHA}}": fecha,
        "{{N_SECCIONES}}": str(len(cfg["secciones"])),
        "{{TABLA_SECCIONES}}": tabla_secciones(cfg),
    }

    copias = []
    for src in sorted(PLANTILLA.rglob("*")):
        if not src.is_file() or src.name == "gitignore.fragmento":
            continue
        copias.append((src, repo / destino_de(src.relative_to(PLANTILLA))))

    conflictos = [d for _, d in copias if d.exists()]
    if conflictos:
        print("No se ha creado nada: estos ficheros ya existen y la plantilla no sobrescribe.")
        for d in conflictos:
            print(f"  - {d.relative_to(repo)}")
        print("\nSi el repo ya tiene un CLAUDE.md, fusiónalo a mano con la plantilla "
              f"({PLANTILLA / 'CLAUDE.md.tpl'}) y vuelve a lanzar sin él.")
        return 1

    for src, dst in copias:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix == ".tpl":
            texto = src.read_text(encoding="utf-8")
            for k, v in valores.items():
                texto = texto.replace(k, v)
            dst.write_text(texto, encoding="utf-8")
        else:
            shutil.copy2(src, dst)

    gi, frag = repo / ".gitignore", (PLANTILLA / "gitignore.fragmento").read_text(encoding="utf-8")
    actual = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if "wiki/.obsidian/workspace" not in actual:
        gi.write_text(actual + frag, encoding="utf-8")

    for s in cfg["secciones"]:
        (repo / "wiki" / s["carpeta"]).mkdir(parents=True, exist_ok=True)
    (repo / "wiki" / "raw").mkdir(parents=True, exist_ok=True)

    print(f"Wiki '{nombre}' andamiada en {repo}: {len(copias)} ficheros.\n", flush=True)
    subprocess.run([sys.executable, str(repo / "wiki" / "scripts" / "generar.py")])
    print("\nSiguiente:")
    print("  1. Declarar el plugin en el repo, para que un clon en otra máquina lo ofrezca:")
    print(f"       cd {repo}")
    print(f"       claude plugin marketplace add {MARKETPLACE} --scope project")
    print("       claude plugin install llm-wiki@llm-wiki --scope project")
    print("  2. Adaptar wiki/_config.json y wiki/_esquema/formatos.md al corpus.")
    print("  3. Sellar el raw con corpus.py y hacer la primera ingesta.")
    return 0


def scripts_plantilla():
    return sorted(p for p in (PLANTILLA / "wiki" / "scripts").iterdir() if p.is_file())


def comprobar(repo, silencioso=False):
    desfasados = []
    for src in scripts_plantilla():
        dst = repo / "wiki" / "scripts" / src.name
        if not dst.exists():
            estado = "falta"
        elif filecmp.cmp(src, dst, shallow=False):
            estado = "al día"
        else:
            estado = "DESACTUALIZADO"
        if estado != "al día":
            desfasados.append(src.name)
        if not silencioso:
            print(f"  {estado:15} wiki/scripts/{src.name}")
    return desfasados


def actualizar(repo):
    if not (repo / "wiki" / "_config.json").exists():
        print("ERROR: este repo no tiene wiki/_config.json y los scripts actuales lo necesitan.\n"
              "Créalo primero declarando sus secciones y su topología (mira el de la plantilla); "
              "si no, los scripts nuevos romperían la wiki.")
        return 1
    desfasados = comprobar(repo, silencioso=True)
    if not desfasados:
        print("Scripts al día. Nada que actualizar.")
        return 0
    for nombre in desfasados:
        shutil.copy2(PLANTILLA / "wiki" / "scripts" / nombre, repo / "wiki" / "scripts" / nombre)
        print(f"  actualizado  wiki/scripts/{nombre}")
    print("\nRevisa el cambio con `git diff wiki/scripts/` y regenera: "
          "python3 wiki/scripts/generar.py")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    c = sub.add_parser("crear")
    c.add_argument("repo")
    c.add_argument("--nombre", required=True)
    c.add_argument("--dominio", required=True, help="una frase: 'la historia del jazz', 'frameworks de agentes'")
    c.add_argument("--fecha", default=dt.date.today().isoformat())
    for orden in ("actualizar", "comprobar"):
        sub.add_parser(orden).add_argument("repo")
    a = ap.parse_args()
    repo = pathlib.Path(a.repo).expanduser().resolve()

    if a.orden == "crear":
        return crear(repo, a.nombre, a.dominio, a.fecha)
    if a.orden == "actualizar":
        return actualizar(repo)
    return 1 if comprobar(repo) else 0


if __name__ == "__main__":
    sys.exit(main())
