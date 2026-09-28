"""Perfil de ChatGPT web. Toda la mecánica está en `core/webchat.py`.

Lo que **sí** se comprobó contra el sitio (2026-08-19, abriendo la página):

- `chatgpt.com` carga sin redirigir, así que `NEW_CHAT_URL` es esa;
- el cuadro de texto es `#prompt-textarea`, un ProseMirror contenteditable, y lo
  encuentra el selector genérico de `COMPOSE_SELECTORS` — no hace falta uno propio;
- **`send_keys` de Selenium NO aterriza en ese editor**: se tipeó "hola" y el
  composer quedó vacío. Es exactamente el fallo que obligó al camino de
  osascript en Gemini, así que la mecánica compartida es la que corresponde acá
  también. Ésta era la suposición grande y quedó confirmada.

Lo que **no** se pudo comprobar, y por qué: el botón de enviar no existe con el
composer vacío —en su lugar está `composer-speech-button`—, y revelarlo exige
tipear DE VERDAD, o sea el permiso de Accesibilidad de macOS que el entorno que
escribió esto no tiene. Los `data-testid` de esa barra siguen todos el patrón
`composer-*` (`composer-plus-btn`, `composer-speech-button`), y por eso
`composer-submit-button` va primero en la lista y `send-button` queda de reserva.

Verificarlo cuesta un comando y CERO cuota:

    python3 generate.py --engine chat-gpt --launch     # una vez, para loguearse
    python3 generate.py --engine chat-gpt --probe      # con algo escrito a mano

`--probe` abre el chat, dice si encontró el cuadro de texto y el botón de enviar
y con qué etiqueta, y no escribe ni envía nada. Si `send_button` sale `null` con
el composer vacío, eso es lo esperado; escribí una palabra a mano en esa ventana
y volvé a correrlo. Si sigue `null`, lo que hay que corregir es UNA línea:

- `SEND_BUTTON_SELECTORS`: el `data-testid` es el más estable de los cuatro; los
  `aria-label` cambian con el idioma de la cuenta.
- `CONVERSATION_URL_MARK`: mirá la barra de direcciones después de mandar un
  mensaje a mano. Hoy asume `chatgpt.com` → `chatgpt.com/c/<id>`.
- `ERROR_PATTERNS`: son las frases con las que el sitio dice "no puedo". Agregá
  la que te aparezca; de más se paga caro (frena el batch de gusto), de menos
  también (sigue mandando prompts contra una cuota agotada).
"""

from __future__ import annotations

from core.webchat import WebChatBrowser


class Browser(WebChatBrowser):
    NAME = "chat-gpt"
    #: Distinto del de Gemini a propósito: cada motor abre SU Chrome.
    DEBUG_PORT = 9223
    HOME_URL = "https://chatgpt.com/"
    NEW_CHAT_URL = "https://chatgpt.com/"
    #: La conversación nueva cuelga de `/c/<uuid>`, así que este substring
    #: aparece recién cuando el envío salió — que es lo que se le pide.
    CONVERSATION_URL_MARK = "/c/"

    #: 2026-09-10: ChatGPT toma `Input.insertText` de CDP como input de verdad
    #: en su ProseMirror [SUPUESTO hasta verificarlo en vivo; `send_keys` NO
    #: entraba]. Con esto el motor no necesita el permiso de Accesibilidad ni la
    #: máquina quieta.
    TYPING = "cdp"

    #: El HTML de ChatGPT trae en scripts los textos de TODA la interfaz, entre
    #: ellos "You've reached your limit of {active_limit} active tasks": leído
    #: del `page_source`, frenaba cada imagen con la cuota intacta. Se mira sólo
    #: lo que se ve (2026-09-10).
    BLOCK_SCAN = "visible"

    #: Las imágenes de la respuesta son `loading="lazy"`: con la ventana tapada no
    #: se cargan y miden 0x0, así que se bajan con `fetch` desde la pestaña. Así
    #: se perdieron `bg_geom`, `bg_disc` y `bg_world` aunque ChatGPT las generó.
    FETCH_IN_PAGE = True

    #: Los `<input type=file>` del composer aceptan `multiple`: las referencias
    #: suben juntas y sin portapapeles. Observados el 2026-09-10 con la página
    #: deslogueada; `upload-files` es el id histórico del composer de escritorio.
    FILE_INPUT_SELECTORS = [
        ("CSS_SELECTOR", "input#upload-files"),
        ("CSS_SELECTOR", "input#octane-mobile-composer-files-input"),
        ("CSS_SELECTOR", "input[type='file'][multiple][accept*='image']"),
    ]

    #: El botón de frenar existe mientras ChatGPT genera; la imagen se pinta de a
    #: poco, y una extracción temprana guarda la versión borrosa.
    GENERATING_SELECTORS = [
        ("CSS_SELECTOR", "button[data-testid='stop-button']"),
        ("CSS_SELECTOR", "button[data-testid='composer-stop-button']"),
        ("CSS_SELECTOR", "button[aria-label='Stop streaming']"),
        ("CSS_SELECTOR", "[data-testid='image-gen-loading-state']"),
    ]

    #: Las imágenes que puede haber generado ChatGPT: las de los turnos que
    #: vienen DESPUÉS del último mensaje del usuario, nunca las de sus mensajes.
    #: El 2026-09-10 el extractor agarró la referencia adjunta (ChatGPT la
    #: recomprime: MAE 4.94, por encima del umbral de 4) segundos después de
    #: enviar, cuando el botón de frenar todavía no existía. Los turnos de
    #: imagen del asistente no llevan `data-message-author-role`, así que se
    #: reconocen por no ser del usuario.
    #: 2026-09-28: los turnos dejaron de tener `data-testid=conversation-turn-*`
    #: (0 turnos en la página) y el extractor no veía nada. La imagen generada
    #: sí trae `alt="Generated image N"`, y la adjunta `alt="User attachment"`:
    #: si hay generadas se usan ésas, mientras no haya un botón de frenar.
    RESULT_IMAGES_JS = """
        const generating = document.querySelector('[data-testid=image-gen-loading-state], button[data-testid*=stop], button[aria-label^=Stop]');
        const generated = [...document.querySelectorAll('img[alt^="Generated image"]')];
        if (generated.length) return generating ? [] : generated.slice(-1);
        const turns = [...document.querySelectorAll('[data-testid^=conversation-turn-]')];
        let lastUser = -1;
        turns.forEach((t, i) => { if (t.querySelector('[data-message-author-role=user]')) lastUser = i; });
        const answer = turns.slice(lastUser + 1);
        if (answer.some(t => t.querySelector('[data-testid=image-gen-loading-state]'))) return [];
        return answer.flatMap(t => [...t.querySelectorAll('img')]);
    """

    def _result_images(self) -> list:
        return self._driver().execute_script(self.RESULT_IMAGES_JS) or []

    #: En orden de estabilidad: el testid sobrevive a los cambios de idioma, los
    #: aria-label no.
    SEND_BUTTON_SELECTORS = [
        ("CSS_SELECTOR", "button[data-testid='composer-submit-button']"),
        ("CSS_SELECTOR", "button[data-testid='send-button']"),
        ("CSS_SELECTOR", "button[aria-label='Send prompt']"),
        #: 2026-09-28: el botón quedó sin data-testid y con aria-label "Send".
        ("CSS_SELECTOR", "button[aria-label='Send']"),
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
