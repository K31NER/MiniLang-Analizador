from analizador.errores import CodigoError, GestorErrores
from analizador.simbolos import TablaSimbolos
from analizador.tipos import TIPO_DECLARADO, Tipo, compatible, resultado, resultado_unario
from analizador.tokens import TIPOS_DATO, TipoToken, Token

T = TipoToken


class ErrorSintactico(Exception):
    """Interrumpe la sentencia actual para recuperarse en modo pánico.

    Es interna del parser: el error ya quedó registrado en el gestor
    antes de lanzarla, y sentencia() siempre la atrapa.
    """


class Parser:

    def __init__(self, tokens: list[Token], errores: GestorErrores) -> None:
        self.tokens = tokens
        self.pos = 0
        self.errores = errores
        self.simbolos = TablaSimbolos()

    # ------------------------------------------------------------------
    # Utilidades para recorrer los tokens
    # ------------------------------------------------------------------

    def actual(self) -> Token:
        """Token de anticipación (lookahead)."""
        return self.tokens[self.pos]

    def anterior(self) -> Token:
        """Último token consumido; se usa para ubicar el ';' faltante."""
        return self.tokens[self.pos - 1]

    def avanzar(self) -> Token:
        """Consume el token actual y lo devuelve. Nunca pasa del EOF."""
        tok = self.actual()
        if tok.tipo != T.EOF:
            self.pos += 1
        return tok

    def es(self, tipo: TipoToken, lexema: str | None = None) -> bool:
        """True si el token actual es de ese tipo (y, si se indica, con ese lexema)."""
        tok = self.actual()
        return tok.tipo == tipo and (lexema is None or tok.lexema == lexema)

    @staticmethod
    def mostrar(tok: Token) -> str:
        """Texto del token para los mensajes de error."""
        return tok.lexema if tok.tipo != T.EOF else "fin de archivo"

    def error(self, codigo: CodigoError, linea: int, columna: int, mensaje: str) -> None:
        self.errores.registrar(codigo, linea, columna, mensaje)

    def esperar(self, tipo: TipoToken, simbolo: str) -> Token:
        """Exige un token de cierto tipo; si no está, SIN-01 y modo pánico."""
        if self.es(tipo):
            return self.avanzar()
        tok = self.actual()
        self.error(CodigoError.SIN_01, tok.linea, tok.columna,
                   f"Se esperaba '{simbolo}' y se encontró '{self.mostrar(tok)}'")
        raise ErrorSintactico

    def esperar_punto_y_coma(self) -> None:
        """Si falta ';', SIN-02 al final de la sentencia y se asume presente."""
        if self.es(T.PUNTOCOMA):
            self.avanzar()
            return
        ultimo = self.anterior()
        self.error(CodigoError.SIN_02, ultimo.linea, ultimo.fin,
                   "Falta ';' al final de la sentencia")

    def cerrar_parentesis(self) -> None:
        """Si falta ')', SIN-03 donde se esperaba y se continúa sin pánico."""
        if self.es(T.PAR_DER):
            self.avanzar()
            return
        tok = self.actual()
        self.error(CodigoError.SIN_03, tok.linea, tok.columna,
                   "Paréntesis '(' abierto sin cerrar")

    def sincronizar(self) -> None:
        """Modo pánico: salta tokens hasta ';' (lo consume), '}' o EOF.

        Si en el camino salta un '{', también salta su '}' correspondiente;
        así esa llave no se reporta después como huérfana (error en cascada).
        """
        profundidad = 0
        while not self.es(T.EOF):
            if self.es(T.LLAVE_IZQ):
                profundidad += 1
            elif self.es(T.LLAVE_DER):
                if profundidad == 0:
                    return                  # '}' del bloque que nos contiene
                profundidad -= 1
            elif self.es(T.PUNTOCOMA) and profundidad == 0:
                self.avanzar()
                return
            self.avanzar()

    # ------------------------------------------------------------------
    # Chequeos semánticos (sección 6.6). Un tipo None significa que la
    # expresión ya tuvo un error: no se reporta nada más (sin cascada).
    # ------------------------------------------------------------------

    def tipo_de_variable(self, tok: Token) -> Tipo | None:
        """SEM-01 si el identificador no está declarado en ningún ámbito visible."""
        tipo = self.simbolos.buscar(tok.lexema)
        if tipo is None:
            self.error(CodigoError.SEM_01, tok.linea, tok.columna,
                       f"Variable '{tok.lexema}' no declarada")
        return tipo

    def verificar_asignacion(self, destino: Tipo | None, origen: Tipo | None, inicio: Token) -> None:
        """SEM-03 si el valor no se puede guardar en la variable (Tabla 6)."""
        if destino is not None and origen is not None and not compatible(destino, origen):
            self.error(CodigoError.SEM_03, inicio.linea, inicio.columna,
                       f"No se puede asignar un valor {origen} a una variable {destino}")

    def verificar_binario(self, op: Token, a: Tipo | None, b: Tipo | None) -> Tipo | None:
        """Tipo de 'a op b'; SEM-04 en el operador si la combinación no está permitida."""
        if a is None or b is None:
            return None
        tipo = resultado(op.lexema, a, b)
        if tipo is None:
            self.error(CodigoError.SEM_04, op.linea, op.columna,
                       f"El operador '{op.lexema}' no admite operandos de tipo {a} y {b}")
        return tipo

    def verificar_unario(self, op: Token, a: Tipo | None) -> Tipo | None:
        """Tipo de '!a' o '-a'; SEM-04 en el operador si no está permitido."""
        if a is None:
            return None
        tipo = resultado_unario(op.lexema, a)
        if tipo is None:
            self.error(CodigoError.SEM_04, op.linea, op.columna,
                       f"El operador '{op.lexema}' no admite un operando de tipo {a}")
        return tipo

    # Sentencias

    def programa(self) -> None:
        """Programa -> ListaSent"""
        while not self.es(T.EOF):
            if self.es(T.LLAVE_DER):
                tok = self.avanzar()
                self.error(CodigoError.SIN_01, tok.linea, tok.columna,
                        "Llave '}' sin su '{' correspondiente")
            else:
                self.sentencia()

    def sentencia(self) -> None:
        """Sentencia -> Decl | Asig | Si | Mientras | Bloque  (Tabla 5)"""
        try:
            tok = self.actual()
            if tok.tipo in TIPOS_DATO:
                self.declaracion()
            elif tok.tipo == T.ID:
                self.asignacion()
            elif tok.tipo == T.PR_IF:
                self.si()
            elif tok.tipo == T.PR_WHILE:
                self.mientras()
            elif tok.tipo == T.LLAVE_IZQ:
                self.bloque()
            else:
                self.error(CodigoError.SIN_01, tok.linea, tok.columna,
                        f"Sentencia no válida: se encontró '{self.mostrar(tok)}'")
                raise ErrorSintactico
        except ErrorSintactico:
            self.sincronizar()

    def declaracion(self) -> None:
        """Decl -> Tipo ID DeclOpc ;     DeclOpc -> = Expr | ε"""
        tipo = TIPO_DECLARADO[self.avanzar().tipo]      # int | float | bool
        nombre = self.esperar(T.ID, "identificador")
        try:
            if self.es(T.ASIGNA):
                self.avanzar()
                inicio = self.actual()
                self.verificar_asignacion(tipo, self.expr(), inicio)
        finally:
            # Se declara aunque la inicialización falle, para que los usos
            # posteriores de la variable no generen SEM-01 en cascada.
            if not self.simbolos.declarar(nombre.lexema, tipo):
                self.error(CodigoError.SEM_02, nombre.linea, nombre.columna,
                           f"La variable '{nombre.lexema}' ya fue declarada en este ámbito")
        self.esperar_punto_y_coma()

    def asignacion(self) -> None:
        """Asig -> ID = Expr ;"""
        destino = self.tipo_de_variable(self.avanzar())  # ID
        self.esperar(T.ASIGNA, "=")
        inicio = self.actual()
        self.verificar_asignacion(destino, self.expr(), inicio)
        self.esperar_punto_y_coma()

    def condicion(self) -> None:
        """( Expr )  — compartida por if y while. SEM-05 si no es bool."""
        self.esperar(T.PAR_IZQ, "(")
        inicio = self.actual()
        tipo = self.expr()
        if tipo is not None and tipo != Tipo.BOOL:
            self.error(CodigoError.SEM_05, inicio.linea, inicio.columna,
                       f"La condición debe ser bool y es {tipo}")
        self.cerrar_parentesis()

    def si(self) -> None:
        """Si -> if ( Expr ) Bloque SiElse     SiElse -> else Bloque | ε"""
        self.avanzar()                                  # if
        self.condicion()
        self.bloque()
        if self.es(T.PR_ELSE):
            self.avanzar()
            self.bloque()

    def mientras(self) -> None:
        """Mientras -> while ( Expr ) Bloque"""
        self.avanzar()                                  # while
        self.condicion()
        self.bloque()

    def bloque(self) -> None:
        """Bloque -> { ListaSent }"""
        if not self.es(T.LLAVE_IZQ):
            tok = self.actual()
            self.error(CodigoError.SIN_01, tok.linea, tok.columna,
                    f"Se esperaba '{{' y se encontró '{self.mostrar(tok)}'")
            return
        apertura = self.avanzar()
        self.simbolos.abrir()                           # cada '{' abre un ámbito
        try:
            while not (self.es(T.LLAVE_DER) or self.es(T.EOF)):
                self.sentencia()
        finally:
            self.simbolos.cerrar()                      # sus variables dejan de existir
        if self.es(T.EOF):
            self.error(CodigoError.SIN_03, apertura.linea, apertura.columna,
                    "Llave '{' abierta sin cerrar")
        else:
            self.avanzar()                              # }

    # Expresiones: un método por nivel de precedencia (de menor a mayor).
    # Cada uno devuelve el tipo de la expresión, o None si ya hubo error.

    def expr(self) -> Tipo | None:
        """Expr -> ExprY ColaO        ColaO -> || ExprY ColaO | ε"""
        tipo = self.expr_y()
        while self.es(T.OP_LOG, "||"):
            op = self.avanzar()
            tipo = self.verificar_binario(op, tipo, self.expr_y())
        return tipo

    def expr_y(self) -> Tipo | None:
        """ExprY -> Igual ColaY       ColaY -> && Igual ColaY | ε"""
        tipo = self.igualdad()
        while self.es(T.OP_LOG, "&&"):
            op = self.avanzar()
            tipo = self.verificar_binario(op, tipo, self.igualdad())
        return tipo

    def igualdad(self) -> Tipo | None:
        """Igual -> Rel ColaIgual     ColaIgual -> (== | !=) Rel ColaIgual | ε"""
        tipo = self.relacional()
        while self.es(T.OP_REL, "==") or self.es(T.OP_REL, "!="):
            op = self.avanzar()
            tipo = self.verificar_binario(op, tipo, self.relacional())
        return tipo

    def relacional(self) -> Tipo | None:
        """Rel -> Suma ColaRel        ColaRel -> (< | > | <= | >=) Suma | ε  (no se encadena)"""
        tipo = self.suma()
        if self.es(T.OP_REL) and self.actual().lexema in ("<", ">", "<=", ">="):
            op = self.avanzar()
            tipo = self.verificar_binario(op, tipo, self.suma())
        return tipo

    def suma(self) -> Tipo | None:
        """Suma -> Prod ColaSuma      ColaSuma -> (+ | -) Prod ColaSuma | ε"""
        tipo = self.producto()
        while self.es(T.OP_ARIT, "+") or self.es(T.OP_ARIT, "-"):
            op = self.avanzar()
            tipo = self.verificar_binario(op, tipo, self.producto())
        return tipo

    def producto(self) -> Tipo | None:
        """Prod -> Unario ColaProd    ColaProd -> (* | / | %) Unario ColaProd | ε"""
        tipo = self.unario()
        while self.es(T.OP_ARIT) and self.actual().lexema in ("*", "/", "%"):
            op = self.avanzar()
            tipo = self.verificar_binario(op, tipo, self.unario())
        return tipo

    def unario(self) -> Tipo | None:
        """Unario -> (! | -) Unario | Primario"""
        if self.es(T.OP_LOG, "!") or self.es(T.OP_ARIT, "-"):
            op = self.avanzar()
            return self.verificar_unario(op, self.unario())
        return self.primario()

    def primario(self) -> Tipo | None:
        """Primario -> NUM_INT | NUM_FLOAT | true | false | ID | ( Expr )"""
        tok = self.actual()
        if tok.tipo == T.NUM_INT:
            self.avanzar()
            return Tipo.INT
        if tok.tipo == T.NUM_FLOAT:
            self.avanzar()
            return Tipo.FLOAT
        if tok.tipo in (T.PR_TRUE, T.PR_FALSE):
            self.avanzar()
            return Tipo.BOOL
        if tok.tipo == T.ID:
            return self.tipo_de_variable(self.avanzar())
        if tok.tipo == T.PAR_IZQ:
            self.avanzar()
            tipo = self.expr()
            self.cerrar_parentesis()
            return tipo
        self.error(CodigoError.SIN_01, tok.linea, tok.columna,
                   f"Se esperaba una expresión y se encontró '{self.mostrar(tok)}'")
        raise ErrorSintactico