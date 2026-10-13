# Revisión de los 11 videos de premios (E14 C26/C27) — 2026-10-12

Modelo: Kling v3.0 (`kling3_0`, std, sin sonido, 1:1, 960×960 a 24 fps). Primer cuadro = la referencia
centrada en 1024×1024 sobre blanco o verde (`primeros-cuadros/`); en los loops y sacudidas también es
el último cuadro. Créditos: 303,98 → 209,48 (**94,5 gastados**, 19 trabajos: 11 + 8 reintentos); colchon_abre v2: 4,5 más (→ 204,98, total 99).

Control: hoja de 8 a 18 cuadros por clip, más medición automática del borde (fondo), de la caja del
objeto cuadro a cuadro (cámara/zoom) y de la diferencia primer↔último cuadro (loop). En todos los
loops la diferencia primer↔último es 0,3–0,6 (en una escala de 0 a 255 por canal, a la altura del
ruido de compresión): cierran bien. Fondo blanco: borde 100 % blanco en los 7 clips blancos. Fondo
verde: el verde es (≈3, 250, 3) en las esquinas; los halos de luz tiñen el verde alrededor del
destello (esperable, lo absorbe el matte). En ningún clip aparecen manos, personajes ni texto.

| clip | veredicto | por qué |
|---|---|---|
| cofre_espera | **aprobado por el dueño 2026-10-12** (QC: ok) | Flota, brillo que cruza el herraje y dos destellos; la tapa no se abre. En unos cuadros la junta tapa-cuerpo se marca como una línea oscura fina (intento 3; los dos primeros abrían una rendija). |
| cofre_sacude | **aprobado por el dueño 2026-10-12** (QC: dudoso) | Salto y meneo correctos y vuelve al cuadro inicial, pero la tapa se levanta ~1 s dejando ver una rendija oscura (sin luz ni objetos). El intento 3 la abría más; Kling insiste en abrir la tapa. Dura 3 s (mínimo de Kling): la acción está en ~0,5–2 s, el resto quieto. |
| cofre_abre | **aprobado por el dueño 2026-10-12** (QC: dudoso) | Intento 3: ya sin monedas (el 1 tiraba monedas, el 2 traía monedas apiladas adentro) y sin zoom. Pero el resplandor se apaga en el último segundo (termina abierto y vacío, sin brillo) y aparece una sombra verde oscura bajo el cofre. |
| paquete_espera | **aprobado por el dueño 2026-10-12** (QC: ok) | Respira apenas, la etiqueta se mueve, destellos; cerrado; loop limpio. |
| paquete_sacude | **aprobado por el dueño 2026-10-12** (QC: ok) | Salto, aplastamiento y las solapas se abomban; nunca se abre; vuelve al inicio. 3 s (acción al principio). |
| paquete_abre | **aprobado por el dueño 2026-10-12** (QC: ok) | Intento 2 (el 1 hacía zoom y redibujaba la caja). Encuadre fijo, las solapas se abren y los rayos dorados siguen hasta el final; sólo luz y destellos. Durante la anticipación la caja se arruga (squash) y queda una sombra leve bajo la caja. |
| colchon_espera | **aprobado por el dueño 2026-10-12** (QC: ok) | Respira, un resorte asoma y vuelve, destellos; loop limpio. |
| colchon_sacude | **aprobado por el dueño 2026-10-12** (QC: ok) | Intento 2 (el 1 le sacaba resortes como patas). Rebote y meneo gelatinoso con polvito; vuelve al inicio. |
| colchon_abre | ok (v2) | Rehecho a pedido del dueño con explosión de dinero (prompt v2, primer intento; la v1 de sólo luz quedó en `colchon_abre.v1.mp4`). Se rasga, estalla con rayos y salen billetes y monedas que vuelan, giran y caen hasta el final. Billetes beige, rosados, naranjas y celestes, sin caras, letras ni números; monedas doradas apagadas (≈187,160,99). Medición de verde: tras sacar los bordes antialias (apertura 7×7) y el billete verde que ya trae el dibujo del colchón, no queda ninguna mancha verde en el dinero; lo que marca son halos de los rayos (cuadros 30–36) y bordes de billetes con desenfoque de movimiento. Encuadre fijo (el colchón mantiene tamaño y lugar). Sin manos ni texto. Ojo: el billetito verde original del colchón sigue ahí y el matte verde lo va a comer. |
| ruleta_espera | **aprobado por el dueño 2026-10-12** (QC: ok) | Disco crema liso que no gira, flecha quieta con un leve movimiento, foquitos que se prenden; loop limpio. Los foquitos más que "correr" se encienden de a poco y quedan todos prendidos hacia el final antes de volver. |
| ruleta_premio | **aprobado por el dueño 2026-10-12** (QC: ok) | Los foquitos destellan, estallido de rayos y confeti detrás del marco, destellos; el disco queda liso y no gira; vuelve al cuadro inicial. Dura 3 s (el .md pide 2; mínimo de Kling). Algo de confeti toca el borde superior. |

## Para quien integre

- Las sacudidas duran 3 s y la ruleta_premio 3 s (Kling no baja de 3 s): recortar o acelerar en el
  pipeline si hace falta 1 s / 2 s.
- La Ruleta se generó desde un cuadro compuesto (marco + disco crema + flecha), porque Kling sólo
  acepta primer y último cuadro. El disco es crema #F1E5C9 plano.
- Los `.mp4` y `primeros-cuadros/` no se versionan (sólo este archivo y `jobs.json`).
