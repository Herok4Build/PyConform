"""
Unit Tests for PhysArray functions

Copyright 2017-2018, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyconform.physarrays import PhysArray, UnitsError, PositiveError

import pyconform.physarrays.functions as fn
import cf_units as cu
import numpy as np
import xarray as xr
import unittest


class FunctionsTests(unittest.TestCase):

    def test_is_equal_dataarray_with_matching_units_and_positive_is_true(self):
        v1 = xr.DataArray(1.4, name='v',
                          attrs={'units': 'g', 'positive': 'up'})
        v2 = xr.DataArray(1.4, name='v',
                          attrs={'units': 'g', 'positive': 'up'})
        self.assertTrue(fn.is_equal(v1, v2))

    def test_is_equal_dataarray_with_mismatched_units_is_false(self):
        v1 = xr.DataArray(1.4, name='v',
                          attrs={'units': 'kg', 'positive': 'up'})
        v2 = xr.DataArray(1.4, name='v',
                          attrs={'units': 'g', 'positive': 'up'})
        self.assertFalse(fn.is_equal(v1, v2))

    def test_is_equal_dataarray_with_mismatched_name_is_false(self):
        v1 = xr.DataArray(1.4, name='u',
                          attrs={'units': 'g', 'positive': 'up'})
        v2 = xr.DataArray(1.4, name='v',
                          attrs={'units': 'g', 'positive': 'up'})
        self.assertFalse(fn.is_equal(v1, v2))

    def test_is_equal_dataarray_with_mismatched_positive_is_false(self):
        v1 = xr.DataArray(1.4, name='v', attrs={'units': 'g'})
        v2 = xr.DataArray(1.4, name='v',
                          attrs={'units': 'g', 'positive': 'up'})
        self.assertFalse(fn.is_equal(v1, v2))

    def test_is_equal_dataarray_with_mismatched_values_is_false(self):
        v1 = xr.DataArray(1.4, name='v', attrs={'units': 'g'})
        v2 = xr.DataArray(1.5, name='v', attrs={'units': 'g'})
        self.assertFalse(fn.is_equal(v1, v2))

    def test_convert(self):
        v = PhysArray([[1, 2], [3, 4]], name='v', dims=['x', 'y'],
                      coords=[[0, 1], [1, 2]], units='g')
        v_kg = fn.convert(v, 'kg')
        self.assertIsInstance(v_kg, PhysArray)

    def test_convert_unconvertable_units_raises_units_error(self):
        v = PhysArray([[1, 2], [3, 4]], name='v', dims=['x', 'y'],
                      coords=[[0, 1], [1, 2]], units='g')
        with self.assertRaises(UnitsError):
            fn.convert(v, 'm')

    def test_convert_time_referenced_with_diff_calendar_units_raises_units_error(self):
        v = PhysArray([[1, 2], [3, 4]], name='v', dims=['x', 'y'],
                      coords=[[0, 1], [1, 2]], units='days since 1974-02-06',
                      calendar='noleap')
        to_units = cu.Unit('hours since 2000-01-01', calendar='gregorian')
        with self.assertRaises(UnitsError):
            fn.convert(v, to_units)

    def test_convert_time_referenced_with_same_calendar_units(self):
        v = PhysArray(0.0, name='v', units='days since 1999-01-01',
                      calendar='noleap')
        to_units = cu.Unit('hours since 2000-01-01', calendar='noleap')
        actual = fn.convert(v, to_units)
        expctd = PhysArray(-8760.0, name="convert(v, to='hours since 2000-01-01')",
                           units='hours since 2000-01-01', calendar='noleap')
        self.assertTrue(fn.is_equal(actual, expctd))

    def test_get_dtype_of_float_returns_float64(self):
        self.assertEqual(fn.get_dtype(2.0), np.dtype('float64'))

    def test_get_dtype_of_str_returns_S(self):
        self.assertEqual(fn.get_dtype('a'), np.dtype('S1'))

    def test_get_dtype_of_int_list_returns_int64(self):
        self.assertEqual(fn.get_dtype([1, 2, 3]), np.dtype('int64'))

    def test_get_dtype_of_float_list_returns_float64(self):
        self.assertEqual(fn.get_dtype([1., 2., 3]), np.dtype('float64'))

    def test_get_dtype_of_f_array_returns_float32(self):
        obj = np.array([1, 2, 3], dtype='f')
        self.assertEqual(fn.get_dtype(obj), np.dtype('float32'))

    def test_get_dtype_of_f_dataarray_returns_float32(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')])
        self.assertEqual(fn.get_dtype(obj), np.dtype('float32'))

    def test_string_is_char_type(self):
        self.assertTrue(fn.is_char_type('a'))

    def test_float_is_not_char_type(self):
        self.assertFalse(fn.is_char_type(1.0))

    def test_get_cfunits_of_float_returns_unit_one(self):
        self.assertEqual(fn.get_cfunits(2.0), cu.Unit(1))

    def test_get_cfunits_of_float_ndarray_returns_unit_one(self):
        obj = np.array([1.4])
        self.assertEqual(fn.get_cfunits(obj), cu.Unit(1))

    def test_get_cfunits_of_str_returns_no_unit(self):
        self.assertEqual(fn.get_cfunits('a'), cu.Unit('no unit'))

    def test_get_cfunits_of_f_dataarray_returns_units_property(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'units': 'g'})
        self.assertEqual(fn.get_cfunits(obj), cu.Unit('grams'))

    def test_set_cfunits_of_float_to_m_raises_units_error(self):
        with self.assertRaises(UnitsError):
            fn.set_cfunits(2.0, 'm')

    def test_set_cfunits_of_float_to_no_unit_does_nothing(self):
        fn.set_cfunits(2.0, 'no unit')

    def test_set_cfunits_of_dataarray_saves_units(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'units': 'g'})
        fn.set_cfunits(obj, 'm')
        self.assertEqual(fn.get_cfunits(obj), cu.Unit('m'))

    def test_get_name_of_float_returns_str(self):
        self.assertEqual(fn.get_name(2.0), '2.0')

    def test_get_name_of_str_returns_itself(self):
        self.assertEqual(fn.get_name('a'), 'a')

    def test_get_name_of_dataarray_returns_name(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')])
        self.assertEqual(fn.get_name(obj), 'x')

    def test_get_name_of_ndarray_returns_one_line_str(self):
        obj = np.array([[1, 2], [3, 4]])
        self.assertEqual(fn.get_name(obj), '[[1 2] [3 4]]')

    def test_get_positive_of_float_returns_none(self):
        self.assertIsNone(fn.get_positive(2.0))

    def test_get_positive_of_dataarray_returns_positive(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'units': 'g', 'positive': 'up'})
        self.assertEqual(fn.get_positive(obj), 'up')

    def test_get_positive_of_dataarray_returns_none_if_no_positive(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'units': 'g'})
        self.assertEqual(fn.get_positive(obj), None)

    def test_set_positive_of_float_to_up_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.assertEqual(fn.set_positive(1.0, 'up'))

    def test_set_positive_of_float_to_down_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.assertEqual(fn.set_positive(1.0, 'down'))

    def test_set_positive_of_float_to_none(self):
        fn.set_positive(1.0, None)

    def test_set_positive_of_dataarray_to_up(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'units': 'g'})
        fn.set_positive(obj, 'up')
        self.assertEqual(fn.get_positive(obj), 'up')

    def test_set_positive_of_dataarray_to_invalid_name_raises_value_error(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'units': 'g'})
        with self.assertRaises(ValueError):
            fn.set_positive(obj, 'x')

    def test_flip_of_dataarray_from_up_to_down(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'positive': 'up'})
        actual = fn.flip(obj, 'down')
        expctd = xr.DataArray(np.array([-5, -8, -7], dtype='f'), name='down(x)',
                              dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                              attrs={'positive': 'down'})
        self.assertTrue(fn.is_equal(actual, expctd))

    def test_flip_of_dataarray_from_down_to_up(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'positive': 'down'})
        actual = fn.flip(obj, 'up')
        expctd = xr.DataArray(np.array([-5, -8, -7], dtype='f'), name='up(x)',
                              dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                              attrs={'positive': 'up'})
        self.assertTrue(fn.is_equal(actual, expctd))

    def test_flip_of_dataarray_from_down_to_none_raises_positive_error(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')],
                           attrs={'positive': 'down'})
        with self.assertRaises(PositiveError):
            fn.flip(obj, None)

    def test_flip_of_dataarray_from_none_to_up_raises_positive_error(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')])
        with self.assertRaises(PositiveError):
            fn.flip(obj, 'up')

    def test_flip_of_dataarray_from_up_to_invalid_raises_positive_error(self):
        obj = xr.DataArray(np.array([5, 8, 7], dtype='f'), name='x',
                           dims=['x'], coords=[np.array([0, 1, 2], dtype='d')])
        with self.assertRaises(PositiveError):
            fn.flip(obj, 'x')


if __name__ == "__main__":
    unittest.main()
