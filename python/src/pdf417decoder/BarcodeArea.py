from pdf417decoder.BorderPattern import BorderPattern

class BarcodeArea:
    MAX_SYMBOL_ERROR = 0.08

    @property
    def left_center_x(self) -> int:
        """ Left border line of PDF 417 barcode excluding start border """
        return self._left_center_x

    @left_center_x.setter
    def left_center_x(self, value: int):    
        self._left_center_x = value    
        
    @property
    def left_center_y(self) -> int:
        """ Left border line of PDF 417 barcode excluding start border """
        return self._left_center_y

    @left_center_y.setter
    def left_center_y(self, value: int):    
        self._left_center_y = value

    @property
    def left_delta_x(self) -> int:
        """ Left border line of PDF 417 barcode excluding start border """
        return self._left_delta_x

    @left_delta_x.setter
    def left_delta_x(self, value: int):    
        self._left_delta_x = value    
        
    @property
    def left_delta_y(self) -> int:
        """ Left border line of PDF 417 barcode excluding start border """
        return self._left_delta_y

    @left_delta_y.setter
    def left_delta_y(self, value: int):    
        self._left_delta_y = value
    
    @property
    def right_center_x(self) -> int:
        """ Right border line of PDF 417 barcode excluding stop border """
        return self._right_center_x

    @right_center_x.setter
    def right_center_x(self, value: int):    
        self._right_center_x = value    
        
    @property
    def right_center_y(self) -> int:
        """ Right border line of PDF 417 barcode excluding stop border """
        return self._right_center_y

    @right_center_y.setter
    def right_center_y(self, value: int):    
        self._right_center_y = value

    @property
    def right_delta_x(self) -> int:
        """ Right border line of PDF 417 barcode excluding stop border """
        return self._right_delta_x

    @right_delta_x.setter
    def right_delta_x(self, value: int):    
        self._right_delta_x = value
        
    @property
    def right_delta_y(self) -> int:
        """ Right border line of PDF 417 barcode excluding stop border """
        return self._right_delta_y

    @right_delta_y.setter
    def right_delta_y(self, value: int):    
        self._right_delta_y = value
        
    @property
    def average_symbol_width(self) -> float:
        """ Average symbol width of start and stop borders """
        return self._average_symbol_width

    @average_symbol_width.setter
    def average_symbol_width(self, value: float):    
        self._average_symbol_width = value
        
    @property
    def max_symbol_error(self) -> float:
        """ Max symbol error """
        return self._max_symbol_error

    @max_symbol_error.setter
    def max_symbol_error(self, value: float):    
        self._max_symbol_error = value


    def __init__(self, startBorder: BorderPattern, stopBorder: BorderPattern):
        # left border line of PDF 417 barcode excluding start border
        self.left_center_x = startBorder.center_x
        self.left_center_y = startBorder.center_y
        self.left_delta_x = startBorder.delta_x
        self.left_delta_y = startBorder.delta_y

        # right border line of PDF 417 barcode excluding stop border
        self.right_center_x = stopBorder.center_x
        self.right_center_y = stopBorder.center_y
        self.right_delta_x = stopBorder.delta_x
        self.right_delta_y = stopBorder.delta_y

		# average symbol width of start and stop borders
        self.average_symbol_width = 0.5 * (startBorder.average_symbol_width + stopBorder.average_symbol_width)
        self.max_symbol_error = self.MAX_SYMBOL_ERROR * self.average_symbol_width

    def left_x_func_y(self, posY: int) -> int:
        return int(self.left_center_x + (self.left_delta_x * (posY - self.left_center_y)) / self.left_delta_y)

    def right_x_func_y(self, posY: int) -> int:
        return int(self.right_center_x + (self.right_delta_x * (posY - self.right_center_y)) / self.right_delta_y)
    