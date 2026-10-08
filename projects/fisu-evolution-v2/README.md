# fisu-evolution-v2 — cómo correrlo

222 prompts para el arte de la 2.0. Qué son y por qué están así: `OBJETIVO.md`. El orden:
`prompts/00_INDICE.md`.

> ⚠️ **El piloto y el lote se corren con la app de Claude CERRADA** (cerrada, no minimizada):
> le roba el foco al tipeo del navegador. Está medido.

Todos los comandos van desde la raíz del repo:

```bash
cd ~/Desktop/projects/automatic-image-generation
```

## 1. Login (una vez)

```bash
.venv/bin/python generate.py --engine chat-gpt --launch
```

Abre el Chrome aislado de ChatGPT (puerto 9223). Iniciá sesión en **esa** ventana y dejala
abierta.

## 2. Probe (cuota cero)

Escribí una palabra a mano en el cuadro de ChatGPT de esa ventana, sin enviarla, y corré:

```bash
.venv/bin/python generate.py --engine chat-gpt --probe
```

Tienen que aparecer el cuadro de texto y un `send_button` distinto de `null`. Si sale `null`,
se corrige una línea de `chat-gpt/browser.py` (el archivo explica cuál). Después borrá la palabra.

## 3. Piloto (5 imágenes)

```bash
for k in npc_comisario npc_vecina npc_comisario_talk homeless__dinosaurio bg_alley; do
  .venv/bin/python generate.py --project fisu-evolution-v2 --only "$k"
done
```

Mirá `projects/fisu-evolution-v2/output/` antes de seguir:

| Imagen | Pasa si… |
|---|---|
| `npc_comisario`, `npc_vecina` | Tienen el trazo, el contorno negro, el sombreado y la proporción cabeza/cuerpo de `references/fisura.png`. No tienen texto ni insignias, y el fondo es blanco liso. |
| `npc_comisario_talk` | Es el mismo comisario de la canónica (cara, bigote, uniforme), cambió sólo la pose y no hay globo dibujado. |
| `homeless__dinosaurio` | Se reconoce a El Fisura (cara bizca, botella) adentro del disfraz, y el estilo no se despega de sus skins de la v1. |
| `bg_alley` | Tiene la misma composición que `references/bg/bg_alley.png`, con más detalle. Medí el tamaño: `sips -g pixelWidth projects/fisu-evolution-v2/output/bg_alley.png`. |

Si una imagen falla, el motivo queda en `state/run.json`. Volver a correr el mismo `for` sólo
pide lo que falta.

## 4. Lote (las 217 restantes)

```bash
.venv/bin/python generate.py --project fisu-evolution-v2
```

La cola saltea lo que ya está en `output/`, así que un corte (Ctrl-C, cuota, logout) se retoma
con el mismo comando.

## Plan B: `gemini`

Los mismos prompts, con el motor verificado en las 335 imágenes de la v1:

```bash
.venv/bin/python generate.py --engine gemini --launch          # login en SU Chrome (puerto 9222)
.venv/bin/python generate.py --project fisu-evolution-v2 --engine gemini
```

**Si la deriva aparece sólo en la skin del piloto**, el resto sale con ChatGPT y las familias
(100–227, al final de la cola) con Gemini:

```bash
.venv/bin/python generate.py --project fisu-evolution-v2 --dry-run --limit 89   # tiene que terminar en 098_bg_god_realm
.venv/bin/python generate.py --project fisu-evolution-v2 --limit 89
.venv/bin/python generate.py --project fisu-evolution-v2 --engine gemini
```

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `timeout esperando la imagen generada (distinta de la referencia)` en una pose, una skin o un fondo | El resultado se parece mucho a su referencia y el filtro se lo comió. Mirá `state/discards/` y reintentá esa clave con `--only <clave> --ref-threshold 2`. |
| `falta la referencia …/output/npc_….png` | La canónica de ese visitante no salió. Generala primero: la pose y la cara la adjuntan. |
| El fondo sale a 1024 px | ChatGPT no entrega 2048 en ese chat. No lo agrandes acá: avisá, porque es una decisión del plan (§2, "Fondos"). |

Lo que sale va a `output/<clave>.png` (crudo) y a `output/assets/` (sin fondo, a 384 y 512). Los
**fondos se integran desde el crudo**. La integración al juego (`dropbox/` → `process_dropbox.py`,
con las categorías `npc` y `skinfam`) es otra tarea.
