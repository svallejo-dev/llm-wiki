# Formatos

Léelo **antes de escribir o modificar cualquier página**. Define tipos, frontmatter, enlaces, topología, nomenclatura, citas y procedencia del raw.

Las secciones, los umbrales y la topología que aplican los scripts están declarados en `wiki/_config.json`. **Este documento y ese fichero tienen que decir lo mismo**: si cambias uno, cambia el otro.

---

## Tipos de página

Ocho tipos base en siete carpetas. El tipo determina qué contiene la página, a qué puede enlazar y qué frontmatter lleva.

| Tipo | Carpeta | Contrato | Cuándo se crea |
|---|---|---|---|
| `resumen` | `resumenes/` | Una por raw largo ingerido. Qué es, qué afirma, cifras clave, a dónde ir. | Al ingerir un raw con disposición "Nueva". |
| `entidad` | `entidades/` | Un actor nombrable: persona, organización, producto, herramienta, lugar, obra. | Cuando aparece en ≥1 raw y tiene sustancia propia. |
| `concepto` | `conceptos/` | Una idea transversal. Definición, variantes, quién lo dice, tensiones. | Cuando aparece en ≥2 raw o vertebra uno entero. |
| `comparativa` | `comparativas/` | A vs B con criterio de decisión. Tabla + veredicto. | Cuando existen las páginas de ambas partes. |
| `disputa` | `comparativas/` | Afirmación en conflicto: quién la sostiene, quién la refuta, con qué fuerza probatoria, veredicto actual. | Cuando dos fuentes se contradicen sobre un hecho. |
| `receta` | `recetas/` | Procedimiento ejecutable: checklist, playbook, plantilla, política. Accionable, con casillas. | Cuando el raw es accionable, no expositivo. |
| `panorama` | `panoramas/` | Mapa de un área. Solo enlaces y orientación, **cero hechos nuevos**. | Solo con ≥3 páginas relacionadas (`cubre` ≥ 3). |
| `sintesis` | `sintesis/` | Opinión propia del usuario derivada de la wiki. Nodo hoja. | Al archivar una consulta que produjo conclusión nueva. |

### Tipos especializados

Si el corpus trae **registros con plantilla fija** —fichas de papers, casos clínicos, sentencias, capítulos de un libro—, no los metas en `resumenes/`: sepultarían los resúmenes reales y el tipo perdería su contrato. Dales tipo y carpeta propios:

1. Una entrada en `secciones` de `wiki/_config.json` (normalmente `exenta_huerfanas: true`, y `agrupar_por` si tienen una categoría natural).
2. El tipo en `topologia`, con `raw` entre sus destinos si citan la fuente directamente.
3. Sus campos propios en el frontmatter, aquí abajo.
4. Si solo algunos merecen enlazarse a mano (los que se citan en otras fuentes), un campo booleano y `exento_salientes_salvo` apuntando a él.

Se generan en lote, no uno a uno: vienen con estructura y metadatos, así que es conversión mecánica, no ingesta.

### Reglas de taxonomía

Aprendidas construyendo otras wikis. Aplican a cualquier corpus:

**Niveles de zoom.** Cuando varios raw son granularidades del mismo cuerpo (informe, resumen, checklist), se escribe **un solo `resumen`** desde el más rico, con todos en su campo `raw:`. Los niveles *accionables* van a `recetas/`. El que es solo un resumen del resumen es **"Sin material"**.

**Código, no prosa.** Los artefactos de código o configuración (JSON, YAML, scripts, CI) **no generan una página cada uno**: se documentan en una sola receta con tabla fichero a fichero.

**Cadenas editoriales.** Si hay un documento, su auditoría y su versión corregida: el concepto se escribe desde la **versión corregida**, la auditoría se convierte en `disputa`, y el original se conserva en raw, se enlaza desde la disputa y **no se resume**.

**Un `panorama` no aporta hechos.** Si escribes un dato nuevo en un panorama, ese dato pertenece a un concepto o una entidad.

**Un hub con demasiados enlaces entrantes se divide en sub-hubs.** El umbral está en `_config.json` y el generador lo reporta.

### Reglas propias de este corpus

_Se completan al crear la wiki, desde el análisis del corpus: qué clusters son niveles de zoom del mismo cuerpo, qué cadenas editoriales hay, qué taxonomía del material original está rota y hay que rehacer._

---

## Frontmatter

Principio: **rico donde se consulta, pobre donde se mantiene.** No añadas campos que sean listas de otras páginas (`contradicciones`, `preguntas_abiertas`, `cluster`): se desincronizan. Las relaciones van como enlaces tipados en el cuerpo, donde se leen y por tanto se mantienen. Las preguntas abiertas van solo en `foco.md`.

