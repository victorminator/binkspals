import random

def generate_confirmation_code(length):
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def generate_char():
    char_type = random.randint(1, 3)
    if char_type == 1:
        rand_char = str(random.randint(0, 9))
    elif char_type == 2:
        rand_char = chr(random.randint(65, 90))
    else:
        rand_char = chr(random.randint(97, 122))
    return rand_char

def generate_activation_key(length):
    return "".join([generate_char() for _ in range(length)])
