---
name: revisar
description: Revisa la salud de una wiki LLM (repo con wiki/_config.json) — enlaces rotos, huérfanas, topología, frontmatter, cifras sin anclaje, contradicciones sin marcar y duplicados. Aplica los arreglos seguros y reporta lo que toque un hecho. Úsala con "pasa el lint", "revisa la wiki", "audita", "verifica las cifras de X" o "busca contradicciones", y cada ~10 ingestas. Acepta una página como argumento. NO para ingerir ni para redactar páginas.
---

# Revisar la wiki

El lint existe porque los síntomas de una wiki enferma son invisibles hasta que son caros: una huérfana no molesta, una contradicción sin marcar no da error, una cifra inventada se lee igual que una verificada. Y hay un modo de fallo peor que no pasar el lint: **pasarlo y que grite tanto que se deje de ejecutar.** Si algo es un falso positivo, arregla la regla, no lo ignores.

## Antes de nada: ¿estás en una wiki?

Trabaja desde la raíz del repo. Una wiki de este plugin se reconoce porque tiene `wiki/_config.json`:

```bash
test -f wiki/_config.json && echo "wiki" || echo "no es una wiki"
```

Si no existe, **para**: este repo no es una wiki LLM, o lo es de una versión anterior sin configuración. Dilo, y si el usuario quiere montar una, ofrece `/llm-wiki:crear`. No improvises la estructura.

La regla que gobierna todo lo que sigue: **el lint propone, el usuario dispone.**

## Alcance

- Sin argumento → toda la wiki.
- Con una página (`conceptos/rag`) → solo esa, incluyendo su anclaje. Útil justo después de escribirla.

## Paso 1 — Escaneo mecánico

Cero criterio, solo comandos:

```bash
python3 wiki/scripts/generar.py
wiki/scripts/verificar_anclaje.py [<pagina>]
wiki/scripts/verificar_anclaje.py --citas
```

El primero regenera los derivados y reporta: enlaces rotos, huérfanas (exentas `resumenes`, `papers`, `sintesis`), páginas con menos de 2 salientes, violaciones de topología, verbos tipados fuera de los cuatro permitidos, `panorama` con `cubre < 3`, pozos gravitatorios (muchos entrantes **y** mucho texto: una página concisa muy enlazada es un hub sano, no un pozo), páginas demasiado largas, el mismo nombre en dos secciones, síntesis con entrantes, frontmatter incompleto, `tldr` de más de 70 caracteres y `confianza` inválida.

El segundo comprueba el invariante de anclaje: que cada cifra, fecha y cita de las páginas con campo `raw:` exista **literal** en su raw. Distingue dos cosas que conviene no confundir:

- **SIN ANCLAJE** en una cifra → puede ser un dato inventado. Es lo grave.
- **CITA NO LITERAL** → casi siempre una traducción. La corrección no es borrar el pasaje: es quitarle las comillas y dejarlo en cursiva como paráfrasis, o citar en el idioma original. Las comillas afirman literalidad.

Para mirar el grafo directamente:

```bash
sort -t$'\t' -k2 -rn wiki/_grafo.tsv | head -15    # páginas más enlazadas
awk -F'\t' '$2==0' wiki/_grafo.tsv                 # sin entrantes
awk -F'\t' '$6!=""' wiki/_grafo.tsv                # con relaciones tipadas
cut -f1 wiki/_alias.tsv | sort | uniq -d           # alias colisionando
```

## Paso 2 — Revisión de contenido

Aquí hace falta criterio, y **nada de esto se auto-arregla**:

- **Contradicciones entre páginas no marcadas como disputa.** Una contradicción marcada es un activo; sin marcar es deuda. Busca en las relaciones tipadas (`contradice::`) y en páginas con `estado: disputado` que no tengan su `disputa` en `comparativas/`.
- **`confianza: alto` cuya única fuente es comunidad o anécdota.** Bájala. Y al revés: una página con dos fuentes independientes puede subir.
- **Marcos mentales presentados como hallazgos.** Si una página afirma que algo funciona sin que haya medición detrás, debería llevar `confianza: medio` y decirlo en el cuerpo.
- **Duplicados semánticos**: dos páginas sobre lo mismo con títulos distintos. Síntomas: dos alias casi iguales apuntando a páginas diferentes, o un enlace roto con más de un candidato plausible.
- **Notas de alcance caducadas**: páginas con `> **Nota de alcance.**` cuyo raw pendiente ya se ingirió. Esa nota ahora miente.
- **Stubs que siguen siendo stubs** después de que llegara su fuente.

## Paso 3 — Sugerencias

Lo que haría la wiki más útil, no lo que está roto:

- Conceptos con ≥3 páginas relacionadas y sin `panorama` que los cubra. `q -h <pagina>` ayuda a ver si hay masa suficiente.
- "Ver también" faltantes entre páginas que se citan en una sola dirección.
- Hubs que deberían partirse en sub-hubs.
- Huecos que merecerían una fuente nueva, cruzando `foco.md` con lo que el grafo no cubre.
- Bitácora con más de ~30 entradas: archivar.
- **Scripts desactualizados**: `python3 $PLUGIN/scripts/andamiar.py comprobar .` dice si los scripts genéricos de la wiki van por detrás de los del plugin, y `actualizar` los pone al día. `$PLUGIN` es la raíz de este plugin, dos niveles por encima del directorio base de esta skill. Es un arreglo seguro: solo toca `wiki/scripts/`.

## Autoridad

**Arreglos seguros** — se aplican y se reportan:

- Regenerar índices, `_alias.tsv` y `_grafo.tsv`: es idempotente, siempre seguro.
- Reparar un enlace roto con **una única** coincidencia obvia.
- Añadir un "Ver también" recíproco.
- Quitar las comillas de un pasaje traducido para que deje de afirmar literalidad.

**Reportes** — se reportan y se **espera confirmación**:

- Cualquier cosa que toque un hecho, una cifra, una contradicción o una `confianza`.
- Enlace roto con 0 candidatos, o con más de 1.
- Posibles duplicados semánticos.
- Fusionar o retirar páginas. Nunca se borra: `estado: obsoleto` y `reemplazado_por:`.

## Informe

Agrupa por categoría, con recuento, y **separa lo aplicado de lo pendiente**. Lo que el usuario necesita saber en una lectura es: ¿hay algo grave, y qué tengo que decidir yo?

Registra en `bitacora.md`:

```markdown
## [YYYY-MM-DD] lint | pasada N
> 3 arreglos seguros aplicados · 2 pendientes de decisión

- **Arreglado**: índices regenerados, 1 enlace roto con coincidencia única, 1 recíproco.
- **Pendiente**: posible duplicado `conceptos/<a>` vs `conceptos/<b>`; `entidades/<x>` con `confianza: alto` y única fuente comunitaria.
```

Si no hubo incidencias, dilo en una línea y regístralo igual: saber que la wiki estaba sana el día N también es información.
