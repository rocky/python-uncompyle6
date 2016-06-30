# Bug in python 3.4 abc.py
# Set comprehension

abstracts = {name
             for name, value in namespace.items()
             if getattr(value, "__isabstractmethod__", False)}
