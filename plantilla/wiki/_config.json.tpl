{
  "_doc": {
    "que_es": "Configuración de esta wiki. Los scripts de wiki/scripts/ son genéricos y leen de aquí todo lo que depende del dominio. Cambiar una sección o una regla es editar este fichero, no el código. Mantenlo coherente con wiki/_esquema/formatos.md.",
    "secciones": "Orden = orden de los índices. Cada una admite: exenta_huerfanas (se alcanza desde el índice por diseño), umbral_pozo (entrantes a partir de los que una página grande es un pozo gravitatorio; ver palabras_pozo), cubre_minimo (exige el campo `cubre`), hoja (nadie puede enlazarle), agrupar_por / ordenar_por (índice por grupos), exento_salientes_salvo (exenta de la regla de salientes salvo que ese campo valga true).",
    "tamaño": "palabras_pozo: un pozo gravitatorio necesita más entrantes que umbral_pozo Y más palabras que esto; muchos entrantes en una página concisa es un hub sano. palabras_max: por encima, la página se reporta como demasiado larga, tenga los entrantes que tenga.",
    "topologia": "Tipo de página -> carpetas a las que puede enlazar. 'raw' solo para los tipos que citan fuentes directamente. Un tipo especializado nuevo necesita su entrada aquí.",
    "sincronizacion": "Los scripts se actualizan con `andamiar.py actualizar <repo>` desde el plugin llm-wiki. Este fichero y el esquema NO se sincronizan: son propios de esta wiki. Las skills de operación viven en el plugin y se actualizan con él."
  },
  "nombre": "{{NOMBRE}}",
  "tldr_max": 70,
  "salientes_minimos": 2,
  "palabras_pozo": 1500,
  "palabras_max": 2500,
  "confianza": ["alto", "medio", "bajo"],
  "obligatorios": ["tipo", "titulo", "tldr", "tags", "confianza", "creado", "actualizado"],
  "verbos_tipados": ["contradice", "reemplaza a", "depende de", "aplica"],
  "secciones": [
    {"carpeta": "resumenes", "titulo": "Resúmenes", "desc": "Una página por fuente ingerida de `raw/`.", "exenta_huerfanas": true},
    {"carpeta": "entidades", "titulo": "Entidades", "desc": "Actores nombrables: personas, organizaciones, productos, herramientas.", "umbral_pozo": 15},
    {"carpeta": "conceptos", "titulo": "Conceptos", "desc": "Ejes transversales que atraviesan varias fuentes.", "umbral_pozo": 15},
    {"carpeta": "comparativas", "titulo": "Comparativas y disputas", "desc": "`comparativa`: A vs B con veredicto. `disputa`: afirmaciones en conflicto."},
    {"carpeta": "recetas", "titulo": "Recetas", "desc": "Procedimientos ejecutables: checklists, playbooks, plantillas."},
    {"carpeta": "panoramas", "titulo": "Panoramas", "desc": "Mapas de área. Solo enlaces, cero hechos nuevos. Requieren `cubre` ≥ 3.", "cubre_minimo": 3},
    {"carpeta": "sintesis", "titulo": "Síntesis", "desc": "Conclusiones propias derivadas de la wiki. Nodo hoja del grafo.", "exenta_huerfanas": true, "hoja": true}
  ],
  "topologia": {
    "resumen":     ["raw", "resumenes", "entidades", "conceptos", "comparativas", "recetas"],
    "receta":      ["raw", "entidades", "conceptos", "recetas"],
    "entidad":     ["resumenes", "entidades", "conceptos", "comparativas", "recetas"],
    "concepto":    ["resumenes", "entidades", "conceptos", "comparativas", "recetas"],
    "comparativa": ["resumenes", "entidades", "conceptos", "comparativas", "recetas"],
    "disputa":     ["resumenes", "entidades", "conceptos", "comparativas"],
    "panorama":    ["resumenes", "entidades", "conceptos", "comparativas", "recetas", "panoramas"],
    "sintesis":    ["resumenes", "entidades", "conceptos", "comparativas", "recetas", "panoramas"]
  }
}
