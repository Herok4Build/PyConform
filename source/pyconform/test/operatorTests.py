"""
Fundamental Operators for the Operation Graph Unit Tests

COPYRIGHT: 2015, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from os import remove
from os.path import exists
from pyconform import operators as ops
from os import linesep

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
class MockOp(ops.Operator):
    def __init__(self):
        super(MockOp, self).__init__()
    def __call__(self):
        super(MockOp, self).__call__()

class OperatorTests(unittest.TestCase):
    """
    Unit tests for the operators.Operator class
    """
    def setUp(self):
        ops.Operator._id_ = 0
    
    def test_abc(self):
        testname = 'Operator.__init__()'
        self.assertRaises(TypeError, ops.Operator)
        print_test_message(testname, TypeError, TypeError)

    def test_init(self):
        testname = 'Mock Operator.__init__()'
        O = MockOp()
        actual = isinstance(O, ops.Operator)
        expected = True
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected,
                         'Could not create mock Operator object')
        
    def test_id(self):
        O0 = MockOp()
        print_test_message('First Operator.id() == 0', O0.id(), 0)
        self.assertEqual(O0.id(), 0, 'First Operator.id() != 0')
        O1 = MockOp()
        print_test_message('Second Operator.id() == 1', O1.id(), 1)
        self.assertEqual(O1.id(), 1, 'Second Operator.id() != 1')
        O2 = MockOp()
        print_test_message('Third Operator.id() == 2', O2.id(), 2)
        self.assertEqual(O2.id(), 2, 'Third Operator.id() != 2')


#===============================================================================
# VariableSliceReaderTests
#===============================================================================
class VariableSliceReaderTests(unittest.TestCase):
    """
    Unit tests for the operators.VariableSliceReader class
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
        testname = 'VariableSliceReader.__init__()'
        VSR = ops.VariableSliceReader(self.ncfile, self.var)
        actual = type(VSR)
        expected = ops.VariableSliceReader
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_init_filename_failure(self):
        testname = 'VariableSliceReader.__init__(bad filename)'
        actual = OSError
        expected = OSError
        self.assertRaises(OSError, 
                          ops.VariableSliceReader, 'badname.nc', self.var)
        print_test_message(testname, actual, expected)

    def test_init_varname_failure(self):
        testname = 'VariableSliceReader.__init__(bad variable name)'
        actual = OSError
        expected = OSError
        self.assertRaises(OSError, 
                          ops.VariableSliceReader, self.ncfile, 'badvar')
        print_test_message(testname, actual, expected)

    def test_init_with_slice(self):
        testname = 'VariableSliceReader.__init__(slice)'
        VSR = ops.VariableSliceReader(self.ncfile, self.var, self.slice)
        actual = type(VSR)
        expected = ops.VariableSliceReader
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_call(self):
        testname = 'VariableSliceReader().__call__()'
        VSR = ops.VariableSliceReader(self.ncfile, self.var)
        actual = VSR()
        expected = self.vardata
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected,
                               '{} failed'.format(testname))

    def test_call_slice(self):
        testname = 'VariableSliceReader(slice).__call__()'
        VSR = ops.VariableSliceReader(self.ncfile, self.var, self.slice)
        actual = VSR()
        expected = self.vardata[self.slice]
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected,
                               '{} failed'.format(testname))


#===============================================================================
# FunctionEvaluatorTests
#===============================================================================
class FunctionEvaluatorTests(unittest.TestCase):
    """
    Unit tests for the operators.VariableCalculator class
    """
    
    def setUp(self):
        self.params = [np.arange(2*3, dtype=np.float64).reshape((2,3)),
                       np.arange(2*3, dtype=np.float64).reshape((2,3)) + 10.]
        
    def tearDown(self):
        pass

    def test_init(self):
        testname = 'FunctionEvaluator.__init__(function)'
        FE = ops.FunctionEvaluator(lambda: 1)
        actual = type(FE)
        expected = ops.FunctionEvaluator
        print_test_message(testname, actual, expected)
        self.assertEqual(actual, expected, '{} failed'.format(testname))

    def test_init_fail(self):
        testname = 'FunctionEvaluator.__init__(non-function)'
        self.assertRaises(TypeError, ops.FunctionEvaluator, 1)
        actual = TypeError
        expected = TypeError
        print_test_message(testname, actual, expected)

    def test_unity(self):
        testname = 'FunctionEvaluator(lambda x: x).__call__(x)'
        FE = ops.FunctionEvaluator(lambda x: x)
        actual = FE(self.params[0])
        expected = self.params[0]
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))
        
    def test_add(self):
        testname = 'FunctionEvaluator(add).__call__(a, b)'
        FE = ops.FunctionEvaluator(operator.add)
        actual = FE(*self.params)
        expected = operator.add(*self.params)
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))

    def test_sub(self):
        testname = 'FunctionEvaluator(sub).__call__(a, b)'
        FE = ops.FunctionEvaluator(operator.sub)
        actual = FE(*self.params)
        expected = operator.sub(*self.params)
        print_test_message(testname, actual, expected)
        npt.assert_array_equal(actual, expected, '{} failed'.format(testname))


#===============================================================================
# Command-Line Operation
#===============================================================================
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
