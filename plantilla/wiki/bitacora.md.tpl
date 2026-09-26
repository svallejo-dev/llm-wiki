# Bitácora

Formato de dos niveles: cabecera grepeable, una línea de estado, detalle.

```
## [YYYY-MM-DD] <operación> | <título>
> <disposición> · <esenciales>
- detalle
```

Operaciones: `sellado`, `ingesta`, `consulta`, `sintesis`, `lint`, `esquema`. Disposiciones de ingesta: `nueva`, `actualiza`, `disputa`, `sin material`.

**Append-only: nunca se edita una entrada anterior.** Pasadas ~30 entradas, las más antiguas se archivan en `wiki/bitacora-archivo/<año>-Q<n>.md`.

Estado reciente sin leer el detalle: `grep -A1 "^## \[" wiki/bitacora.md | tail -8`

---

## [{{FECHA}}] esquema | wiki creada con el plugin llm-wiki

> esquema · andamiaje inicial · {{N_SECCIONES}} secciones · sin contenido todavía

- **Dominio**: {{DOMINIO}}
- **Andamiaje**: núcleo `CLAUDE.md`, especificación `wiki/_esquema/formatos.md`, configuración `wiki/_config.json` y scripts genéricos en `wiki/scripts/`. Las operaciones (ingerir, revisar, sintetizar) las aporta el plugin `llm-wiki`.
- **Los scripts son compartidos** con las demás wikis del plugin y se actualizan con `andamiar.py actualizar`. El esquema y la configuración son propios de esta wiki.
