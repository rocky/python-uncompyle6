# Bug from python 3.x handling set comprehensions
{y for y in range(3)}

# Bug in python 3.4 (base64.py) in handling dict comprehension
b = {v: k for k, v in enumerate(b3)}

# Bug from Python 3.4 enum
def __new__(classdict):
    members = {k: classdict[k] for k in classdict._member_names}
    return members

# Bug from 3.5.1 enum.py in 2.7, and 3.x
{a for b in bases for a in b.__dict__}
