import pytest

from analizador.simbolos import TablaSimbolos
from analizador.tipos import Tipo


def test_tabla_nueva_esta_en_el_ambito_global():
    ts = TablaSimbolos()
    assert ts.profundidad == 0
    assert ts.buscar("x") is None


def test_declarar_y_buscar():
    ts = TablaSimbolos()
    assert ts.declarar("edad", Tipo.INT) is True
    assert ts.buscar("edad") == Tipo.INT


def test_declaracion_repetida_en_el_mismo_ambito():
    ts = TablaSimbolos()
    ts.declarar("x", Tipo.INT)
    assert ts.declarar("x", Tipo.BOOL) is False   # SEM-02
    assert ts.buscar("x") == Tipo.INT             # conserva el tipo original


def test_variable_deja_de_existir_al_cerrar_su_bloque():
    """Programa de la Figura 9: 'c' se declara dentro del while."""
    ts = TablaSimbolos()
    ts.declarar("a", Tipo.INT)
    ts.declarar("b", Tipo.FLOAT)
    ts.abrir()                                    # while (...) {
    ts.declarar("c", Tipo.INT)
    assert ts.profundidad == 1
    assert ts.buscar("a") == Tipo.INT             # se ve la variable de afuera
    assert ts.buscar("c") == Tipo.INT
    ts.cerrar()                                   # }
    assert ts.profundidad == 0
    assert ts.buscar("c") is None                 # a = c;  -> SEM-01
    assert ts.buscar("b") == Tipo.FLOAT


def test_bloque_interno_puede_ocultar_una_variable():
    ts = TablaSimbolos()
    ts.declarar("x", Tipo.INT)
    ts.abrir()
    assert ts.declarar("x", Tipo.BOOL) is True    # no es SEM-02: otro ámbito
    assert ts.buscar("x") == Tipo.BOOL
    ts.cerrar()
    assert ts.buscar("x") == Tipo.INT             # vuelve la de afuera


def test_bloques_anidados():
    ts = TablaSimbolos()
    ts.abrir()
    ts.declarar("y", Tipo.FLOAT)
    ts.abrir()
    assert ts.profundidad == 2
    assert ts.buscar("y") == Tipo.FLOAT
    ts.cerrar()
    ts.cerrar()
    assert ts.buscar("y") is None


def test_no_se_puede_cerrar_el_ambito_global():
    ts = TablaSimbolos()
    with pytest.raises(RuntimeError):
        ts.cerrar()