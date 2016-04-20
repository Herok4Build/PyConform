"""
Parsing Unit Tests

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyconform import parsing
from os import linesep

import unittest


#===============================================================================
# General Functions
#===============================================================================
def print_test_message(testname, indata=None, actual=None, expected=None):
    print '{0}:'.format(testname)
    print ' - input    = {0!r}'.format(indata).replace(linesep, ' ')
    print ' - actual   = {0!r}'.format(actual).replace(linesep, ' ')
    print ' - expected = {0!r}'.format(expected).replace(linesep, ' ')
    print


#===============================================================================
# ParsedStringTypeTests
#===============================================================================
class ParsedStringTypeTests(unittest.TestCase):
    
    def test_pst_init(self):
        indata = (['x'], {})
        pst = parsing.FunctionStringType(indata)
        actual = type(pst)
        expected = parsing.FunctionStringType
        testname = 'FunctionStringType.__init__({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Types do not match')
    
    def test_varpst_init(self):
        indata = (['x'], {})
        pst = parsing.VariableStringType(indata)
        actual = type(pst)
        expected = parsing.VariableStringType
        testname = 'VariableStringType.__init__({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Types do not match')
    
    def test_funcpst_init(self):
        indata = (['x'], {})
        pst = parsing.FunctionStringType(indata)
        actual = type(pst)
        expected = parsing.FunctionStringType
        testname = 'FunctionStringType.__init__({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Types do not match')
    
    def test_operpst_init(self):
        indata = (['x'], {})
        pst = parsing.BinOpStringType(indata)
        actual = type(pst)
        expected = parsing.BinOpStringType
        testname = 'BinOpStringType.__init__({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Types do not match')
        
    def test_pst_init_args(self):
        indata = (['x', 1, -3.2], {})
        pst = parsing.FunctionStringType(indata)
        actual = type(pst)
        expected = parsing.FunctionStringType
        testname = 'FunctionStringType.__init__({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Types do not match')

    def test_pst_obj(self):
        indata = (['x', 1, -3.2], {})
        pst = parsing.FunctionStringType(indata)
        actual = pst.key
        expected = indata[0][0]
        testname = 'FunctionStringType.__init__({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Names do not match')

    def test_pst_args(self):
        indata = (['x', 1, -3.2], {})
        pst = parsing.FunctionStringType(indata)
        actual = pst.args
        expected = tuple(indata[0][1:])
        testname = 'FunctionStringType.__init__({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Names do not match')
                

#===============================================================================
# DefinitionParserTests
#===============================================================================
class DefinitionParserTests(unittest.TestCase):

#===== INTEGERS ================================================================

    def test_parse_integer(self):
        indata = '1'
        actual = parsing.parse_definition(indata)
        expected = int(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Integer parsing failed')

    def test_parse_integer_large(self):
        indata = '98734786423867234'
        actual = parsing.parse_definition(indata)
        expected = int(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Integer parsing failed')

#===== FLOATS ==================================================================

    def test_parse_float_dec(self):
        indata = '1.'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_long(self):
        indata = '1.8374755'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_nofirst(self):
        indata = '.35457'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_exp(self):
        indata = '1e7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_pos_exp(self):
        indata = '1e+7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_neg_exp(self):
        indata = '1e-7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_exp(self):
        indata = '1.e7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_pos_exp(self):
        indata = '1.e+7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_neg_exp(self):
        indata = '1.e-7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_long_exp(self):
        indata = '1.324523e7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_long_pos_exp(self):
        indata = '1.324523e+7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_long_neg_exp(self):
        indata = '1.324523e-7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_nofirst_exp(self):
        indata = '.324523e7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_nofirst_pos_exp(self):
        indata = '.324523e+7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

    def test_parse_float_dec_nofirst_neg_exp(self):
        indata = '.324523e-7'
        actual = parsing.parse_definition(indata)
        expected = float(indata)
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Float parsing failed')

#===== FUNCTIONS ===============================================================

    def test_parse_func(self):
        indata = 'f()'
        actual = parsing.parse_definition(indata)
        expected = parsing.FunctionStringType(('f', {}))
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Function parsing failed')

    def test_parse_func_arg(self):
        indata = 'f(1)'
        actual = parsing.parse_definition(indata)
        expected = parsing.FunctionStringType([['f', 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Function parsing failed')

    def test_parse_func_nested(self):
        g2 = parsing.FunctionStringType([['g', 2]])
        f1g = parsing.FunctionStringType([['f', 1, g2]])
        indata = 'f(1, g(2))'
        actual = parsing.parse_definition(indata)
        expected = f1g
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Function parsing failed')

#===== VARIABLES ===============================================================

    def test_parse_var(self):
        indata = 'x'
        actual = parsing.parse_definition(indata)
        expected = parsing.VariableStringType([['x']])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Variable parsing failed')

    def test_parse_var_index(self):
        indata = 'x[1]'
        actual = parsing.parse_definition(indata)
        expected = parsing.VariableStringType([['x', 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Variable parsing failed')

    def test_parse_var_slice(self):
        indata = 'x[1:2:3]'
        actual = parsing.parse_definition(indata)
        expected = parsing.VariableStringType([['x', slice(1,2,3)]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Variable parsing failed')

#     def test_parse_var_index_nested(self):
#         y0 = parsing.VariableStringType([['y', 0]])
#         x1y = parsing.VariableStringType([['x', 1, y0]])
#         indata = 'x[1, y[0]]'
#         actual = parsing.parse_definition(indata)
#         expected = x1y
#         testname = 'parse_definition({0!r})'.format(indata)
#         print_test_message(testname, indata=indata,
#                            actual=actual, expected=expected)
#         self.assertEqual(actual, expected,
#                          'Variable parsing failed')

#     def test_parse_var_slice_nested(self):
#         y03 = parsing.VariableStringType([['y', slice(0,3)]])
#         x14y = parsing.VariableStringType([['x', slice(1,4), y03]])
#         indata = 'x[1:4, y[0:3]]'
#         actual = parsing.parse_definition(indata)
#         expected = x14y
#         testname = 'parse_definition({0!r})'.format(indata)
#         print_test_message(testname, indata=indata,
#                            actual=actual, expected=expected)
#         self.assertEqual(actual, expected,
#                          'Variable parsing failed')

#===== NEGATION ================================================================

    def test_parse_neg_integer(self):
        indata = '-1'
        actual = parsing.parse_definition(indata)
        expected = parsing.UniOpStringType([['-', 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Negation parsing failed')

    def test_parse_neg_float(self):
        indata = '-1.4'
        actual = parsing.parse_definition(indata)
        expected = parsing.UniOpStringType([['-', 1.4]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Negation parsing failed')

    def test_parse_neg_var(self):
        indata = '-x'
        actual = parsing.parse_definition(indata)
        x = parsing.VariableStringType([['x']])
        expected = parsing.UniOpStringType([['-', x]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Negation parsing failed')

    def test_parse_neg_func(self):
        indata = '-f()'
        actual = parsing.parse_definition(indata)
        f = parsing.FunctionStringType([['f']])
        expected = parsing.UniOpStringType([['-', f]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Negation parsing failed')

#===== POSITIVE ================================================================

    def test_parse_pos_integer(self):
        indata = '+1'
        actual = parsing.parse_definition(indata)
        expected = 1
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Positive operator parsing failed')

    def test_parse_pos_float(self):
        indata = '+1e7'
        actual = parsing.parse_definition(indata)
        expected = 1e7
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Positive operator parsing failed')

    def test_parse_pos_func(self):
        indata = '+f()'
        actual = parsing.parse_definition(indata)
        expected = parsing.FunctionStringType([['f']])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Positive operator parsing failed')

    def test_parse_pos_var(self):
        indata = '+x[1]'
        actual = parsing.parse_definition(indata)
        expected = parsing.VariableStringType([['x', 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Positive operator parsing failed')

#===== POWER ===================================================================

    def test_parse_int_pow_int(self):
        indata = '2^1'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['^', 2, 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Power operator parsing failed')

    def test_parse_float_pow_float(self):
        indata = '2.4 ^ 1e7'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['^', 2.4, 1e7]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Power operator parsing failed')

    def test_parse_func_pow_func(self):
        indata = 'f() ^ g(1)'
        actual = parsing.parse_definition(indata)
        f = parsing.FunctionStringType([['f']])
        g1 = parsing.FunctionStringType([['g', 1]])
        expected = parsing.BinOpStringType([['^', f, g1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Power operator parsing failed')

    def test_parse_var_pow_var(self):
        indata = 'x[1] ^ y'
        actual = parsing.parse_definition(indata)
        x1 = parsing.VariableStringType([['x', 1]])
        y = parsing.VariableStringType([['y']])
        expected = parsing.BinOpStringType([['^', x1, y]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Power operator parsing failed')

#===== DIV =====================================================================

    def test_parse_int_div_int(self):
        indata = '2/1'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['/', 2, 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Division operator parsing failed')

    def test_parse_float_div_float(self):
        indata = '2.4/1e7'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['/', 2.4, 1e7]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Division operator parsing failed')

    def test_parse_func_div_func(self):
        indata = 'f() / g(1)'
        actual = parsing.parse_definition(indata)
        f = parsing.FunctionStringType([['f']])
        g1 = parsing.FunctionStringType([['g', 1]])
        expected = parsing.BinOpStringType([['/', f, g1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Division operator parsing failed')

    def test_parse_var_div_var(self):
        indata = 'x[1] / y'
        actual = parsing.parse_definition(indata)
        x1 = parsing.VariableStringType([['x', 1]])
        y = parsing.VariableStringType([['y']])
        expected = parsing.BinOpStringType([['/', x1, y]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Division operator parsing failed')

#===== MUL =====================================================================

    def test_parse_int_mul_int(self):
        indata = '2*1'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['*', 2, 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Multiplication operator parsing failed')

    def test_parse_float_mul_float(self):
        indata = '2.4*1e7'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['*', 2.4, 1e7]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Multiplication operator parsing failed')

    def test_parse_func_mul_func(self):
        indata = 'f() * g(1)'
        actual = parsing.parse_definition(indata)
        f = parsing.FunctionStringType([['f']])
        g1 = parsing.FunctionStringType([['g', 1]])
        expected = parsing.BinOpStringType([['*', f, g1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Multiplication operator parsing failed')

    def test_parse_var_mul_var(self):
        indata = 'x[1] * y'
        actual = parsing.parse_definition(indata)
        x1 = parsing.VariableStringType([['x', 1]])
        y = parsing.VariableStringType([['y']])
        expected = parsing.BinOpStringType([['*', x1, y]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Multiplication operator parsing failed')

#===== ADD =====================================================================

    def test_parse_int_add_int(self):
        indata = '2+1'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['+', 2, 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Addition operator parsing failed')

    def test_parse_float_add_float(self):
        indata = '2.4+1e7'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['+', 2.4, 1e7]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Addition operator parsing failed')

    def test_parse_func_add_func(self):
        indata = 'f() + g(1)'
        actual = parsing.parse_definition(indata)
        f = parsing.FunctionStringType([['f']])
        g1 = parsing.FunctionStringType([['g', 1]])
        expected = parsing.BinOpStringType([['+', f, g1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Addition operator parsing failed')

    def test_parse_var_add_var(self):
        indata = 'x[1] + y'
        actual = parsing.parse_definition(indata)
        x1 = parsing.VariableStringType([['x', 1]])
        y = parsing.VariableStringType([['y']])
        expected = parsing.BinOpStringType([['+', x1, y]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Addition operator parsing failed')

#===== SUB =====================================================================

    def test_parse_int_sub_int(self):
        indata = '2-1'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['-', 2, 1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Subtraction operator parsing failed')

    def test_parse_float_sub_float(self):
        indata = '2.4-1e7'
        actual = parsing.parse_definition(indata)
        expected = parsing.BinOpStringType([['-', 2.4, 1e7]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Subtraction operator parsing failed')

    def test_parse_func_sub_func(self):
        indata = 'f() - g(1)'
        actual = parsing.parse_definition(indata)
        f = parsing.FunctionStringType([['f']])
        g1 = parsing.FunctionStringType([['g', 1]])
        expected = parsing.BinOpStringType([['-', f, g1]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Subtraction operator parsing failed')

    def test_parse_var_sub_var(self):
        indata = 'x[1] - y'
        actual = parsing.parse_definition(indata)
        x1 = parsing.VariableStringType([['x', 1]])
        y = parsing.VariableStringType([['y']])
        expected = parsing.BinOpStringType([['-', x1, y]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Subtraction operator parsing failed')

#===== Integration =============================================================

    def test_parse_integrated_1(self):
        indata = '2-17.3*x^2'
        actual = parsing.parse_definition(indata)
        x = parsing.VariableStringType([['x']])
        x2 = parsing.BinOpStringType([['^', x, 2]])
        m17p3x2 = parsing.BinOpStringType([['*', 17.3, x2]])
        expected = parsing.BinOpStringType([['-', 2, m17p3x2]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Integrated operator parsing failed')
        
    def test_parse_integrated_2(self):
        indata = '2-17.3*x / f(2.3, x[2:5])'
        actual = parsing.parse_definition(indata)
        x = parsing.VariableStringType([['x']])
        x25 = parsing.VariableStringType([['x', slice(2,5)]])
        f = parsing.FunctionStringType([['f', 2.3, x25]])
        dxf = parsing.BinOpStringType([['/', x, f]])
        m17p3dxf = parsing.BinOpStringType([['*', 17.3, dxf]])
        expected = parsing.BinOpStringType([['-', 2, m17p3dxf]])
        testname = 'parse_definition({0!r})'.format(indata)
        print_test_message(testname, indata=indata,
                           actual=actual, expected=expected)
        self.assertEqual(actual, expected,
                         'Integrated operator parsing failed')


#===============================================================================
# Command-Line Operation
#===============================================================================
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