### Comunes obligatorios

```yaml
---
tipo: concepto              # resumen|entidad|concepto|comparativa|disputa|receta|panorama|sintesis
titulo: Título legible, con tildes
tldr: Resumen de una línea que permita decidir si abrir la página
tags: [etiqueta, otra]
confianza: alto             # alto|medio|bajo
creado: {{FECHA}}
actualizado: {{FECHA}}
---
```

**`tldr` es el campo de mayor apalancamiento del esquema.** Rellena la tabla del `_indice.md` y es lo que devuelve `q`, así que es lo que permite decidir qué abrir sin abrir nada. **Máximo 70 caracteres.** Obligatorio sin excepción.

`confianza`: `alto` = fuente oficial o académica, o ≥2 fuentes independientes del corpus. `medio` = una sola fuente, fuente comunitaria consistente, o **un marco conceptual sin medición detrás**. `bajo` = anécdota, extrapolación, o algo que el propio raw marca como hipótesis.

### Por tipo

```yaml
resumen:              raw: [...]          alias: [...]
entidad:              alias: [...]        clase: persona   # persona|organizacion|producto|herramienta|...
concepto:             alias: [...]
comparativa/disputa:  partes: ["[[...]]", "[[...]]"]
                      veredicto: "..."    # ≤120 caracteres
receta:               raw: [...]          aplica: ["[[...]]"]
panorama:             cubre: 7            # páginas que mapea, ≥3
sintesis:             deriva_de: ["[[...]]", "[[...]]"]   # ≥2
```

### Opcionales en cualquier tipo

```yaml
estado: vigente          # vigente|disputado|obsoleto   (ausente = vigente)
reemplazado_por: "[[...]]"
fuentes: [https://..., https://...]      # URLs externas primarias
```

`alias` incluye siempre las formas en otros idiomas y las abreviaturas: es lo que alimenta `_alias.tsv` y por tanto lo que evita duplicados.

---

## Enlaces

**Wikilinks con prefijo de carpeta, siempre:** `[[conceptos/nombre]]`. Nunca `[[nombre]]` ni `[texto](../conceptos/nombre.md)`.

El prefijo hace la topología grepeable y parseable por el generador, y el autocompletado de Obsidian resuelve por `alias`: si al teclear `[[conceptos/nom` aparece una página, ya existe y no debes crear otra.

### Enlaces tipados

Verbos **cerrados** (lista en `_config.json`), y solo bajo una sección `## Relaciones` al final de la página. Sintaxis de campo inline de Dataview:

```markdown
## Relaciones

- contradice:: [[resumenes/fuente-antigua]]
- reemplaza a:: [[resumenes/fuente-antigua]]
- depende de:: [[entidades/otra]]
- aplica:: [[conceptos/otro]]
```

Los enlaces del cuerpo son wikilinks normales sin tipo. El generador extrae las tipadas a la columna `TIPADAS` de `_grafo.tsv`, y `q -n <pagina>` las muestra. Un verbo fuera de la lista se reporta como incidencia.

---

## Topología permitida

```
                       wiki/raw/  [INMUTABLE]
                            ▲
                 ┌──────────┴──────────┐
            resumenes/              recetas/        ← únicos tipos que tocan raw
                 └──────────┬──────────┘
                            ▼
              entidades/  ◄────►  conceptos/        ← núcleo bidireccional
                     ▲             ▲
                     └──comparativas/ (comparativa | disputa)
                              ▲
                         panoramas/  (cubre ≥ 3)
                              ▲
                          sintesis/  ← NODO HOJA: solo salientes
```

| Origen | raw | resumenes | entidades | conceptos | comparativas | recetas | panoramas | sintesis |
|---|---|---|---|---|---|---|---|---|
| `resumen` | **sí** | sí | sí | sí | sí | sí | no | no |
| `receta` | **sí** | no | sí | sí | no | sí | no | no |
| `entidad` | no | sí | sí | sí | sí | sí | no | no |
| `concepto` | no | sí | sí | sí | sí | sí | no | no |
| `comparativa` | no | sí | sí | sí | sí | sí | no | no |
| `disputa` | no | sí | sí | sí | sí | no | no | no |
| `panorama` | no | sí | sí | sí | sí | sí | sí | no |
| `sintesis` | no | sí | sí | sí | sí | sí | sí | no |

Invariantes que verifica `generar.py`:

