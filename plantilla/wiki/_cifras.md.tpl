# Cifras ancla

Inventario de los datos citables del corpus, **con su literal exacto tal como aparece en el raw**. Es el índice invertido del invariante de anclaje: para verificar cualquier fila,

```bash
grep -rn "<literal>" wiki/raw/
wiki/scripts/verificar_anclaje.py --cifras
```

Se actualiza a mano en cada ingesta (paso 8 de `/llm-wiki:ingerir`). Copia el literal, no lo normalices: la verificación es por coincidencia de cadena.

Cuando una cifra venga de una fuente débil (un blog comercial, una anécdota, una proyección), dilo debajo de su tabla: la fuerza probatoria es parte del dato.

---

_Sin cifras todavía._
