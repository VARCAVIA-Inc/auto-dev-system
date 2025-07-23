```python
# math_utils.py

import math

def add(a, b):
    """Restituisce la somma di due numeri."""
    return a + b

def subtract(a, b):
    """Restituisce la differenza tra due numeri."""
    return a - b

def multiply(a, b):
    """Restituisce il prodotto di due numeri."""
    return a * b

def divide(a, b):
    """
    Restituisce il quoziente di due numeri.
    Solleva un ValueError se il divisore è zero.
    """
    if b == 0:
        raise ValueError("Impossibile dividere per zero.")
    return a / b

def power(base, exponent):
    """Restituisce la base elevata all'esponente."""
    return base ** exponent

def square_root(number):
    """
    Restituisce la radice quadrata di un numero.
    Solleva un ValueError se il numero è negativo.
    """
    if number < 0:
        raise ValueError("Impossibile calcolare la radice quadrata di un numero negativo.")
    return math.sqrt(number)

def factorial(n):
    """
    Restituisce il fattoriale di un intero non negativo.
    Solleva un ValueError se il numero non è un intero non negativo.
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("Il fattoriale è definito solo per interi non negativi.")
    if n == 0:
        return 1
    return math.factorial(n)

def is_prime(n):
    """
    Controlla se un numero è primo.
    Restituisce True se n è primo, False altrimenti.
    """
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def find_gcd(a, b):
    """
    Restituisce il Massimo Comune Divisore (GCD) di due numeri interi.
    """
    return math.gcd(a, b)

def find_lcm(a, b):
    """
    Restituisce il Minimo Comune Multiplo (LCM) di due numeri interi.
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)
```