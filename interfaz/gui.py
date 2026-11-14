import re
from dataclasses import replace
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button, DataTable, DirectoryTree, Footer, Header, Label, Select, Static, TextArea,
)
from textual.widgets.text_area import Selection, TextAreaTheme

from analizador import Error, Fase, analizar
from interfaz.cli import COLOR_FASE

CARPETA_EJEMPLOS = Path(__file__).resolve().parent.parent / "ejemplos"

# Nombres descriptivos del menú Ejemplos (Tabla 8). Si aparece un archivo
# que no está aquí, se muestra su nombre de archivo.
NOMBRES_EJEMPLOS = {
    "01_valido_basico": "1 · Válido básico",
    "02_valido_if_else": "2 · Válido if / else",
    "03_error_lexico": "3 · Error léxico",
    "04_falta_punto_coma": "4 · Falta ';'",
    "05_llave_sin_cerrar": "5 · Llave sin cerrar",
    "06_parentesis_sin_cerrar": "6 · Paréntesis sin cerrar",
    "07_variable_no_declarada": "7 · Variable no declarada",
    "08_declaracion_doble_y_tipos": "8 · Declaración doble y tipos",
    "09_condicion_no_booleana": "9 · Condición no booleana",
}

AMARILLO = "#ffe9a8"
FILA_SIN_ERRORES = "sin-errores"


# ----------------------------------------------------------------------
# Editor con resaltado de MiniLang y marcas rojas en los errores (2 y 3)
# ----------------------------------------------------------------------

_BASE = TextAreaTheme.get_builtin_theme("css")
_ESTILOS_MINI = {
    **_BASE.syntax_styles,
    "keyword": Style(color="#569cd6", bold=True),
    "number": Style(color="#b5cea8"),
    "comment": Style(color="#6a9955", italic=True),
    "error": Style(color="#ff5f5f", bold=True, underline=True, bgcolor="#5a1d1d"),
}
# Tema normal y tema con la línea del error seleccionado resaltada en amarillo.
TEMA_MINI = replace(_BASE, name="mini", syntax_styles=_ESTILOS_MINI)
TEMA_MINI_ERROR = replace(_BASE, name="mini-error", syntax_styles=_ESTILOS_MINI,
                          cursor_line_style=Style(bgcolor="#4d4220"))

_TOKENS_MINI = re.compile(
    r"(?P<comment>//.*$)"
    r"|(?P<keyword>\b(?:int|float|bool|if|else|while|true|false)\b)"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
)
_PALABRA = re.compile(r"[A-Za-z0-9_.]+")


