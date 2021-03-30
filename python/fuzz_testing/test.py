import string
import random
import numpy as np
import cv2 
import time
import csv

from PIL import Image
from pdf417decoder import PDF417Decoder
from pdf417gen import encode, render_image

class BarcodeTest:
    ''' Class to generate and store details for a test barcode '''
    def __init__(self, encodedData: string, columns: int, security_level: int, scale: int, ratio: int):
        codes = encode(text, columns=columns, security_level=security_level)

        self.EncodedData = encodedData
        self.OriginalImage = render_image(codes, scale=scale, ratio=ratio) 
        self.OriginalNumpy = np.array(self.OriginalImage)
        self.crappify()

    def crappify(self):
        crap_image = np.array(self.OriginalImage) #.rotate(1))
        self.CrappifiedNumpy = cv2.blur(crap_image,(3,3))
        self.CrappifiedImage = Image.fromarray(self.CrappifiedNumpy, 'RGB')

# Collection of test result successes, failures and decode time for this test run.
fields = ['Columns', 'Security Level', 'Scale', 'Ratio', 'Length', 'Successes', 'Failures', 'Average Decode Time'] 
test_results = list[(int, int, int, int, int, int, int, float)]()
test_number = 0

while (True):
    test_number += 1
    
    # Randomize barcode settings
    columns = random.randint(10,15)
    security_level = random.randint(2,5)
    scale = random.randint(3,5)
    ratio = random.randint(2,5)
    
    # With random text valid for a PDF417 barcode
    text_length = random.randint(1, 5) * 100
    text = ''.join(random.choices(string.ascii_letters + string.digits + "&,:#-.$/+%* =^;<>@[\\]_'~!|()?{}", k=text_length))
    
    # and Create the barcode.
    barcode = BarcodeTest(text, columns, security_level, scale, ratio)
    
    # Search for existing configuration of above settings in test results.
    test_result = (0,0,0,0,0,0,0,0.0)
    for result in test_results:
        if (result[0] == columns and result[1] == security_level and result[2] == scale and result[3] == ratio and result[4] == text_length):
            test_result = result
            break
        
    # Create a new one if not found or remove it from the list if it was found.
    if (test_result[0] == 0):
        test_result == (columns, security_level, scale, ratio, text_length, 0, 0, 0.0)
    else:
        test_results.remove(test_result)

    # Start decoding
    decode_start_time = time.perf_counter()
    try:
        decoder = PDF417Decoder(barcode.CrappifiedImage)
        barcode_count = decoder.decode()
        
        if (barcode_count == 0):
            decoded = ''
        else:
            decoded = decoder.barcode_data_index_to_string(0)
    except:
        decoded = ''
    decode_stop_time = time.perf_counter()
    decode_time = round(decode_stop_time - decode_start_time, 2)

    # Record Success or Failure of decoding
    if (decoded == barcode.EncodedData):
        successes = test_result[1] + 1
        failures = test_result[2]
        total = successes + failures
        total_decode = test_result[3] + decode_time
        avg_decode = round(total_decode / total, 2)
        
        print(f"SUCCESS #{successes} out of {total}: Columns: {columns} Security: {security_level} Scale: {scale} Ratio: {ratio} Length: {text_length} Average time to Decode: {avg_decode} seconds")
        
        # Add updated test result for this random barcode configuration back to the test results.
        test_results.append((columns, security_level, scale, ratio, text_length, successes, failures, total_decode))
    else:
        successes = test_result[1]
        failures = test_result[2] + 1
        total = successes + failures
        total_decode = test_result[3] + decode_time
        avg_decode = round(total_decode / total, 2)
        
        print(f"FAILURE #{failures} out of {total}: Columns: {columns} Security: {security_level} Scale: {scale} Ratio: {ratio} Length: {text_length} Average time to Decode: {avg_decode} seconds")
        
        # Add updated test result for this random barcode configuration back to the test results.
        test_results.append((columns, security_level, scale, ratio, text_length, successes, failures, total_decode))
        
        # Save out failure image if necessary for debugging.
        #barcode.CrappifiedImage.save("errors/failure-" + str(failures) + "_columns-" + str(columns) + "_security-" + str(security_level) + "_ratio-" + str(ratio) + ".png")

    # Export test run results every 20 tests.
    if (test_number % 20 == 0):
        with open('test_results.csv', 'w') as f:
            
            # using csv.writer method from CSV package
            write = csv.writer(f)
            
            write.writerow(fields)
            write.writerows(test_results)
