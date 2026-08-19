"""Los errores que el runner sabe manejar sin voltear el batch.

Selenium se importa de forma defensiva porque este paquete se carga sin
navegador: la cola, el checkpoint y la verificación de PNG se testean sin
Chrome, y no vale que falte una dependencia opcional para no poder leerlos.
"""

from __future__ import annotations


class GenerationBlocked(RuntimeError):
    """El proveedor pidió intervención humana o la UI no fue reconocida.

    Es la frontera entre "esta imagen no salió" y "algo se rompió de verdad": el
    runner la atrapa, la anota en el checkpoint y sigue con la próxima.
    """


try:  # pragma: no cover - depende del entorno
    from selenium.common.exceptions import (
        StaleElementReferenceException,
        WebDriverException,
    )

    #: "El DOM cambió debajo nuestro", NO "se rompió todo": se reintenta.
    TRANSIENT_DOM_ERRORS: tuple = (StaleElementReferenceException,)
    #: Cualquier otro fallo del navegador. Hunde UNA imagen, no la corrida.
    BROWSER_ERRORS: tuple = (WebDriverException,)
except ImportError:  # pragma: no cover
    TRANSIENT_DOM_ERRORS = ()
    BROWSER_ERRORS = ()
