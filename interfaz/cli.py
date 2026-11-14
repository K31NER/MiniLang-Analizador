import sys
from pathlib import Path

from rich.console import Console
from rich.text import Text

from analizador import Error, Fase, analizar

SIN_ERRORES = 0
CON_ERRORES = 1
ENTRADA_INVALIDA = 2

# Color del código de error según su fase
COLOR_FASE = {
    Fase.LEXICA: "bold dark_orange",
    Fase.SINTACTICA: "bold dodger_blue1",
    Fase.SEMANTICA: "bold magenta",
}

# soft_wrap=True: nunca partir una línea de error, aunque la salida vaya a un archivo
consola = Console(highlight=False, soft_wrap=True)
consola_err = Console(stderr=True, highlight=False, soft_wrap=True)


def analizar_archivo(ruta: str) -> int:
    """Lee un archivo .mini, lo analiza y muestra el reporte."""
    archivo = Path(ruta)
    if not archivo.is_file():
        return aviso(f"no se encontró el archivo '{ruta}'.")
    try:
        texto = archivo.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return aviso(f"el archivo '{ruta}' no es un texto UTF-8 válido.")
    if not texto.strip():
        return aviso(f"el archivo '{ruta}' está vacío.")
    return reportar(texto, f"Analizando {ruta} ...")


def analizar_entrada_estandar() -> int:
    """Lee el código desde la entrada estándar (tubería o teclado)."""
    if sys.stdin.isatty():
        consola_err.print("Escribe o pega el código. Para terminar: Ctrl+Z y Enter (Windows) "
                        "o Ctrl+D (Linux/macOS).", style="dim")
    texto = sys.stdin.read()
    if not texto.strip():
        return aviso("no se recibió código por la entrada estándar.")
    return reportar(texto, "Analizando texto de la entrada estándar ...")


def reportar(texto: str, encabezado: str) -> int:
    """Analiza el texto, imprime el reporte y devuelve el código de salida."""
    consola.print(encabezado, style="dim")
    errores = analizar(texto)

    if not errores:
        consola.print("Sin errores.", style="bold green")
        return SIN_ERRORES

    lineas = texto.splitlines()
    consola.print()
    for error in errores:
        imprimir_error(error, lineas)
    imprimir_resumen(errores)
    return CON_ERRORES


def imprimir_error(error: Error, lineas: list[str]) -> None:
    """Línea del error (formato de la Tabla 7) y el código fuente señalado."""
    estilo = COLOR_FASE[error.codigo.fase]
    consola.print(Text.assemble(
        (f"[{error.codigo.value}]", estilo),
        f" línea {error.linea}, columna {error.columna}: {error.mensaje}",
    ))

    if 1 <= error.linea <= len(lineas):
        codigo = lineas[error.linea - 1].expandtabs(1)  # una tabulación = una columna
        margen = f"{error.linea:>5} │ "
        consola.print(Text.assemble((margen, "dim"), codigo))
        consola.print(Text.assemble((" " * 6 + "│ ", "dim"),
                                    " " * (error.columna - 1), ("^", estilo)))
    consola.print()


def imprimir_resumen(errores: list[Error]) -> None:
    conteo = {fase: 0 for fase in Fase}
    for error in errores:
        conteo[error.codigo.fase] += 1
    total = len(errores)
    palabra = "error" if total == 1 else "errores"
    consola.print(Text.assemble(
        ("Resumen: ", "bold"),
        (f"{total} {palabra}", "bold red"),
        f" (léxicos: {conteo[Fase.LEXICA]}, sintácticos: {conteo[Fase.SINTACTICA]}, "
        f"semánticos: {conteo[Fase.SEMANTICA]})",
    ))


def aviso(mensaje: str) -> int:
    """Entrada inválida: se informa y no se analiza nada."""
    consola_err.print(Text.assemble(("Error: ", "bold red"), mensaje))
    return ENTRADA_INVALIDA