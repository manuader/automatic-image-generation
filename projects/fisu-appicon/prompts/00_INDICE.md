# Índice

Los `.md` de este directorio son la cola: **uno por imagen**, llamados
`NN_clave.md`. El `NN` es el orden de generación y la `clave` es el nombre que va
a tener el PNG (`12_logo_principal.md` → `output/logo_principal.png`).

Este archivo empieza con `00_` y por eso el script lo saltea: acá va el índice
del set, no un prompt.

Un prompt tiene esta forma exacta —el formato completo está en el §4 del README:

```markdown
# 12 — Logo principal

- **estado**: pendiente
- **referencia**: adjuntar `references/paleta.png`

## Prompt

El texto exacto que se le manda al modelo, tal cual, sin que el script le agregue
ni le saque nada.
```

- `estado` lo pasa a `hecho` el script, y recién después de verificar el PNG.
  Ponerlo a mano es la forma de saltear un prompt.
- `referencia` es opcional y se resuelve desde la raíz del proyecto:
  `references/…` para lo que trajiste vos, `output/…` para algo que este mismo
  script generó antes en la cola.
