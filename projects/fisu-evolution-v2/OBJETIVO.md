# Objetivo — FisuEvolution 2.0 (épica E8)

**Qué:** el arte nuevo de la 2.0 de *FisuEvolution*: los 8 visitantes nuevos (canónica,
hablando, acción y cara), la pose "hablando" y la cara de los 10 especiales, el Paquete de la
Aduana, El Colchón, la Ruleta, los íconos de la tienda de ORO, el Álbum de especiales, las 3
familias de skins dibujadas (Pijama de Ositos, Gaucho y Disfraz de Dinosaurio, × 43 personajes)
y los 10 fondos regenerados. Son 222 prompts. El orden y el encadenamiento están en
`prompts/00_INDICE.md`.

**No se mezcla con `fisu-evolution/`**, que es el archivo de las 335 imágenes de la v1.

**Fuente de verdad del contenido:** `Docs/PLAN-v2.md` del juego (E8, §5, Anexo A y Anexo B) y la
biblia de personajes, `Docs/biblia-visitantes.md`, ambas en el repo de FisuEvolution. El
descriptor de cada personaje sale de la biblia: si cambia uno, cambia en los dos lados.

**Estilo común:** el de la v1. Cada cuerpo entero arranca con la frase fija del Anexo B ("Match
EXACTLY the art style…") y cierra con la de cuerpo entero sobre blanco. Prompts en ASCII puro.

## Referencias

| Archivo | De dónde sale |
|---|---|
| `references/fisura.png` | `Tools/asset-pipeline/heroes/approved/fisura.png` del juego |
| `references/chars/<tipo>.png` (43) | `Tools/asset-pipeline/dropbox/procesadas/<tipo>.png`: el original que se integró |
| `references/chars/homeless.png` | el mismo `fisura.png` (el original de El Fisura no quedó en `procesadas/`) |
| `references/chars/junior_programmer.png` | `earth.atlas/junior_programmer_idle@3x.png` aplanado sobre blanco: no queda el original sin recortar, así que es de 512 px |
| `references/chars/sp_<id>.png` (10) | `dropbox/procesadas/sp_<id>.png` |
| `references/bg/bg_<piso>.png` (10) | `dropbox/procesadas/bg_<piso>.png`, iguales a los del juego hoy |
| `references/style/icon.png` | `dropbox/procesadas/ui_menu_trophy.png`, guía de estilo de los íconos |

⚠️ **No se tomaron de `fisu-evolution/output/`.** Ahí el `sp_influencer.png` no es el del juego:
es una versión vieja con marcas de moda reales en las bolsas. Lo integrado está en `procesadas/`, y
se verificó contra el atlas, personaje por personaje.

## Decisiones que no se re-discuten

- **Números de tres cifras.** La cola ordena los archivos alfabéticamente, no por número. Con
  dos y tres cifras mezcladas, `100_` sale antes que `10_` y una pose se genera antes que su
  canónica.
- **El piloto es 001–005** y corre primero, aparte (ver `README.md`).
- **Las familias van al final (100–227)**. Así, si el piloto muestra deriva en la skin, el resto
  sale con ChatGPT y las 129 skins con `gemini`, cortando la cola en un solo punto.
- **Encadenado:** la pose y la cara de un visitante nuevo adjuntan `output/npc_<nombre>.png`, la
  canónica que generó el prompt anterior. Cada skin adjunta SU personaje, nunca El Fisura.
- **Sin texto en ninguna imagen.** El cartel LLENO sale en blanco y el juego escribe la palabra,
  porque hay es + en.
- **`punch_holes` vacío.** El marco de la ruleta y el de la carta del Álbum se dibujan debajo de
  lo que el juego pone adentro. Si alguno termina encima, se agrega su clave y se corre
  `--reprocess`, que no gasta cuota.
- **Fondos: se usa el crudo** (`output/bg_*.png`), no `output/assets/`. El recorte por
  conectividad es para personajes sobre blanco, no para un fondo.
- **Las caras no cierran con la frase de cuerpo entero**, porque la contradice: usan el cierre
  de las 43 caras de la v1. Íconos y fondos tienen sus propias frases fijas.
