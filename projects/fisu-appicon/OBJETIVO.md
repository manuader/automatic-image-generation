# App icon de FisuEvolution

La cara de El Fisura sobre un fondo celeste con degradado dinamico, para el
AppIcon de 1024x1024 del juego (repo `FisuEvolution`).

## Decisiones que no se re-discuten

- **La cara es la que ya existe.** `references/fisura_face.png` es
  `homeless_face`, un asset YA INTEGRADO al juego (atlas `ui`,
  `assets_manifest.json`). Si el icono no es esa cara, el juego y la App Store
  muestran dos personajes distintos. Cualquier candidata que "mejore" la cara
  se descarta.
- **Modo `raw`, no `game-asset`.** El fondo celeste es parte del icono: no se
  recorta. Un icono de App Store no puede tener alfa.
- **El degradado va solo en el fondo.** El estilo canonico del pipeline es
  plano y sin degradados; el personaje mantiene color plano y contorno de
  tinta uniforme. La unica excepcion es el fondo.
- Sin texto de ninguna clase, sin esquinas redondeadas, sin sombra externa:
  iOS pone su propia mascara.

Direccion completa y checklist de aceptacion:
`FisuEvolution/Docs/PROMPT-appicon-fisuevolution.md`.
