"""
Unit Tests for Yacc Parser

Copyright 2017-2018, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyconform.defparser import yacc

import unittest


def yacc_parse(s):
    return yacc.yacc.parse(s)  # @UndefinedVariable


class YaccTests(unittest.TestCase):

    def test_int(self):
        p = yacc_parse('143')
        self.assertEqual(p, 143)

    def test_int_positive(self):
        p = yacc_parse('+143')
        self.assertEqual(p, 143)

    def test_int_negative(self):
        p = yacc_parse('-143')
        self.assertEqual(p, -143)

    def test_float(self):
        p = yacc_parse('12.34')
        self.assertEqual(p, 12.34)

    def test_variable_name_only(self):
        p = yacc_parse('x')
        self.assertEqual(p, yacc.VarType('x', []))

    def test_variable_time(self):
        p = yacc_parse('time')
        self.assertEqual(p, yacc.VarType('time', []))

    def test_variable_positive(self):
        p = yacc_parse('+x')
        self.assertEqual(p, yacc.VarType('x', []))

    def test_variable_negative(self):
        p = yacc_parse('-x')
        self.assertEqual(p, yacc.OpType('-', [yacc.VarType('x', [])]))

    def test_variable_integer_index(self):
        p = yacc_parse('x[2]')
        self.assertEqual(p, yacc.VarType('x', [2]))

    def test_variable_negative_integer_index(self):
        p = yacc_parse('x[-2]')
        self.assertEqual(p, yacc.VarType('x', [-2]))

    def test_variable_positive_integer_index(self):
        p = yacc_parse('x[+2]')
        self.assertEqual(p, yacc.VarType('x', [2]))

    def test_variable_integer_indices(self):
        p = yacc_parse('xyz[ 2 , -3 ,4]')
        self.assertEqual(p, yacc.VarType('xyz', [2, -3, 4]))

    def test_variable_slice(self):
        p = yacc_parse('x[2:-3:4]')
        self.assertEqual(p, yacc.VarType('x', [slice(2, -3, 4)]))

    def test_variable_slice_index(self):
        p = yacc_parse('x[2:-3:4, 7]')
        self.assertEqual(p, yacc.VarType('x', [slice(2, -3, 4), 7]))

    def test_variable_slice_none_1(self):
        p = yacc_parse('x[:-3:4]')
        self.assertEqual(p, yacc.VarType('x', [slice(None, -3, 4)]))

    def test_variable_slice_none_2(self):
        p = yacc_parse('x[1::4]')
        self.assertEqual(p, yacc.VarType('x', [slice(1, None, 4)]))

    def test_variable_slice_none_3(self):
        p = yacc_parse('x[1:4]')
        self.assertEqual(p, yacc.VarType('x', [slice(1, 4)]))

    def test_function_no_args(self):
        p = yacc_parse('f()')
        self.assertEqual(p, yacc.FuncType('f', [], {}))

    def test_function_negative(self):
        p = yacc_parse('-f()')
        self.assertEqual(p, yacc.OpType('-', [yacc.FuncType('f', [], {})]))

    def test_function_one_arg(self):
        p = yacc_parse('f(1)')
        self.assertEqual(p, yacc.FuncType('f', [1], {}))

    def test_function_str1_arg(self):
        p = yacc_parse('f("1")')
        self.assertEqual(p, yacc.FuncType('f', ['1'], {}))

    def test_function_str2_arg(self):
        p = yacc_parse("f('1')")
        self.assertEqual(p, yacc.FuncType('f', ['1'], {}))

    def test_function_two_arg(self):
        p = yacc_parse('f(1, 2)')
        self.assertEqual(p, yacc.FuncType('f', [1, 2], {}))

    def test_function_one_kwd(self):
        p = yacc_parse('f(x=4)')
        self.assertEqual(p, yacc.FuncType('f', [], {'x': 4}))

    def test_function_one_arg_one_kwd(self):
        p = yacc_parse('f(1, a = 4)')
        self.assertEqual(p, yacc.FuncType('f', [1], {'a': 4}))

    def test_function_two_arg_two_kwd(self):
        p = yacc_parse('f(1, 2, a = 4, b=-8)')
        self.assertEqual(p, yacc.FuncType('f', [1, 2], {'a': 4, 'b': -8}))

    def test_add_numbers(self):
        p = yacc_parse('1 + 3.5')
        self.assertEqual(p, 4.5)

    def test_add_number_and_var(self):
        p = yacc_parse('1 + x')
        self.assertEqual(p, yacc.OpType('+', [1, yacc.VarType('x', [])]))

    def test_add_func_and_var(self):
        p = yacc_parse('f(1,2) + x')
        f = yacc.FuncType('f', [1, 2], {})
        x = yacc.VarType('x', [])
        self.assertEqual(p, yacc.OpType('+', [f, x]))

    def test_sub_numbers(self):
        p = yacc_parse('1 - 3.5')
        self.assertEqual(p, -2.5)

    def test_mul_numbers(self):
        p = yacc_parse('2 * 3.5')
        self.assertEqual(p, 7.0)

    def test_div_numbers(self):
        p = yacc_parse('2 / 3.5')
        self.assertEqual(p, 4 / 7.0)

    def test_pow_numbers(self):
        p = yacc_parse('2 ** 3.5')
        self.assertEqual(p, 2**3.5)

    def test_precedence(self):
        p = yacc_parse('6 + -5.0/2 ** 3 - 2*3/2.0 + -(2**2) + (2*2)**3')
        self.assertEqual(p, 6 - 5.0 / 8.0 - 3.0 - 4 + 64)

    def test_lt_numbers(self):
        p = yacc_parse('2 < 3')
        self.assertTrue(p)

    def test_gt_numbers(self):
        p = yacc_parse('5 > 3')
        self.assertTrue(p)

    def test_leq_numbers(self):
        p = yacc_parse('3 <= 3')
        self.assertTrue(p)

    def test_geq_numbers(self):
        p = yacc_parse('3 >= 3')
        self.assertTrue(p)

    def test_eq_numbers(self):
        p = yacc_parse('3 == 3')
        self.assertTrue(p)

    def test_leq_number_variable(self):
        p = yacc_parse('x[2,3] > 4.0')
        self.assertEqual(p, yacc.OpType('>', [yacc.VarType('x', [2, 3]), 4.0]))

    def test_function_variable_group(self):
        p = yacc_parse('2*(f(1,2, c=4) - x[2:3])')
        f = yacc.FuncType('f', [1, 2], {'c': 4})
        x = yacc.VarType('x', [slice(2, 3)])
        f_minus_x = yacc.OpType('-', [f, x])
        self.assertEqual(p, yacc.OpType('*', [2, f_minus_x]))

    def test_sum_vars_factors(self):
        p = yacc_parse('MEG_ISOP*60/68+MEG_MTERP*120/136+MEG_BCARY*180/204')
        MEG_ISOP = yacc.VarType(name='MEG_ISOP', indices=[])
        A = yacc.OpType(name='*', arguments=[MEG_ISOP, 60])
        A = yacc.OpType(name='/', arguments=[A, 68])
        MEG_MTERP = yacc.VarType('MEG_MTERP', [])
        B = yacc.OpType(name='*', arguments=[MEG_MTERP, 120])
        B = yacc.OpType(name='/', arguments=[B, 136])
        MEG_BCARY = yacc.VarType('MEG_BCARY', [])
        C = yacc.OpType(name='*', arguments=[MEG_BCARY, 180])
        C = yacc.OpType(name='/', arguments=[C, 204])
        A_plus_B = yacc.OpType('+', arguments=[A, B])
        A_plus_B_plus_C = yacc.OpType(name='+', arguments=[A_plus_B, C])
        self.assertEqual(p, A_plus_B_plus_C)

    def test_pyparsing_killer(self):
        s = 'MEG_ISOP*60/68+MEG_MTERP*120/136+MEG_BCARY*180/204+MEG_CH3OH*12/32+MEG_CH3COCH3*36/58+MEG_CH3CHO*24/44+MEG_CH2O*12/30+MEG_CO*12/28+MEG_C2H6*24/30+MEG_C3H8*36/44+MEG_C2H4*24/28+MEG_C3H6*36/42+MEG_C2H5OH*24/46+MEG_BIGALK*60/72+MEG_BIGENE*48/56+MEG_TOLUENE*84/92+MEG_HCN*12/27+MEG_HCOOH*12/46+MEG_CH3COOH*24/60'
        yacc_parse(s)


if __name__ == '__main__':
    unittest.main()