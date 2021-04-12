import math
from pdf417decoder import Modulus

class Polynomial:

    @property
    def coefficients(self) -> list:
        """ Polynomial coefficients """
        return self._coefficients

    @coefficients.setter
    def coefficients(self, value: list):    
        self._coefficients = value

    @property
    def length(self) -> int:
        """ Polynomial length (Typically Coefficients.Length) """
        return self._length

    @length.setter
    def length(self, value: int):    
        self._length = value

    @property
    def degree(self) -> int:
        """ Polynomial degree (Typically Coefficients.Length - 1) """
        return self._degree

    @degree.setter
    def degree(self, value: int):    
        self._degree = value

    def __init__(self, degree: int, coefficient: int, coefficients: list = None):
        if (coefficients is None):
            """ Create a polynomial with one leading non zero value """
            self.degree = degree
            self.length = degree + 1
            self.coefficients = list([0] * self.length)
            self.coefficients[0] = coefficient
            return
        
        self.length = len(coefficients)

        if (self.length > 1 and coefficients[0] == 0):
            first_non_zero = 0

            # count leading zeros
            for i in range(self.length):
                first_non_zero = i
                if (coefficients[i] != 0):
                    break

            if (first_non_zero == self.length):
                # all coefficients are zeros
                self.coefficients = list([0])
                self.length = 1
            else:
                # new length
                self.length -= first_non_zero

                # create shorter coefficients array
                self.coefficients = list([0] * self.length)

                # copy non zero part to new array
                # Array.Copy(Coefficients, FirstNonZero, this.Coefficients, 0, PolyLength);
                for i in range(first_non_zero, len(coefficients)):
                    self.coefficients[i - first_non_zero] = coefficients[i]
        else:
            # save coefficient array argument unchanged
            self.coefficients = coefficients

        # set polynomial degree
        self.degree = self.length - 1;
        
    @property
    def is_zero(self) -> bool:
        """ Test for zero polynomial """
        return self.coefficients[0] == 0

    def get_coefficient(self, degree: int) -> int:
        """ Coefficient value of degree term in this polynomial """
        return self.coefficients[self.degree - degree]

    def last_coefficient(self) -> int:
        """ Coefficient value of zero degree term in this polynomial """
        return self.coefficients[self.degree]

    def leading_coefficient(self) -> int:
        """ Leading coefficient """
        return self.coefficients[0]

    def evaluate_at(self, x) -> int:
        """ Evaluation of this polynomial at a given point """
        if (x == 0): return self.coefficients[0]

        result = 0

        # Return the x^1 coefficient
        if (x == 1):
            # Return the sum of the coefficients
            for coefficient in self.coefficients:
                result = Modulus.add(result, coefficient)
        else:
            result = self.coefficients[0]
            for i in range (1, self.length):
                multiply_result = Modulus.multiply(x, result)
                add_result = Modulus.add(multiply_result, self.coefficients[i])
                result = add_result

        return result

    def make_negative(self) -> 'Polynomial':
        """ Returns a Negative version of this instance """
        result = list([0] * self.length)

        for i in range(self.length):
            result[i] = Modulus.negate(self.coefficients[i])
            
        return Polynomial(0, 0, result)

    def add(self, other: 'Polynomial') -> 'Polynomial':
        if (self.is_zero): 
            return other

        if (other.is_zero):
            return self

        # Assume this polynomial is smaller than the other one
        smaller = self.coefficients
        larger = other.coefficients

        # Assumption is wrong. exchange the two arrays
        if (len(smaller) > len(larger)):
            smaller = other.coefficients
            larger = self.coefficients

        result = list([0] * len(larger))
        delta = len(larger) - len(smaller)

        # Copy high-order terms only found in higher-degree polynomial's coefficients
        # Array.Copy(Larger, 0, Result, 0, Delta);
        for i in range(len(larger)):
            result[i] = larger[i]

        # Add the coefficients of the two polynomials
        # for(int Index = Delta; Index < Larger.Length; Index++)
        for i in range(delta, len(larger)):
            # Result[Index] = Modulus.Add(Smaller[Index - Delta], Larger[Index]);
            result[i] = Modulus.add(smaller[i - delta], larger[i])

        return Polynomial(0, 0, result)

    def subtract(self, other: 'Polynomial') -> 'Polynomial':
        """ Subtract two polynomials """
        if (other.is_zero): return self

        return self.add(other.make_negative())

    def multiply(self, other: 'Polynomial') -> 'Polynomial':
        """ Multiply two polynomials """
        if (self.is_zero or other.is_zero): return ZERO

        result = list([0] * (self.length + other.length - 1))

        for i in range(self.length):
            coeff = self.coefficients[i]
            for j in range(other.length):
                result[i+j] = Modulus.add(result[i+j], Modulus.multiply(coeff, other.coefficients[j]))
                
        return Polynomial(0, 0, result)

    def multiply_by_constant(self, constant: int) -> 'Polynomial':
        """ Multiply by an integer constant """
        if (constant == 0): return ZERO
        if (constant == 1): return self

        result = list([0] * self.length)

        for i in range(self.length):
            result[i] = Modulus.multiply(self.coefficients[i], constant)

        return Polynomial(0, 0, result)

    def multiply_by_monomial(self, degree: int, constant: int) -> 'Polynomial':
        """ Multipies by a Monomial """
        if (constant == 0): return ZERO

        result = list([0] * (self.length + degree))

        for i in range(self.length):
            result[i] = Modulus.multiply(self.coefficients[i], constant)

        return Polynomial(0, 0, result)

    def __str__(self):
        coefficients = '\n'.join([str(num) for num in self.coefficients])
        return 'Degree: {degree}, Length: {length}\r\n{coefficients}'.format(degree=self.degree, length=self.length, coefficients=coefficients)
    
    def export(self, filename):
        text_file = open(filename, "w")
        n = text_file.write(str(self))
        text_file.close()



ZERO = Polynomial(0, 0, list([0]))
ONE = Polynomial(0, 0, list([1]))
