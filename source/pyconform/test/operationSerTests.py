"""
Fundamental Operators for the Operation Graph Unit Tests

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from os import remove
from os.path import exists
from pyconform import operations as ops
from pyconform.slicetuple import SliceTuple
from os import linesep
from cf_units import Unit

import operator
import numpy as np
import numpy.testing as npt
import netCDF4 as nc
import unittest


#===============================================================================
# General Functions
#===============================================================================
def print_test_message(testname, actual, expected):
    print '{}:'.format(testname)
    print ' - actual   = {}'.format(actual).replace(linesep, ' ')
    print ' - expected = {}'.format(expected).replace(linesep, ' ')
    print
    

#===============================================================================
# OperatorTests
#===============================================================================
class MockOp(ops.Operation):
    def __init__(self, name):
        super(MockOp, self).__init__(name)
    def __eq__(self, other):
        return super(MockOp, self).__eq__(other)
    def __call__(self):
        super(MockOp, self).__call__()


class OperatorTests(unittest.TestCase):
    """
    Unit tests for the operators.Operation class
    """
    def setUp(self):
        ops.Operation._id_ = 0
    
    def test_abc(self):
        opname = 'xop'
        testname = 'Operation.__init__()'
        self.assertRaises(TypeError, ops.Operation, opname)
        print_test_message(testname, TypeError, TypeError)

    def test_init(self):
        opname = 'xop'
        testname = 'Mock Operation.__init__()'
        O = MockOp(opname)
        actual = isinstance(O, ops.Operation)
        expected = True
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Could not create mock Operation object')

    def test_name(self):
        opname = 'xop'
        testname = 'Mock Operation.__init__({!r})'.format(opname)
        O = MockOp(opname)
        actual = O.name
        expected = opname
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation name incorrect')

    def test_str(self):
        opname = 'xop'
        testname = 'Mock Operation.__str__()'.format(opname)
        O = MockOp(opname)
        actual = str(O)
        expected = opname
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation string conversion incorrect')
    
    def test_units_default(self):
        opname = 'xop'
        testname = 'Mock Operation.units'.format(opname)
        O = MockOp(opname)
        actual = O.units
        expected = Unit(1)
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation units incorrect')

    def test_units_from_Unit(self):
        opname = 'xop'
        testname = 'Mock Operation.units = Unit(m)'.format(opname)
        O = MockOp(opname)
        O.units = Unit('m')
        actual = O.units
        expected = Unit('m')
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation units incorrect')

    def test_units_from_str(self):
        opname = 'xop'
        testname = 'Mock Operation.units = m'.format(opname)
        O = MockOp(opname)
        O.units = 'm'
        actual = O.units
        expected = Unit('m')
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation units incorrect')
    
    def test_units_from_tuple(self):
        opname = 'xop'
        testname = 'Mock Operation.units = (days, standard)'.format(opname)
        O = MockOp(opname)
        O.units = ('days from 0001-01-01 00:00:00', 'standard')
        actual = O.units
        expected = Unit('days from 0001-01-01 00:00:00', calendar='standard')
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation units incorrect')
    
    def test_units_bad_unit(self):
        opname = 'xop'
        testname = 'Mock Operation.units = ncxedajbec'.format(opname)
        O = MockOp(opname)
        expected = ValueError
        try:
            O.units = 'ncxedajbec'
        except ValueError:
            actual = ValueError
        else:
            actual = None
            self.assertTrue(False, 'Operation units did not fail')
        print_test_message(testname, actual, expected)

    def test_units_bad_calendar(self):
        opname = 'xop'
        testname = 'Mock Operation.units = (days, ncxedajbec)'.format(opname)
        O = MockOp(opname)
        expected = ValueError
        try:
            O.units = ('days since 0001-01-01 00:00:00', 'ncxedajbec')
        except ValueError:
            actual = ValueError
        else:
            actual = None
            self.assertTrue(False, 'Operation units did not fail')
        print_test_message(testname, actual, expected)
    
    def test_equal_same(self):
        nm = 'xop'
        testname = ('Mock Operation({!r}) == Operation('
                    '{!r})').format(nm, nm)
        O1 = MockOp(nm)
        O2 = MockOp(nm)
        actual = (O1 == O2)
        expected = True
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation equality not correct')

    def test_equal_diff_names(self):
        nm1 = 'xop'
        nm2 = 'yop'
        testname = ('Mock Operation({!r}) == Operation('
                    '{!r})').format(nm1, nm2)
        O1 = MockOp(nm1)
        O2 = MockOp(nm2)
        actual = (O1 == O2)
        expected = False
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Operation equality not correct')    


#===============================================================================
# InputSliceReaderTests
#===============================================================================
class InputSliceReaderTests(unittest.TestCase):
    """
    Unit tests for the operators.InputSliceReader class
    """
    
    def setUp(self):
        self.ncfile = 'vslicetest.nc'
        self.shape = (2,4)
        self.size = reduce(lambda x,y: x*y, self.shape, 1)
        dataset = nc.Dataset(self.ncfile, 'w')
        dataset.createDimension('x', self.shape[0])
        dataset.createDimension('t')
        dataset.createVariable('x', 'd', ('x',))
        dataset.variables['x'][:] = np.arange(self.shape[0])
        dataset.createVariable('t', 'd', ('t',))
        dataset.variables['t'][:] = np.arange(self.shape[1])
        self.var = 'v'
        dataset.createVariable(self.var, 'd', ('x', 't'))
        self.vardata = np.arange(self.size, dtype=np.float64).reshape(self.shape)
        dataset.variables[self.var][:] = self.vardata
        dataset.close()
        self.slice = (slice(0, 1), slice(1, 3))
        
    def tearDown(self):
        if exists(self.ncfile):
            remove(self.ncfile)

    def test_init(self):
        testname = 'InputSliceReader.__init__()'
        VSR = ops.InputSliceReader(self.ncfile, self.var)
        actual = type(VSR)
        expected = ops.InputSliceReader
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_init_filename_failure(self):
        testname = 'InputSliceReader.__init__(bad filename)'
        actual = OSError
        expected = OSError
        self.assertRaises(OSError, 
                          ops.InputSliceReader, 'badname.nc', self.var)
        print_test_message(testname, actual, expected)

    def test_init_varname_failure(self):
        testname = 'InputSliceReader.__init__(bad variable name)'
        actual = OSError
        expected = OSError
        self.assertRaises(OSError, 
                          ops.InputSliceReader, self.ncfile, 'badvar')
        print_test_message(testname, actual, expected)

    def test_init_with_slice(self):
        testname = 'InputSliceReader.__init__(slice)'
        VSR = ops.InputSliceReader(self.ncfile, self.var, self.slice)
        actual = type(VSR)
        expected = ops.InputSliceReader
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_call(self):
        testname = 'InputSliceReader().__call__()'
        VSR = ops.InputSliceReader(self.ncfile, self.var)
        actual = VSR()
        expected = self.vardata
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected,
                               '{} failed'.format(testname))

    def test_call_slice(self):
        testname = 'InputSliceReader(slice).__call__()'
        VSR = ops.InputSliceReader(self.ncfile, self.var, self.slice)
        actual = VSR()
        expected = self.vardata[self.slice]
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected,
                               '{} failed'.format(testname))

    def test_equal(self):
        testname = 'InputSliceReader() == InputSliceReader()'
        VSR1 = ops.InputSliceReader(self.ncfile, self.var, self.slice)
        VSR2 = ops.InputSliceReader(self.ncfile, self.var, self.slice)
        actual = VSR1 == VSR2
        expected = True
        print_test_message(testname, actual, expected)
        self.assertTrue(actual, '{} failed'.format(testname))


#===============================================================================
# FunctionEvaluatorTests
#===============================================================================
class FunctionEvaluatorTests(unittest.TestCase):
    """
    Unit tests for the operators.FunctionEvaluator class
    """
    
    def setUp(self):
        self.params = [np.arange(2*3, dtype=np.float64).reshape((2,3)),
                       np.arange(2*3, dtype=np.float64).reshape((2,3)) + 10.]
        
    def tearDown(self):
        pass

    def test_init(self):
        opname = '1'
        testname = 'FunctionEvaluator.__init__(function)'
        FE = ops.FunctionEvaluator(opname, lambda: 1)
        actual = type(FE)
        expected = ops.FunctionEvaluator
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_init_fail(self):
        opname = 'int(1)'
        testname = 'FunctionEvaluator.__init__(non-function)'
        self.assertRaises(TypeError, ops.FunctionEvaluator, opname, 1)
        actual = TypeError
        expected = TypeError
        print_test_message(testname, actual, expected)

    def test_unity(self):
        opname = 'identity'
        testname = 'FunctionEvaluator(lambda x: x).__call__(x)'
        FE = ops.FunctionEvaluator(opname, lambda x: x)
        actual = FE(self.params[0])
        expected = self.params[0]
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))
        
    def test_add(self):
        opname = 'add(a,b)'
        testname = 'FunctionEvaluator(add).__call__(a, b)'
        FE = ops.FunctionEvaluator(opname, operator.add)
        actual = FE(*self.params)
        expected = operator.add(*self.params)
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))

    def test_add_constant_1st(self):
        opname = 'add(1,a)'
        testname = 'FunctionEvaluator(add, 1).__call__(a)'
        FE = ops.FunctionEvaluator(opname, operator.add, args=[1])
        actual = FE(self.params[0])
        expected = operator.add(1, self.params[0])
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))

    def test_add_constant_2nd(self):
        opname = 'add(a,2)'
        testname = 'FunctionEvaluator(add, None, 2).__call__(a)'
        FE = ops.FunctionEvaluator(opname, operator.add, args=[None, 2])
        actual = FE(self.params[0])
        expected = operator.add(self.params[0], 2)
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))

    def test_sub(self):
        opname = 'sub(a,b)'
        testname = 'FunctionEvaluator(sub).__call__(a, b)'
        FE = ops.FunctionEvaluator(opname, operator.sub)
        actual = FE(*self.params)
        expected = operator.sub(*self.params)
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))

    def test_equal(self):
        opname = 'sub(a,b)'
        testname = 'FunctionEvaluator() == FunctionEvaluator()'
        FE1 = ops.FunctionEvaluator(opname, operator.sub)
        FE2 = ops.FunctionEvaluator(opname, operator.sub)
        actual = FE1 == FE2
        expected = True
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected,
                               '{} failed'.format(testname))


#===============================================================================
# OutputSliceHandleTests
#===============================================================================
class OutputSliceHandleTests(unittest.TestCase):
    """
    Unit tests for the operators.OutputSliceHandle class
    """
    
    def setUp(self):
        self.ncfile = 'vslicetest.nc'
        self.shape = (2,4)
        self.size = reduce(lambda x,y: x*y, self.shape, 1)
        dataset = nc.Dataset(self.ncfile, 'w')
        dataset.createDimension('x', self.shape[0])
        dataset.createDimension('t')
        dataset.createVariable('x', 'd', ('x',))
        dataset.variables['x'][:] = np.arange(self.shape[0])
        dataset.createVariable('t', 'd', ('t',))
        dataset.variables['t'][:] = np.arange(self.shape[1])
        self.var = 'v'
        dataset.createVariable(self.var, 'd', ('x', 't'))
        self.vardata = np.arange(self.size, dtype=np.float64).reshape(self.shape)
        dataset.variables[self.var][:] = self.vardata
        dataset.close()
        self.slice = (slice(0, 1), slice(1, 3))
        
    def tearDown(self):
        if exists(self.ncfile):
            remove(self.ncfile)

    def test_init(self):
        testname = 'OutputSliceHandle.__init__()'
        OSH = ops.OutputSliceHandle('x')
        actual = type(OSH)
        expected = ops.OutputSliceHandle
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_min_ok(self):
        indata = 1.0
        testname = 'OutputSliceHandle({})'.format(indata)
        OSH = ops.OutputSliceHandle('x', minimum=0.0)
        actual = OSH(indata)
        expected = indata
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))
        
    def test_min_warn(self):
        indata = -1.0
        testname = 'OutputSliceHandle({})'.format(indata)
        OSH = ops.OutputSliceHandle('x', minimum=0.0)
        actual = OSH(indata)
        expected = indata
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_max_ok(self):
        indata = 1.0
        testname = 'OutputSliceHandle({})'.format(indata)
        OSH = ops.OutputSliceHandle('x', maximum=10.0)
        actual = OSH(indata)
        expected = indata
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))
        
    def test_max_warn(self):
        indata = 11.0
        testname = 'OutputSliceHandle({})'.format(indata)
        OSH = ops.OutputSliceHandle('x', maximum=10.0)
        actual = OSH(indata)
        expected = indata
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))


#===============================================================================
# Command-Line Operation
#===============================================================================
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
