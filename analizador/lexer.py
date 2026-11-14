import re
from typing import Final

from analizador.errores import CodigoError, GestorErrores
from analizador.tokens import RESERVADAS, TipoToken, Token

ESPEC: Final[list[tuple[str, str]]] = [
    ("COMENTARIO", r"//[^\n]*"),
    ("ESPACIO",    r"[ \t\r]+"),
    ("NL",         r"\n"),
    ("NUM_FLOAT",  r"[0-9]+\.[0-9]+"),
    ("NUM_INT",    r"[0-9]+"),
    ("ID",         r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OP_REL",     r"==|!=|<=|>=|<|>"),
    ("OP_LOG",     r"&&|\|\||!"),
    ("ASIGNA",     r"="),
    ("OP_ARIT",    r"[+\-*/%]"),
    ("PAR_IZQ",    r"\("),
    ("PAR_DER",    r"\)"),
    ("LLAVE_IZQ",  r"\{"),
    ("LLAVE_DER",  r"\}"),
    ("PUNTOCOMA",  r";"),
    ("INVALIDO",   r"."),  # siempre de último
]

MAESTRA: Final[re.Pattern[str]] = re.compile("|".join(f"(?P<{n}>{p})" for n, p in ESPEC))

def tokenizar(texto:str, errores: GestorErrores) -> list[Token]:
    tokens: list[Token] = []
    linea = 1
    inicio_linea = 0
    
    # Analizamos la entrada
    for m in MAESTRA.finditer(texto):
        grupo = m.lastgroup
        lexema = m.group()
        columna = m.start() - inicio_linea + 1
        
        if grupo == "NL":
            # Salto de linea
            linea += 1
            inicio_linea = m.end()
        
        elif grupo in ("ESPACIO", "COMENTARIO"):
            # Se descartan (Ignoramos)
            pass  
        
        elif grupo == "INVALIDO":
            # Registramos el error
            errores.registrar(CodigoError.LEX_01, linea, columna, f"Carácter no válido '{lexema}'")
            
        elif grupo == "ID":
            # Registamos el token de tipo id
            tipo = RESERVADAS.get(lexema, TipoToken.ID)
            tokens.append(Token(tipo, lexema, linea, columna))
            
        else:
            # Registramos el resto de tokens
            tokens.append(Token(TipoToken[grupo], lexema, linea, columna))
    
    # Registramos el token de cierre
    tokens.append(Token(TipoToken.EOF, "", linea, len(texto) - inicio_linea + 1))
    return tokens
        