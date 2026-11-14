import asyncio

from textual.widgets import DataTable, Static, TextArea

from interfaz.gui import CARPETA_EJEMPLOS, AbrirArchivo, AnalizadorApp


def probar(escenario):
    """Ejecuta la interfaz sin pantalla y le aplica un escenario de prueba."""
    async def correr():
        app = AnalizadorApp()
        async with app.run_test(size=(120, 34)) as pilot:
            await escenario(app, pilot)
    asyncio.run(correr())


def test_analizar_muestra_los_errores_en_la_tabla():
    async def escenario(app, pilot):
        app.query_one("#editor", TextArea).text = "int precio$ = 10\nprecio = 1;"
        await pilot.press("f5")
        await pilot.pause()
        assert app.query_one("#tabla", DataTable).row_count == 2
        assert [e.codigo.value for e in app.errores] == ["LEX-01", "SIN-02"]
    probar(escenario)


def test_elegir_un_error_marca_su_posicion_en_el_editor():
    async def escenario(app, pilot):
        editor = app.query_one("#editor", TextArea)
        editor.text = "int precio$ = 10;"
        await pilot.press("f5")
        await pilot.pause()
        assert editor.selection.start == (0, 10)          # línea 1, columna 11
        assert "[LEX-01] línea 1, columna 11" in str(app.query_one("#detalle", Static).render())
    probar(escenario)


def test_programa_valido_dice_sin_errores():
    async def escenario(app, pilot):
        app.cargar_archivo(CARPETA_EJEMPLOS / "01_valido_basico.mini")
        await pilot.press("f5")
        await pilot.pause()
        tabla = app.query_one("#tabla", DataTable)
        assert app.errores == []
        assert tabla.row_count == 1                      # la tabla muestra «Sin errores»
        assert "Sin errores" in str(tabla.get_row_at(0)[3])
        assert "Sin errores." in str(app.query_one("#detalle", Static).render())
        assert "Sin errores" in str(app.query_one("#estado", Static).render())
    probar(escenario)


def test_limpiar_borra_el_editor_y_los_resultados():
    async def escenario(app, pilot):
        app.query_one("#editor", TextArea).text = "a = ;"
        await pilot.press("f5")
        await pilot.press("ctrl+l")
        await pilot.pause()
        assert app.query_one("#editor", TextArea).text == ""
        assert app.query_one("#tabla", DataTable).row_count == 0
    probar(escenario)


def test_abrir_archivo_y_cancelar():
    async def escenario(app, pilot):
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, AbrirArchivo)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, AbrirArchivo)
    probar(escenario)