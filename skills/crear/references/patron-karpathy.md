# El patrón LLM Wiki de Karpathy — lo que hay que saber antes de construir una

Destilado de la investigación hecha al crear la primera wiki (septiembre de 2026). Léelo en lugar de volver a investigar; investiga de nuevo solo si el usuario lo pide o si ha pasado mucho tiempo y el ecosistema puede haber cambiado.

## Contenido

1. El patrón original
2. Implementaciones de referencia y qué tomar de cada una
3. Lo que dice el uso prolongado
4. Escala y coste
5. Anti-patrones consolidados
6. Herramientas: qué sí y qué no
7. Críticas que conviene conocer
8. Lo que no se pudo verificar

---

## 1. El patrón original

- **2 abr 2026** — tweet "LLM Knowledge Bases": https://x.com/karpathy/status/2039805659525644595
- **4 abr 2026** — gist `llm-wiki.md`: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

Karpathy lo llama **"idea file"**: se comparte la idea y el agente de cada uno la construye a su medida. El gist es **deliberadamente abstracto** — no fija árbol de directorios, frontmatter ni sintaxis de enlaces. Todo eso lo pone quien lo implementa.

**Tres capas**: fuentes en bruto inmutables · la wiki, markdown escrito y mantenido por el LLM · el esquema (`CLAUDE.md` / `AGENTS.md`) que convierte al LLM en un mantenedor disciplinado.

**Tres operaciones**:
- **Ingest** — una fuente nueva se lee, se discute, se resume y se integra. *"A single source might touch 10-15 wiki pages."*
- **Query** — se responde contra la wiki con citas; *"good answers can be filed back into the wiki as new pages"*, así las exploraciones también se acumulan.
- **Lint** — revisión periódica: contradicciones, afirmaciones obsoletas, huérfanas, conceptos sin página, referencias cruzadas que faltan.

**Dos ficheros especiales**: `index.md` (catálogo por contenido, se lee primero al responder) y `log.md` (append-only, con prefijo parseable `## [YYYY-MM-DD] operación | Título` para poder usar `grep`).

**El argumento central**: *"The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping."* Los humanos abandonan las wikis porque el mantenimiento crece más rápido que el valor; el LLM no se aburre y toca 15 ficheros de una pasada. Cita el Memex de Vannevar Bush (1945): lo que Bush no resolvió era quién mantiene.

## 2. Implementaciones de referencia y qué tomar de cada una

**zhurudong/andrej-karpathy-llm-wiki** — https://github.com/zhurudong/andrej-karpathy-llm-wiki
- Tipos `summaries/entities/concepts/comparisons/overviews/synthesis`, wikilinks `[[carpeta/nombre]]`.
- **Topología de enlaces explícita**: solo los resúmenes tocan raw; `synthesis` es nodo hoja. → *Adoptado.*
- "Busca antes de crear", incluyendo `aliases`. Overviews solo con ≥3 artículos relacionados. Archivar una consulta solo si sintetizó ≥2 páginas. → *Adoptado.*

**Astro-Han/karpathy-llm-wiki** (2.322★, la más popular) — https://github.com/Astro-Han/karpathy-llm-wiki
- **Grounding Invariant**: *"Every load-bearing fact in wiki/ — numbers, dates, direct quotes — exists verbatim in the raw/ files linked by that article's Raw field."* Verificado por script. → *Adoptado: `verificar_anclaje.py`.*
- Fidelidad literal: *"if the source says 42K, write 42K, not 42,000"*. → *Adoptado.*
- Triage New / Update / Disputed / **No material** (*"Do not force an article out of a thin source"*). → *Adoptado.*
- Bloques `Status: Outdated` / `Status: Disputed` en lugar de sobrescribir. → *Adoptado.*
- *"Searching may run in parallel; compilation must not."* → *Adoptado.*
- Lint dividido por autoridad: arreglos seguros frente a reportes que nunca se autoarreglan. → *Adoptado.*
- Usa enlaces markdown relativos y estructura plana por tema. → *Descartado en favor de wikilinks: sin ellos se pierde el grafo y los backlinks de Obsidian.*

**ScrapingArt/Karpathy-LLM-Wiki-Stack** — https://github.com/ScrapingArt/Karpathy-LLM-Wiki-Stack
- Frontmatter rico con `confidence`, `cluster`, `contradictions`, `open_questions`. → *`confidence` adoptado; los campos-lista, descartados: se desincronizan pasadas unas decenas de páginas.*
- `hot.md`: caché de sesión de ~500 palabras. → *Adoptado como `foco.md`.*
- Hub con más de 15 miembros → sub-hub (evita "gravity wells"). → *Adoptado como umbral de pozo.*
- Toda página nueva enlaza a ≥2 existentes. → *Adoptado.*

**rohitg00, "LLM Wiki v2"** — https://rohitghumare.com/blog/llm-wiki-v2/
- Diagnóstico: *"a flat store slowly fills with equally-weighted claims of wildly unequal quality."*
- Enlaces tipados (`uses`, `depends on`, `contradicts`, `caused`, `fixed`, `supersedes`). → *Adoptados solo cuatro verbos cerrados y solo bajo `## Relaciones`; el set completo es sobreingeniería.*

## 3. Lo que dice el uso prolongado

