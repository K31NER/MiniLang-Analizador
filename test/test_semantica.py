"""Fase semántica integrada en el parser (sección 6.6, Tablas 6, 7 y 8)."""
import pytest

from analizador import analizar


def errores_de(texto):
    return [e.formato() for e in analizar(texto)]


# --- Criterios de aceptación: ejemplos 7, 8 y 9 de la Tabla 8 ---

def test_ejemplo_7_variable_no_declarada():
    assert errores_de("int a = 1;\nb = a + 2;\n") == [
        "[SEM-01] línea 2, columna 1: Variable 'b' no declarada",
    ]


def test_ejemplo_8_declaracion_doble_y_tipos():
    assert errores_de("int x = 1;\nint x = 2;\nbool ok = 3.5;\n") == [
        "[SEM-02] línea 2, columna 5: La variable 'x' ya fue declarada en este ámbito",
        "[SEM-03] línea 3, columna 11: No se puede asignar un valor float a una variable bool",
    ]


def test_ejemplo_9_condicion_no_booleana():
    assert errores_de("int n = 3;\nwhile (n) {\n    n = n - 1;\n}\n") == [
        "[SEM-05] línea 2, columna 8: La condición debe ser bool y es int",
    ]


@pytest.mark.parametrize("texto", [
    "int edad = 18;\nfloat precio = 2.5;\nbool activo = true;\nwhile (edad < 21) {\n    edad = edad + 1;\n}\n",
    "int a = 5;\nfloat b = a * 2.5;\nif (b >= 10.0 && a != 0) {\n    b = b - 1;\n} else {\n    a = a + 1;\n}\n",
])
def test_ejemplos_validos_1_y_2(texto):
    assert errores_de(texto) == []


# --- SEM-01: uso dentro de expresiones ---

def test_variable_no_declarada_en_expresion():
    assert errores_de("int a = c + 1;") == [
        "[SEM-01] línea 1, columna 9: Variable 'c' no declarada",
    ]


# --- Ámbitos ---

def test_variable_de_bloque_deja_de_existir_al_cerrarlo():
    assert errores_de("{ int t = 1; }\nt = 2;") == [
        "[SEM-01] línea 2, columna 1: Variable 't' no declarada",
    ]


def test_bloque_interno_puede_ocultar_variable_externa():
    assert errores_de("int x = 1;\n{ bool x = true; x = false; }\nx = 2;") == []


def test_variable_externa_visible_dentro_del_bloque():
    assert errores_de("float y = 1.0;\nwhile (y < 3.0) { y = y + 1; }") == []


# --- SEM-03: asignación e inicialización (Tabla 6) ---

def test_float_recibe_int_por_ampliacion():
    assert errores_de("float f = 3;") == []


def test_int_no_recibe_float():
    assert errores_de("int i = 0;\ni = 2.5;") == [
        "[SEM-03] línea 2, columna 5: No se puede asignar un valor float a una variable int",
    ]


# --- SEM-04: operadores (Tabla 6) ---

@pytest.mark.parametrize("texto, esperado", [
    ("bool b = true + 1;",
     "[SEM-04] línea 1, columna 15: El operador '+' no admite operandos de tipo bool y int"),
    ("bool b = true < 1;",
     "[SEM-04] línea 1, columna 15: El operador '<' no admite operandos de tipo bool y int"),
    ("bool b = 1 == true;",
     "[SEM-04] línea 1, columna 12: El operador '==' no admite operandos de tipo int y bool"),
    ("bool b = 1 && true;",
     "[SEM-04] línea 1, columna 12: El operador '&&' no admite operandos de tipo int y bool"),
    ("bool b = !1;",
     "[SEM-04] línea 1, columna 10: El operador '!' no admite un operando de tipo int"),
    ("int i = -true;",
     "[SEM-04] línea 1, columna 9: El operador '-' no admite un operando de tipo bool"),
])
def test_operadores_con_tipos_no_permitidos(texto, esperado):
    assert errores_de(texto) == [esperado]


@pytest.mark.parametrize("texto", [
    "float r = 1 + 2.5;",
    "int r = 7 % 2;",
    "bool r = 1 < 2.5;",
    "bool r = true == false;",
    "bool r = 1 != 2.0;",
    "bool r = true || false && !true;",
    "float r = -2.5;",
])
def test_operadores_con_tipos_permitidos(texto):
    assert errores_de(texto) == []


def test_aritmetica_de_floats_no_cabe_en_int():
    assert errores_de("int r = 1 + 2.5;") == [
        "[SEM-03] línea 1, columna 9: No se puede asignar un valor float a una variable int",
    ]


# --- SEM-05 en if ---

def test_condicion_de_if_no_booleana():
    assert errores_de("float f = 1.0;\nif (f) { }") == [
        "[SEM-05] línea 2, columna 5: La condición debe ser bool y es float",
    ]


# --- Sin errores en cascada ---

def test_expresion_con_error_no_genera_mas_errores():
    # 'c' no existe: solo SEM-01; ni '+' ni la asignación ni la condición reportan algo más.
    assert errores_de("int a = 1;\na = c + 1;\nwhile (c > 0) { }") == [
        "[SEM-01] línea 2, columna 5: Variable 'c' no declarada",
        "[SEM-01] línea 3, columna 8: Variable 'c' no declarada",
    ]


def test_declaracion_con_error_sintactico_igual_declara_la_variable():
    assert errores_de("int x = ;\nx = 2;") == [
        "[SIN-01] línea 1, columna 9: Se esperaba una expresión y se encontró ';'",
    ]


def test_las_tres_fases_juntas_ordenadas():
    assert errores_de("int a$ = 1\nb = a;\nwhile (a) { }") == [
        "[LEX-01] línea 1, columna 6: Carácter no válido '$'",
        "[SIN-02] línea 1, columna 11: Falta ';' al final de la sentencia",
        "[SEM-01] línea 2, columna 1: Variable 'b' no declarada",
        "[SEM-05] línea 3, columna 8: La condición debe ser bool y es int",
    ]
