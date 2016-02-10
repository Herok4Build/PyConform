"""
Parsing Unit Tests

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from os import linesep, remove
from os.path import exists
from pyconform import parsing
from pyconform import dataset
from pyconform.operators import VariableSliceReader, FunctionEvaluator
from netCDF4 import Dataset as NCDataset
from collections import OrderedDict
from cf_units import Unit

import operator
import numpy
import unittest


#=========================================================================
# print_test_message - Helper function
#=========================================================================
def print_test_message(testname, indata=None, actual=None, expected=None):
    """
    Pretty-print a test message

    Parameters:
        testname: String name of the test
        indata: Input data for testing (if any)
        actual: Actual return value/result
        expected: Expected return value/result
    """
    indent = linesep + ' ' * 14
    print '{}:'.format(testname)
    if indata:
        s_indata = str(indata).replace(linesep, indent)
        print '    input:    {}'.format(s_indata)
    if actual:
        s_actual = str(actual).replace(linesep, indent)
        print '    actual:   {}'.format(s_actual)
    if expected:
        s_expected = str(expected).replace(linesep, indent)
        print '    expected: {}'.format(s_expected)
    print


#=========================================================================
# ParsingTests - Tests for the parsing module
#=========================================================================
class ParsingTests(unittest.TestCase):
    """
    Unit Tests for the pyconform.parsing module
    """

    def setUp(self):        
        self.filenames = OrderedDict([('u1', 'u1.nc'), ('u2', 'u2.nc')])
        self._clear_()
        
        self.fattribs = OrderedDict([('a1', 'attribute 1'),
                                     ('a2', 'attribute 2')])
        self.dims = OrderedDict([('time', 4), ('lat', 3), ('lon', 2)])
        self.vdims = OrderedDict([('u1', ('time', 'lat', 'lon')),
                                  ('u2', ('time', 'lat', 'lon'))])
        self.vattrs = OrderedDict([('lat', {'units': 'degrees_north',
                                            'standard_name': 'latitude'}),
                                   ('lon', {'units': 'degrees_east',
                                            'standard_name': 'longitude'}),
                                   ('time', {'units': 'days since 1979-01-01 0:0:0',
                                             'calendar': 'noleap',
                                             'standard_name': 'time'}),
                                   ('u1', {'units': 'm',
                                           'standard_name': 'u variable 1'}),
                                   ('u2', {'units': 'm',
                                           'standard_name': 'u variable 2'})])
        self.dtypes = {'lat': 'f', 'lon': 'f', 'time': 'f', 'u1': 'd', 'u2': 'd'}
        ydat = numpy.linspace(-90, 90, num=self.dims['lat'],
                              endpoint=True, dtype=self.dtypes['lat'])
        xdat = numpy.linspace(-180, 180, num=self.dims['lon'],
                              endpoint=False, dtype=self.dtypes['lon'])
        tdat = numpy.linspace(0, self.dims['time'], num=self.dims['time'],
                              endpoint=False, dtype=self.dtypes['time'])
        ulen = reduce(lambda x,y: x*y, self.dims.itervalues(), 1)
        ushape = tuple(d for d in self.dims.itervalues())
        u1dat = numpy.linspace(0, ulen, num=ulen, endpoint=False,
                               dtype=self.dtypes['u1']).reshape(ushape)
        u2dat = numpy.linspace(0, ulen, num=ulen, endpoint=False,
                               dtype=self.dtypes['u2']).reshape(ushape)
        self.vdat = {'lat': ydat, 'lon': xdat, 'time': tdat,
                     'u1': u1dat, 'u2': u2dat}

        for vname, fname in self.filenames.iteritems():
            ncf = NCDataset(fname, 'w')
            ncf.setncatts(self.fattribs)
            ncvars = {}
            for dname, dvalue in self.dims.iteritems():
                dsize = dvalue if dname!='time' else None
                ncf.createDimension(dname, dsize)
                ncvars[dname] = ncf.createVariable(dname, 'd', (dname,))
            ncvars[vname] = ncf.createVariable(vname, 'd', self.vdims[vname])
            for vnam, vobj in ncvars.iteritems():
                for aname, avalue in self.vattrs[vnam].iteritems():
                    setattr(vobj, aname, avalue)
                vobj[:] = self.vdat[vnam]
            ncf.close()
            
        self.inpds = dataset.InputDataset('inpds', self.filenames.values())

    def tearDown(self):
        self._clear_()
        
    def _clear_(self):
        for fname in self.filenames.itervalues():
            if exists(fname):
                remove(fname)

    def test_type(self):
        dparser = parsing.DefitionParser()
        actual = type(dparser)
        expected = parsing.DefitionParser
        print_test_message('type(DefinitionParser)', actual, expected)
        self.assertEqual(actual, expected,
                         'DefinitionParser type not correct')

    def test_parse_definition_pow_numbers(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = '2^2.0'
        actual = dparser.parse_definition(indata)
        expected = eval(indata.replace('^','**'))
        print_test_message('DefinitionParser.parse_definition({!r})'.format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parsed incorrectly')

    def test_parse_definition_add_numbers(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = '2 + 1.0'
        actual = dparser.parse_definition(indata)
        expected = eval(indata)
        print_test_message('DefinitionParser.parse_definition({!r})'.format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parsed incorrectly')

    def test_parse_definition_sub_numbers(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = '2 - 1.0'
        actual = dparser.parse_definition(indata)
        expected = eval(indata)
        print_test_message('DefinitionParser.parse_definition({!r})'.format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parsed incorrectly')

    def test_parse_definition_mul_numbers(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = '7 * 2.0'
        actual = dparser.parse_definition(indata)
        expected = eval(indata)
        print_test_message('DefinitionParser.parse_definition({!r})'.format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parsed incorrectly')

    def test_parse_definition_div_numbers(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = '7 / 2.0'
        actual = dparser.parse_definition(indata)
        expected = eval(indata)
        print_test_message('DefinitionParser.parse_definition({!r})'.format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parsed incorrectly')

    def test_parse_definition_neg_numbers(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = '- +2.0'
        actual = dparser.parse_definition(indata)
        expected = eval(indata)
        print_test_message('DefinitionParser.parse_definition({!r})'.format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parsed incorrectly')

    def test_parse_definition_all_numbers(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = '((- +2.0)^4 * 3 / 8.2 + 8) * 3 - 7'
        actual = dparser.parse_definition(indata)
        expected = eval(indata.replace('^', '**'))
        print_test_message('DefinitionParser.parse_definition({!r})'.format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parsed incorrectly')

    def test_parse_definition_var_only(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = 'u1'
        actual = dparser.parse_definition(indata)
        expected = VariableSliceReader(self.filenames[indata], indata)
        print_test_message(('DefinitionParser.'
                            'parse_definition({!r})').format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                      'Definition parser returned wrong type')

    def test_parse_definition_var_plus_1(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = 'u1 + 1'
        self.assertRaises(parsing.UnitsError, dparser.parse_definition, indata)
        actual = parsing.UnitsError
        expected = parsing.UnitsError
        print_test_message(('DefinitionParser.'
                            'parse_definition({!r})').format(indata),
                           actual, expected)
        self.assertIs(actual, expected,
                      'Definition parser returned wrong type')

    def test_parse_definition_var_plus_var(self):
        dparser = parsing.DefitionParser(self.inpds)
        indata = 'u1 + u2'
        actual = dparser.parse_definition(indata)
        expected = FunctionEvaluator('(u1+u2)', operator.add, args=[None, None], units=Unit('m'))
        print_test_message(('DefinitionParser.'
                            'parse_definition({!r})').format(indata),
                           actual, expected)
        self.assertEqual(actual, expected,
                         'Definition parser returned wrong name')
        
        
#===============================================================================
# Command-Line Execution
#===============================================================================
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
