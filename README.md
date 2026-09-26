# llm-wiki

Plugin de Claude Code para crear y mantener **wikis de conocimiento escritas y mantenidas por el LLM**, siguiendo el patrón [`llm-wiki`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) de Andrej Karpathy.

La idea: en vez de que el modelo redescubra tus documentos en cada pregunta (RAG), los lee una vez y **compone una wiki persistente** —resúmenes, entidades, conceptos, comparativas— que se mantiene al día con cada fuente nueva. Tú curas las fuentes y haces las preguntas; el LLM hace la contabilidad que hace que una wiki siga siendo útil a los seis meses: enlazar, archivar, marcar contradicciones, mantener los índices.

## Instalación

```bash
claude plugin marketplace add svallejo-dev/llm-wiki
claude plugin install llm-wiki@llm-wiki
```

Reinicia Claude Code para que cargue las skills.

## Skills

| Skill | Para qué |
|---|---|
| `/llm-wiki:crear` | Crea una wiki desde cero a partir de una carpeta de documentación reunida: inventaría el corpus, acuerda el esquema contigo, andamia la estructura, sella las fuentes y hace la primera ingesta |
| `/llm-wiki:ingerir` | Integra una fuente nueva (fichero, URL o PDF): triage, páginas nuevas o ampliadas, cascada de índices, bitácora |
| `/llm-wiki:revisar` | Revisión de salud: enlaces rotos, huérfanas, topología, cifras sin anclaje, contradicciones sin marcar |
| `/llm-wiki:sintetizar` | Archiva una conclusión como comparativa, panorama o síntesis propia |

Se disparan solas cuando la petición encaja: "convierte ./docs en una wiki", "ingiere este PDF", "pasa el lint", "archiva esa comparación". Responder preguntas contra la wiki no necesita skill: lo hace el `CLAUDE.md` de cada wiki.

## Cómo es una wiki

```
tu-repo/
├── CLAUDE.md                 núcleo: reglas duras y cómo responder, siempre cargado
├── .claude/settings.json     declara este plugin
└── wiki/                     bóveda de Obsidian
    ├── raw/                  fuentes inmutables (PDF → .pdf + .md extraído)
    ├── resumenes/ entidades/ conceptos/ comparativas/ recetas/ panoramas/ sintesis/
    ├── indice.md  bitacora.md  foco.md  _cifras.md
    ├── _alias.tsv  _grafo.tsv  (generados)
    ├── _config.json          secciones, topología y umbrales
    ├── _esquema/formatos.md  la especificación
    └── scripts/              generar.py · q · capturar.py · verificar_anclaje.py
```

## Principios

- **Schema first, content second, tooling third.** El esquema se escribe antes que la primera página.
- **Invariante de anclaje.** Toda cifra, fecha o cita existe literalmente en la fuente enlazada, y `verificar_anclaje.py` lo comprueba. Las comillas afirman literalidad: una traducción va en cursiva, sin comillas.
- **Las contradicciones son activos, no errores.** Se marcan como disputa; nunca se sobrescribe una afirmación con otra.
- **Leer lo mínimo.** `q` devuelve el resumen de una línea de cada página, así que se decide qué abrir sin abrir nada; `_grafo.tsv` da el vecindario de cualquier página en una línea.
- **Sin infraestructura que la escala no justifique.** Ni base vectorial, ni base de datos de grafos, ni GraphRAG: grep y un grafo en texto plano bastan para cientos de páginas.

## Requisitos

Python 3.9+ (solo biblioteca estándar). Para PDFs, `poppler` (`brew install poppler`). Obsidian es opcional pero recomendado.

## Actualizar

```bash
claude plugin update llm-wiki                                # las skills
python3 <plugin>/scripts/andamiar.py actualizar <tu-repo>    # los scripts de una wiki
```

Los scripts de cada wiki son copias de los del plugin, para que la wiki funcione también sin Claude Code (desde la terminal, en Obsidian o con otro agente). `andamiar.py comprobar` dice si van por detrás; `/llm-wiki:revisar` lo sugiere cuando toca.

## Idioma

Las skills, las plantillas y las wikis que generan están en español. Los scripts son independientes del idioma: las secciones y sus nombres se declaran en `wiki/_config.json`.
