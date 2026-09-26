---
name: crear
description: Crea desde cero una wiki LLM (patrón llm-wiki de Karpathy) a partir de una carpeta de documentación — analiza el corpus, acuerda el esquema, andamia, sella las fuentes y hace la primera ingesta. Úsala cuando el usuario quiera convertir documentos, PDFs o investigación en una wiki, base de conocimiento o second brain, aunque no diga "wiki" ("organiza esta carpeta", "monta un second brain con esto", "aplica el patrón de Karpathy"), o para poner al día los scripts de una wiki. NO para ingerir en una wiki existente (/llm-wiki:ingerir).
---

# Crear una wiki desde cero

Una wiki LLM no se construye escribiendo páginas: se construye escribiendo primero **el esquema que gobierna cómo se escriben**. La lección más repetida por quien lleva meses con este patrón es *schema first, content second, tooling third*: las wikis sin esquema antes de acumular masa *"degeneran en cementerio en dos meses"*. Esta skill existe para que eso no dependa de acordarse.

El resultado es un repo con tres capas —raw inmutable, wiki derivada, esquema— y scripts genéricos para buscar, generar índices y verificar el anclaje. El mantenimiento posterior lo hacen las otras skills de este plugin (`/llm-wiki:ingerir`, `/llm-wiki:revisar`, `/llm-wiki:sintetizar`), así que no depende de esta sesión.

En los comandos, **`$SKILL`** es el directorio base de esta skill (Claude Code lo indica al cargarla) y **`$PLUGIN`** la raíz del plugin, dos niveles por encima: `$SKILL/../..`. Los scripts están en `$PLUGIN/scripts/` y la plantilla en `$PLUGIN/plantilla/`.

## Antes de empezar

Lee `$SKILL/references/patron-karpathy.md`. Es lo destilado de investigar el patrón, sus implementaciones de referencia, lo que dice el uso prolongado y los anti-patrones conocidos. **No vuelvas a investigar** salvo que el usuario lo pida o sospeches que el ecosistema ha cambiado mucho.

## Fase 0 — El encargo

Aclara, preguntando solo lo que no puedas deducir:

- Dónde está el corpus y dónde vivirá la wiki. Normalmente el mismo repo: la carpeta del corpus acaba sellada dentro de `wiki/raw/`.
- Un nombre corto (para `CLAUDE.md`, la configuración y las skills) y el dominio en una frase.
- Si el repo es git y tiene remoto: el sellado va en un commit propio.

## Fase 1 — Inventario mecánico

```bash
python3 $PLUGIN/scripts/corpus.py inventario <carpeta-del-corpus>
```

Sin leer nada a mano, te da: formatos y tamaños, **duplicados byte a byte** (en el primer corpus hubo 4 de 19, con nombres distintos), **duplicados entre ficheros sueltos y contenido de zips**, **colecciones con plantilla fija** (candidatas a tipo especializado), PDFs sin capa de texto, nombres que romperán grep y una estimación gruesa del número de páginas.

Si hay PDFs y faltan `pdftotext`/`pdfinfo`, dilo: `brew install poppler`. No lo instales sin permiso.

## Fase 2 — Análisis del contenido

Ahora sí, a leer. Lo que buscas:

- **Clusters temáticos** y qué documentos pertenecen a cada uno.
- **Entidades y conceptos que aparecen en varios documentos**: serán las páginas con más enlaces entrantes, y las que debe crear la primera ingesta.
- **Niveles de zoom**: varios documentos que son granularidades del mismo cuerpo (informe → resumen → checklist).
- **Cadenas editoriales**: documento → auditoría → versión corregida.
- **Artefactos de código** o configuración, que irán a una sola receta.
- **Taxonomías del material original que están rotas** (en el primer corpus, 58 de 60 obras en una sola categoría).
- **La epistemología de las fuentes**: si marcan confianza, si distinguen lo oficial de lo comunitario, si citan. Decide cuánta epistemología llevará la wiki.
- **Huecos**: lo que el corpus no cubre. Se declaran en `foco.md` para que nadie invente páginas.

Si el corpus es grande —más de ~10 documentos largos o de ~50.000 palabras—, **delega la lectura a un subagente Explore** y pídele un informe por documento más los clusters, las entidades transversales y los duplicados. Te quedas con la conclusión, no con los volcados. Si además hay que investigar algo fuera del corpus, lanza un segundo subagente en paralelo.

