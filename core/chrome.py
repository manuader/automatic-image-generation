"""Abre el chat en un Chrome aislado y depurable por Selenium.

Aislado y no el Chrome de todos los días por dos razones que se pagan caro si se
mezclan: el perfil guarda la sesión del chat sin tocar la personal, y una ventana
dedicada es la que puede quedarse al frente durante todo un batch sin que el
dueño pierda su navegador.

Un perfil por motor: así se puede tener la sesión de Gemini y la de ChatGPT
abiertas a la vez sin que una desloguee a la otra.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 9222
PROFILES = ROOT / ".chrome-profile"


def debug_url(port: int = DEFAULT_PORT) -> str:
    return f"http://127.0.0.1:{port}/json/version"


def profile_for(engine: str) -> Path:
    return PROFILES / engine


def chrome_binary() -> str:
    """Encuentra Chrome estable en macOS, Linux o PATH."""
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("Google Chrome"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise RuntimeError("No encontré Google Chrome. Instalalo y volvé a correr el launcher.")


def chrome_command(profile: Path, url: str, port: int = DEFAULT_PORT) -> list[str]:
    return [
        chrome_binary(),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={Path(profile)}",
        "--no-first-run",
        "--no-default-browser-check",
        url,
    ]


def targets_url(port: int = DEFAULT_PORT) -> str:
    return f"http://127.0.0.1:{port}/json"


def debug_is_ready(port: int = DEFAULT_PORT) -> bool:
    """¿Hay un Chrome USABLE en este puerto?

    Usable quiere decir dos cosas y hasta el 2026-08-20 se comprobaba una sola.
    Que el endpoint conteste no alcanza: si al Chrome aislado le cierran la
    última ventana, el proceso sigue vivo y `/json/version` sigue devolviendo
    200, pero `/json` devuelve CERO targets y Selenium no puede engancharse
    —"unable to discover open pages"—. Con el chequeo viejo `--launch` daba por
    bueno ese Chrome fantasma y no abría nada, así que el batch fallaba imagen
    tras imagen contra un navegador sin páginas y el mensaje mandaba a correr
    justo el comando que acababa de no hacer nada.
    """
    try:
        with urlopen(debug_url(port), timeout=1) as response:
            if response.status != 200:
                return False
        with urlopen(targets_url(port), timeout=1) as response:
            if response.status != 200:
                return False
            return any(
                target.get("type") == "page"
                for target in json.loads(response.read().decode("utf-8"))
            )
    except (URLError, TimeoutError, OSError, ValueError):
        return False


def ensure_debug_chrome(url: str, profile: Path, port: int = DEFAULT_PORT) -> bool:
    """Devuelve True si lo lanzó; False si ya había un Chrome depurable."""
    if debug_is_ready(port):
        return False
    profile = Path(profile)
    profile.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        chrome_command(profile, url, port),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if debug_is_ready(port):
            return True
        time.sleep(0.25)
    raise RuntimeError(
        f"Chrome abrió pero no expuso {debug_url(port)} en 20 segundos. "
        "Cerrá la ventana aislada y reintentá."
    )
