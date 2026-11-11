# football-evolution-piloto — la compuerta de estilo del dueño (E18-F6)

Antes de gastar 420 imágenes, los **mismos 10 prompts** se generan en Gemini y en ChatGPT y el dueño compara la hoja
de contactos lado a lado. **Frena hasta su OK.** Si los dos motores no dan el mismo estilo, se ajustan la biblia y las
referencias de `projects/football-evolution/` (y se vuelven a copiar acá) y se repite.

- Los prompts, la biblia de estilo, la paleta y la lista negra legal son los de `projects/football-evolution/`
  (`OBJETIVO.md` de ese proyecto). Los `.md` de acá son copias exactas; el orden está en `prompts/00_INDICE.md`.
- Qué cubre: 4 personajes (el 04 es el cuarto de un piso), 2 skins, 1 fondo, 1 ícono de UI, el guía y el Dios.
- Referencias: `references/protagonista_hoja.png` (personajes) y `references/pantalla.png` (UI y fondo), las mismas.

## Cómo se corre: dos corridas con `--engine`, la salida separada por motor

La cola saltea todo lo que ya tiene PNG en `output/` o dice `hecho` en el `.md`, así que entre las dos corridas se
aparta la salida y se devuelven los `.md` a `pendiente`. Desde la raíz del repo:

```bash
# 0. una vez: el dueño se loguea en las dos ventanas aisladas
.venv/bin/python generate.py --engine gemini --launch
.venv/bin/python generate.py --engine chat-gpt --launch
.venv/bin/python generate.py --project football-evolution-piloto --dry-run      # 10 en la cola

# 1. Gemini
.venv/bin/python generate.py --project football-evolution-piloto --engine gemini
mv projects/football-evolution-piloto/output projects/football-evolution-piloto/output-gemini
mv projects/football-evolution-piloto/state  projects/football-evolution-piloto/state-gemini
git checkout -- projects/football-evolution-piloto/prompts                        # los 10 vuelven a «pendiente»

# 2. ChatGPT
.venv/bin/python generate.py --project football-evolution-piloto --engine chat-gpt
mv projects/football-evolution-piloto/output projects/football-evolution-piloto/output-chat-gpt
mv projects/football-evolution-piloto/state  projects/football-evolution-piloto/state-chat-gpt
git checkout -- projects/football-evolution-piloto/prompts
```

Quedan `output-gemini/` y `output-chat-gpt/`, cada uno con los 10 originales y sus `assets/` recortados; `output-*/`
y `state-*/` no se versionan (`.gitignore`). La hoja de contactos lado a lado se arma con los dos `output-*/<clave>.png`
y va al dueño apenas está.

Qué mirar al comparar: los cuatro rasgos del protagonista en las 7 imágenes donde aparece (remolino, pecas, curita en la
rodilla IZQUIERDA, botines lima), que el 04 se vea mucho más destacado que el 02, que la skin 05 conserve la silueta del
04, el Dios sin número, sin rulos y sin celeste y blanca, y la lista negra legal en todas. Desde la corrección del
dueño del 2026-11-11 (~15:30), además la regla de recorte de la biblia: nada bajo ni alrededor de los pies (ni base,
ni nubes, ni sombra), nada de blanco puro dentro del personaje (crema) y nada fuera de la silueta (ni aura, ni
destellos); el 04 destaca por la ropa, la pose y los materiales.
