import pytest

from analizador.errores import Fase, GestorErrores
from analizador.lexer import tokenizar
from analizador.parser import Parser


def errores_de(texto):
    """Ejecuta lexer + parser y devuelve los errores léxicos y sintácticos, ordenados.

    Estas pruebas cubren la sintaxis; los errores semánticos (SEM-xx), que aquí
    aparecerían por usar variables sin declarar, se prueban en test_semantica.py.
    """
    g = GestorErrores()
    Parser(tokenizar(texto, g), g).programa()
    return [e.formato() for e in g.ordenados() if e.codigo.fase != Fase.SEMANTICA]


# --- Criterios de aceptación (Tabla 14, fase 4): ejemplos 4, 5 y 6 de la Tabla 8 ---

def test_ejemplo_4_falta_punto_y_coma():
    assert errores_de("int a = 5\na = a + 1;\n") == [
        "[SIN-02] línea 1, columna 10: Falta ';' al final de la sentencia",
    ]


def test_ejemplo_5_llave_sin_cerrar():
    assert errores_de("int n = 3;\nwhile (n > 0) {\n    n = n - 1;\n") == [
        "[SIN-03] línea 2, columna 15: Llave '{' abierta sin cerrar",
    ]


def test_ejemplo_6_parentesis_sin_cerrar():
    assert errores_de("int a = 1;\nif (a > 0 {\n    a = 2;\n}\n") == [
        "[SIN-03] línea 2, columna 11: Paréntesis '(' abierto sin cerrar",
    ]


# --- Programas sintácticamente correctos (ejemplos 1, 2, 7, 8 y 9) ---
# Los ejemplos 7, 8 y 9 solo tienen errores semánticos (ver test_semantica.py).

@pytest.mark.parametrize("texto", [
    "int edad = 18;\nfloat precio = 2.5;\nbool activo = true;\nwhile (edad < 21) {\n    edad = edad + 1;\n}\n",
    "int a = 5;\nfloat b = a * 2.5;\nif (b >= 10.0 && a != 0) {\n    b = b - 1;\n} else {\n    a = a + 1;\n}\n",
    "int a = 1;\nb = a + 2;\n",
    "int x = 1;\nint x = 2;\nbool ok = 3.5;\n",
    "int n = 3;\nwhile (n) {\n    n = n - 1;\n}\n",
])
def test_ejemplos_sin_errores_sintacticos(texto):
    assert errores_de(texto) == []


def test_programa_vacio():
    assert errores_de("") == []


def test_expresiones_con_precedencia_y_parentesis():
    assert errores_de("x = -(a + 2) * 3 % b - !c || d && e == f;") == []


def test_bloques_anidados_y_sueltos():
    assert errores_de("{ int a; { a = 1; } }\nif (x) { while (y) { } } else { }") == []


def test_declaracion_sin_inicializar():
    assert errores_de("bool listo;") == []


# --- SIN-01: token inesperado ---

def test_falta_identificador_en_declaracion():
    assert errores_de("int = 5;") == [
        "[SIN-01] línea 1, columna 5: Se esperaba 'identificador' y se encontró '='",
    ]


def test_falta_asignacion():
    assert errores_de("a 5;") == [
        "[SIN-01] línea 1, columna 3: Se esperaba '=' y se encontró '5'",
    ]


def test_falta_expresion():
    assert errores_de("a = ;") == [
        "[SIN-01] línea 1, columna 5: Se esperaba una expresión y se encontró ';'",
    ]


def test_sentencia_no_valida():
    assert errores_de("5 = a;") == [
        "[SIN-01] línea 1, columna 1: Sentencia no válida: se encontró '5'",
    ]


def test_else_sin_if():
    assert errores_de("else { }") == [
        "[SIN-01] línea 1, columna 1: Sentencia no válida: se encontró 'else'",
    ]


def test_llave_de_cierre_sobrante():
    assert errores_de("a = 1;\n}") == [
        "[SIN-01] línea 2, columna 1: Llave '}' sin su '{' correspondiente",
    ]


def test_if_exige_llaves():
    assert errores_de("if (a) b = 1;") == [
        "[SIN-01] línea 1, columna 8: Se esperaba '{' y se encontró 'b'",
    ]


def test_relacionales_no_se_encadenan():
    errores = errores_de("x = a < b < c;")
    assert errores[0] == "[SIN-02] línea 1, columna 10: Falta ';' al final de la sentencia"


# --- Recuperación: sin errores en cascada ---

def test_tras_un_error_la_siguiente_sentencia_se_analiza_normal():
    assert errores_de("a = ;\nb = 2;\nc = ;") == [
        "[SIN-01] línea 1, columna 5: Se esperaba una expresión y se encontró ';'",
        "[SIN-01] línea 3, columna 5: Se esperaba una expresión y se encontró ';'",
    ]


def test_error_dentro_de_un_bloque_no_rompe_el_bloque():
    assert errores_de("while (x) {\n    a = ;\n    b = 1;\n}\nc = 2;") == [
        "[SIN-01] línea 2, columna 9: Se esperaba una expresión y se encontró ';'",
    ]


def test_varios_punto_y_coma_faltantes():
    assert errores_de("a = 1\nb = 2\nc = 3;") == [
        "[SIN-02] línea 1, columna 6: Falta ';' al final de la sentencia",
        "[SIN-02] línea 2, columna 6: Falta ';' al final de la sentencia",
    ]


def test_errores_lexicos_y_sintacticos_juntos():
    assert errores_de("int precio$ = 10\nx = 1;") == [
        "[LEX-01] línea 1, columna 11: Carácter no válido '$'",
        "[SIN-02] línea 1, columna 17: Falta ';' al final de la sentencia",
    ]