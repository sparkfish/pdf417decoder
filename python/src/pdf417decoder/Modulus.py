# PDF 417 uses a Base 929 encoding
MOD = 929

exp_table = list[int]([0] * MOD)
log_table = list[int]([0] * MOD)

# Populate exponent and log tables 
current_value = 1
for i in range(MOD):
    exp_table[i] = current_value
    log_table[current_value] = i
    current_value = (3 * current_value) % MOD

def add(a, b) -> int:
    result = (a + b) % MOD
    return result

def subtract(a, b) -> int:
    result = (MOD + a - b) % MOD
    return result

def negate(a) -> int:
    result = (MOD - a) % MOD
    return result

def invert(a) -> int:
    result = exp_table[MOD - log_table[a] - 1]
    return result

def multiply(a, b) -> int:
    if (a == 0 or b == 0):
        return 0

    result = exp_table[(log_table[a] + log_table[b]) % (MOD - 1)]
    return result

def divide(a, b) -> int:
    result = multiply(a, invert(b))
    return result
