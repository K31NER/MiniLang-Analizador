"""API pública del analizador de MiniLang (sección 7.1).

Las interfaces (consola y gráfica) solo usan analizar(); nunca importan
el lexer ni el parser directamente.
"""
from analizador.errores import CodigoError, Error, Fase, GestorErrores
from analizador.lexer import tokenizar
from analizador.parser import Parser

__all__ = ["analizar", "Error", "CodigoError", "Fase"]


def analizar(texto: str) -> list[Error]:
    """Analiza un programa MiniLang y devuelve sus errores ordenados por posición."""
    errores = GestorErrores()
    tokens = tokenizar(texto, errores)
    Parser(tokens, errores).programa()
    return errores.ordenados()