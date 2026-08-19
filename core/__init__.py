"""Núcleo del generador: todo lo que no depende ni del proveedor ni del proyecto.

Tres capas, y esta es la de abajo:

- `core/`      cola, checkpoint, verificación de PNG, post-proceso y la mecánica
               de manejar un chat web desde macOS. No sabe qué modelo se usa ni
               para qué son las imágenes.
- `gemini/`, `chat-gpt/`  un archivo por proveedor: URLs, selectores y frases de
               error. Nada más.
- `projects/`  los prompts, las referencias y la salida de cada objetivo.
"""
