"""
Parsing Module

This module defines the necessary elements to parse a string variable definition
into the recognized elements that are used to construct an Operation Graph.

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyparsing import (nums, alphas, alphanums, oneOf, delimitedList,
                       operatorPrecedence, opAssoc, Word, Combine, Literal,
                       Forward, Suppress, Group, CaselessLiteral, Optional)

#===============================================================================
# FunctionStringType
#===============================================================================
class FunctionStringType(object):
    """
    A parsed function string-type
    """

    def __init__(self, tokens):
        token = tokens[0]
        self.key = token[0]
        self.args = tuple(token[1:])
    def __repr__(self):
        return "<{0} {1}{2} ({3!s}) at {4!s}>".format(self.__class__.__name__,
                                                      self.key,
                                                      self.args,
                                                      repr(str(self)),
                                                      hex(id(self)))
    def __str__(self):
        return "{0}{1!s}".format(self.key, self.args)
    def __eq__(self, other):
        return ((type(self) == type(other)) and
                (self.key == other.key) and
                (self.args == other.args))


#===============================================================================
# VariableStringType - Variable FunctionStringType
#===============================================================================
class VariableStringType(FunctionStringType):
    """
    A parsed variable string-type
    """
    def __str__(self):
        return "{0}{1!s}".format(self.key, list(self.args))


#===============================================================================
# UniOpStringType - Unary Operator FunctionStringType
#===============================================================================
class UniOpStringType(FunctionStringType):
    """
    A parsed unary-operator string-type
    """
    def __str__(self):
        return "({0}{1!s})".format(self.key, self.args[0])


#===============================================================================
# BinOpStringType - Binary Operator FunctionStringType
#===============================================================================
class BinOpStringType(FunctionStringType):
    """
    A parsed binary-operator string-type
    """
    def __str__(self):
        return "({0!s}{1}{2!s})".format(self.args[0], self.key, self.args[1])


#===============================================================================
# DefinitionParser
#===============================================================================

# Negation operator
def _negop_(tokens):
    op, val = tokens[0]
    if op == '+':
        return val
    else:
        return UniOpStringType([[op, val]])

# Binary Operators
def _binop_(tokens):
    left, op, right = tokens[0]
    return BinOpStringType([[op, left, right]])

# INTEGERS: Just any word consisting only of numbers
_INT_ = Word(nums)
_INT_.setParseAction(lambda t: int(t[0]))

# FLOATS: More complicated... can be decimal format or exponential
#         format or a combination of the two
_DEC_FLT_ = ( Combine( Word(nums) + '.' + Word(nums) ) |
              Combine( Word(nums) + '.' ) |
              Combine( '.' + Word(nums) ) )
_EXP_FLT_ = ( Combine( CaselessLiteral('e') +
                       Optional( oneOf('+ -') ) +
                       Word(nums) ) )
_FLOAT_ = ( Combine( Word(nums) + _EXP_FLT_ ) |
            Combine( _DEC_FLT_ + Optional(_EXP_FLT_) ) )
_FLOAT_.setParseAction(lambda t: float(t[0]))

# String _NAME_s ...identifiers for function or variable _NAME_s
_NAME_ = Word( alphas+"_", alphanums+"_" )

# FUNCTIONS: Function arguments can be empty or any combination of
#            ints, _FLOAT_, variables, and even other functions.  Hence,
#            we need a Forward place-holder to start...
_EXPR_PARSER_ = Forward()
_FUNC_ = Group(_NAME_ + (Suppress('(') + 
                         Optional(delimitedList(_EXPR_PARSER_)) +
                         Suppress(')')))
_FUNC_.setParseAction(FunctionStringType)

# VARIABLE NAMES: Can be just string _NAME_s or _NAME_s with blocks
#                 of indices (e.g., [1,2,-4])    
_INDEX_ = Combine( Optional('-') + Word(nums) )
_INDEX_.setParseAction(lambda t: int(t[0]))
_ISLICE_ = _INDEX_ + Optional(Suppress(':') + _INDEX_ +
                              Optional(Suppress(':') + _INDEX_))
_ISLICE_.setParseAction(lambda t: slice(*t) if len(t) > 1 else t[0])
#         variable = Group(_NAME_ + Optional(Suppress('[') +
#                                            delimitedList(_ISLICE_ | 
#                                                          _EXPR_PARSER_) +
#                                          Suppress(']')))
_VARIABLE_ = Group(_NAME_ + Optional(Suppress('[') +
                                     delimitedList(_ISLICE_) +
                                     Suppress(']')))
_VARIABLE_.setParseAction(VariableStringType)

# Expression parser
_EXPR_PARSER_ << operatorPrecedence(_FLOAT_ | _INT_ | _FUNC_ | _VARIABLE_,
                                    [(Literal('^'), 2, opAssoc.RIGHT, _binop_),
                                     (oneOf('+ -'), 1, opAssoc.RIGHT, _negop_),
                                     (oneOf('* /'), 2, opAssoc.RIGHT, _binop_),
                                     (oneOf('+ -'), 2, opAssoc.RIGHT, _binop_)])

# Parse a string variable definition
def parse_definition(strexpr):
    return _EXPR_PARSER_.parseString(strexpr)[0]


#===============================================================================
# Command-Line Operation
#===============================================================================
if __name__ == "__main__":
    pass
