class BorderSymbol:
    def __init__(self, x1, y1, x2):
        self._x1 = x1
        self._y1 = y1
        self._x2 = x2

    @property
    def x1(self) -> int:
        """ Top Left X """
        return self._x1

    @x1.setter
    def x1(self, value: int):    
        self._x1 = value

    @property
    def y1(self) -> int:
        """ Top Left Y """
        return self._y1

    @y1.setter
    def y1(self, value: int):    
        self._y1 = value

    @property
    def x2(self) -> int:
        """ Bottom Right X """
        return self._x2

    @x2.setter
    def x2(self, value: int):    
        self._x2 = value
