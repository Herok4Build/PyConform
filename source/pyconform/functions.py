"""
Functions for FunctionEvaluator Actions

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from abc import ABCMeta, abstractmethod
from pyconform.physarray import PhysArray, UnitsError
from numpy import sqrt


#===================================================================================================
# Find a function or operator based on key and number of arguments
#===================================================================================================
def find(key, numargs=None):
    try:
        fop = find_operator(key, numargs=numargs)
    except:
        pass
    else:
        return fop
    
    if numargs is not None:
        raise KeyError('No operator {!r} with {} arguments found'.format(key, numargs))

    try:
        fop = find_function(key)
    except:
        raise KeyError('No operator or function {!r} found'.format(key))
    else:
        return fop


#===================================================================================================
# FunctionBase - base class for Function and Operator Classes
#===================================================================================================
class FunctionBase(object):
    __metaclass__ = ABCMeta
    key = 'function'

    @abstractmethod
    def __call__(self, *args, **kwds):
        return 1


####################################################################################################
##### OPERATORS ####################################################################################
####################################################################################################


#===================================================================================================
# Get the function associated with the given key-symbol
#===================================================================================================
def find_operator(key, numargs=None):
    if key not in __OPERATORS__:
        raise KeyError('Operator {!r} not found'.format(key))
    ops = __OPERATORS__[key]
    if numargs is None:
        if len(ops) == 0:
            raise KeyError('Operator {!r} found but not defined'.format(key))
        elif len(ops) == 1:
            return ops.values()[0]
        else:
            raise KeyError(('Operator {!r} has multiple definitions, '
                            'number of arguments required').format(key))
    elif numargs not in ops:
        raise KeyError('Operator {!r} with {} arguments not found'.format(key, numargs))
    else:
        return ops[numargs]


#===================================================================================================
# Operator - From which all 'X op Y'-pattern operators derive
#===================================================================================================
class Operator(FunctionBase):
    key = '?'
    numargs = 2


#===================================================================================================
# NegationOperator
#===================================================================================================
class NegationOperator(Operator):
    key = '-'
    numargs = 1

    def __call__(self, arg):
        return -arg


#===================================================================================================
# AdditionOperator
#===================================================================================================
class AdditionOperator(Operator):
    key = '+'
    numargs = 2

    def __call__(self, left, right):
        return left + right


#===================================================================================================
# SubtractionOperator
#===================================================================================================
class SubtractionOperator(Operator):
    key = '-'
    numargs = 2

    def __call__(self, left, right):
        return left - right


#===================================================================================================
# PowerOperator
#===================================================================================================
class PowerOperator(Operator):
    key = '**'
    numargs = 2

    def __call__(self, left, right):
        return left ** right


#===================================================================================================
# MultiplicationOperator
#===================================================================================================
class MultiplicationOperator(Operator):
    key = '*'
    numargs = 2

    def __call__(self, left, right):
        return left * right


#===================================================================================================
# DivisionOperator
#===================================================================================================
class DivisionOperator(Operator):
    key = '-'
    numargs = 2

    def __call__(self, left, right):
        return left / right


#===================================================================================================
# Operator map - Fixed to prevent user-redefinition!
#===================================================================================================

__OPERATORS__ = {'-': {1: NegationOperator(), 2: SubtractionOperator()},
                 '**': {2: PowerOperator()},
                 '+': {2: AdditionOperator()},
                 '*': {2: MultiplicationOperator()},
                 '/': {2: DivisionOperator()}}

####################################################################################################
##### FUNCTIONS ####################################################################################
####################################################################################################

#===================================================================================================
# Recursively return all subclasses of a given class
#===================================================================================================
def _all_subclasses_(cls):
    return cls.__subclasses__() + [c for s in cls.__subclasses__() for c in _all_subclasses_(s)]


#===================================================================================================
# Function - From which all 'func(...)'-pattern functions derive
#===================================================================================================
class Function(FunctionBase):
    key = 'func'


#===================================================================================================
# Get the function associated with the given key-symbol
#===================================================================================================
def find_function(key):
    func = None
    for c in _all_subclasses_(Function):
        if c.key == key:
            if func is None:
                func = c
            else:
                raise RuntimeError('Function {!r} is multiply defined'.format(key))
    if func is None:
        raise KeyError('Function {!r} not found'.format(key))
    else:
        return func()


#===================================================================================================
# SquareRoot
#===================================================================================================
class SquareRootFunction(Function):
    key = 'sqrt'

    def __call__(self, data):
        if isinstance(data, PhysArray):
            try:
                units = data.units.root(2)
            except:
                raise UnitsError('Cannot take square-root of units {!r}'.format(data.units))
            return PhysArray(sqrt(data), units=units, name='sqrt({})'.format(data.name))
        else:
            return sqrt(data)
