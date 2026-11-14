import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# En Windows, la salida de un proceso hijo usa cp1252 si va a una tubería.
# Se fuerza UTF-8 para que la prueba pueda leer las tildes ("línea", "está").
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8"}

def ejecutar(*args, entrada=None):
    """Ejecuta 'python main.py ...' y devuelve (código de salida, salida, errores)."""
    r = subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=RAIZ, input=entrada, capture_output=True, text=True, encoding="utf-8",
        env=ENTORNO,
    )
    return r.returncode, r.stdout, r.stderr


def test_archivo_con_errores(tmp_path):
    archivo = tmp_path / "prueba.mini"
    archivo.write_text("int a = 5\na = a + 1;\n", encoding="utf-8")
    codigo, salida, _ = ejecutar(str(archivo))
    assert codigo == 1
    assert "[SIN-02] línea 1, columna 10: Falta ';' al final de la sentencia" in salida
    assert "Resumen: 1 error (léxicos: 0, sintácticos: 1, semánticos: 0)" in salida


def test_archivo_sin_errores(tmp_path):
    archivo = tmp_path / "valido.mini"
    archivo.write_text("int edad = 18;\n", encoding="utf-8")
    codigo, salida, _ = ejecutar(str(archivo))
    assert codigo == 0
    assert "Sin errores." in salida


def test_archivo_inexistente():
    codigo, _, errores = ejecutar("no_existe.mini")
    assert codigo == 2
    assert "no se encontró el archivo 'no_existe.mini'" in errores


def test_archivo_vacio(tmp_path):
    archivo = tmp_path / "vacio.mini"
    archivo.write_text("   \n", encoding="utf-8")
    codigo, _, errores = ejecutar(str(archivo))
    assert codigo == 2
    assert "está vacío" in errores


def test_entrada_estandar():
    codigo, salida, _ = ejecutar("--texto", entrada="int precio$ = 10;\n")
    assert codigo == 1
    assert "[LEX-01] línea 1, columna 11: Carácter no válido '$'" in salida


def test_sin_argumentos_muestra_la_ayuda():
    codigo, salida, _ = ejecutar()
    assert codigo == 0
    assert "uso: python main.py" in salida