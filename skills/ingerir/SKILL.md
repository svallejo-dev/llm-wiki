---
name: ingerir
description: Integra una fuente nueva en una wiki LLM (repo con wiki/_config.json) — captura, triage, páginas nuevas o ampliadas, cascada de índices y bitácora. Úsala cuando el usuario deje un fichero en wiki/raw/, pase una URL o un PDF, o diga "ingiere", "añade esta fuente" o "mete esto en la wiki", también en lote. NO para responder preguntas, ni para el lint (/llm-wiki:revisar), ni para archivar una conclusión (/llm-wiki:sintetizar).
---

# Ingerir una fuente

Integrar una fuente nueva en la wiki sin romper lo que ya hay. El riesgo no es escribir poco: es escribir una página que duplique otra, que afirme una cifra que nadie puede verificar, o que sobrescriba una contradicción en silencio.

## Antes de nada: ¿estás en una wiki?

Trabaja desde la raíz del repo. Una wiki de este plugin se reconoce porque tiene `wiki/_config.json`:

```bash
test -f wiki/_config.json && echo "wiki" || echo "no es una wiki"
```

Si no existe, **para**: este repo no es una wiki LLM, o lo es de una versión anterior sin configuración. Dilo, y si el usuario quiere montar una, ofrece `/llm-wiki:crear`. No improvises la estructura.

**Lee `wiki/_esquema/formatos.md` antes de escribir la primera página.** Ahí están tipos, frontmatter, topología y nomenclatura, y equivocarse cuesta más que leerlo.

**Una ingesta a la vez.** Buscar y leer se paraleliza; escribir no. Los índices, `_grafo.tsv`, `bitacora.md` y las cascadas son estado compartido.

## Fase 0 — Capturar

Si la fuente aún no está sellada en `wiki/raw/` con su encabezado de procedencia, pásala por el script. Hace los cinco pasos que a mano se olvidan y se niega a pisar un raw existente:

```bash
wiki/scripts/capturar.py <fichero-o-URL> --fuente "<URL u origen>" [--publicado FECHA] [--autor X]
```

- **PDF** → deja el `.pdf` original inmutable **y** un `.md` hermano extraído con `pdftotext -layout`. El campo `raw:` de las páginas apunta **siempre al `.md`**: el binario no es greppable y el invariante de anclaje dejaría de verificarse.
- **PDF escaneado** → el script se detiene sin sellar nada. Hace falta OCR, y eso lo decide el usuario: **avisa y para**, no instales nada.
- **URL** → extrae el texto del HTML. Es un derivado, y el encabezado lo dice. Si el usuario tiene el clip de Obsidian Web Clipper, ese es mejor: viene del DOM real.
- **Sin URL de origen** → no la inventes. `--fuente "no proporcionada"` y sigue; autores, título y fecha sostienen la atribución.

El script avisa de posibles duplicados. Si avisa, **para y pregunta** antes de ingerir.

## 1. Arranque

```bash
cat wiki/foco.md
grep -A2 "^## \[" wiki/bitacora.md | grep -E "^(## \[|> )" | tail -8
```

Comprueba que este raw no se ingirió ya, y mira si `foco.md` tiene una decisión que afecte a esta fuente (orden de ingesta, páginas que ampliar en vez de crear, huecos declarados).

## 2. Lee el raw entero

Si supera las ~700 líneas, léelo por secciones — pero no resumas nada hasta haberlo recorrido completo. Un resumen escrito desde la primera mitad inventa la segunda.

## 3. Inventario

Extrae tres cosas:

- **Entidades nombrables**: framework, persona, organización, producto, protocolo, benchmark.
- **Conceptos transversales**.
- **Cifras de alta señal**: números grandes o con sufijo, porcentajes, multiplicadores, tamaños muestrales, fechas. Las necesitas en el paso 6 y para `_cifras.md`.

## 4. Busca antes de crear

Para cada elemento, en este orden — del chequeo más barato al más caro:

```bash
grep -i "<termino>" wiki/_alias.tsv     # alias -> página, una línea de salida
wiki/scripts/q <termino>                 # qué páginas lo tratan, con su TL;DR
```

Busca también sinónimos y la forma en inglés. **Nunca confíes solo en `indice.md`**: el índice miente a partir de ~150 páginas, y por eso existe `_alias.tsv`.

## 5. Triage

Clasifica el raw completo y cada elemento del inventario:

| Disposición | Qué significa | Qué haces |
|---|---|---|
| **Nueva** | No existe en la wiki | Crear páginas |
| **Actualiza** | Existe y el raw añade hechos, cifras o fuentes | Ampliar la existente, subir `actualizado`, añadir el raw a su `raw:` si es un resumen |
| **Disputa** | El raw contradice algo ya escrito | **No sobrescribas.** `estado: disputado` y `> **Estado: Disputado** (fecha)` en ambas, y crear o ampliar una página de tipo `disputa` |
| **Sin material** | No aporta ningún hecho, cifra ni fuente ausente, o es otro nivel de zoom de algo ya ingerido | Entrada de bitácora y **para aquí** |

"Sin material" es un resultado legítimo y a veces el correcto. Una fuente floja no produce una página mala: produce una wiki inflada.

**Si una entidad aparece solo de pasada**, no le hagas página: menciónala dentro del concepto que la contiene y anota en `foco.md` que espera una fuente con sustancia. Un stub solo se justifica si hace falta para enlazar algo, y entonces lleva `> **Nota de alcance.**` diciendo qué falta.

