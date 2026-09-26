# {{NOMBRE}} — wiki LLM

Wiki sobre {{DOMINIO}}, con el patrón `llm-wiki` de Karpathy. Se **compone una vez y se mantiene al día**, no se re-deriva en cada pregunta.

El reparto es estricto: **el usuario cura fuentes, dirige y pregunta; tú escribes y mantienes todo lo demás.** El usuario no escribe páginas. Tú no decides qué entra en `raw/`.

## Arranque de sesión

```bash
cat wiki/foco.md
grep -A1 "^## \[" wiki/bitacora.md | tail -8
```

`foco.md` dice en qué estamos y qué está decidido; la bitácora, qué se hizo. No trabajes sin leer ambos: es la diferencia entre continuar la wiki y empezar otra encima.

## Las tres capas

| Capa | Dónde | Quién escribe | Regla |
|---|---|---|---|
| **Fuentes** | `wiki/raw/` | El usuario | Inmutable. Es la verdad. |
| **Wiki** | `wiki/<seccion>/` | Tú, íntegramente | Derivada de raw. Regenerable. |
| **Esquema** | este fichero + `wiki/_esquema/` | Usuario y tú, de acuerdo | Gobierna las otras dos. |

Si la wiki se borrara entera, debería poder reconstruirse desde `raw/`. Por eso ningún dato existe solo en la wiki, y por eso `raw/` no se toca.

## Las operaciones

Este fichero es el núcleo y se carga siempre. Los procedimientos los aporta el plugin **`llm-wiki`** (declarado en `.claude/settings.json`), y se cargan **solo cuando la tarea los pide**:

| Vas a… | Skill |
|---|---|
| Capturar una fuente e integrarla (URL, PDF, fichero en `raw/`) | `/llm-wiki:ingerir` |
| Revisar la salud de la wiki, o verificar las cifras de una página | `/llm-wiki:revisar` |
| Archivar una conclusión como comparativa, panorama o síntesis | `/llm-wiki:sintetizar` |
| **Responder una pregunta** | aquí mismo, más abajo |

**No escribas ni edites una página sin haber leído `wiki/_esquema/formatos.md` en esta sesión.** Tipos, frontmatter, topología y nomenclatura están ahí, es la única especificación y no se duplica dentro de las skills.

## Responder una pregunta

Es el camino más frecuente, así que va aquí y no en una skill. El objetivo es doble: responder bien y **leer lo mínimo**. Cada página abierta de más son ~850 tokens que no hacían falta.

1. **Siembra con la búsqueda, no con el índice.** `wiki/scripts/q <termino>` devuelve `página · TL;DR · (confianza, grado entrante)`. Con eso decides qué abrir **sin abrir nada**. Para una pregunta concreta esto sustituye a leer `indice.md` y el índice de sección; úsalos solo si la pregunta es amplia o no sabes por dónde empezar.
2. **Expande por el grafo.** `q -n <pagina>` da entrantes, salientes y relaciones tipadas; `q -h` llega a 2 saltos. Encuentra lo estructuralmente cercano que **no contiene el término buscado** — la página que no sabías que tenías que buscar. Mira la columna de tipadas: si algo `contradice` o `reemplaza a` otra cosa, la respuesta probablemente deba mencionarlo.
3. **Lee 1-3 páginas.** No más, salvo que la pregunta sea genuinamente transversal.
4. **Responde citando** con wikilinks. Si el dato es una cifra, di de qué raw viene. Si una página tiene `confianza: medio` o `bajo`, o lleva un bloque `Estado: Disputado`, dilo: la fuerza de la evidencia es parte del contenido.
5. **Si no está, dilo.** Revisa los huecos conocidos de `foco.md` antes de improvisar y no inventes páginas sobre lo que el corpus no cubre. Propón buscar una fuente.
6. **¿Archivar?** Si sintetizaste ≥2 páginas y saliste con una conclusión que no estaba escrita, propón archivarla con `/llm-wiki:sintetizar` y espera confirmación. Si fue un dato puntual, no archives nada.

Sé crítico. Ofrece profundidad de opinión; no confirmes por defecto lo que el usuario parece querer oír.

## Las 12 reglas duras

Innegociables. Cada una corresponde a un modo documentado de arruinar una wiki.

