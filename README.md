# MiniLang · Analizador de errores de código

MiniLang es un lenguaje pequeño con variables tipadas (`int`, `float`, `bool`), expresiones, `if`/`else`, `while` y bloques. Este proyecto es un analizador de errores escrito en Python: recibe un programa MiniLang, desde un archivo `.mini` o como texto pegado, y reporta sus errores léxicos (`LEX`), sintácticos (`SIN`) y semánticos (`SEM`), cada uno con su código, línea, columna y un mensaje explicativo. No ejecuta el programa: solo lo valida. Se puede usar desde la consola o desde una interfaz gráfica en la terminal.

## Requisitos

- Python 3.13 o superior.
- [uv](https://docs.astral.sh/uv/) para instalar las dependencias y ejecutar el proyecto.

## Instalación

Desde la carpeta `minilang-analizador`:

```bash
uv sync
```

## Interfaz gráfica

La interfaz se abre en la misma terminal (está hecha con Textual):

```bash
uv run python main.py --gui
```

Uso:

1. Escribe o pega el código en el panel «Código fuente», abre un archivo `.mini` con «Abrir archivo» (`Ctrl+O`) o elige un programa del menú «Ejemplos».
2. Presiona «Analizar» (`F5`).
3. Los errores aparecen en la tabla, ordenados por línea y columna, y quedan marcados en rojo en el editor. Al elegir un error con las flechas o el ratón se resalta su línea y se muestra el mensaje completo en «Detalle del error seleccionado».
4. «Limpiar» (`Ctrl+L`) borra el editor y los resultados; `Ctrl+Q` cierra la interfaz.

Se recomienda una terminal de al menos 120 columnas por 30 filas.

## Consola

Analizar un archivo:

```bash
uv run python main.py ejemplos/03_error_lexico.mini
```

Analizar texto pegado en la consola (para terminar: `Ctrl+Z` y `Enter` en Windows, `Ctrl+D` en Linux o macOS):

```bash
uv run python main.py --texto
```

Ver todas las opciones:

```bash
uv run python main.py --help
```

El programa termina con código de salida `0` si no hay errores, `1` si encuentra alguno y `2` si la entrada no es válida (archivo inexistente, vacío o que no está en UTF-8).

En Windows, si la salida se redirige a un archivo o a otro programa, define `PYTHONIOENCODING=utf-8` para que se muestren bien las tildes y los símbolos.

## Pruebas

```bash
uv run pytest
```
