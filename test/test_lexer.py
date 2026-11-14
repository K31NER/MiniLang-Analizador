from analizador.errores import CodigoError, GestorErrores
from analizador.lexer import tokenizar
from analizador.tokens import TipoToken as T


def analizar_lexico(texto):
    """Devuelve (tokens, errores ordenados) para no repetir código en cada prueba."""
    g = GestorErrores()
    tokens = tokenizar(texto, g)
    return tokens, g.ordenados()


def tipos(tokens):
    return [t.tipo for t in tokens]


# --- Criterios de aceptación (Tabla 14, fase 2) ---

def test_ejemplo_1_genera_29_tokens_mas_eof():
    texto = (
        "int edad = 18;\n"
        "float precio = 2.5;\n"
        "bool activo = true;\n"
        "while (edad < 21) {\n"
        "    edad = edad + 1;\n"
        "}\n"
    )
    tokens, errores = analizar_lexico(texto)
    assert len(tokens) == 30
    assert tokens[-1].tipo == T.EOF
    assert errores == []


def test_ejemplo_3_caracter_invalido():
    tokens, errores = analizar_lexico("int precio$ = 10;")
    assert len(errores) == 1
    assert errores[0].formato() == "[LEX-01] línea 1, columna 11: Carácter no válido '$'"
    assert tipos(tokens) == [T.PR_INT, T.ID, T.ASIGNA, T.NUM_INT, T.PUNTOCOMA, T.EOF]
    assert tokens[1].lexema == "precio"


# --- Palabras reservadas e identificadores ---

def test_palabras_reservadas():
    tokens, _ = analizar_lexico("int float bool if else while true false")
    assert tipos(tokens)[:-1] == [
        T.PR_INT, T.PR_FLOAT, T.PR_BOOL, T.PR_IF,
        T.PR_ELSE, T.PR_WHILE, T.PR_TRUE, T.PR_FALSE,
    ]


def test_reservadas_distinguen_mayusculas_y_prefijos():
    tokens, _ = analizar_lexico("If WHILE int2 _x entero")
    assert tipos(tokens)[:-1] == [T.ID] * 5


# --- Mayor coincidencia (sección 6.3) ---

def test_numero_real_no_se_parte():
    tokens, _ = analizar_lexico("2.5 10")
    assert [(t.tipo, t.lexema) for t in tokens[:-1]] == [(T.NUM_FLOAT, "2.5"), (T.NUM_INT, "10")]


def test_operadores_de_dos_caracteres():
    tokens, _ = analizar_lexico("== != <= >= && || = < > !")
    assert [(t.tipo, t.lexema) for t in tokens[:-1]] == [
        (T.OP_REL, "=="), (T.OP_REL, "!="), (T.OP_REL, "<="), (T.OP_REL, ">="),
        (T.OP_LOG, "&&"), (T.OP_LOG, "||"),
        (T.ASIGNA, "="), (T.OP_REL, "<"), (T.OP_REL, ">"), (T.OP_LOG, "!"),
    ]


def test_aritmeticos_y_delimitadores():
    tokens, _ = analizar_lexico("+ - * / % ( ) { } ;")
    assert tipos(tokens)[:-1] == [T.OP_ARIT] * 5 + [
        T.PAR_IZQ, T.PAR_DER, T.LLAVE_IZQ, T.LLAVE_DER, T.PUNTOCOMA,
    ]


# --- Elementos que se descartan ---

def test_comentarios_y_espacios_se_descartan():
    tokens, errores = analizar_lexico("a = 1; // comentario con $ y @\n\t b = 2;")
    assert [t.lexema for t in tokens[:-1]] == ["a", "=", "1", ";", "b", "=", "2", ";"]
    assert errores == []


def test_division_no_es_comentario():
    tokens, _ = analizar_lexico("a / b")
    assert tipos(tokens)[:-1] == [T.ID, T.OP_ARIT, T.ID]


# --- Errores léxicos ---

def test_ampersand_y_barra_sueltos_son_invalidos():
    _, errores = analizar_lexico("a & b | c")
    assert [(e.codigo, e.columna) for e in errores] == [(CodigoError.LEX_01, 3), (CodigoError.LEX_01, 7)]


def test_punto_sin_decimales_es_invalido():
    tokens, errores = analizar_lexico("2.")
    assert tipos(tokens) == [T.NUM_INT, T.EOF]
    assert errores[0].formato() == "[LEX-01] línea 1, columna 2: Carácter no válido '.'"


def test_varios_errores_en_una_linea():
    _, errores = analizar_lexico("x = 3 @ # ?;")
    assert [e.columna for e in errores] == [7, 9, 11]


# --- Líneas y columnas ---

def test_columna_se_reinicia_en_cada_linea():
    tokens, _ = analizar_lexico("int a = 5\na = a + 1;")
    a = tokens[4]
    assert (a.lexema, a.linea, a.columna) == ("a", 2, 1)


def test_tabulacion_cuenta_como_una_columna():
    tokens, _ = analizar_lexico("\tx")
    assert tokens[0].columna == 2


def test_fin_de_linea_windows():
    tokens, errores = analizar_lexico("a = 1;\r\nb = 2;")
    assert errores == []
    b = tokens[4]
    assert (b.lexema, b.linea, b.columna) == ("b", 2, 1)


def test_propiedad_fin():
    tokens, _ = analizar_lexico("int a = 5")
    assert tokens[3].lexema == "5"
    assert tokens[3].fin == 10


# --- Fin de archivo ---

def test_texto_vacio_solo_eof():
    tokens, errores = analizar_lexico("")
    assert tipos(tokens) == [T.EOF]
    assert (tokens[0].linea, tokens[0].columna) == (1, 1)
    assert errores == []


def test_eof_queda_despues_del_ultimo_caracter():
    tokens, _ = analizar_lexico("a;\nbc")
    eof = tokens[-1]
    assert (eof.lexema, eof.linea, eof.columna) == ("", 2, 3)