1. **`wiki/raw/` es inmutable.** No edites, renombres, reformatees ni borres nada ahí. Si una fuente cambia, se añade un raw nuevo con fecha nueva. Si crees que hay que tocar raw, para y pregunta.
2. **Busca antes de crear.** `grep -i "<termino>" wiki/_alias.tsv` y `wiki/scripts/q <termino>`, incluyendo sinónimos y la forma en inglés. Nunca confíes solo en `indice.md`: miente a partir de ~150 páginas.
3. **Invariante de anclaje.** Todo dato de carga —cifras, porcentajes, fechas, nombres propios, citas— existe **literalmente** en alguno de los raw del campo `raw:` de esa página o de su procedencia. Si no puedes localizar el literal, no lo escribas.
4. **Fidelidad literal.** `USD 4.5 mil millones`, no `4.500 millones`. La verificación es por coincidencia de cadena, no por aritmética: respeta el separador decimal y el formato del original.
5. **Las contradicciones son activos, no errores.** Nunca sobrescribas una afirmación con otra que la contradice: marca `> **Estado: Disputado** (fecha)`, crea o amplía la página de tipo `disputa`, y deja ambas trazables. Igual con lo superado: `> **Estado: Obsoleto** (fecha)`.
6. **Nunca borres una página.** Marca `estado: obsoleto` y `reemplazado_por:`. Borrar rompe enlaces entrantes que nadie va a reparar.
7. **Toda página nueva enlaza a ≥2 páginas existentes.** Si no encuentras dos, o la página no pertenece aquí, o te falta contexto. Excepción: `papers/` en lote.
8. **No fuerces un artículo de una fuente pobre.** Triage obligatorio: Nueva / Actualiza / Disputa / **Sin material**. Si es "sin material", registra en bitácora y para.
9. **Una compilación a la vez.** Buscar y leer se paraleliza; escribir no. Índices, `_grafo.tsv`, `bitacora.md` y las cascadas son estado compartido.
10. **Toda operación cierra el ciclo.** `python3 wiki/scripts/generar.py` → `_cifras.md` y `indice.md` si aplica → entrada en `bitacora.md` → refrescar `foco.md`.
11. **El lint propone, el usuario dispone.** Los arreglos seguros se aplican y se reportan. Todo lo que toque un hecho, una cifra, una contradicción o una confianza se **reporta, nunca se auto-arregla**. Enlace roto con 1 candidato → arreglar; con 0 o más de 1 → reportar.
12. **Español, kebab-case, sin tildes en nombres de fichero.** Las tildes viven en `titulo:` y `alias:`. Prefijo `_` = fichero de sistema o generado: no lo edites a mano ni lo enlaces como contenido.

## Mapa de ficheros

| Fichero | Qué es |
|---|---|
| `wiki/indice.md` | Router de secciones y puertas de entrada. **No es un catálogo**: para buscar algo puntual usa `q`. |
| `wiki/<seccion>/_indice.md` | Catálogo de la sección. **Generado.** |
| `wiki/_alias.tsv` | alias → página. **Generado.** El chequeo antiduplicado más barato. |
| `wiki/_grafo.tsv` | Adyacencia: grado, entrantes, salientes, relaciones tipadas. **Generado.** |
| `wiki/_cifras.md` | Inventario de cifras citables con su literal exacto. A mano, en cada ingesta. |
| `wiki/bitacora.md` | Append-only. Cabecera grepeable + una línea de estado + detalle. |
| `wiki/foco.md` | Caché de sesión, ~500 palabras. Se sobrescribe. |
| `wiki/_esquema/formatos.md` | **La** especificación: tipos, frontmatter, topología, nomenclatura, citas, procedencia del raw, fuentes no textuales. |
| `wiki/_config.json` | Secciones, topología y umbrales que aplican los scripts. Coherente con `formatos.md`. |
| `.claude/settings.json` | Declara el plugin `llm-wiki`, que aporta los procedimientos. Quien clone el repo verá que Claude Code se lo ofrece. |

## Comandos

```bash
wiki/scripts/q <termino>              # buscar: devuelve página · TL;DR · confianza · grado
wiki/scripts/q -n <pagina>            # vecindario en el grafo (la cascada de una ingesta)
wiki/scripts/q -h <pagina>            # además, a 2 saltos
wiki/scripts/q -c                     # cuántas páginas por sección
grep -i "<termino>" wiki/_alias.tsv   # ¿ya existe algo con ese nombre o alias?
python3 wiki/scripts/generar.py       # regenerar índices, alias y grafo + lint mecánico
wiki/scripts/verificar_anclaje.py     # ¿toda cifra existe literal en su raw?
wiki/scripts/capturar.py <origen>     # sellar una fuente en raw/ con procedencia
grep -rn "<literal>" wiki/raw/        # comprobar un literal a mano
grep -A1 "^## \[" wiki/bitacora.md | tail -8
```

## Qué NO hacer todavía

**Si un `grep` o `q` resuelve la pregunta, no escribas un script.**

| Cosa | Disparador |
|---|---|
| Búsqueda híbrida (`qmd`), embeddings, base vectorial | ~500 páginas. El gist de Karpathy nombra `qmd`, pero grep y `q` bastan muy por encima de lo que suele alcanzar una wiki personal. |
| Base de datos de grafos (SQLite, Kuzu, Neo4j) | ~1.000 páginas o multiusuario. A esta escala `_grafo.tsv` es más barato y más legible. |
| GraphRAG con resúmenes de comunidad | Nunca: es una alternativa a este patrón, no un complemento, y rompe el invariante de anclaje. |
| Servidor MCP, CI en GitHub Actions, ingesta multiagente | No previsto |

Tampoco: subcarpetas dentro de las ocho secciones, ni frontmatter adicional al de `formatos.md`. `wiki/raw/assets/` solo cuando entre un raw con imágenes necesarias para entenderlo — ver "Fuentes que no son texto plano" en `formatos.md`.