**Si la fuente es la que esperaba un stub**, el triage de esa página es **Actualiza**, no Nueva: se amplía en su sitio, se retira la nota de alcance, se conserva `creado` y lo que aportaron otras fuentes, y la `confianza` puede subir si la fuente nueva es más sólida.

**Tensión no es contradicción.** Si la fuente confirma los hechos de otra pero con otro énfasis (más prudente, menos entusiasta), no crees una `disputa`: anótalo en la página como forma de pesar ambas fuentes. La disputa es para hechos incompatibles.

## 6. Localiza antes de escribir

Para cada cifra o cita que vayas a poner, ten delante la línea exacta del raw:

```bash
grep -n "<cifra tal como aparece>" wiki/raw/<fichero>.md
```

Si no puedes localizar el literal, no lo escribas. Copia el formato exacto: si dice `USD 4.5 mil millones`, no escribas `4.500 millones`. Respeta el separador decimal del original, porque la verificación es por coincidencia de cadena.

**Si el raw está en otro idioma**, las comillas son una afirmación de literalidad que no puedes cumplir al traducir. Cita entre comillas **en el idioma original** cuando la frase lo merezca, y pon las traducciones en *cursiva sin comillas*, como paráfrasis. Así el lector sabe qué es verbatim.

## 7. Escribe las páginas

Respetando tipos, frontmatter y topología de `formatos.md`. Cada página nueva enlaza a **≥2 páginas existentes**.

Una fuente bien ingerida toca típicamente **8-15 páginas**. Menos de 4 suele ser quedarse corto; más de 20, fragmentar de más.

Cuando una página queda incompleta a propósito porque el grueso llegará de otro raw, dilo dentro con un bloque `> **Nota de alcance.**`. Es la diferencia entre una página incompleta y una página engañosa, y evita que la próxima ingesta la reescriba en vez de ampliarla.

**Nombres**: un resumen no se llama igual que la entidad de la que trata (`resumenes/guia-<tema>`, no `resumenes/<tema>` si existe `entidades/<tema>`).

## 8. Cascada

```bash
python3 wiki/scripts/generar.py
```

Regenera los 8 `_indice.md`, `_alias.tsv` y `_grafo.tsv`, y reporta el lint mecánico. **No edites esos ficheros a mano**: se sobrescriben.

Para saber qué páginas existentes hay que revisar por haber tocado una entidad o concepto:

```bash
wiki/scripts/q -n conceptos/<pagina>
```

Los **entrantes** son las páginas cuyo texto puede haberse quedado desactualizado. Esa es la cascada real, y es el paso donde este patrón se juega su premisa: que nadie se olvide de actualizar una referencia cruzada. Busca también las páginas existentes que **mencionan** algo que ahora tiene página propia, y enlázalas.

**Revisa las notas de alcance** de cada página que tocaste: si decían *pendiente de tal fuente* y esa fuente es la que acabas de ingerir, o si ahora cubre más de lo que dicen, actualízalas. Una nota de alcance caducada miente.

**Si el lint reporta algo estructural** (un pozo, un nombre repetido, una página larga), no bloquees la ingesta: termínala y repórtalo al final. Es una decisión del usuario, no un paso de la ingesta.

Luego, a mano, solo lo que el generador no cubre:

- `wiki/indice.md` — solo si cambió el mapa de secciones, una puerta de entrada o el recuento.
- `wiki/_cifras.md` — añade las cifras nuevas con su literal exacto.

Y verifica el anclaje de lo que acabas de escribir:

```bash
wiki/scripts/verificar_anclaje.py            # cifras y citas de las páginas con raw:
wiki/scripts/verificar_anclaje.py --citas    # las citas entre comillas de toda la wiki
```

## 9. Bitácora

Formato de dos niveles: cabecera grepeable, línea de estado, detalle.

```markdown
## [YYYY-MM-DD] ingesta | <título de la fuente>
> nueva · raw: YYYY-MM-DD-<slug> · +9 páginas · 2 actualizadas · lint ok

- **Creadas**: `entidades/<x>`, `conceptos/<y>`
- **Actualizadas**: `conceptos/<z>` (+lo que aportó)
- **Anclaje**: N literales verificados
- **Notas**: decisiones de triage, qué quedó fuera y por qué, stubs creados, sesgos de la fuente.
```

Para "sin material" basta cabecera y motivo:

```markdown
## [YYYY-MM-DD] ingesta | sin material: raw/<fichero>.md
> sin material · no aporta hecho, cifra ni fuente ausente en `resumenes/<pagina>`
```

**Append-only: nunca edites entradas anteriores.** Pasadas ~30, archiva las viejas en `wiki/bitacora-archivo/<año>-Q<n>.md`.

Las notas son lo que más vale a los tres meses. Registra sobre todo lo que **decidiste no hacer**: sin eso, la próxima sesión rehace la discusión.

## 10. Foco

Sobrescribe `wiki/foco.md`: en qué estoy · cómo encontrar cosas · decisiones recientes · preguntas abiertas · huecos conocidos · páginas activas. Máximo ~500 palabras.

Si una decisión de esta ingesta cambia el plan (una fuente adelantó a otra, un stub espera un raw concreto, un hueco quedó cubierto), va aquí. Y si algo se cerró definitivamente, dilo con un **"no volver a preguntar"** para que ninguna sesión futura lo persiga.

## Al terminar

Reporta al usuario, breve: disposición, cuántas páginas se crearon y se ampliaron, qué quedó fuera y por qué, y cualquier tensión o sesgo de la fuente que convenga que sepa. Si el lint o el anclaje dejaron algo pendiente de decisión, dilo explícitamente en vez de resolverlo por tu cuenta.
