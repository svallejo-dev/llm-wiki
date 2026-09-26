---
name: sintetizar
description: Archiva una conclusión como página permanente de una wiki LLM (repo con wiki/_config.json) — comparativa (A vs B), panorama (mapa de un área) o síntesis (opinión propia del usuario). Úsala con "archiva esto", "déjalo escrito", "haz un panorama de X" o "compara X con Y y guárdalo", o cuando una respuesta tuya sintetizó varias páginas en una conclusión que no estaba escrita. NO para una pregunta puntual ni para ingerir fuentes (/llm-wiki:ingerir).
---

# Sintetizar y archivar

Las buenas respuestas no deberían morir en el chat. Este es el mecanismo por el que **las exploraciones se acumulan igual que las fuentes**: una comparación que pediste, una conexión que apareció, una decisión que tomaste. Sin esto, la wiki solo crece cuando llega material de fuera, y la mitad del valor se pierde.

## Antes de nada: ¿estás en una wiki?

Trabaja desde la raíz del repo. Una wiki de este plugin se reconoce porque tiene `wiki/_config.json`:

```bash
test -f wiki/_config.json && echo "wiki" || echo "no es una wiki"
```

Si no existe, **para**: este repo no es una wiki LLM, o lo es de una versión anterior sin configuración. Dilo, y si el usuario quiere montar una, ofrece `/llm-wiki:crear`. No improvises la estructura.

**Lee `wiki/_esquema/formatos.md` antes de escribir.** Los tres tipos tienen frontmatter y topología propios, y el de `sintesis` es peculiar.

## Cuándo NO archivar

Primero el filtro, porque archivar de más infla la wiki igual que ingerir fuentes flojas:

- Fue la **búsqueda de un dato puntual** → no archives nada.
- La conclusión **ya está escrita** en una página existente → amplíala en vez de crear otra. Comprueba con `wiki/scripts/q <termino>` y `grep -i "<termino>" wiki/_alias.tsv`.
- La respuesta sintetizó **una sola página** → no hay síntesis, hay lectura.

Si dudas, propónselo al usuario y **espera confirmación** antes de escribir. Es su wiki y su criterio de qué merece quedarse.

## Qué tipo es

| Si es… | Tipo | Dónde | Requisito |
|---|---|---|---|
| A contra B, con criterio de decisión | `comparativa` | `comparativas/` | Deben existir las páginas de ambas partes |
| Dos fuentes que se contradicen sobre un hecho | `disputa` | `comparativas/` | Quién lo sostiene, quién lo refuta, con qué fuerza probatoria |
| Mapa de un área, solo enlaces y orientación | `panorama` | `panoramas/` | **`cubre` ≥ 3** páginas, y **cero hechos nuevos** |
| Lo que el usuario concluye o decide | `sintesis` | `sintesis/` | `deriva_de` con ≥2 páginas; es **nodo hoja** |

Dos reglas que se saltan a menudo:

- **Un panorama no aporta hechos.** Si te descubres escribiendo un dato nuevo ahí, ese dato pertenece a un concepto o una entidad: escríbelo allí y enlázalo.
- **A `sintesis/` no le enlaza nadie.** Lo que opinas no es fuente de lo que sabes. Solo tiene enlaces salientes.

## Cuando la síntesis es del usuario

El caso más valioso y el único sitio donde entra su voz. Suele llegar desordenado: déjale soltarlo y estructúralo tú.

- **No lo suavices hasta volverlo genérico.** Una síntesis que podría haber escrito cualquiera no sirve de nada; lo que vale es su criterio concreto, con sus razones y sus dudas.
- **Ancla sus afirmaciones a páginas** de la wiki cuando existan, y di cuándo no existen: una opinión sin respaldo es legítima, pero conviene que se vea.
- **Conserva lo que rechazó y por qué.** A los tres meses, "descarté X porque Y" vale más que la conclusión.
- Si contradice algo escrito en la wiki, no lo escondas: eso es una `disputa`, y es información.

## Escribir

1. **Reúne las páginas** que sostienen la conclusión: `wiki/scripts/q <termino>` para sembrar, `q -n <pagina>` para expandir por el grafo y encontrar lo estructuralmente cercano que no contiene el término.
2. **Escribe la página** con su frontmatter y su `veredicto` o `deriva_de`. Enlaza a ≥2 páginas existentes.
3. **Nómbrala por el tema de la conclusión, no por la pregunta** que la originó. `comparativas/<a>-vs-<b>-para-<criterio>`, no `comparativas/que-uso-para-<caso>`. Las preguntas envejecen; los temas no.
4. **Añade el recíproco**: si comparas dos entidades, cada una debería enlazar a la comparativa. Si no, nace huérfana.

## Cascada

```bash
python3 wiki/scripts/generar.py
```

Regenera índices, alias y grafo, y pasa el lint mecánico. Luego a mano: `wiki/indice.md` solo si merece una puerta de entrada nueva.

Y registra en `bitacora.md` — una síntesis sin registrar es indistinguible de una página que apareció sola:

```markdown
## [YYYY-MM-DD] consulta | <la pregunta que originó la conclusión>
> archivada · comparativas/<a>-vs-<b>-para-<criterio> · sintetizó 3 páginas
```

Para una síntesis propia del usuario, `sintesis` como operación y di de qué deriva.

Por último, refresca `wiki/foco.md` si esto cambia en qué estáis o cierra una pregunta abierta.

## Al terminar

Dile al usuario qué página creaste, de qué deriva y qué **no** metiste dentro. Si al escribirla apareció una tensión con algo ya escrito, dilo: puede que lo siguiente sea una disputa, no un retoque.
