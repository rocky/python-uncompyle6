# From 3.6.4 test_argparse.py
# Bug was in parsing ** args
import argparse
def test_namespace_starkwargs_notidentifier(self):
    ns = argparse.Namespace(**{'"': 'quote'})
    string = """Namespace(**{'"': 'quote'})"""
    assert ns ==  string

def test_namespace_kwargs_and_starkwargs_notidentifier(self):
    ns = argparse.Namespace(a=1, **{'"': 'quote'})
    string = """Namespace(a=1, **{'"': 'quote'})"""
    assert ns == string


def test_namespace(self):
    ns = argparse.Namespace(foo=42, bar='spam')
    string = "Namespace(bar='spam', foo=42)"
    assert ns == string
