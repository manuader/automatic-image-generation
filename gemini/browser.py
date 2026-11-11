"""Perfil de Gemini web. Toda la mecánica está en `core/webchat.py`.

Este archivo es la prueba de que la separación es real: lo único propio de Gemini
son una URL, un selector y una lista de frases. Es también el motor **verificado
en producción** — 335 imágenes generadas con él antes de esta migración.
"""

from __future__ import annotations

from core.webchat import WebChatBrowser


class Browser(WebChatBrowser):
    NAME = "gemini"
    DEBUG_PORT = 9222
    HOME_URL = "https://gemini.google.com/"
    #: Se entra por `/app` (sin barra) y la conversación agrega `/app/<id>`, que
    #: es justo lo que confirma que el envío salió.
    NEW_CHAT_URL = "https://gemini.google.com/app"
    CONVERSATION_URL_MARK = "/app/"

    SEND_BUTTON_SELECTORS = [
        ("CSS_SELECTOR", "button[aria-label='Enviar mensaje']"),
        ("CSS_SELECTOR", "button[aria-label='Send message']"),
    ]

    #: El cartel de "generando". Con la cuota de imágenes agotada Gemini lo deja
    #: puesto para siempre en vez de avisar (medido: 10 minutos sin cambio, y con
    #: un prompt trivial sin referencia pasa igual). Ver `_explain_silence`.
    GENERATING_MARKERS = ("creando tu imagen", "creating your image")

    ERROR_PATTERNS = {
        "captcha": "Gemini mostró un CAPTCHA",
        "límite de uso": "Gemini alcanzó su límite de uso",
        "llegaste a tu límite": "Gemini alcanzó su límite de uso",
        # 2026-11-11: con la cuota de imágenes agotada, la respuesta dice
        # «Se alcanzó el límite · Se restablece a la(s) 6:25 p.m.». Sin esto el
        # supervisor lo tomaba como timeout de la imagen y quemaba sus 3 intentos.
        "se alcanzó el límite": "Gemini alcanzó su límite de uso",
        "se alcanzo el limite": "Gemini alcanzó su límite de uso",
        "limit reached": "Gemini alcanzó su límite de uso",
        "try again later": "Gemini pidió reintentar más tarde",
        "something went wrong": "Gemini devolvió un error",
        "no se pudo generar": "Gemini no pudo generar la imagen",
    }

    #: El banner "estás por alcanzar el límite" es preventivo: el chat sigue
    #: generando. Contiene "límite de uso", así que sin descontarlo primero
    #: TODAS las imágenes fallan con "límite alcanzado" y el batch se frena
    #: creyendo que la cuota se agotó.
    BENIGN_NOTICES = (
        "estás por alcanzar el límite de uso",
        "estas por alcanzar el limite de uso",
        "you're approaching your usage limit",
        "youre approaching your usage limit",
    )
