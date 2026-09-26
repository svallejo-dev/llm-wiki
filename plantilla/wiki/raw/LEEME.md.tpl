# raw/ — capa inmutable

**No edites, renombres ni borres nada de esta carpeta.** Ni un typo, ni un formato, ni un enlace roto.

Esto es la verdad de la que deriva toda la wiki. El invariante de anclaje dice que toda cifra, fecha y cita de `wiki/` existe literalmente en alguno de estos ficheros. Si el raw cambia, las verificaciones anteriores dejan de valer en silencio.

Si una fuente se actualiza, se añade un fichero nuevo con fecha nueva. La versión antigua se queda.

## Cómo entra algo aquí

```bash
wiki/scripts/capturar.py <fichero-o-URL> --fuente "<origen>"
```

Normaliza el nombre a `YYYY-MM-DD-<slug>`, pone encabezado de procedencia, avisa de duplicados y, si es un PDF, deja el original junto a un `.md` extraído con `pdftotext -layout`. La fecha del prefijo es la de **captura**, no la de autoría.

Los paquetes (`.zip`) se conservan tal cual en `_paquetes/` y su contenido se extrae a una carpeta con su nombre.