- **Retrospectiva a 6 meses** (https://www.openaitoolshub.org/en/blog/karpathy-llm-wiki): 80 raws → 35 páginas, 8-12 páginas tocadas por ingesta, ~15 min/semana de mantenimiento, **~3 semanas y ~20 entradas hasta que la wiki fue útil**. Tesis: **"Schema first, content second, tooling third"** — sin esquema escrito antes de acumular masa, las wikis *"devolve into a graveyard within two months"*. Sus fallos, mes a mes: saltarse el lint tras ingestas masivas; dejar que el LLM "suavizara" material original; sobrescribir una contradicción que necesitó dos meses después (*"contradictions are assets, not errors"*); migrar de herramienta sin releer el esquema y perder los `aliases` → duplicados.
- **Casey Newton, Platformer** (https://www.platformer.news/karpathy-llm-wiki-journalism-productivity/): 1.440 páginas desde su archivo; la página de Meta llegó a 12.000 palabras y 1.300 enlaces internos → *"pages grow unwieldy"*. No se atreve a recomendarlo sin reservas.
- **R&D World, un mes** (https://www.rdworldonline.com/is-karpathys-viral-llm-wiki-helpful-mostly-yes-one-month-in/): ~760 páginas, lint que exige citas en línea. Veredicto: *"the time I spend maintaining and the time it saves me are roughly a wash"*. Y si ya existe una fuente curada buena sobre el tema, la wiki no aporta.

## 4. Escala y coste

- `index.md` plano deja de ser fiable pasados ~50-100K tokens; el desbordamiento de contexto es el problema número uno **pasadas ~150-200 páginas**. De fondo: para decidir qué páginas actualizar en una ingesta hay que poder navegar ya un índice grande.
- Benchmark de coste (https://dev.to/jgravelle/a-radical-diet-for-karpathys-token-eating-llm-wiki-59ng): cargar la wiki entera frente a acceso por secciones = **19,9× más tokens**. *"The LLM Wiki doesn't eliminate token cost. It moves it"* — de la recuperación por consulta a la compilación por sesión. (El post promociona su propia herramienta; la dirección es correcta aunque la cifra esté inflada.)

**Consecuencia de diseño**: índice jerárquico (router + índice por sección) desde el día uno si la estimación pasa de ~100 páginas, y búsqueda que devuelva el resumen de una línea en vez de rutas. La plantilla ya lo trae.

## 5. Anti-patrones consolidados

1. Saltarse el lint porque "nada parece roto".
2. Sobrescribir contradicciones en vez de marcarlas.
3. Dejar que el LLM toque el material literal.
4. **No escribir el esquema antes del contenido** — el más citado.
5. Forzar una página desde una fuente pobre.
6. Confiar solo en el índice para saber qué actualizar.
7. Hechos sin anclaje verificable: los errores del modelo se cristalizan y se propagan a cada consulta futura. Es la crítica número uno en Hacker News.
8. Compilar en paralelo: índice, log y cascadas son estado compartido.
9. Migrar de herramienta sin releer el esquema.
10. Hubs con demasiados enlaces entrantes.
11. Sobreingeniería temprana: bases vectoriales, multiagente, Postgres.
12. Compresión con pérdida sin conservar el raw.
13. Confundir curaduría con aprendizaje (ver críticas).

## 6. Herramientas: qué sí y qué no

- **qmd** (https://github.com/tobi/qmd, ~30K★): búsqueda local BM25 + vectorial + reranking, con servidor MCP. El único tool que nombra el gist. **Diferir hasta ~500 páginas**: grep responde en menos de 50 ms muy por encima de eso.
- **Obsidian** + wikilinks + Dataview: la interfaz que usa Karpathy (el LLM a un lado, Obsidian al otro).
- **Base de datos de grafos** (SQLite con CTEs, Kuzu, Neo4j): no por debajo de ~1.000 páginas o uso multiusuario. La wiki ya es un grafo; basta materializar la adyacencia en texto plano.
- **GraphRAG** (Microsoft): **nunca como complemento**. Es una alternativa al patrón: extrae su propio grafo y genera resúmenes de comunidad sin anclaje literal, que rompen el invariante y duplican lo que la wiki ya es, con coste por reindexación.

## 7. Críticas que conviene conocer

- **Zettelkasten** (https://yu-wenhao.com/en/blog/karpathy-zettelkasten-comparison/): las páginas por tema recrean el "problema del contenedor" (hay que decidir fronteras y fusiones), y reescribir salida de LLM una y otra vez puede perder matices.
- **"No aprendes tú"** (https://bitsofchris.com/p/an-llm-wiki-wont-compound-your-knowledge): si el LLM lee, resume y conecta, *"at what point did YOU learn something?"*. La contabilidad que se externaliza es justo donde se forma la comprensión. Mitigación: la sección `sintesis/` es donde entra el criterio del usuario, y conviene animarle a usarla.
- Hacker News (hilo de WUPHF, https://news.ycombinator.com/item?id=47899844): *"Garbage facts in, garbage briefs out"*; los flujos borrador→promoción necesitan revisión humana para no envenenar el contexto.

## 8. Lo que no se pudo verificar

- Reddit (r/ObsidianMD, r/LocalLLaMA, r/ClaudeAI): inaccesible en la investigación original. Cero evidencia de Reddit aquí.
- Visualizaciones del tweet (las fuentes dan 16M, 17M o 21M) y estrellas del gist (las fuentes se contradicen): no citar.
- La afirmación de que Cognition, Factory o LangChain construyeron productos derivados apareció en un sitio de baja calidad que luego dio 404: probablemente texto generado, no citar.
