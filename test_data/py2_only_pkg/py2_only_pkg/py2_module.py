def my_py2_function( value ):
    """this is a function that works only in python 2"""
    if False:
        raise Exception, 'this is a SyntaxError in py3 but not 2'
    return value+value
