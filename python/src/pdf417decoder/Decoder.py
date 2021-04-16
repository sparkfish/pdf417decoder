from math import sqrt
import math
import numpy as np
import cv2
import time
from enum import Enum, auto
from PIL import Image as PIL
from typing import Tuple

import pdf417decoder.Modulus
import pdf417decoder.Polynomial
import pdf417decoder.StaticTables
import pdf417decoder.ErrorCorrection
from pdf417decoder.BarcodeInfo import BarcodeInfo
from pdf417decoder.BarcodeArea import BarcodeArea
from pdf417decoder.BorderPattern import BorderPattern
from pdf417decoder.BorderSymbol import BorderSymbol

class EncodingMode(Enum):
    BYTE = auto()
    TEXT = auto()
    NUMERIC = auto()

class TextEncodingMode(Enum):
    UPPER = auto()
    LOWER = auto()
    MIXED = auto()
    PUNCT = auto()
    SHIFT_UPPER = auto()
    SHIFT_PUNCT = auto()

class PDF417Decoder:
    # Width of Symbol in Bars
    MODULES_IN_CODEWORD = 17

    # Control codewords
    SWITCH_TO_TEXT_MODE = 900
    SWITCH_TO_BYTE_MODE = 901
    SWITCH_TO_NUMERIC_MODE = 902
    SHIFT_TO_BYTE_MODE = 913
    SWITCH_TO_BYTE_MODE_FOR_SIX = 924

    #  User-Defined GLis:
    # Codeword 925 followed by one codeword
    # The program allows for value of 0 to 899.
    # The documentation is not clear one codeword
    # cannot be 810,900 to 811,799.
    # (GLI values from 810,900 to 811,799). These GLis
    # should be used for closed-system applications
    GLI_USER_DEFINED = 925

    # General Purpose GLis:
    # Codeword 926 followed by two codewords
    # representing GLI values from 900 to 810,899
    GLI_GENERAL_PURPOSE = 926

    # international character set
    # Codeword 927 followed by a single codeword
    # with a value ranging from O to 899. The GLI
    # value of 0 is the default interpretation
    # This value is probably ISO 8859 part number
    GLI_CHARACTER_SET = 927

    START_SIG = [9, 2, 2, 2, 2, 2]
    STOP_SIG = [8, 2, 4, 4, 2, 2]

    Y_STEP = [1, -1, 2, -2, 3, -3]

    @property
    def barcodes_info(self) -> list:
        """ Returned array of barcodes binary data plus extra information """
        return self._barcodes_info

    @barcodes_info.setter
    def barcodes_info(self, value: list):    
        self._barcodes_info = value

    def __init__(self, input_image: PIL.Image):
        self.input_image = input_image
        self.global_label_id_character_set = None
        self.global_label_id_character_set_number = None
        self.global_label_id_general_purpose = None
        self.global_label_id_user_defined = None
        self.scan_x = np.zeros((9), dtype = int)
        self.scan_y = np.zeros((9), dtype = int)

    def decode(self) -> int:
        """Decode PDF417 barcode image into binary array

        Args:
            input_image (Image): Barcode image bitmap

        Returns:
            int: Count of decoded barcodes or zero
        """        
        
        if (not self.convert_image()):
            return 0

        if (not self.locate_barcodes()):
            return 0

        # reset results list
        self.barcodes_extra_info_list = list()
        
        # loop for all barcodes found
        for barcode_area in self.barcode_list:
            self.barcode_area = barcode_area
            
            # reset some variables
            self.ind_control = 0
            self.data_rows = 0
            self.data_columns = 0
            self.error_correction_length = 0
            self.error_correction_count = 0
            self.barcode_binary_data = None
            self.barcodes_data = None
            self.barcodes_info = None
            
            self.average_symbol_width = barcode_area.average_symbol_width
            self.max_symbol_error = barcode_area.max_symbol_error

            if (not self.left_indicators()):
                continue
            
            if (not self.right_indicators()):
                continue
            
            if (not self.set_trans_matrix()):
                continue
            
            if (not self.get_codewords()):
                continue

            if (not self.codewords_to_data()): # convert codewords to bytes and text
                continue
            
            result = BarcodeInfo()
            result.barcode_data = self.barcode_binary_data
            result.character_set = self.global_label_id_character_set
            result.gli_character_set_number = self.global_label_id_character_set_number
            result.gli_general_purpose = self.global_label_id_general_purpose
            result.gli_user_defined = self.global_label_id_user_defined
            result.data_columns = self.data_columns
            result.data_rows = self.data_rows
            result.error_correction_length = self.error_correction_length
            result.error_correction_count = self.error_correction_count
            self.barcodes_extra_info_list.append(result)
            
        barcodes_count = len(self.barcodes_extra_info_list)
        
        if (barcodes_count == 0):
            return 0
        
        self.barcodes_info = self.barcodes_extra_info_list
        
        self.barcodes_data = list()
        
        for i in range(barcodes_count):
                self.barcodes_data.append(self.barcodes_info[i].barcode_data)

        return barcodes_count

    def barcode_data_index_to_string(self, index: int) -> str:
        """Convert binary data to string for one result"""
        
        if (self.barcodes_info[index].character_set != None):
            return self.binary_data_to_string(self.barcodes_info[index].barcode_data, self.barcodes_info[index].character_set)
        
        return self.binary_data_to_string(self.barcodes_info[index].barcode_data)

    def binary_data_to_string(self, barcode_binary_data: bytearray, iso_standard: str = "ISO-8859-1") -> str:
        """Convert binary data array to text string

        Args:
            barcode_binary_data (bytearray): Binary byte array
            iso_standard (str, optional): ISO standard "ISO-8859-part". Defaults to "ISO-8859-1".

        Returns:
            str: Text string of binary data
        """
        # convert byte array to string
        binary = barcode_binary_data
        decoded = barcode_binary_data.decode(iso_standard)
        return decoded

    def locate_barcodes(self) -> bool:
        self.bar_pos = list([0] * self.image_width)
        self.barcode_list = list()
        
        start_symbols = list()
        stop_symbols = list()
        
        scan = 0
        
        while (True):
            for row in range(self.image_height):
                # scan the line for array of bars
                if (not self.scan_line(row)):
                    continue
                
                #look for start signature
                self.border_signature(start_symbols, self.START_SIG, row)
                self.border_signature(stop_symbols, self.STOP_SIG, row)
            
            remove_symbols = list()
            # remove all lists with less than 18 symbols
            for index in range(len(start_symbols)):
                if (len(start_symbols[index]) < 18):
                    remove_symbols.append(start_symbols[index])
            
            for remove in remove_symbols:
                start_symbols.remove(remove)
                
            remove_symbols = list()
            # remove all lists with less than 18 symbols
            for index in range(len(stop_symbols)):
                if (len(stop_symbols[index]) < 18):
                    remove_symbols.append(stop_symbols[index])
            
            for remove in remove_symbols:
                stop_symbols.remove(remove)

            # match start and stop patterns
            if (len(start_symbols) != 0 and len(stop_symbols) != 0):
                for start_list in start_symbols:
                    for stop_list in stop_symbols:
                        self.match_start_and_stop(start_list, stop_list)

            if (len(self.barcode_list) > 0 or scan == 1):
                break
            
            # rotate image by 180 degrees and try again
            self.rotate_image_by_180()
            start_symbols.clear()
            stop_symbols.clear()
            self.barcode_list.clear()
            
            scan += 1

        return len(self.barcode_list) > 0

    def rotate_image_by_180(self):
        """ Rotate image by 180 degrees """
        last_row = self.image_height
        last_col = self.image_width - 1
        rev_image_matrix = np.zeros((self.image_height, self.image_width), dtype=bool)
        
        for row in range(self.image_height):
            last_row -= 1
            for col in range(self.image_width):
                rev_image_matrix[row, col] = self.image_matrix[last_row, last_col - col]

        self.image_matrix = rev_image_matrix

    def scan_line(self, row: int) -> bool:
