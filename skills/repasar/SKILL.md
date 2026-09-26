---
name: repasar
description: Pone a prueba lo que sabes de una wiki LLM (repo con wiki/_config.json) — pregunta sobre sus páginas de una en una, corrige contra lo que dicen, explica el error y registra lo que cuesta para volver sobre ello con repetición espaciada. Úsala con "pregúntame sobre X", "ponme a prueba", "hazme un quiz", "repasemos", "qué tengo flojo" o para exportar tarjetas a Anki. NO para explicar un tema desde cero (/llm-wiki:explicar).
---

# Repasar

Una wiki bien hecha da la sensación de saber cosas que en realidad solo se han leído. Es la crítica más seria a este patrón: si el LLM lee, resume y conecta, ¿en qué momento aprende el usuario? Recordar sin mirar —responder de memoria— es lo que fija el conocimiento, y además descubre qué páginas no se entendieron de verdad.

## Antes de nada: ¿estás en una wiki?

Trabaja desde la raíz del repo. Una wiki de este plugin se reconoce porque tiene `wiki/_config.json`:

```bash
test -f wiki/_config.json && echo "wiki" || echo "no es una wiki"
```

Si no existe, **para**: este repo no es una wiki LLM. Dilo, y si el usuario quiere montar una, ofrece `/llm-wiki:crear`.

Comprueba también que existe `wiki/scripts/repaso.py`. Si no, los scripts de la wiki son de una versión anterior del plugin: `python3 $PLUGIN/scripts/andamiar.py actualizar .` los pone al día (`$PLUGIN` es la raíz del plugin, dos niveles por encima del directorio base de esta skill).

## El estado

Lo lleva `wiki/scripts/repaso.py` en `wiki/_repaso.tsv`, con repetición espaciada por cajas: un acierto sube una caja, un parcial la mantiene, un fallo vuelve a la 1, y cada caja tarda más en volver (1, 2, 4, 8 y 16 días). **No edites ese fichero a mano**: úsalo solo a través del script.

```bash
wiki/scripts/repaso.py pendientes [N]                    # qué toca repasar
wiki/scripts/repaso.py registrar <pagina> <resultado>    # acierto | parcial | fallo
wiki/scripts/repaso.py estado                            # resumen
```

Es estado personal de estudio, no contenido: no va en la bitácora ni cuenta para el lint.

## 1. Qué repasar

- **Con tema** ("pregúntame sobre RAG") → `wiki/scripts/q <tema>` y quédate con las 3-5 páginas más relevantes.
- **Sin tema** ("repasemos") → `wiki/scripts/repaso.py pendientes 5`. Prioriza lo vencido, después lo nunca repasado empezando por lo más central del grafo, y si todo está al día, adelanta lo más flojo.

Por defecto son 5 preguntas. El usuario puede parar cuando quiera.

## 2. Una pregunta cada vez

Para cada página: léela (solo esa), haz **una** pregunta y **espera la respuesta** antes de seguir. No encadenes preguntas en el mismo mensaje: la gracia es responder sin ver la siguiente ni la solución.

Qué preguntar:

- **Comprensión antes que memoria.** *¿Por qué…?*, *¿qué pasa si…?*, *¿cuándo usarías X en vez de Y?*, o un escenario corto al que aplicarlo. Una cifra solo si es de las que importan (las de `_cifras.md`), nunca un dato trivial.
- **Respondible desde la página.** Si la respuesta no está en la wiki, no es una pregunta de repaso.
- **Sin pistas en el enunciado.** La pregunta no debe contener la respuesta.
- **Lo disputado, como disputado.** Si la página lleva `Estado: Disputado` o `confianza: bajo`, pregunta por la disputa o por la fuerza de la evidencia, no como si fuera un hecho asentado.
- **Pregunta abierta por defecto.** Recordar sin opciones fija más que reconocer entre opciones. Usa opción múltiple solo si el usuario la pide.

## 3. Corrige contra la página

Compara la respuesta con lo que dice la página y di cuál de las tres fue:

- **Acierto** — la idea central está, aunque falten matices.
- **Parcial** — va en la buena dirección pero falta algo que importa, o mezcla algo incorrecto.
- **Fallo** — no está, o es incorrecto.

Luego, breve y concreto: qué estuvo bien, qué faltó o falló, y la respuesta correcta con su wikilink. **No halagues.** Un "¡muy bien!" ante una respuesta a medias le quita al repaso lo único que aporta. Si la respuesta es correcta pero la página dice otra cosa, gana la página, aunque puedes señalar la discrepancia como posible hueco de la wiki.

Registra el resultado antes de pasar a la siguiente:

```bash
wiki/scripts/repaso.py registrar <seccion/pagina> acierto
```

## 4. Al terminar

Un resumen corto: cuántas bien, qué costó y qué páginas conviene releer (wikilinks), y cuándo toca el próximo repaso (`repaso.py estado`). Para lo que falló, ofrece `/llm-wiki:explicar`: fallar una pregunta suele significar que la explicación no llegó, no que falte repetir.

Si un fallo se repite en la misma página, puede que el problema sea la página (confusa, incompleta o mal enlazada), no el usuario. Dilo: es información para `/llm-wiki:revisar`.

## Tarjetas para Anki

Si el usuario las pide, genera pares pregunta-respuesta desde las páginas elegidas, con las mismas reglas: comprensión antes que memoria, respondibles desde la página y sin pistas. Formato CSV con `;` de separador y tres columnas: `anverso;reverso;etiquetas`, con la página de origen como etiqueta (`conceptos::rag`). Guárdalo donde diga el usuario o, por defecto, en la raíz del repo como `repaso-anki-YYYY-MM-DD.csv`, **nunca dentro de `wiki/`**, porque no es contenido de la wiki. Dile cómo importarlo: en Anki, *Archivo → Importar*, separador punto y coma.