## Fase 3 — Decisiones con el usuario

Resume lo encontrado —clusters, duplicados, colecciones, tamaño estimado— y pregunta con AskUserQuestion solo lo que cambia el trabajo. Las cuatro decisiones de base, con su recomendación:

| Decisión | Recomendación | Por qué |
|---|---|---|
| Dónde vive el raw | **Dentro de `wiki/raw/`** | La bóveda de Obsidian es `wiki/`: verificar un dato es abrir página y raw en paneles contiguos, y un `grep` cubre ambas capas |
| Alcance de la primera entrega | **Andamiaje completo + ingesta piloto** | La wiki es navegable el primer día sin comprometer horas en ingestas que nadie revisó |
| Navegación | **Obsidian con wikilinks** | Grafo, backlinks y autocompletado por alias, que es el antiduplicado aplicado en el momento de escribir |
| Epistemología | **Media**: `confianza` + disputas + anclaje | La alta (enlaces tipados completos, confianza por afirmación) cuesta mantenimiento; la baja (solo citas) no separa evidencia de opinión |

A eso súmale las adaptaciones que salgan del análisis: tipos especializados para colecciones con plantilla, secciones que sobran o faltan para el dominio, categorías que rehacer.

## Fase 4 — Andamiar

```bash
python3 $PLUGIN/scripts/andamiar.py crear <repo> --nombre <nombre> --dominio "<frase>"
```

Crea `CLAUDE.md`, `wiki/` (esquema, configuración, ficheros de sistema, scripts) y el fragmento de `.gitignore`. Las skills de operación **no se copian**: las aporta este plugin. **Nunca sobrescribe**: si el repo ya tiene `CLAUDE.md`, se detiene, y hay que fusionarlo a mano.

Declara el plugin en el repo, con permiso del usuario:

```bash
cd <repo>
claude plugin marketplace add svallejo-dev/llm-wiki --scope project
claude plugin install llm-wiki@llm-wiki --scope project
```

Queda escrito en `.claude/settings.json`, y es lo que hace que quien clone el repo en otra máquina vea que Claude Code le ofrece el plugin: la wiki declara de qué depende. Si el usuario prefiere no tocar la configuración del repo, sáltalo; el plugin instalado a nivel de usuario basta en esta máquina.

Después, adapta al corpus. Esto es criterio, no plantilla:

1. **`wiki/_config.json`** — secciones y topología. Un tipo especializado necesita su sección (con `exenta_huerfanas` y, si tiene categoría natural, `agrupar_por`) y su entrada en `topologia`.
2. **`wiki/_esquema/formatos.md`** — tiene que decir lo mismo que la configuración. Rellena **"Reglas propias de este corpus"** con lo encontrado en la fase 2 y añade el frontmatter de los tipos especializados.
3. **`wiki/indice.md`** — si cambiaste secciones, actualiza la tabla. Lista lo pendiente de ingerir.
4. **`wiki/foco.md`** — decisiones tomadas, huecos declarados, orden de ingesta previsto.
5. **`CLAUDE.md`** — que el dominio encaje. Las 12 reglas duras no se tocan salvo acuerdo con el usuario.

Comprueba: `python3 <repo>/wiki/scripts/generar.py` debe salir sin incidencias.

## Fase 5 — Sellar el raw

```bash
python3 $PLUGIN/scripts/corpus.py sellar <carpeta-del-corpus> <repo>/wiki             # plan
python3 $PLUGIN/scripts/corpus.py sellar <carpeta-del-corpus> <repo>/wiki --aplicar   # ejecución
```

El plan dice qué se sella y con qué nombre, qué duplicado se descarta y frente a cuál, qué paquetes se extraen. **Revísalo antes de aplicar**, y si el usuario está presente, enséñaselo. Al aplicar, cada fuente pasa por el `capturar.py` de la wiki (nombre normalizado, encabezado de procedencia, PDF → `.pdf` + `.md`), los zips se extraen sin basura y se conservan en `raw/_paquetes/`, y el script imprime la **entrada de bitácora** del sellado: añádela a `wiki/bitacora.md`.

Si un PDF está escaneado, `capturar.py` lo rechaza sin sellarlo. Avisa: el OCR lo decide el usuario.

Los originales no se borran. Si la carpeta del corpus está dentro del repo, bórrala tras verificar el sellado para no versionarlo dos veces.

