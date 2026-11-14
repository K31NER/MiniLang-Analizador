from enum import StrEnum
from typing import Final
from analizador.tokens import TipoToken

class Tipo(StrEnum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"

# Palabra de la declaración -> tipo de la variable (int x, float y, bool z)
TIPO_DECLARADO: Final[dict[TipoToken, Tipo]] = {
    TipoToken.PR_INT: Tipo.INT,
    TipoToken.PR_FLOAT: Tipo.FLOAT,
    TipoToken.PR_BOOL: Tipo.BOOL,
}

# Operadores agrupados según la Tabla 6 (se comparan por lexema)
ARITMETICOS: Final[frozenset[str]] = frozenset({"+", "-", "*", "/", "%"})
RELACIONALES: Final[frozenset[str]] = frozenset({"<", ">", "<=", ">="})
IGUALDAD: Final[frozenset[str]] = frozenset({"==", "!="})
LOGICOS: Final[frozenset[str]] = frozenset({"&&", "||"})


def es_numerico(t: Tipo) -> bool:
    """True si el tipo es int o float."""
    return t in (Tipo.INT, Tipo.FLOAT)


def compatible(destino: Tipo, origen: Tipo) -> bool:
    """Regla de asignación: mismo tipo, o un float que recibe un int."""
    return destino == origen or (destino == Tipo.FLOAT and origen == Tipo.INT)


def resultado(op: str, a: Tipo, b: Tipo) -> Tipo | None:
    """Tipo resultante de 'a op b', o None si la combinación no está permitida."""
    if op in ARITMETICOS:
        if es_numerico(a) and es_numerico(b):
            return Tipo.FLOAT if Tipo.FLOAT in (a, b) else Tipo.INT
        return None

    if op in RELACIONALES:
        return Tipo.BOOL if es_numerico(a) and es_numerico(b) else None

    if op in IGUALDAD:
        if (es_numerico(a) and es_numerico(b)) or (a == Tipo.BOOL and b == Tipo.BOOL):
            return Tipo.BOOL
        return None

    if op in LOGICOS:
        return Tipo.BOOL if a == Tipo.BOOL and b == Tipo.BOOL else None

    raise ValueError(f"Operador binario desconocido: {op!r}")


def resultado_unario(op: str, a: Tipo) -> Tipo | None:
    """Tipo resultante de '!a' o '-a', o None si no está permitido."""
    if op == "!":
        return Tipo.BOOL if a == Tipo.BOOL else None

    if op == "-":
        return a if es_numerico(a) else None

    raise ValueError(f"Operador unario desconocido: {op!r}")