class EditorMini(TextArea):
    """TextArea que colorea MiniLang y marca en rojo la posición de cada error.

    MiniLang no tiene gramática tree-sitter, así que el mapa de resaltado se
    arma con expresiones regulares. Las posiciones del mapa van en bytes UTF-8.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.marcas: list[tuple[int, int]] = []        # (fila, columna) desde 0

    def marcar_errores(self, errores: list[Error]) -> None:
        self.marcas = [(e.linea - 1, e.columna - 1) for e in errores]
        self._build_highlight_map()
        self.refresh()

    def _build_highlight_map(self) -> None:
        super()._build_highlight_map()
        resaltado = self._highlights
        for fila in range(self.document.line_count):
            linea = self.document.get_line(fila)
            for m in _TOKENS_MINI.finditer(linea):
                resaltado[fila].append((_byte(linea, m.start()), _byte(linea, m.end()), m.lastgroup))
        for fila, col in getattr(self, "marcas", []):
            if fila >= self.document.line_count:
                continue
            linea = self.document.get_line(fila)
            if col >= len(linea):                       # error al final de la línea
                resaltado[fila].append((_byte(linea, len(linea)), None, "error"))
                continue
            palabra = _PALABRA.match(linea, col)
            fin = palabra.end() if palabra else col + 1
            resaltado[fila].append((_byte(linea, col), _byte(linea, fin), "error"))


def _byte(linea: str, columna: int) -> int:
    """Convierte una columna (en caracteres) a desplazamiento en bytes UTF-8."""
    return len(linea[:columna].encode("utf-8"))


class ArbolMini(DirectoryTree):
    """Explorador de archivos que solo muestra carpetas y archivos .mini."""

    def filter_paths(self, paths):
        return [p for p in paths
                if not p.name.startswith(".") and (p.is_dir() or p.suffix == ".mini")]


class AbrirArchivo(ModalScreen[Path | None]):
    """Ventana para elegir un archivo .mini. Devuelve la ruta, o None si se cancela."""

    BINDINGS = [Binding("escape", "cancelar", "Cancelar")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialogo"):
            yield Label("Abrir archivo .mini", classes="titulo")
            yield ArbolMini(Path.cwd())
            yield Button("Cancelar", id="cancelar")

    @on(DirectoryTree.FileSelected)
    def elegido(self, evento: DirectoryTree.FileSelected) -> None:
        self.dismiss(evento.path)

    @on(Button.Pressed, "#cancelar")
    def action_cancelar(self) -> None:
        self.dismiss(None)


class AnalizadorApp(App):
    """Ventana principal: editor, tabla de errores, detalle y barra de estado."""

    TITLE = "Analizador de errores · MiniLang"
    ENABLE_COMMAND_PALETTE = False

    CSS = f"""
    #barra {{ height: auto; padding: 0 1; }}
    #barra Button {{ margin-right: 1; }}
    #ejemplos {{ width: 36; }}
    #archivo {{ width: 1fr; height: 3; content-align: right middle;
               text-wrap: nowrap; text-overflow: ellipsis; color: $text-muted; }}
    #cuerpo {{ height: 1fr; }}
    #izquierda, #derecha {{ width: 1fr; }}
    .panel {{ border: round $primary-darken-1; border-title-color: $text-muted; }}
    #izquierda {{ margin: 0 0 0 1; }}
    #derecha {{ margin: 0 1 0 1; }}
    #editor {{ height: 1fr; border: none; }}
    #tabla {{ height: 1fr; }}
    #tabla > .datatable--cursor {{ background: {AMARILLO}; color: black; }}
    #detalle {{ height: auto; min-height: 5; padding: 0 1;
               border: round $warning; border-title-color: $warning;
               background: #3d3420; }}
    #estado {{ height: 1; padding: 0 1; background: $panel; }}
    AbrirArchivo {{ align: center middle; }}
    #dialogo {{ width: 70; height: 26; border: thick $primary; background: $surface; padding: 1; }}
    #dialogo DirectoryTree {{ height: 1fr; }}
    """

    BINDINGS = [
        Binding("f5", "analizar", "Analizar"),
        Binding("ctrl+o", "abrir", "Abrir archivo"),
        Binding("ctrl+l", "limpiar", "Limpiar"),
        Binding("ctrl+q", "quit", "Salir"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.errores: list[Error] = []
        self.sin_errores = False      # True tras analizar un programa válido

    # ------------------------------------------------------------------
    # Composición de la pantalla (Figura 10)
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        with Horizontal(id="barra"):                                      # (1)
            yield Button("Abrir archivo", id="abrir")
            yield Button("Analizar", id="analizar", variant="primary")
            yield Button("Limpiar", id="limpiar")
            ejemplos = sorted(CARPETA_EJEMPLOS.glob("*.mini"))
            yield Select([(NOMBRES_EJEMPLOS.get(p.stem, p.stem), p) for p in ejemplos],
                         prompt="Ejemplos", id="ejemplos", disabled=not ejemplos)
            yield Label("archivo: sin título", id="archivo")
        with Horizontal(id="cuerpo"):
            with Vertical(id="izquierda", classes="panel"):                  # (2) y (3)
                editor = EditorMini("", id="editor", show_line_numbers=True,
                                    tab_behavior="indent", soft_wrap=False)
                editor.register_theme(TEMA_MINI)
                editor.register_theme(TEMA_MINI_ERROR)
                editor.theme = "mini"
                yield editor
            with Vertical(id="derecha"):
                with Vertical(id="panel-tabla", classes="panel"):            # (4)
                    yield DataTable(id="tabla", cursor_type="row", zebra_stripes=True)
                yield Static("Escribe o abre un programa y presiona Analizar (F5).",
                             id="detalle")                                     # (5)
        yield Static("", id="estado")                                         # (6)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#izquierda").border_title = "Código fuente"
        self.query_one("#panel-tabla").border_title = "Errores encontrados"
        self.query_one("#detalle").border_title = "Detalle del error seleccionado"
        tabla = self.query_one("#tabla", DataTable)
        tabla.add_column("Código", width=7)
        tabla.add_column("Lín.", width=4)
        tabla.add_column("Col.", width=4)
        tabla.add_column("Mensaje", key="mensaje")
        self.query_one("#editor", TextArea).focus()
        self.actualizar_estado()

    # ------------------------------------------------------------------
    # Acciones de la barra de herramientas
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#analizar")
    def action_analizar(self) -> None:
        editor = self.query_one("#editor", EditorMini)
        tabla = self.query_one("#tabla", DataTable)
        detalle = self.query_one("#detalle", Static)

        self.errores = analizar(editor.text) if editor.text.strip() else []
        self.sin_errores = bool(editor.text.strip()) and not self.errores
        editor.marcar_errores(self.errores)
        editor.theme = "mini"
        tabla.clear()
        ancho = self.ancho_mensaje()
        if ancho:                                     # ancho fijo: el mensaje se parte en líneas
            columna = tabla.columns["mensaje"]
            columna.auto_width = False
            columna.width = ancho
        for i, e in enumerate(self.errores):
            codigo = Text(e.codigo.value, style=COLOR_FASE[e.codigo.fase])
            mensaje = Text(e.mensaje)
            alto = len(mensaje.wrap(self.console, ancho)) if ancho else 1
            tabla.add_row(codigo, str(e.linea), str(e.columna), mensaje, height=alto, key=str(i))

        self.query_one("#panel-tabla").border_title = f"Errores encontrados ({len(self.errores)})"
        if not editor.text.strip():
            detalle.update("No hay código para analizar.")
        elif not self.errores:
            tabla.add_row(Text("—", style="bold green"), "", "",
                          Text("Sin errores", style="bold green"), key=FILA_SIN_ERRORES)
            detalle.update(Text("Sin errores.", style="bold #4ade80"))
        else:
            tabla.focus()
            tabla.move_cursor(row=0)
        self.actualizar_estado()

    def ancho_mensaje(self) -> int:
        """Ancho disponible para la columna Mensaje, para que el texto se parta en líneas."""
        tabla = self.query_one("#tabla", DataTable)
        fijo = 7 + 4 + 4 + 4 * 2 + 1                 # columnas fijas + relleno de celdas
        return max(tabla.size.width - fijo, 20) if tabla.size.width else 0

    @on(Button.Pressed, "#abrir")
    def action_abrir(self) -> None:
        self.push_screen(AbrirArchivo(), self.cargar_archivo)

    @on(Button.Pressed, "#limpiar")
    def action_limpiar(self) -> None:
        self.query_one("#editor", TextArea).text = ""
        self.query_one("#archivo", Label).update("archivo: sin título")
        self.limpiar_resultados("Escribe o abre un programa y presiona Analizar (F5).")

    @on(Select.Changed, "#ejemplos")
    def ejemplo_elegido(self, evento: Select.Changed) -> None:
        if evento.value is not Select.NULL:
            self.cargar_archivo(evento.value)

    # ------------------------------------------------------------------
    # Carga de archivos y resultados
    # ------------------------------------------------------------------

    def cargar_archivo(self, ruta: Path | None) -> None:
        if ruta is None:
            return
        try:
            texto = ruta.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            self.notify(f"No se pudo leer '{ruta.name}' como texto UTF-8.", severity="error")
            return
        # Sin la línea vacía final que dejaría el último salto de línea del archivo.
        self.query_one("#editor", TextArea).text = texto.removesuffix("\n")
        self.query_one("#archivo", Label).update(f"archivo: {ruta.name}")
        self.limpiar_resultados("Archivo cargado. Presiona Analizar (F5).")

    def limpiar_resultados(self, mensaje: str) -> None:
        self.errores = []
        self.sin_errores = False
        editor = self.query_one("#editor", EditorMini)
        editor.marcar_errores([])
        editor.theme = "mini"
        self.query_one("#tabla", DataTable).clear()
        self.query_one("#panel-tabla").border_title = "Errores encontrados"
        self.query_one("#detalle", Static).update(mensaje)
        self.actualizar_estado()

    @on(TextArea.Changed, "#editor")
    def codigo_editado(self) -> None:
        """Al escribir, las marcas dejan de corresponder al código: se quitan."""
        editor = self.query_one("#editor", EditorMini)
        if editor.marcas:
            editor.marcar_errores([])
        editor.theme = "mini"

    @on(DataTable.RowHighlighted, "#tabla")
    def error_seleccionado(self, evento: DataTable.RowHighlighted) -> None:
        """Al elegir un error: muestra el detalle y resalta su línea en el editor."""
        clave = evento.row_key.value
        if clave is None or clave == FILA_SIN_ERRORES:
            return
        error = self.errores[int(clave)]
        self.query_one("#detalle", Static).update(Text(error.formato()))
        editor = self.query_one("#editor", EditorMini)
        fila, col = error.linea - 1, error.columna - 1
        largo = len(editor.document.get_line(fila)) if fila < editor.document.line_count else 0
        col = min(col, largo)
        editor.selection = Selection((fila, col), (fila, min(col + 1, largo)))
        editor.theme = "mini-error"                   # línea del error en amarillo
        editor.scroll_cursor_visible(center=True)

    @on(TextArea.SelectionChanged, "#editor")
    def cursor_movido(self) -> None:
        self.actualizar_estado()

    # ------------------------------------------------------------------
    # Barra de estado
    # ------------------------------------------------------------------

    def actualizar_estado(self) -> None:
        fila, col = self.query_one("#editor", TextArea).cursor_location
        posicion = f"Lín. {fila + 1}, col. {col + 1}"
        if self.errores:
            conteo = {fase: 0 for fase in Fase}
            for e in self.errores:
                conteo[e.codigo.fase] += 1
            total = len(self.errores)
            resumen = Text.assemble(
                (f"{total} {'error' if total == 1 else 'errores'}", "bold"),
                "  ·  ", ("léxicos: ", COLOR_FASE[Fase.LEXICA]), str(conteo[Fase.LEXICA]),
                "  ·  ", ("sintácticos: ", COLOR_FASE[Fase.SINTACTICA]), str(conteo[Fase.SINTACTICA]),
                "  ·  ", ("semánticos: ", COLOR_FASE[Fase.SEMANTICA]), str(conteo[Fase.SEMANTICA]),
            )
        elif self.sin_errores:
            resumen = Text("Sin errores", style="bold #4ade80")
        else:
            resumen = Text("")
        estado = self.query_one("#estado", Static)
        ancho = max(estado.size.width - 2, 0)
        relleno = " " * max(ancho - resumen.cell_len - len(posicion), 2)
        estado.update(Text.assemble(resumen, relleno, posicion))

    def on_resize(self) -> None:
        self.actualizar_estado()


def iniciar() -> None:
    AnalizadorApp().run()