- Ningún enlace a `raw/` desde tipos que no lo tienen permitido. *El dato llega por la cadena de procedencia, no por atajo.*
- Ningún enlace entrante a `sintesis/`. *Lo que opinas no es fuente de lo que sabes.*
- Ningún `panorama` con `cubre < 3`.
- Ninguna página con menos de 2 enlaces salientes internos.
- Ninguna entidad o concepto por encima del umbral de entrantes sin subdividir.
- Huérfanas: se exigen entrantes salvo en `resumenes` y `sintesis`, que se alcanzan desde el índice por diseño.

---

## Nomenclatura

- **Ficheros**: minúscula, kebab-case, sin tildes ni eñes. `conceptos/nombre-del-concepto.md`. Las tildes viven en `titulo:` y `alias:`.
- **Raw**: `YYYY-MM-DD-<slug>.md`, con la fecha de **captura**, no de autoría.
- **Tipos especializados**: `<carpeta>/<clave-natural>-<slug>.md` (p. ej. `papers/2023-react.md`).
- **Comparativas**: `comparativas/<a>-vs-<b>.md`. **Disputas**: `comparativas/disputa-<tema>.md`.
- **Síntesis**: se nombran por el **tema de la conclusión**, no por la pregunta que la originó.
- **Prefijo `_`**: fichero de sistema o generado, no una página. No lo enlaces como contenido.

---

## Citas

**Las comillas afirman literalidad.** Todo pasaje entre comillas tiene que existir tal cual en el raw, y `verificar_anclaje.py` lo comprueba.

- **Cita verbatim** → entre comillas y **en el idioma del original**.
- **Traducción o paráfrasis** → en *cursiva sin comillas*. Una traducción no puede cumplir el invariante de anclaje, así que no debe aparentarlo.

Cuando el raw está en otro idioma, cita en el original las frases que merezcan ser verbatim y traduce el resto como paráfrasis. Así el lector distingue de un vistazo qué dice la fuente y qué dice la wiki.

---

## Procedencia del raw

Todo raw lleva encabezado de procedencia. Es lo que hace mecánicas la atribución y la deduplicación, y `wiki/scripts/capturar.py` lo pone solo:

```markdown
# Título del documento

> Fuente: https://... (o "transcripción de la charla X", "notas de reunión", "no proporcionada")
> Capturado: {{FECHA}}
> Publicado: 2026-03-14   (o Desconocido)
> Autor: ...              (si se sabe)
```

Cuando la captura **no es fiel al original**, dilo en el encabezado: condiciona la `confianza` de todo lo que derive de ahí.

```markdown
> Capturado: {{FECHA}} · vía fetch del agente (texto procesado, no HTML original)
```

Deduplicar por origen es entonces un grep:

```bash
grep -r "^> Fuente:" wiki/raw/ | grep <dominio-o-doi>
```

Si no se conoce el origen, `no proporcionada`: no se inventa. Autores, título y fecha sostienen la atribución.

---

## Fuentes que no son texto plano

### PDF

Un PDF no es greppable, así que no puede ser la única fuente: el invariante de anclaje dejaría de verificarse para todo lo que derive de él. Un PDF entra como **dos ficheros con el mismo nombre base**:

```
wiki/raw/YYYY-MM-DD-<slug>.pdf    ← original inmutable, el artefacto recibido
wiki/raw/YYYY-MM-DD-<slug>.md     ← texto extraído, greppable, con encabezado de procedencia
```

El campo `raw:` de las páginas apunta **siempre al `.md`**; el `.md` apunta al `.pdf` en su encabezado. Así `ls wiki/raw/*.md` sigue significando "todas las fuentes verificables".

La extracción la hace `capturar.py` con `pdftotext -layout`. El `-layout` no es opcional: sin él las tablas se aplanan y las cifras se pegan entre sí, que es justo lo que rompe la verificación literal.

**Trampa del texto extraído**: `pdftotext` conserva los saltos de línea del maquetado, así que una frase puede quedar partida en dos líneas. Al anclar, **ancla la cifra y sus dos o tres palabras contiguas, no la frase entera**. `verificar_anclaje.py` ya normaliza los saltos; un `grep -F` a mano, no.

Si la extracción sale vacía, el PDF está escaneado y no tiene capa de texto. `capturar.py` se detiene sin sellar nada. Hace falta OCR (`brew install tesseract`), y eso **lo decide el usuario**.

**Si la obra ya tiene ficha** en una sección especializada, el PDF no crea página nueva: el triage es **Actualiza** sobre esa ficha.

### Imágenes

Si un raw trae imágenes necesarias para entenderlo, van a `wiki/raw/assets/<slug>/` y se referencian desde el `.md`. Hasta entonces `assets/` no existe: no lo crees "por si acaso".
