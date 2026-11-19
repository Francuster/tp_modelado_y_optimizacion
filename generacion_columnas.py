"""Interfaz de compatibilidad; las etapas están implementadas por separado."""

from etapa3 import (
    catalogo_inicial,
    crear_modelo_gc,
    resolver_GC,
    resolver_GC_entero,
    resolver_GC_pricing,
    resolver_GC_relajado,
)
from etapa4 import resolver_GC_nativo

__all__ = [
    "catalogo_inicial",
    "crear_modelo_gc",
    "resolver_GC",
    "resolver_GC_entero",
    "resolver_GC_nativo",
    "resolver_GC_pricing",
    "resolver_GC_relajado",
]
