from enum import StrEnum
from dataclasses import dataclass

class Fase(StrEnum):
    LEXICA = "léxica"
    SINTACTICA = "sintáctica"
    SEMANTICA = "semántica"

class CodigoError(StrEnum):
    # Fase léxica
    LEX_01 = "LEX-01"  # Carácter fuera del alfabeto, o & | . que no forman un token

    # Fase sintáctica
    SIN_01 = "SIN-01"  # Token inesperado (no coincide con la gramática)
    SIN_02 = "SIN-02"  # Falta ';' al final de una declaración o asignación
    SIN_03 = "SIN-03"  # '{' o '(' sin cerrar

    # Fase semántica
    SEM_01 = "SEM-01"  # Variable no declarada
    SEM_02 = "SEM-02"  # Declaración repetida en el mismo ámbito
    SEM_03 = "SEM-03"  # Asignación o inicialización con tipo incompatible
    SEM_04 = "SEM-04"  # Operador con operandos de tipo no permitido
    SEM_05 = "SEM-05"  # Condición de if o while que no es bool

    @property
    def fase(self) -> Fase:
        match self.value[:3]:
            case "LEX":
                return Fase.LEXICA
            case "SIN":
                return Fase.SINTACTICA
            case "SEM":
                return Fase.SEMANTICA
        raise ValueError(f"Código sin fase: {self.value}")

@dataclass(frozen=True)
class Error:
    codigo: CodigoError
    linea: int
    columna: int
    mensaje: str
    
    def formato(self):
        return f"[{self.codigo.value}] línea {self.linea}, columna {self.columna}: {self.mensaje}"
    
class GestorErrores:
    
    def __init__(self):
        self._errores: list[Error] = []
    
    def registrar(self, codigo: CodigoError, linea: int, columna: int, mensaje: str) -> None:
        self._errores.append(Error(codigo, linea, columna, mensaje))
    
    def hay_errores(self) -> bool:
        return True if len(self._errores) > 0 else False
    
    def ordenados(self) -> list[Error]:
        return sorted(self._errores,
                    key=lambda error: (error.linea,error.columna)
                    )
    
    def resumen(self) -> dict[Fase, int]:
        conteo = {
            Fase.LEXICA:     0,
            Fase.SINTACTICA: 0,
            Fase.SEMANTICA:  0
        }
        
        for error in self._errores:
            conteo[error.codigo.fase] += 1
        
        return conteo