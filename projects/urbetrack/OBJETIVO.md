# Objetivo — Urbetrack

**Qué:** 20 assets de marca para **Urbetrack** (urbetrack.com), la suite
tecnológica de administración de flotas para el sector público. Identidad,
producto, sectores, corporativo y feria. La imagen es el producto final: modo
`raw`.

**Qué hace la empresa:** software SaaS + hardware IoT + consultoría para gestión
de flotas y aseo urbano. Opera en Argentina, México, Colombia, Chile y España.
Sectores: aseo & smart city (el principal), oil & gas, minería, fleet management
y construcción. Certificada TÜV Rheinland.

**Copy de la casa** (sacado del sitio, no inventado): «Inteligencia en tu
Gestión» · «SOLUCIONES QUE RESPALDAN TU GESTIÓN» · «CONSULTORÍA | SOFTWARE |
INNOVACIÓN» · «UNA PLATAFORMA, INFINITAS POSIBILIDADES PARA TU GESTIÓN».
Cifras de impacto: +62 ciudades, +700k toneladas al mes, +11k vehículos
conectados, +26M ciudadanos.

## El sistema

| | |
|---|---|
| morado (primario) | `#6E4299` |
| naranja (CTA) | `#F38435` |
| navy casi negro | `#171B25` |
| pizarra oscura | `#282B34` |
| texto | `#383838` |
| gris claro | `#F4F4F4` |

- **Isotipo:** una `U` de trazo grueso, lados rectos, base semicircular y
  extremos cortados a plomo, con un **pin de ubicación naranja** —gota con un
  agujero circular blanco— colgando dentro del contador.
- **Wordmark:** `URBETRACK` en mayúscula, Montserrat, tracking muy abierto.
- **Gráfico de firma:** el degradado morado → naranja, que en el sitio aparece
  como banda separadora, en la franja de cifras y en el footer.
- **Tipografía:** Montserrat 400/500/700/800. Titulares en mayúscula y bold.

## De dónde salió cada cosa

Todo de **urbetrack.com**. La paleta y la tipografía salieron del CSS del sitio
(`--clr-primary`, `--clr-btn-primary`, `--ff-base`), no de mirar una captura.

⚠️ **El logo en color hubo que reconstruirlo.** El sitio sirve el logo de
navegación en **monocromo** (`logo-light.png` todo blanco, `logo-dark.png` todo
`#232323`), y la única versión en color está fotografiada sobre la pantalla del
hero, con perspectiva y velo encima: mala referencia. Lo que se hizo fue tomar la
silueta nítida del monocromo, separar el pin de la U **por componentes conexos**
—son dos islas distintas del canal alfa— y pintar cada una con su color del CSS.
El resultado (`brand/logo-color.png`) es el logo real, nítido y en vector-limpio.

**No se usan los logos de clientes** de la sección "ya confiaron en nosotros"
(municipios, Cliba, LIME, GISA…): son marcas de terceros, no identidad de
Urbetrack.

## Las tres referencias

Una por prompt, porque el script adjunta una sola:

- `board_identidad.png` — logo en color, sobre claro y sobre oscuro, favicon,
  la banda de degradado y la paleta con hex. Va en las piezas gráficas.
- `board_foto.png` — las imágenes de sección del propio sitio. Va en las piezas
  fotográficas: define luz fría, azules y morados, y overlays de datos.
- `board_web.png` — cuatro capturas de la página. Va en las piezas con
  maquetación: jerarquía, mayúsculas, botones naranjas.

## Decisiones que no se re-discuten

- **El prompt arranca por el sistema de marca, no por la pieza.**
- **La composición se describe en porcentajes del cuadro**, no en adjetivos.
- **Las piezas fotográficas piden "realistic corporate photography, not an
  illustration and not a 3D render"**; las gráficas piden "flat vector". Sin esa
  línea el modelo entrega renders 3D genéricos de stock.
- **Los overlays de datos se piden "crisp and flat" sobre foto real**: es el
  recurso visual del sitio y el que distingue estas piezas de una foto de banco.
