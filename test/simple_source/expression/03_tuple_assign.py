# Github Issue #57 with Python 2.7
def some_function():
    return ['some_string']

def some_other_function():
    some_variable, = some_function()
    print(some_variable)

empty_tup = ()
one_item_tup = ("item1", )
one_item_tup_without_parentheses = "item", 
many_items_tup = ("item1", "item2", "item3")
