# Objetivo — FisuEvolution

**Qué:** todo el arte de *FisuEvolution*, un merge-idle argentino donde un
linyera evoluciona hasta dios: los 60 personajes de la torre, sus skins
alternativas, los 10 fondos de etapa y los íconos de UI.

**Este proyecto es el archivo y la fábrica, no el pipeline del juego.** Las 335
imágenes de `output/` son los originales ya generados, copiados acá para que
**nunca haya que volver a pagarlos**: la cola los ve y no los vuelve a pedir. El
juego sigue integrando su arte con sus propios scripts en
`FisuEvolution/Tools/asset-pipeline/`, que no se tocaron. Lo que se genere acá se
copia a mano al `dropbox/` del juego.

**Estilo común:** cartoon argentino de línea gruesa y color plano, cuerpo entero,
fondo blanco puro, cuadrado, sin texto ni watermark. Cada prompt lo repite arriba
de todo y adjunta una referencia, que es lo que sostiene que 300 imágenes
generadas en meses distintos parezcan del mismo estudio.

**Referencias:** `references/fisura.png` es el personaje base y el patrón de
estilo de los tiers. Cada skin adjunta a SU personaje desde `output/`, no al
Fisura: adjuntar siempre el mismo mandaba el estilo equivocado.

**Modo de salida:** `game-asset`. Recorta el fondo por conectividad —el que no se
come el guardapolvo blanco del `senior_doctor`— y exporta 384 y 512.

## Decisiones que no se re-discuten

- **El recorte va por conectividad, no por saliencia.** `rembg` dejaba
  transparente todo lo blanco del personaje. Medido sobre 219 originales: de 1183
  islas blancas encerradas, la enorme mayoría es dibujo, no hueco.
- **`reference_threshold` en 4, no en 12.** Con las skins la referencia es el
  MISMO personaje con otra ropa: con 12 el filtro se comía el resultado legítimo
  y el runner esperaba el timeout entero sin encontrar nada.
- **`punch_holes` sólo para los cuatro declarados** (`fx_tap` y los tres
  trofeos): son los únicos cuyo blanco encerrado es aire y no dibujo.
- **La composición va primero en el prompt.** Con el párrafo de composición al
  final, los fondos salían con el piso en el 34% del cuadro en vez del 50%.
