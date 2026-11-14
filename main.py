import argparse
import sys


class AyudaEnEspanol(argparse.HelpFormatter):
    """Traduce el encabezado 'usage:' de argparse."""

    def add_usage(self, usage, actions, groups, prefix=None):
        super().add_usage(usage, actions, groups, prefix or "uso: ")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Analizador de errores léxicos, sintácticos y semánticos de MiniLang.",
        formatter_class=AyudaEnEspanol,
        add_help=False,
    )
    parser._positionals.title = "argumentos"
    parser._optionals.title = "opciones"
    parser.add_argument("-h", "--help", action="help", help="mostrar esta ayuda y salir")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("archivo", nargs="?", help="ruta del programa .mini a analizar")
    modo.add_argument("--texto", action="store_true", help="leer el código de la entrada estándar")
    modo.add_argument("--gui", action="store_true", help="abrir la interfaz gráfica")
    args = parser.parse_args()

    if args.gui:
        from interfaz import gui
        gui.iniciar()
        return 0

    from interfaz import cli

    if args.texto:
        return cli.analizar_entrada_estandar()
    if args.archivo:
        return cli.analizar_archivo(args.archivo)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())