**Commit aislado del sellado** (raw + andamiaje). A partir de ahí `wiki/raw/` es inmutable, y que el sellado sea un commit propio es lo que lo hace auditable.

## Fase 6 — Primera ingesta

**Elige la fuente por lo que crea, no por lo importante que parezca.** La primera ingesta debe ser la que introduce **las entidades con más enlaces entrantes potenciales** —las que aparecían en más documentos en la fase 2—, para que cada ingesta posterior las encuentre en vez de duplicarlas. De lo concreto y nombrable a lo abstracto: empezar por el documento más conceptual crea conceptos sin entidades de las que colgar, y las entidades llegan después duplicadas.

Sigue el procedimiento de la skill `ingerir` de este plugin: lee `$PLUGIN/skills/ingerir/SKILL.md`.

El objetivo son 8-15 páginas enlazadas, lint limpio y anclaje verificado. Es lo que convierte "una carpeta de markdown" en "una wiki" a ojos del usuario: abre Obsidian y ve un grafo con aristas.

## Fase 7 — Verificar y entregar

```bash
cd <repo>
python3 wiki/scripts/generar.py                        # sin incidencias
wiki/scripts/verificar_anclaje.py                      # todo anclado
wiki/scripts/q <un término del corpus>                 # páginas con su TL;DR
python3 $PLUGIN/scripts/andamiar.py comprobar <repo>   # scripts al día
```

Commit, y push si hay remoto y el usuario lo quiere. Entrega en pocas líneas: qué se selló y qué se descartó, qué esquema se acordó, qué creó la primera ingesta, qué queda pendiente y en qué orden, y dónde mirar (`wiki/indice.md` en Obsidian).

## Trampas conocidas

Cada una costó algo en la primera wiki:

- **Duplicados con distinto nombre.** El mismo documento con nombre "humano" y en snake_case. `corpus.py` los detecta por md5: nunca te fíes de los nombres.
- **Nombres con espacios, tildes o guiones largos**, que rompen grep y los scripts. Se normalizan **una vez, antes de sellar**; después, raw es inmutable.
- **Niveles de zoom tratados como fuentes distintas** → cinco resúmenes del mismo cuerpo. Uno solo, desde el más rico.
- **Registros con plantilla metidos en `resumenes/`** → entierran los resúmenes reales. Tipo propio y generación en lote.
- **Citas traducidas entre comillas.** Afirman una literalidad que no pueden cumplir. Comillas solo para texto literal en el idioma original; lo traducido, en cursiva.
- **Saltos de línea de `pdftotext`.** Una frase del PDF puede quedar partida en dos líneas: ancla la cifra y sus palabras contiguas, no la frase entera.
- **Reemplazos masivos con regex que tocan el frontmatter.** En la primera wiki rompió el entrecomillado de un campo. Opera solo sobre el cuerpo, o revisa el frontmatter después.
- **Stubs sin nota de alcance.** Si una página nace incompleta porque su fuente llegará después, dilo dentro con `> **Nota de alcance.**`; si no, la próxima ingesta la reescribirá en vez de ampliarla.
- **El esquema entero en `CLAUDE.md`.** Se carga en cada sesión: ahí va el núcleo, y los procedimientos en skills. La plantilla ya viene partida; no la vuelvas a juntar.

## Mantener los scripts al día

`generar.py`, `q`, `capturar.py` y `verificar_anclaje.py` son **los mismos en todas las wikis** y leen de `wiki/_config.json` lo que depende del dominio. Cuando mejoran en la plantilla:

```bash
python3 $PLUGIN/scripts/andamiar.py comprobar <repo>    # ¿cuáles están desactualizados?
python3 $PLUGIN/scripts/andamiar.py actualizar <repo>   # copia solo los scripts
```

El esquema y la configuración **no se sincronizan**: son de cada wiki y están adaptados a su dominio. Las skills de operación viven en el plugin y se actualizan con él: `claude plugin update llm-wiki`.

## Qué no hacer

- No investigues el patrón otra vez: está en la referencia.
- No escribas páginas antes de tener el esquema adaptado y el raw sellado.
- No añadas base vectorial, `qmd`, base de datos de grafos ni GraphRAG: los umbrales y los motivos están en el `CLAUDE.md` generado.
- No sobrescribas nada del repo del usuario sin preguntar.
- No hagas más que la ingesta piloto sin que el usuario lo pida. La ingesta completa sin supervisión es justo lo que produce wikis que nadie ha revisado.
