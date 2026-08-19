"""Perfil de ChatGPT web. Toda la mecánica está en `core/webchat.py`.

⚠️ **Este motor está escrito pero NO verificado contra el sitio.** No es lo mismo
que "no funciona": la mecánica que hace el trabajo pesado —el tipeo por tandas,
la recuperación de foco, el paste de la referencia, la extracción por canvas— es
exactamente la misma que generó 335 imágenes con Gemini, y no tiene nada de
Google adentro. Lo que no pude comprobar son las cuatro constantes de acá abajo,
porque comprobarlas exige abrir el navegador y este entorno no tiene el permiso
de Accesibilidad que macOS pide para mandar teclas.

Verificarlas cuesta un comando y CERO cuota:

    python3 generate.py --engine chat-gpt --launch     # una vez, para loguearse
    python3 generate.py --engine chat-gpt --probe

`--probe` abre el chat, dice si encontró el cuadro de texto y el botón de enviar
y con qué etiqueta, y no escribe ni envía nada. Si alguno sale `null`, lo que hay
que corregir es UNA línea de este archivo:

- `NEW_CHAT_URL` / `CONVERSATION_URL_MARK`: mirá la barra de direcciones antes y
  después de mandar un mensaje a mano. Hoy asume `chatgpt.com` → `chatgpt.com/c/<id>`.
- `SEND_BUTTON_SELECTORS`: el `data-testid` es el más estable de los tres; los
  `aria-label` cambian con el idioma de la cuenta.
- `ERROR_PATTERNS`: son las frases con las que el sitio dice "no puedo". Agregá
  la que te aparezca; de más se paga caro (frena el batch de gusto), de menos
  también (sigue mandando prompts contra una cuota agotada).

El cuadro de texto no está en la lista porque lo cubre el selector genérico:
ChatGPT usa un editor contenteditable, igual que Gemini.
"""

from __future__ import annotations

from core.webchat import WebChatBrowser


class Browser(WebChatBrowser):
    NAME = "chat-gpt"
    HOME_URL = "https://chatgpt.com/"
    NEW_CHAT_URL = "https://chatgpt.com/"
    #: La conversación nueva cuelga de `/c/<uuid>`, así que este substring
    #: aparece recién cuando el envío salió — que es lo que se le pide.
    CONVERSATION_URL_MARK = "/c/"

    #: En orden de estabilidad: el testid sobrevive a los cambios de idioma, los
    #: aria-label no.
    SEND_BUTTON_SELECTORS = [
        ("CSS_SELECTOR", "button[data-testid='send-button']"),
        ("CSS_SELECTOR", "button[aria-label='Send prompt']"),
        ("CSS_SELECTOR", "button[aria-label='Enviar mensaje']"),
        ("CSS_SELECTOR", "button[aria-label='Enviar prompt']"),
    ]

    ERROR_PATTERNS = {
        "captcha": "ChatGPT mostró un CAPTCHA",
        "unusual activity": "ChatGPT marcó la sesión como actividad inusual",
        "you've reached your limit": "ChatGPT alcanzó su límite de uso",
        "youve reached your limit": "ChatGPT alcanzó su límite de uso",
        "alcanzaste tu límite": "ChatGPT alcanzó su límite de uso",
        "too many requests": "ChatGPT pidió esperar por exceso de pedidos",
        "something went wrong": "ChatGPT devolvió un error",
        "se produjo un error": "ChatGPT devolvió un error",
    }

    #: Mismo problema que en Gemini y misma solución: el aviso preventivo
    #: comparte substring con el bloqueo real y sin descontarlo primero frenaría
    #: el batch con la cuota intacta.
    BENIGN_NOTICES = (
        "you're approaching your limit",
        "youre approaching your limit",
        "estás por alcanzar tu límite",
        "estas por alcanzar tu limite",
    )
