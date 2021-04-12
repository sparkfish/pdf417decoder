import math

from pdf417decoder.BorderSymbol import BorderSymbol

class BorderPattern:
    @property
    def center_x(self) -> int:
        """  """
        return self._center_x

    @center_x.setter
    def center_x(self, value: int):
        self._center_x = value

    @property
    def center_y(self) -> int:
        """  """
        return self._center_y

    @center_y.setter
    def center_y(self, value: int):
        self._center_y = value

    @property
    def delta_x(self) -> int:
        """  """
        return self._delta_x

    @delta_x.setter
    def delta_x(self, value: int):
        self._delta_x = value

    @property
    def delta_y(self) -> int:
        """  """
        return self._delta_y

    @delta_y.setter
    def delta_y(self, value: int):
        self._delta_y = value

    @property
    def border_length(self) -> float:
        """ Border line length """
        return self._border_length

    @border_length.setter
    def border_length(self, value: float):
        self._border_length = value

    @property
    def average_symbol_width(self) -> float:
        """ Barcode average pattern width """
        return self._average_symbol_width

    @average_symbol_width.setter
    def average_symbol_width(self, value: float):
        self._average_symbol_width = value

    def round_away_from_zero(self, x) -> int:
        if x >= 0.0:
            return int(math.floor(x + 0.5))
        else:
            return int(math.ceil(x - 0.5))

    def __init__(self, stop_pattern: bool, symbol_list: list):
        self.center_x = 0
        self.center_y = 0
        self.delta_x = 0
        self.delta_y = 0
        self.border_length = 0.0
        self.average_symbol_width = 0.0

        symbol_count = len(symbol_list)
        total_width = 0
        float_delta_x = 0.0
        float_delta_y = 0.0

        if stop_pattern:
            for symbol in symbol_list:
                self.center_x += symbol.x1
                self.center_y += symbol.y1
                total_width += symbol.x2 - symbol.x1

            self.center_x = int(self.center_x / symbol_count)
            self.center_y = int(self.center_y / symbol_count)

            for symbol in symbol_list:
                float_delta_x += (symbol.x1 - self.center_x) * \
                    (symbol.y1 - self.center_y)
                float_delta_y += (symbol.y1 - self.center_y) * \
                    (symbol.y1 - self.center_y)
        else:
            for symbol in symbol_list:
                self.center_x += symbol.x2
                self.center_y += symbol.y1
                total_width += symbol.x2 - symbol.x1

            self.center_x = int(self.center_x / symbol_count)
            self.center_y = int(self.center_y / symbol_count)

            # slope of x as func of y
            for symbol in symbol_list:
                float_delta_x += (symbol.x2 - self.center_x) * \
                    (symbol.y1 - self.center_y)
                float_delta_y += (symbol.y1 - self.center_y) * \
                    (symbol.y1 - self.center_y)

        # border line length
        self.border_length = math.sqrt(
            (float_delta_x * float_delta_x) + (float_delta_y * float_delta_y))

        # calculate barcode angle of rotation relative to the image
        cos_rot = float_delta_y / self.border_length
        sin_rot = float_delta_x / self.border_length

        # horizontal pattern width
        hor_width = float(total_width) / symbol_count

        # barcode average pattern width
        self.average_symbol_width = cos_rot * hor_width

        # the center position is either too high or too low
        # if the barcode is not parallel to the image coordinates
        center_adj = 0.5 * sin_rot * hor_width

        if (stop_pattern):
            self.center_x += self.round_away_from_zero(center_adj * sin_rot)
            self.center_y += self.round_away_from_zero(center_adj * cos_rot)
        else:
            self.center_x -= self.round_away_from_zero(center_adj * sin_rot)
            self.center_y -= self.round_away_from_zero(center_adj * cos_rot)
            
        self.delta_y = 1000
        self.delta_x = int((self.delta_y * float_delta_x) / float_delta_y)

        # convert to ints (became float during division operations above)
        self.center_x = self.round_away_from_zero(self.center_x)
        self.center_y = self.round_away_from_zero(self.center_y)
