from enum import StrEnum
from typing import Final
from dataclasses import dataclass

class TipoToken(StrEnum):
    # Palabras reservadas
    PR_INT = "PR_INT"
    PR_FLOAT = "PR_FLOAT"
    PR_BOOL = "PR_BOOL"
    PR_IF = "PR_IF"
    PR_ELSE = "PR_ELSE"
    PR_WHILE = "PR_WHILE"
    PR_TRUE = "PR_TRUE"
    PR_FALSE = "PR_FALSE"
    
    # Identificadores y literales
    ID = "ID"
    NUM_INT = "NUM_INT"
    NUM_FLOAT = "NUM_FLOAT"
    
    # Operadores
    OP_ARIT = "OP_ARIT"
    OP_REL = "OP_REL"
    OP_LOG = "OP_LOG"
    ASIGNA = "ASIGNA"
    
    # Delimitadores
    PAR_IZQ = "PAR_IZQ"
    PAR_DER = "PAR_DER"
    LLAVE_IZQ = "LLAVE_IZQ"
    LLAVE_DER = "LLAVE_DER"
    PUNTOCOMA = "PUNTOCOMA"
    
    # Fin de archivo
    EOF = "EOF"

RESERVADAS: Final[dict[str, TipoToken]] = {
    "int": TipoToken.PR_INT,
    "float": TipoToken.PR_FLOAT,
    "bool": TipoToken.PR_BOOL,
    "if": TipoToken.PR_IF,
    "else": TipoToken.PR_ELSE,
    "while": TipoToken.PR_WHILE,
    "true": TipoToken.PR_TRUE,
    "false": TipoToken.PR_FALSE,
}

TIPOS_DATO: Final[frozenset[TipoToken]] = frozenset(
    {TipoToken.PR_INT, TipoToken.PR_FLOAT, TipoToken.PR_BOOL}
)

@dataclass(frozen=True)
class Token:
    tipo: TipoToken
    lexema: str
    linea: int
    columna: int
    
    @property
    def fin(self) -> int:
        return self.columna + len(self.lexema)

