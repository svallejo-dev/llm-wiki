---
name: explicar
description: Explica un tema de una wiki LLM (repo con wiki/_config.json) de forma concreta y fácil, anclado a sus páginas y en el orden que marca el grafo — ejemplo real del corpus, analogía con su límite y cuánto pesa la evidencia. Úsala con "explícame X", "no entiendo X", "qué es X en palabras simples" o "cómo le explico X a mi equipo". Complementa a una skill pedagógica. NO para un dato puntual ni para archivar (/llm-wiki:sintetizar).
---

# Explicar un tema de la wiki

Hacer que entender algo sea barato, sin perder el anclaje. El fallo a evitar no es una explicación difícil: es una explicación fluida que suena bien pero **no es lo que dice la wiki**, o que esconde que la evidencia detrás es floja. Una explicación genérica la puede dar cualquiera; esta tiene que salir de las páginas del usuario y decir qué está respaldado y qué no.

## Antes de nada: ¿estás en una wiki?

Trabaja desde la raíz del repo. Una wiki de este plugin se reconoce porque tiene `wiki/_config.json`:

```bash
test -f wiki/_config.json && echo "wiki" || echo "no es una wiki"
```

Si no existe, **para**: este repo no es una wiki LLM. Dilo, y si el usuario quiere montar una, ofrece `/llm-wiki:crear`.

## 1. Pregunta el nivel

Salvo que el usuario ya lo haya dicho en la petición ("como a alguien no técnico", "para mi equipo de backend", "a fondo"), pregúntalo con AskUserQuestion antes de explicar. El nivel cambia qué se explica, no solo cómo:

- **Sin base técnica** — analogías, nada de código, el énfasis en para qué sirve.
- **Técnico, sin jerga del tema** — sabe programar y leer una arquitectura; cada término del dominio se define la primera vez que aparece.
- **Practicante** — conoce el área; directo a matices, compensaciones y cuándo falla.

Si la explicación es para que el usuario se la cuente a otros, tenlo en cuenta: tiene que sostenerse sin la wiki delante.

## 2. Localiza y traza la ruta

```bash
wiki/scripts/q <tema>
wiki/scripts/q -n <pagina-principal>
```

La página principal es la que mejor casa con el tema, normalmente un concepto o una entidad. El vecindario dice qué hay que entender **antes**: los enlaces salientes a conceptos y entidades, y sobre todo las relaciones tipadas `depende-de>`. Esa es la ventaja de esta wiki frente a una explicación genérica: sabe qué conceptos sostienen a cuál.

- **Sin base** → incluye 1-2 prerrequisitos, en orden.
- **Técnico** → como mucho uno, y solo si sin él no se entiende.
- **Practicante** → ninguno.

Lee la página principal y, como mucho, dos de prerrequisitos. No leas el vecindario entero.

Si el tema **no está en la wiki**, dilo antes de nada. Revisa los huecos declarados en `wiki/foco.md`. Puedes ofrecer una explicación general, pero marcada entera como *fuera de la wiki*, y proponer buscar una fuente para ingerirla.

## 3. Construye la explicación

Una forma fija, adaptada al nivel. Hace que las explicaciones se parezcan entre sí y que el usuario sepa dónde mirar:

1. **En una frase** — qué es, sin jerga.
2. **Un ejemplo concreto** — mejor si sale del corpus: un caso real, un framework real, una cifra de `wiki/_cifras.md` con su literal exacto. Lo concreto se entiende; lo abstracto se olvida. Si el corpus no tiene ejemplo y te lo inventas, dilo: *ejemplo ilustrativo*.
3. **Cómo funciona** — de 3 a 5 pasos en lenguaje llano. Para practicantes, el mecanismo y sus compensaciones.
4. **Una analogía, y dónde se rompe** — una analogía sin su límite enseña algo falso. Una línea basta: *la analogía falla en que…*
5. **Cuándo sirve y cuándo no** — lo que convierte entender en poder decidir.
6. **Qué tan sólido es** — la `confianza` de las páginas, si hay un bloque `Estado: Disputado`, si es un marco conceptual sin medición detrás. Si todo es `alto` y sin disputas, basta una línea.
7. **Para seguir** — 2 o 3 wikilinks en orden de lectura.

### Reglas

- **Todo lo factual sale de las páginas que leíste.** Lo que añadas desde fuera de la wiki, márcalo *(fuera de la wiki)*. Es lo que permite al usuario saber qué está respaldado por sus fuentes.
- **Las comillas afirman literalidad**, como en toda la wiki: cita entre comillas solo lo que está tal cual en la página o el raw.
- **Jerga**: cada término del dominio, definido en una línea la primera vez, o evitado. Sin código en el nivel sin base.
- **Brevedad**: un concepto cabe en una pantalla, unas 250-400 palabras. Si te sale el doble, no es "fácil". Los temas transversales pueden alargarse, pero divididos por los pasos de la ruta.
- **Diagrama cuando es un flujo**: si el concepto es un proceso o una arquitectura, un diagrama mermaid pequeño explica más que dos párrafos.
- **No rellenes**: si la wiki cubre el tema con poco material, dilo en vez de disimularlo con prosa.

## 4. Si hay una skill pedagógica

Si el usuario tiene otra skill dedicada a enseñar el dominio (por ejemplo, una de pedagogía para IA), esa manda en el **método**: secuencia, verificación socrática, ejercicios. Esta skill se encarga de que el **contenido** salga de la wiki y de marcar lo que no. No dupliques sus comprobaciones.

## 5. Al terminar

- **Ofrece comprobar que se entendió** con `/llm-wiki:repasar` sobre esas páginas. No hagas el examen aquí: explicar y preguntar son momentos distintos, y mezclarlos hace las dos cosas peor.
- **No archives por defecto.** Una explicación no aporta hechos nuevos. Si recorrió ≥3 páginas como ruta de aprendizaje y el usuario quiere conservarla, encaja como `panorama` (mapa de un área, cero hechos nuevos): pásala a `/llm-wiki:sintetizar`.
- **Sin entrada de bitácora** salvo que se archive: explicar es leer, como consultar.
