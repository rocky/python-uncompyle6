def handle(module):
    try:
        module = 1
    except ImportError as exc:
        module = exc
    return module

def handle2(module):
    if module == 'foo':
        try:
            module = 1
        except ImportError as exc:
            module = exc
    return module

try:
    pass
except ImportError as exc:
    pass
finally:
    y = 1
