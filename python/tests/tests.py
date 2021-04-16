import pytest

from PIL import Image as PIL
from pdf417decoder import PDF417Decoder

def test_rotated():
    # given an image that has been rotated
    image = PIL.open("tests/rotated.png")
    
    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()
    
    # then the message should be decoded
    assert barcode_count == 1
    assert decoder.barcode_data_index_to_string(0) == "Rotated Image Test"

def test_blurred():
    # given an image that has errors due to blurring
    image = PIL.open("tests/blurred_error_correction.png")
    
    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()
    
    # then the message should be decoded
    assert barcode_count == 1
    assert decoder.barcode_data_index_to_string(0) == "Blurred Image Test: Additional data is being added to this test increase error count. ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"

def test_missing_data():
    # given an image that is upside down
    image = PIL.open("tests/missing_data.png")
    
    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()
    
    # then the message should be decoded
    assert barcode_count == 1
    assert decoder.barcode_data_index_to_string(0) == "Barcode with missing data codewords."
    
def test_character_decodes():
    # given an image that has a barcode with each character type transition
    # permutation (Upper, Lower, Mixed and Punctuation)
    image = PIL.open("tests/character_type_transitions.png")
    
    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()
    
    # then the message should be decoded
    assert barcode_count == 1
    assert decoder.barcode_data_index_to_string(0) == "Character Type Switches Test: AaAAA1A@bbbBb1b@1c1C1111@@d@D@1@@A aA AA 1A @b bb Bb 1b @1 c1 C1 11 1@@ d@ D@ 1@ @"

def test_binary_data():
    # given an image that has a barcode with binary data
    image = PIL.open("tests/binary_data.png")
    
    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()
    
    # then the message should be decoded
    assert barcode_count == 1
    assert decoder.barcode_data_index_to_string(0) == "Pdf417DecoderDemo - Rev 1.0.0 - 2019-05-01 © 2019 Uzi Granot. All rights reserved."

def test_byte_mode_data():
    # given an image that has a barcode with a byte mode block
    image = PIL.open("tests/byte_mode.png")

    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()

    # then the message should match the expected binary data block
    assert barcode_count == 1
    assert decoder.barcode_binary_data == bytearray(b"\x05\x01\xff\xff\x00\x00062S;Gp\x00\xf2\xed\x10\x00\x00\x14\x1e\x00VR3\x01Y3\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x02\x00\x00\\\xda\x00\x008034\xaeiW\rYB\x1c\xd4\x0b\x00\xf2\xd3\x7fO\xf8\xefiS\xa0\xaa\xfb\x9b\xcf0\x16\x13\xc3\x08>\x86Jz\xe8L\xfe\x1f\xebM,R\x05\x00o3\x01\x00")

def test_multiple_barcodes():
    # given an image that has multiple barcodes
    image = PIL.open("tests/multiple_barcodes.png")
    
    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()
    
    # then multiple barcodes should be decoded
    assert barcode_count == 2
    assert decoder.barcode_data_index_to_string(0) == "Multiple"
    assert decoder.barcode_data_index_to_string(1) == "Barcodes Test"

def test_upside_down():
    # given an image that is upside down
    image = PIL.open("tests/upside_down.png")
    
    # when we decode the image
    decoder = PDF417Decoder(image)
    barcode_count = decoder.decode()
    
    # then the message should be decoded
    assert barcode_count == 1
    assert decoder.barcode_data_index_to_string(0) == "Upside Down Test"
    