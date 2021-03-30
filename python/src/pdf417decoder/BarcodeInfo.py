class BarcodeInfo:
    """Barcode results extra information"""

    @property
    def barcode_data(self) -> bytearray:
        """Barcode binary (byte array) data"""
        return self._barcode_data

    @barcode_data.setter
    def barcode_data(self, value: bytearray):    
        self._barcode_data = value

    @property
    def character_set(self) -> bytearray:
        """
            Global Label Identifier character sets (ISO-8859-n)
            The n in ISO-8859-n represents numbers 1 to 9, 13 and 15
        """
        return self._character_set

    @character_set.setter
    def character_set(self, value: bytearray):    
        self._character_set = value

    @property
    def gli_character_set_number(self) -> int:
        """
            Global Label Identifier character set number
            This number is two more than the part number
        """
        return self._gli_character_set_number

    @gli_character_set_number.setter
    def gli_character_set_number(self, value: int):    
        self._gli_character_set_number = value

    @property
    def gli_general_purpose(self) -> int:
        """
            Global label identifier general purpose number
            code word 926 value 900 to 810899
        """
        return self._gli_general_purpose

    @gli_general_purpose.setter
    def gli_general_purpose(self, value: int):    
        self._gli_general_purpose = value

    @property
    def gli_user_defined(self) -> int:
        """
            Global label identifier user defined number
            code word 925 value 810,900 to 811,799
        """
        return self._gli_user_defined

    @gli_user_defined.setter
    def gli_user_defined(self, value: int):    
        self._gli_user_defined = value

    @property
    def data_columns(self) -> int:
        """ Data columns """
        return self._data_columns

    @data_columns.setter
    def data_columns(self, value: int):    
        self._data_columns = value

    @property
    def data_rows(self) -> int:
        """ Data rows """
        return self._data_rows

    @data_rows.setter
    def data_rows(self, value: int):    
        self._data_rows = value

    @property
    def error_correction_length(self) -> int:
        """ Error correction length """
        return self._error_correction_length

    @error_correction_length.setter
    def error_correction_length(self, value: int):    
        self._error_correction_length = value

    @property
    def error_correction_count(self) -> int:
        """ Error correction count """
        return self._error_correction_count

    @error_correction_count.setter
    def error_correction_count(self, value: int):    
        self._error_correction_count = value
