"""
Variable Metadata Class

Copyright 2017-2018, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from cf_units import Unit
from numpy import ndarray, dtype
from namedobjects import NamedObject


class Variable(NamedObject):
    """
    Metadata describing a NetCDF variable
    """

    _NETCDF_TYPES_ = ('byte', 'ubyte', 'char',
                      'short', 'ushort',
                      'int', 'uint',
                      'int64', 'uint64',
                      'float', 'double', 'real')

    _NUMPY_DTYPES_ = (dtype('b'), dtype('u1'), dtype('S1'),
                      dtype('i2'), dtype('u2'),
                      dtype('i4'), dtype('u4'),
                      dtype('i8'), dtype('u8'),
                      dtype('f4'), dtype('f8'), dtype('f4'))

    @classmethod
    def datatype_from_dtype(cls, dt):
        if not isinstance(dt, dtype) or dt not in Variable._NUMPY_DTYPES_:
            raise TypeError('Unrecognized variable dtype {}'.format(dt))
        idt = Variable._NUMPY_DTYPES_.index(dt)
        return Variable._NETCDF_TYPES_[idt]

    def __init__(self, name, definition=None, datatype=None, dimensions=None):
        super(Variable, self).__init__(name)
        self.__definition = self.__validate_definition(definition)
        self.__datatype = self.__validate_datatype(datatype)
        self.__dimensions = self.__validate_dimensions(dimensions)
        self.__attributes = {}

    def __validate_definition(self, definition):
        if definition is None:
            return None
        if not isinstance(definition, (basestring, ndarray)):
            msg = 'Variable {} must have a string or array definition'
            raise TypeError(msg.format(self.name))
        return definition

    def __validate_datatype(self, datatype):
        if datatype is None:
            return None
        if datatype not in Variable._NETCDF_TYPES_:
            msg = 'Variable {} has invalid datatype {!r}'
            raise ValueError(msg.format(self.name, datatype))
        return datatype

    def __validate_dimensions(self, dimensions):
        if dimensions is None:
            return None
        if not isinstance(dimensions, (list, tuple)):
            msg = 'Variable {} must have a list or tuple of dimension names'
            raise TypeError(msg.format(self.name))
        return dimensions

    @classmethod
    def from_netcdf4(cls, ncvar):
        print ncvar.dtype
        dt = cls.datatype_from_dtype(ncvar.dtype)
        print dt
        v = Variable(ncvar.name, datatype=dt, dimensions=ncvar.dimensions)
        for k in ncvar.ncattrs():
            v.attributes[k] = ncvar.getncattr(k)
        return v

    @property
    def definition(self):
        return self.__definition

    @property
    def datatype(self):
        return self.__datatype

    @property
    def dtype(self):
        idt = Variable._NETCDF_TYPES_.index(self.__datatype)
        return Variable._NUMPY_DTYPES_[idt]

    @property
    def dimensions(self):
        return self.__dimensions

    @property
    def attributes(self):
        return self.__attributes

    @property
    def units(self):
        ustr = str(self.attributes.get('units', '?')).split('since')[0].strip()
        return None if ustr in ('', '?', 'unknown') else ustr

    @property
    def refdatetime(self):
        lstr = str(self.attributes.get('units', '?')).split('since')
        rstr = lstr[1].strip() if len(lstr) > 1 else ''
        return None if rstr in ('', '?', 'unknown') else rstr

    @property
    def calendar(self):
        return self.attributes.get('calendar', None)

    def cfunits(self):
        return Unit(self.attributes.get('units'), calendar=self.calendar)

    @property
    def positive(self):
        return self.attributes.get('positive', None)

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False
        elif self.definition != other.definition:
            return False
        elif self.datatype != other.datatype:
            return False
        elif self.dimensions != other.dimensions:
            return False
        elif self.units != other.units:
            return False
        elif self.refdatetime != other.refdatetime:
            return False
        elif self.calendar != other.calendar:
            return False
        elif self.positive != other.positive:
            return False
        else:
            return True