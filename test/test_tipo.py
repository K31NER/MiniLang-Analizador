import pytest

from analizador.tipos import Tipo, compatible, es_numerico, resultado, resultado_unario

I, F, B = Tipo.INT, Tipo.FLOAT, Tipo.BOOL


# --- Tabla 6: operadores binarios válidos ---

@pytest.mark.parametrize("op, a, b, esperado", [
    # aritméticos: float si alguno es float; si no, int
    ("+", I, I, I), ("-", I, I, I), ("*", I, I, I), ("/", I, I, I), ("%", I, I, I),
    ("+", I, F, F), ("*", F, I, F), ("/", F, F, F),
    # relacionales: numéricos -> bool
    ("<", I, I, B), (">", I, F, B), ("<=", F, I, B), (">=", F, F, B),
    # igualdad: numéricos, o los dos bool -> bool
    ("==", I, F, B), ("!=", I, I, B), ("==", B, B, B), ("!=", B, B, B),
    # lógicos: bool y bool -> bool
    ("&&", B, B, B), ("||", B, B, B),
])
def test_binario_valido(op, a, b, esperado):
    assert resultado(op, a, b) == esperado


# --- Tabla 6: combinaciones no permitidas (el parser las convierte en SEM-04) ---

@pytest.mark.parametrize("op, a, b", [
    ("+", B, I), ("*", I, B), ("%", B, B),
    ("<", B, I), (">=", F, B),
    ("==", B, I), ("!=", F, B),
    ("&&", I, B), ("||", B, F), ("&&", I, I),
])
def test_binario_invalido(op, a, b):
    assert resultado(op, a, b) is None


# --- Tabla 6: operadores unarios ---

@pytest.mark.parametrize("op, a, esperado", [
    ("!", B, B), ("!", I, None), ("!", F, None),
    ("-", I, I), ("-", F, F), ("-", B, None),
])
def test_unario(op, a, esperado):
    assert resultado_unario(op, a) == esperado


# --- Tabla 6: asignación e inicialización ---

@pytest.mark.parametrize("destino, origen, esperado", [
    (I, I, True), (F, F, True), (B, B, True),
    (F, I, True),                 # ampliación: float recibe int
    (I, F, False),                # no se pierde la parte decimal sin avisar
    (B, I, False), (I, B, False), (B, F, False),
])
def test_compatible(destino, origen, esperado):
    assert compatible(destino, origen) is esperado


def test_es_numerico():
    assert es_numerico(I) and es_numerico(F)
    assert not es_numerico(B)


# --- Errores de nuestro código, no del programa MiniLang ---

def test_operador_desconocido_lanza_error():
    with pytest.raises(ValueError):
        resultado("^", I, I)
    with pytest.raises(ValueError):
        resultado_unario("+", I)