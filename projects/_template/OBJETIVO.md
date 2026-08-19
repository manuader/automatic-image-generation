# Objetivo

<!-- Copiá este directorio: cp -R projects/_template projects/<tu-proyecto> -->

**Qué:** una frase. Para qué son estas imágenes y quién las va a usar.
Ejemplos: "las cinco skins alternativas de los personajes del juego", "los
assets de marca de una cafetería de barrio: logo, ícono, patrón y packaging".

**Estilo común:** lo que TODAS las imágenes tienen que compartir — trazo, paleta,
encuadre, fondo. Esto es lo que después se repite arriba de cada prompt. Si hay
una imagen de referencia, decí cuál y por qué es ésa.

**Lista:** qué imágenes van, con la clave que va a tener cada archivo. Es el
índice del set y de acá salen los `.md` de `prompts/`.

| # | clave | qué es | referencia |
|---|---|---|---|
| 01 | `logo_principal` | … | — |
| 02 | `icono_app` | … | `output/logo_principal.png` |

**Decisiones que no se re-discuten:** lo que ya se probó y salió mal, para que el
próximo no lo vuelva a intentar. Esta sección se llena sobre la marcha y es la
que más vale dentro de tres meses.

---

Cómo escribir los prompts y cómo correr el script: `README.md` en la raíz.
