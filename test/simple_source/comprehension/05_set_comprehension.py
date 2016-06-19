# Bug in python 3.x handling set comprehensions
{y for y in range(3)}

# Bug in python 3.4 (base64.py) in handling dict comprehension
b = {v: k for k, v in enumerate(b3)}
