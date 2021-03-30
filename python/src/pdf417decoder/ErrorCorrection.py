from typing import Tuple
from pdf417decoder import Modulus
from pdf417decoder.Polynomial import ONE, Polynomial, ZERO

def test_codewords(codewords: list[int], error_correction_length: int) -> tuple[int, list[int]]:
    """ Decode the received codewords """
    poly_codewords = Polynomial(0, 0, codewords)

    # create syndrom coefficients array
    syndrome = list[int]([0] * error_correction_length)

    # assume new errors
    error = False
    
    # test for errors
    # if the syndrom array is all zeros, there is no error
    for i in range(error_correction_length, 0, -1):
        # TODO: This may have been translated incorrectly! Confirm it's not broken.
        # Original Code: if((Syndrome[ErrorCorrectionLength - Index] = PolyCodewords.EvaluateAt(Modulus.ExpTable[Index])) != 0) Error = true;
        mod_exp_table_result = Modulus.exp_table[i]
        evaluate_result = poly_codewords.evaluate_at(mod_exp_table_result)
        syndrome_index = error_correction_length - i
        syndrome[syndrome_index] = evaluate_result
        if (syndrome[syndrome_index] != 0):
            error = True
    
    if (not error):
        return (0, codewords)

    # convert syndrom array to polynomial
    poly_syndrome = Polynomial(0, 0, syndrome)
    
    # Greatest Common Divisor (return -1 if error cannot be corrected)
    result = euclidean_algorithm(error_correction_length, poly_syndrome)

    if (not result[0]):
        return (-1, codewords)

    error_locator = result[1]
    error_evaluator = result[2]

    error_locations = find_error_locations(error_locator)

    if (error_locations is None):
        return (-1, codewords)

    formal_derivative = find_formal_derivatives(error_locator)

    errors = len(error_locations)

    # This is directly applying Forney's Formula
    for i in range(errors):
        error_location = error_locations[i]
        error_position = len(codewords) - 1 - Modulus.log_table[Modulus.invert(error_location)]

        if (error_position < 0):
            return (-1, codewords)

        error_magnitude = Modulus.divide(Modulus.negate(error_evaluator.evaluate_at(error_location)), formal_derivative.evaluate_at(error_location))
        corrected_codeword = Modulus.subtract(codewords[error_position], error_magnitude)
        codewords[error_position] = corrected_codeword
        error_locations[i] = error_position

    return (errors, codewords)

def euclidean_algorithm(error_correction_length: int, poly_r: Polynomial) -> Tuple[bool,Polynomial,Polynomial]:
    """ Runs the euclidean algorithm (Greatest Common Divisor) until r's degree is less than R/2 """
    poly_r_last = Polynomial(error_correction_length, 1)
    poly_t_last = ZERO
    poly_t = ONE

    # Run Euclidean algorithm until r's degree is less than R/2
    while (poly_r.degree >= (error_correction_length / 2)):
        poly_r_last2 = poly_r_last
        poly_t_last2 = poly_t_last
        poly_r_last = poly_r
        poly_t_last = poly_t

        if (poly_r_last.is_zero):
            return (False, None, None)

        # Divide rLastLast by PolyRLast, with quotient in q and remainder in r
        poly_r = poly_r_last2

        # initial quotient polynomial
        quotient = ZERO

        dlt_inverse = Modulus.invert(poly_r_last.leading_coefficient())

        while (poly_r.degree >= poly_r_last.degree and not poly_r.is_zero):
            # divide polyR and polyRLast leading coefficients
            scale = Modulus.multiply(poly_r.leading_coefficient(), dlt_inverse)

            # degree difference between polyR and polyRLast
            degree_diff = poly_r.degree - poly_r_last.degree
            quotient = quotient.add(Polynomial(degree_diff, scale))
            poly_r = poly_r.subtract(poly_r_last.multiply_by_monomial(degree_diff, scale))

        poly_t = quotient.multiply(poly_t_last).subtract(poly_t_last2).make_negative()

    sigma_tilde_at_zero = poly_t.last_coefficient()

    if (sigma_tilde_at_zero == 0):
        return (False, None, None)
    
    inverse = Modulus.invert(sigma_tilde_at_zero)
    error_locator = poly_t.multiply_by_constant(inverse)
    error_evaluator = poly_r.multiply_by_constant(inverse)

    return (True, error_locator, error_evaluator)

def find_error_locations(error_locator: Polynomial) -> list[int]:
    """
        Finds the error locations as a direct application of Chien's search
        error locations are not error positions within codewords array
    """

    # This is a direct application of Chien's search
    locator_degree = error_locator.degree;
    error_locations = list[int]([0] * locator_degree)
    error_count = 0
    
    for i in range(1, Modulus.MOD):
        if (error_count >= locator_degree): 
            break

        if (error_locator.evaluate_at(i) == 0):
            error_locations[error_count] = i
            error_count += 1
    
    if error_count == locator_degree:
        return error_locations
    else:
        return None


def find_formal_derivatives(error_locator: Polynomial) -> Polynomial:
    """ Finds the error magnitudes by directly applying Forney's Formula """
    locator_degree = error_locator.degree
    derivative_coefficients = list[int]([0] * locator_degree)
    
    for i in range(1, locator_degree + 1):
        derivative_coefficients[locator_degree - i] = Modulus.multiply(i, error_locator.get_coefficient(i))

    return Polynomial(0, 0, derivative_coefficients)
