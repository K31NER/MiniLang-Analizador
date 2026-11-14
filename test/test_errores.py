from analizador.errores import CodigoError, Fase, GestorErrores

def test_formato_exacto():
    g = GestorErrores()
    g.registrar(CodigoError.SEM_01, 8, 5, "Variable 'c' no declarada")
    assert g.ordenados()[0].formato() == "[SEM-01] línea 8, columna 5: Variable 'c' no declarada"


def test_gestor_vacio():
    g = GestorErrores()
    assert g.hay_errores() is False
    assert g.ordenados() == []
    assert g.resumen() == {Fase.LEXICA: 0, Fase.SINTACTICA: 0, Fase.SEMANTICA: 0}


def test_ordenados_por_posicion():
    g = GestorErrores()
    g.registrar(CodigoError.SEM_03, 3, 11, "No se puede asignar un valor float a una variable bool")
    g.registrar(CodigoError.LEX_01, 1, 11, "Carácter no válido '$'")
    g.registrar(CodigoError.SEM_02, 2, 5, "La variable 'x' ya fue declarada en este ámbito")

    assert g.hay_errores() is True
    assert [e.linea for e in g.ordenados()] == [1, 2, 3]


def test_misma_linea_ordena_por_columna():
    g = GestorErrores()
    g.registrar(CodigoError.LEX_01, 8, 13, "Carácter no válido '@'")
    g.registrar(CodigoError.SEM_01, 8, 1, "Variable 'precio' no declarada")

    assert [e.columna for e in g.ordenados()] == [1, 13]


def test_resumen_por_fase():
    g = GestorErrores()
    g.registrar(CodigoError.LEX_01, 1, 11, "Carácter no válido '$'")
    g.registrar(CodigoError.SEM_02, 2, 5, "La variable 'x' ya fue declarada en este ámbito")
    g.registrar(CodigoError.SEM_03, 3, 11, "No se puede asignar un valor float a una variable bool")

    assert g.resumen() == {Fase.LEXICA: 1, Fase.SINTACTICA: 0, Fase.SEMANTICA: 2}


def test_ordenados_no_modifica_el_orden_interno():
    g = GestorErrores()
    g.registrar(CodigoError.SEM_01, 5, 1, "Variable 'b' no declarada")
    g.registrar(CodigoError.SEM_01, 2, 1, "Variable 'a' no declarada")

    g.ordenados()
    assert [e.linea for e in g._errores] == [5, 2]


def test_cada_codigo_tiene_fase():
    for codigo in CodigoError:
        assert codigo.fase in Fase