# 		"""Convert image line to black and white bars"""
        
        col = 0
        
        while (col <self.image_width):
            # look for first white pixel
            if (not self.image_matrix[row, col]):
                break
            col += 1
    
        # No transition found
        if (col == self.image_width):
            return False

        col += 1
        while (col <self.image_width):
            # Check if pixel is black and if so, break
            if (self.image_matrix[row, col]):
                break
            col += 1
            
        # No transition found
        if (col == self.image_width):
            return False

        # save first black pixel
        self.bar_end = 0
        self.bar_pos[self.bar_end] = col
        self.bar_end += 1
        
        # loop for pairs
        while (True):
            # look for end of black bar
            while (col < self.image_width and self.image_matrix[row, col] == True):
                col += 1
            
            # make sure last transition was black to white
            if (col == self.image_width):
                 self.bar_end -= 1

            # save white bar position
            self.bar_pos[self.bar_end] = col
            self.bar_end += 1
            
            while (col < self.image_width and self.image_matrix[row, col] == False):
                col += 1

            if (col == self.image_width):
                break
            
            # save black bar position
            self.bar_pos[self.bar_end] = col
            self.bar_end += 1
      
        # make sure there are at least 8 black and white bars
        return self.bar_end > 8

    def border_signature(self, border_symbols: list, signature: list, row: int):
            # search for start or stop signature
            bar_ptr_end = self.bar_end - 8
            
            for bar_ptr in range(0, bar_ptr_end, 2):
                # width of 8 bars
                width = self.bar_pos[bar_ptr + 8] - self.bar_pos[bar_ptr]
                
                # test for signature
                index = 0
                for i in range(6):
                    index = i
                    calc = (34 * (self.bar_pos[bar_ptr + index + 2] - self.bar_pos[bar_ptr + index]) + width) / (2 * width)
                    calc_int = int(calc)
                    if (calc_int != signature[index]):
                        break
                    index += 1

                # no start or stop signature
                if (index < 6):
                    continue

                new_symbol = BorderSymbol(self.bar_pos[bar_ptr], row, self.bar_pos[bar_ptr + 8])

                if (len(border_symbols) == 0):
                    new_symbol_list = list([new_symbol])
                    border_symbols.append(new_symbol_list)
                else:
                    # try to match it to one of the existing lists
                    for symbols in border_symbols:
                        # compare to last symbol
                        last_symbol = symbols[len(symbols) - 1]
                        
                        # not part of current list
                        if (row - last_symbol.y1 >= 18 or abs(new_symbol.x1 - last_symbol.x1) >= 5 or abs(new_symbol.x2 - last_symbol.x2) >= 5):
                            continue
                        
                        # add to current list
                        symbols.append(new_symbol)
                        new_symbol = None
                        break
                        
                    # start a new list
                    if (new_symbol is not None):
                        new_symbol_list = list([new_symbol])
                        border_symbols.append(new_symbol_list)

                # continue search after start signature
                bar_ptr += 6;

    def match_start_and_stop(self, start_list: list, stop_list: list) -> bool:
        # calculate start and stop patterns relative to image coordinates
        start_border = BorderPattern(False, start_list)
        stop_border = BorderPattern(True, stop_list)
        
        # borders slopes must be less than 45 deg
        if (start_border.delta_y <= abs(start_border.delta_x) or stop_border.delta_y <= abs(stop_border.delta_x)):
            return False

        # stop must be to the right of start
        if (stop_border.center_x <= start_border.center_x):
            return False

        # center line
        center_delta_x = stop_border.center_x - start_border.center_x
        center_delta_y = stop_border.center_y - start_border.center_y
        center_length = sqrt(center_delta_x * center_delta_x + center_delta_y * center_delta_y)
        
        # angle bewteen start line and center line must be about 84 to 96
        cos = (start_border.delta_x * center_delta_x + start_border.delta_y * center_delta_y) / (center_length * start_border.border_length)
        if (abs(cos) > 0.1):
            return False
        
        # angle bewteen start line and center line must be about 85 to 95
        cos = (stop_border.delta_x * center_delta_x + stop_border.delta_y * center_delta_y) / (center_length * stop_border.border_length)
        if (abs(cos) > 0.1):
            return False

        # add to the list
        self.barcode_list.append(BarcodeArea(start_border, stop_border));
        return True

    def left_indicators(self) -> bool: 
        # get mid column codeword
        pos_x = self.barcode_area.left_center_x
        pos_y = self.barcode_area.left_center_y
        mid_codeword = self.get_codeword(pos_x, pos_y, self.barcode_area.left_delta_y, -self.barcode_area.left_delta_x)
        last_codeword = mid_codeword
        top_codeword = -1
        bottom_codeword = -1
        
        # move up from center
        error_count = 0
        pos_y -= 1
        for pos_y in range(pos_y, 0, -1):
            pos_x = self.barcode_area.left_x_func_y(pos_y)
            # get cluster plus codeword
            codeword = self.get_codeword(pos_x, pos_y, self.barcode_area.left_delta_y, -self.barcode_area.left_delta_x)

            # valid codeword
            if (codeword >= 0):
                if (codeword == last_codeword):
                    if (self.ind_control != 7):
                        self.set_info(codeword)
                        
                    #save position
                    self.top_left_x = self.scan_x[0]
                    self.top_left_y = self.scan_y[0]
                    top_codeword = codeword
                else:
                    last_codeword = codeword
                    
                error_count = 0
                continue
            
            # error
            error_count += 1
            if (error_count > 20):
                break

        # move down from center
        pos_x = self.barcode_area.left_center_x
        pos_y = self.barcode_area.left_center_y
        last_codeword = mid_codeword
        error_count = 0
        
        pos_y += 1
        for pos_y in range(pos_y, self.image_height):
            # get cluster plus codeword
            pos_x = self.barcode_area.left_x_func_y(pos_y)
            codeword = self.get_codeword(pos_x, pos_y, self.barcode_area.left_delta_y, -self.barcode_area.left_delta_x)
                
            # valid codeword
            if (codeword >= 0):
                if (codeword == last_codeword):
                    if (self.ind_control != 7):
                        self.set_info(codeword)

                    #save position
                    self.bottom_left_x = self.scan_x[0]
                    self.bottom_left_y = self.scan_y[0]
                    bottom_codeword = codeword
                else:
                    last_codeword = codeword
                
                error_count = 0
                continue
            
            # error
            error_count += 1
            if (error_count > 20):
                break

        if (top_codeword < 0 or bottom_codeword < 0):
            return False
        
        cluster = top_codeword >> 10
        self.top_left_row = 3 * int((top_codeword & 0x3ff) / 30) + cluster
        self.top_left_col = -1
        
        cluster = bottom_codeword >> 10
        self.bottom_left_row = 3 * int((bottom_codeword & 0x3ff) / 30) + cluster
        self.bottom_left_col = -1
        
        return True

    def right_indicators(self) -> bool:
        # get mid column codeword
        pos_x = self.barcode_area.right_center_x
        pos_y = self.barcode_area.right_center_y
        mid_codeword = self.rev_get_codeword(pos_x, pos_y, self.barcode_area.right_delta_y, -self.barcode_area.right_delta_x)
        last_codeword = mid_codeword
        top_codeword = -1
        bottom_codeword = -1
        
        # move up from center
        error_count = 0
        for pos_y in range(pos_y, 0, -1):
            pos_x = self.barcode_area.right_x_func_y(pos_y)
            # get cluster plus codeword
            codeword = self.rev_get_codeword(pos_x, pos_y, self.barcode_area.right_delta_y, -self.barcode_area.right_delta_x)

            # valid codeword
            if (codeword >= 0):
                if (codeword == last_codeword):
                    if (self.ind_control != 7):
                        self.set_info(codeword)
                        
                    #save position
                    self.top_right_x = self.scan_x[0]
                    self.top_right_y = self.scan_y[0]
                    top_codeword = codeword
                else:
                    last_codeword = codeword
                    
                error_count = 0
                continue
            
            # error
            error_count += 1
            if (error_count > 20):
                break

        # move down from center
        pos_x = self.barcode_area.right_center_x
        pos_y = self.barcode_area.right_center_y
        last_codeword = mid_codeword
        error_count = 0
        
        pos_y += 1
        for pos_y in range(pos_y, self.image_height):
            # get cluster plus codeword
            pos_x = self.barcode_area.right_x_func_y(pos_y)
            codeword = self.rev_get_codeword(pos_x, pos_y, self.barcode_area.right_delta_y, -self.barcode_area.right_delta_x)
                
            # valid codeword
            if (codeword >= 0):
                if (codeword == last_codeword):
                    if (self.ind_control != 7):
                        self.set_info(codeword)

                    #save position
                    self.bottom_right_x = self.scan_x[0]
                    self.bottom_right_y = self.scan_y[0]
                    bottom_codeword = codeword
                else:
                    last_codeword = codeword
                
                error_count = 0
                continue
            
            # error
            error_count += 1
            if (error_count > 20):
                break

        if (self.ind_control != 7 or top_codeword < 0 or bottom_codeword < 0):
            return False
        
        cluster = top_codeword >> 10
        self.top_right_row = 3 * int((top_codeword & 0x3ff) / 30) + cluster
        self.top_right_col = self.data_columns
        
        cluster = bottom_codeword >> 10
        self.bottom_right_row = 3 * int((bottom_codeword & 0x3ff) / 30) + cluster
        self.bottom_right_col = self.data_columns
        
        return True

    def set_info(self, codeword: int):
        cluster = codeword >> 10
        info = (codeword & 0x3ff) % 30
        
        if (cluster == 0):
            if ((self.ind_control & 1) == 0):
                self.data_rows += info * 3 + 1
                self.ind_control |= 1
            
        elif (cluster == 1):
            if ((self.ind_control & 2) == 0):
                data_rows_extra = info % 3
                self.error_correction_length = 1 << int((info / 3 + 1))
                self.data_rows += data_rows_extra
                self.ind_control |= 2
        elif (cluster == 2):
            if ((self.ind_control & 4) == 0):
                self.data_columns = info + 1
                self.ind_control |= 4
                 
    def set_trans_matrix(self) -> bool:
        matrix = np.zeros((8, 9), dtype = float)
    
        matrix[0, 0] = self.top_left_col
        matrix[0, 1] = self.top_left_row
        matrix[0, 2] = 1.0
        matrix[0, 6] = -self.top_left_col * self.top_left_x
        matrix[0, 7] = -self.top_left_row * self.top_left_x
        matrix[0, 8] = self.top_left_x

        matrix[1, 0] = self.top_right_col
        matrix[1, 1] = self.top_right_row
        matrix[1, 2] = 1.0
        matrix[1, 6] = -self.top_right_col * self.top_right_x
        matrix[1, 7] = -self.top_right_row * self.top_right_x
        matrix[1, 8] = self.top_right_x

        matrix[2, 0] = self.bottom_left_col
        matrix[2, 1] = self.bottom_left_row
        matrix[2, 2] = 1.0
        matrix[2, 6] = -self.bottom_left_col * self.bottom_left_x
        matrix[2, 7] = -self.bottom_left_row * self.bottom_left_x
        matrix[2, 8] = self.bottom_left_x

        matrix[3, 0] = self.bottom_right_col
        matrix[3, 1] = self.bottom_right_row
        matrix[3, 2] = 1.0
        matrix[3, 6] = -self.bottom_right_col * self.bottom_right_x
        matrix[3, 7] = -self.bottom_right_row * self.bottom_right_x
        matrix[3, 8] = self.bottom_right_x

        matrix[4, 3] = self.top_left_col
        matrix[4, 4] = self.top_left_row
        matrix[4, 5] = 1.0
        matrix[4, 6] = -self.top_left_col * self.top_left_y
        matrix[4, 7] = -self.top_left_row * self.top_left_y
        matrix[4, 8] = self.top_left_y

        matrix[5, 3] = self.top_right_col
        matrix[5, 4] = self.top_right_row
        matrix[5, 5] = 1.0
        matrix[5, 6] = -self.top_right_col * self.top_right_y
        matrix[5, 7] = -self.top_right_row * self.top_right_y
        matrix[5, 8] = self.top_right_y

        matrix[6, 3] = self.bottom_left_col
        matrix[6, 4] = self.bottom_left_row
        matrix[6, 5] = 1.0
        matrix[6, 6] = -self.bottom_left_col * self.bottom_left_y
        matrix[6, 7] = -self.bottom_left_row * self.bottom_left_y
        matrix[6, 8] = self.bottom_left_y

        matrix[7, 3] = self.bottom_right_col
        matrix[7, 4] = self.bottom_right_row
        matrix[7, 5] = 1.0
        matrix[7, 6] = -self.bottom_right_col * self.bottom_right_y
        matrix[7, 7] = -self.bottom_right_row * self.bottom_right_y
        matrix[7, 8] = self.bottom_right_y

        for row in range(8):
            row
            # If the element is zero, make it non zero by adding another row
            if (matrix[row, row] == 0):
                for row1 in range(row + 1, 8):
                    if (matrix[row1, row] != 0):
                        break
                    
                if (row1 == 8):
                    return False
                
                for col in range(row, 9):
                    matrix[row, col] += matrix[row1, col]
            
            #make the diagonal element 1.0 
            for col in range(8, row, -1):
                m1 = matrix[row, col]
                m2 = matrix[row, row]
                m3 = m1 / m2
                matrix[row, col] = m3
            
            # subtract current row from next rows to eliminate one value
            for row1 in range(row + 1, 8):
                for col in range(8, row, -1):
                    m1 = matrix[row, col]
                    m2 =  matrix[row1, row]
                    m3 = m1 * m2
                    matrix[row1, col] -= m3

        # go up from last row and eliminate all solved values
        for col in range(7, 0, -1):
            for row in range(col - 1, -1, -1):
                m1 = matrix[row, col]
                m2 = matrix[col, 8]
                m3 = m1 * m2
                matrix[row, 8] -= m3

        # save transformation matrix coefficients
        self.trans4a = matrix[0, 8];
        self.trans4b = matrix[1, 8];
        self.trans4c = matrix[2, 8];
        self.trans4d = matrix[3, 8];
        self.trans4e = matrix[4, 8];
        self.trans4f = matrix[5, 8];
        self.trans4g = matrix[6, 8];
        self.trans4h = matrix[7, 8];
        
        return True

    def get_codewords(self) -> bool:
        try:
            # codewords array
            self.codewords = list([0] * (self.data_columns * self.data_rows))
            cwptr = 0
            
            erasures_count = 0
            
            for barcode_y in range(self.data_rows):
                for barcode_x in range(self.data_columns):
                    codeword = self.data_codeword(barcode_x, barcode_y)
                    
                    if (codeword < 0):
                        self.codewords[cwptr] = 0
                        cwptr += 1
                        erasures_count += 1
                        if (erasures_count > self.error_correction_length / 2):
                            return False
                    else:
                        self.codewords[cwptr] = codeword
                        cwptr += 1
            
            test_result = pdf417decoder.ErrorCorrection.test_codewords(self.codewords, self.error_correction_length)
            error_correction_count = test_result[0]

            # Too many errors decode failed
            if (error_correction_count < 0):
                return False
            
            self.codewords = test_result[1]
            
            return True
        except:
            return False

    def round_away_from_zero(self, x) -> int:
        if x >= 0.0:
            return int(math.floor(x + 0.5))
        else:
            return int(math.ceil(x - 0.5))
        
    def data_codeword(self, data_matrix_x: int, data_matrix_y: int) -> int:
        w = self.trans4g * data_matrix_x + self.trans4h * data_matrix_y + 1.0
        orig_x = self.round_away_from_zero((self.trans4a * data_matrix_x + self.trans4b * data_matrix_y + self.trans4c) / w)
        orig_y = self.round_away_from_zero((self.trans4d * data_matrix_x + self.trans4e * data_matrix_y + self.trans4f) / w)
        
        data_matrix_x += 1
        w = self.trans4g * data_matrix_x + self.trans4h * data_matrix_y + 1.0
        delta_x = self.round_away_from_zero((self.trans4a * data_matrix_x + self.trans4b * data_matrix_y + self.trans4c) / w) - orig_x
        delta_y = self.round_away_from_zero((self.trans4d * data_matrix_x + self.trans4e * data_matrix_y + self.trans4f) / w) - orig_y
        
        codeword = self.get_codeword(orig_x, orig_y, delta_x, delta_y)
        
        if (codeword >= 0 and codeword >> 10 == data_matrix_y % 3):
            return codeword & 0x3ff
        
        # try to fix the problem
        for index in range(len(self.Y_STEP)):
            y = orig_y + self.Y_STEP[index]
            x = orig_x - int((y - orig_y) * delta_y / delta_x)
            codeword = self.get_codeword(x, y, delta_x, delta_y)
            
            if (codeword >= 0 and codeword >> 10 == data_matrix_y % 3):
                return codeword & 0x3ff

        # error return
        return -1;

    def codewords_to_text(self, binary_data: bytearray, seg_len: int):
        """Convert codewords to text"""        
        text_len = 2 * seg_len
        code = 0
        next = 0
        save_mode = TextEncodingMode.UPPER
        ascii_char = 0
        
        for i in range(text_len):
            if ((i & 1) == 0):
                codeword = self.codewords[self.codewords_ptr]
                self.codewords_ptr += 1
                code = int(codeword / 30)
                next = codeword % 30
            else:
                code = next
                if (code == 29 and i == text_len - 1):
                    break

            #switch
            
            loop = True
            
            # While loop is a hack to allow breaking out of the if.
            while (loop):
                loop = False
                if (self._text_encoding_mode == TextEncodingMode.UPPER):
                    ascii_char = pdf417decoder.StaticTables.UPPER_TO_TEXT[code]
                    if (ascii_char != 0):
                        binary_data += ascii_char.to_bytes(1, "little")
                        break
                    
                    if (code == 27):
                        self._text_encoding_mode = TextEncodingMode.LOWER
                    elif (code == 28):
                        self._text_encoding_mode = TextEncodingMode.MIXED
                    else:
                        save_mode = self._text_encoding_mode
                        self._text_encoding_mode = TextEncodingMode.SHIFT_PUNCT
                elif (self._text_encoding_mode == TextEncodingMode.LOWER):
                    ascii_char = pdf417decoder.StaticTables.LOWER_TO_TEXT[code]
                    if (ascii_char != 0):
                        binary_data += ascii_char.to_bytes(1, "little")
                        break
                    
                    if (code == 27):
                        self._text_encoding_mode = TextEncodingMode.SHIFT_UPPER
                    elif (code == 28):
                        self._text_encoding_mode = TextEncodingMode.MIXED
                    else:
                        save_mode = self._text_encoding_mode
                        self._text_encoding_mode = TextEncodingMode.SHIFT_PUNCT
                elif (self._text_encoding_mode == TextEncodingMode.MIXED):
                    ascii_char = pdf417decoder.StaticTables.MIXED_TO_TEXT[code]
                    if (ascii_char != 0):
                        binary_data += ascii_char.to_bytes(1, "little")
                        break
                    
                    if (code == 25):
                        self._text_encoding_mode = TextEncodingMode.PUNCT
                    elif (code == 27):
                        self._text_encoding_mode = TextEncodingMode.LOWER
                    elif (code == 28):
                        self._text_encoding_mode = TextEncodingMode.UPPER
                    else:
                        save_mode = self._text_encoding_mode
                        self._text_encoding_mode = TextEncodingMode.SHIFT_PUNCT
                elif (self._text_encoding_mode == TextEncodingMode.PUNCT):
                    ascii_char = pdf417decoder.StaticTables.PUNCT_TO_TEXT[code]
                    if (ascii_char != 0):
                        binary_data += ascii_char.to_bytes(1, "little")
                        break
                    
                    self._text_encoding_mode = TextEncodingMode.UPPER
                elif (self._text_encoding_mode == TextEncodingMode.SHIFT_UPPER):
                    self._text_encoding_mode = TextEncodingMode.LOWER
                    ascii_char = pdf417decoder.StaticTables.UPPER_TO_TEXT[code]
                    if (ascii_char != 0):
                        binary_data += ascii_char.to_bytes(1, "little")
                        break
                elif (self._text_encoding_mode == TextEncodingMode.SHIFT_PUNCT):
                    self._text_encoding_mode = save_mode
                    ascii_char = pdf417decoder.StaticTables.PUNCT_TO_TEXT[code]
                    if (ascii_char != 0):
                        binary_data += ascii_char.to_bytes(1, "little")
                        break
            
    def get_codeword(self, left_x: int, left_y: int, delta_x: int, delta_y: int):
        # make sure we are on a white to black transition
        result = self.white_to_black_transition(left_x, left_y, delta_x, delta_y)
        left_x = result[0]
        left_y = result[1]
        
        if (left_x == -1 and left_y == -1):
            return -2
            
        # go right looking for color transition
        self.scan_x[0] = left_x
        self.scan_y[0] = left_y
        
        dot_color = True
        t = 1
        x = left_x + 1
        
        while (True):
            if (t >= 9):
                break

            y = left_y + int((x - left_x) * delta_y / delta_x)
            
            if (y >= len(self.image_matrix) or x >= len(self.image_matrix[0])):
                return -2
            
            if (self.image_matrix[y, x] == dot_color):
                x += 1
                continue
            
            dot_color = not dot_color
            self.scan_x[t] = x
            self.scan_y[t] = y
            
            t += 1
            x += 1

        return self.scan_to_codeword()

    def rev_get_codeword(self, right_x: int, right_y: int, delta_x: int, delta_y: int) -> int:
        # make sure we are on a white to black transition
        result = self.white_to_black_transition(right_x, right_y, delta_x, delta_y)
        right_x = result[0]
        right_y = result[1]
        
        if (right_x == -1 and right_y == -1):
            return -1
        
        # go left looking for color transition
        self.scan_x[8] = right_x
        self.scan_y[8] = right_y
        
        dot_color = False
        t = 7
        x = right_x - 1
        
        while (True):
            y = right_y + int((x - right_x) * delta_y / delta_x)
            
            if (abs(y) >= len(self.image_matrix) or abs(x) >= len(self.image_matrix[0])):
                return -2
            
            if (self.image_matrix[y, x] == dot_color):
                x -= 1
                continue
            
            dot_color = not dot_color
            self.scan_x[t] = x
            self.scan_y[t] = y
            
            t -= 1
            x -= 1
            
            if (t < 0):
                break

        return self.scan_to_codeword()

    def white_to_black_transition(self, pos_x: int, pos_y: int, delta_x: int, delta_y: int) -> Tuple[int, int]:
        try:
            # current pixel is black
            if (self.image_matrix[pos_y, pos_x]):
                # pixel on the left is white
                if (not self.image_matrix[pos_y, pos_x - 1]):
                    return (pos_x, pos_y)

                # go left to find first white pixel
                x = pos_x - 1
                while (True):
                    # matching y coordinate
                    y = pos_y + int((x - pos_x) * delta_y / delta_x)

                    if (abs(y) >= len(self.image_matrix) or abs(x) >= len(self.image_matrix[0])):
                        return (-1, -1)
            
                    # pixel is white
                    if (not self.image_matrix[y, x]):
                        return (pos_x, pos_y)

                    # move current pixel one to the left
                    pos_x = x
                    pos_y = y
                    x -= 1

            # current pixel is white
            # go right to the next transition from white to black
            x = pos_x + 1
            while (True):
                # matching y coordinate
                y = pos_y + int((x - pos_x) * delta_y / delta_x)
                
                
                if (abs(y) >= len(self.image_matrix) or abs(x) >= len(self.image_matrix[0])):
                    return (-1, -1)

                # pixel is white
                if (self.image_matrix.shape[0] <= y or self.image_matrix.shape[1] <= x):
                    return (-1, -1)
                
                if (not self.image_matrix[y, x]):
                    x += 1
                    continue

                # return black point
                pos_x = x
                pos_y = y
                return (pos_x, pos_y)
        except:
            return (-1, -1)

    def scan_to_codeword(self) -> int:
        # line slope
        scan_delta_x = self.scan_x[8] - self.scan_x[0]
        scan_delta_y = self.scan_y[8] - self.scan_y[0]

        # line length
        length = sqrt(scan_delta_x * scan_delta_x + scan_delta_y * scan_delta_y)
        
        if (abs(length - self.average_symbol_width) > self.max_symbol_error):
            return -1
        
        # one over one bar width
        inv_width = self.MODULES_IN_CODEWORD / length

        symbol = 0
        mode = 9
        
        # loop for two bars
        for bar_index in range(6):
            bdx = self.scan_x[bar_index + 2] - self.scan_x[bar_index]
            bdy = self.scan_y[bar_index + 2] - self.scan_y[bar_index]
            
            # two bars width must be 2 to 9
            two_bars = self.round_away_from_zero(inv_width * sqrt(bdx * bdx + bdy * bdy))
            
            if (two_bars < 2 or two_bars > 9):
                return -1
            
            # accumulate symbol
            # symbol is made of 6 two bars width
            # we subtract 2 to make the range of 0 to 7 (3 bits)
            # we pack 6 two bar width into 18 bits
            symbol |= (two_bars - 2) << 3 * (5 - bar_index)

            if (bar_index == 0 or bar_index == 4):
                mode += two_bars
            elif (bar_index == 1 or bar_index == 5):
                mode -= two_bars
            
        # test mode
        mode = mode % 9
        
        if (mode != 0 and mode != 3 and mode != 6):
            return -1
            
        # translate symbol to cluster plus codeword
        symbol_table = pdf417decoder.StaticTables.SYMBOL_TABLE
        symbol_found = self.find_symbol(symbol_table, symbol << 12);

        # symbol not found
        if (symbol_found < 0):
            return -1;

        # symbol found
        return symbol_found & 0xfff

    def find_symbol(self, array, element):
        for symbol in array:
            if ((symbol & 0x7ffff000) == element):
                return symbol
            
        return -1

    def codewords_to_data(self) -> bool:
        """Convert codewords to data"""
        # data codewords pointer and end
        self.codewords_ptr = 1;
        codewords_end = self.codewords[0]

        # make sure data length make sense
        if (codewords_end + self.error_correction_length != self.data_columns * self.data_rows):
            return False

        # initialize encoding modes
        self._encoding_mode = EncodingMode.TEXT;
        self._text_encoding_mode = TextEncodingMode.UPPER;

        # binary data result
        binary_data = bytearray()

        while (self.codewords_ptr < codewords_end):
            # load codeword at current pointer
            command = self.codewords[self.codewords_ptr]
            self.codewords_ptr += 1

            # for the first time this codeword can be data
            if (command < 900):
                command = self.SWITCH_TO_TEXT_MODE
                self.codewords_ptr -= 1
            
            # count codewords data 
            seg_end = self.codewords_ptr
            while (seg_end < codewords_end and self.codewords[seg_end] < 900):
                seg_end += 1

            seg_len = seg_end - self.codewords_ptr
            
            if (seg_len == 0):
                continue
            
            if (command == self.SWITCH_TO_BYTE_MODE):
                self._text_encoding_mode = TextEncodingMode.UPPER
                self.codewords_to_bytes(binary_data, seg_len, False)
            elif (command == self.SWITCH_TO_BYTE_MODE_FOR_SIX):
                self._text_encoding_mode = TextEncodingMode.UPPER
                self.codewords_to_bytes(binary_data, seg_len, True)
            elif (command == self.SHIFT_TO_BYTE_MODE):
                shift_byte = self.codewords[self.codewords_ptr]
                self.codewords_ptr += 1
                if (shift_byte >= 900):
                    return False
                binary_data.append(shift_byte)
            elif (command == self.SWITCH_TO_TEXT_MODE):
                self.codewords_to_text(binary_data, seg_len)
            elif (command == self.SWITCH_TO_NUMERIC_MODE):
                self._text_encoding_mode = TextEncodingMode.UPPER
                self.codewords_to_numeric(binary_data, seg_len)
            elif (command == self.GLI_CHARACTER_SET):
                if (len(binary_data) > 0):
                    return False
                
                g1 = self.codewords[self.codewords_ptr]
                self.codewords_ptr += 1
                
                if (g1 >= 900):
                    return False
                
                self.global_label_id_character_set_number = g1
                part = g1 - 2
                
                if (part < 1 or part > 9 and part != 13 and part != 15):
                    part = 1

                self.global_label_id_character_set = "ISO-8859-" + str(part)
            elif (command == self.GLI_GENERAL_PURPOSE):
                if (len(binary_data) > 0):
                    return False
                
                g2 = self.codewords[self.codewords_ptr]
                self.codewords_ptr += 1
                g3 = self.codewords[self.codewords_ptr]
                self.codewords_ptr += 1
                
                if (g2 >= 900 or g3 >= 900):
                    return False
                
                self.global_label_id_general_purpose = 900 * (g2 + 1) + g3
            elif (command == self.GLI_USER_DEFINED):
                if (len(binary_data) > 0):
                    return False
                
                g4 = self.codewords[self.codewords_ptr]
                self.codewords_ptr += 1
                
                if (g4 >= 900):
                    return False
                
                self.global_label_id_user_defined = 810900 + g4
            else:
                return False

        self.barcode_binary_data = binary_data

        # return binary bytes array
        return True

    def codewords_to_bytes(self, binary_data: bytearray, seg_len: int, six_flag: bool):
        """Convert codewords to bytes"""
        # Number of whole 5 codewords blocks
        blocks = int(seg_len / 5)

        # if number of blocks is one or more and SixFlag is false, the last block is not converted 5 to 6
        if ((seg_len % 5) == 0 and blocks >= 1 and not six_flag):
            blocks -= 1

        # loop for blocks 
        for block in range(blocks):
            temp = (900 ** 4) * self.codewords[self.codewords_ptr]
            self.codewords_ptr += 1
            temp += (900 ** 3) * self.codewords[self.codewords_ptr]
            self.codewords_ptr += 1
            temp += (900 ** 2) * self.codewords[self.codewords_ptr]
            self.codewords_ptr += 1
            temp += (900 ** 1) * self.codewords[self.codewords_ptr]
            self.codewords_ptr += 1
            temp += self.codewords[self.codewords_ptr]
            self.codewords_ptr += 1
            
            # convert to bytes
            for index in range(6):
                val = temp >> (40 - 8 * index)
                val_byte = val % 256
                binary_data.append(val_byte);

        # left over
        seg_len -= 5 * blocks
        
        while (seg_len > 0):
            binary_data.append(self.codewords[self.codewords_ptr] % 256)
            self.codewords_ptr += 1
            seg_len -= 1

    def codewords_to_numeric(self, binary_data: bytearray, seg_len: int):
        """Convert codewords to numeric characters"""
        # loop for blocks of 15 or less codewords
        block_len = 0
        
        while (seg_len > 0):
            block_len = min(seg_len, 15)
            
            temp = 0
            
            for index in range(block_len - 1, -1, -1):
                temp += (900 ** index) * self.codewords[self.codewords_ptr]
                self.codewords_ptr += 1

            # convert number to a string
            num_str = str(temp)[1:] # skip first digit, it is 1
            
            for num in num_str:
                binary_data.append(ord(num))
                
            seg_len -= block_len

    def convert_image(self) -> bool:
        """ Convert image to black and white boolean matrix """
        self.image_width = self.input_image.width
        self.image_height = self.input_image.height
        
        np_image = np.array(self.input_image)
        if np_image.shape[2] >= 3:
            gray = cv2.cvtColor(np_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = np_image
        black_white = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        # Save the final cleaned up black and white image.
        #PIL.fromarray(black_white).save("black_and_white.png")
        
        #Load a Black and White created from C# version.
        # bwimage = PIL.open("BlackWhiteImage.png").convert('RGB')
        # black_white_color = np.asarray(bwimage)
        # threshold_result = cv2.threshold(black_white_color, 0, 255, cv2.THRESH_BINARY)
        # threshold_result_0 = threshold_result[0]
        # threshold_result_1 = threshold_result[1]

        self.image_matrix = np.zeros((self.image_height, self.image_width), dtype=bool)
        for y in range(self.image_height):
            for x in range(self.image_width):
                self.image_matrix[y,x] = (black_white[y][x] != 255)
                #self.image_matrix[y,x] = (threshold_result_1[y][x][0] != 255)
        
        return True
