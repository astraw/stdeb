def my_py3_function(value: int = 2) -> int:  # SyntaxError in py2 (but not 3)
    """this is a function that works only in python 3"""
    return value+value
