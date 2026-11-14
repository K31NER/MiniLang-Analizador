from analizador.tipos import Tipo

class TablaSimbolos:

    def __init__(self) -> None:
        self._ambitos: list[dict[str, Tipo]] = [{}]  # [0] es el ámbito global

    @property
    def profundidad(self) -> int:
        """0 en el ámbito global, 1 dentro de un bloque, 2 en un bloque anidado..."""
        return len(self._ambitos) - 1

    def abrir(self) -> None:
        """Abre un ámbito nuevo al leer '{'."""
        self._ambitos.append({})

    def cerrar(self) -> None:
        """Cierra el ámbito actual al leer '}'; sus variables dejan de existir."""
        if len(self._ambitos) == 1:
            raise RuntimeError("No se puede cerrar el ámbito global")
        self._ambitos.pop()

    def declarar(self, nombre: str, tipo: Tipo) -> bool:
        """Declara la variable en el ámbito actual.

        Devuelve False si ya estaba declarada en ESTE ámbito (SEM-02);
        en ese caso no la modifica.
        """
        actual = self._ambitos[-1]
        if nombre in actual:
            return False
        actual[nombre] = tipo
        return True

    def buscar(self, nombre: str) -> Tipo | None:
        """Busca desde el ámbito más interno hasta el global.

        Devuelve el tipo, o None si la variable no está declarada (SEM-01).
        """
        for ambito in reversed(self._ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None