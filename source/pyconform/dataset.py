"""
Dataset Interface Class

This file contains the interface classes to the input and output multi-file
datasets.

COPYRIGHT: 2015, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from collections import OrderedDict

import netCDF4


#=========================================================================
# parse_dataset_dictionary
#=========================================================================
def parse_dataset_dictionary(dsdict):
    """
    Parse a fully defined dataset dictionary and return a list of FileInfos

    Parameters:
        dsdict (dict): The complete Dataset dictionary definition

    Returns:
        dict: A map of filenames to FileInfo objects
    """
    if not isinstance(dsdict, dict):
        raise TypeError('Dataset dictionary must be of dict type')

    files = OrderedDict()

    # Parse the Dataset dictionary
    for fname, fdict in dsdict.iteritems():
        fobj = FileInfo(fname)

        # Value Type Checking
        if not isinstance(fdict, dict):
            raise TypeError('Dataset file must be specified with a dict')

        # Parse file dimensions (required section)
        if 'dimensions' not in fdict:
            raise KeyError(('Dataset file {!r}: File dict must have dimensions '
                            'section').format(fname))
        if not isinstance(fdict['dimensions'], dict):
            raise TypeError(('Dataset file {!r}: File dimensions section must '
                             'be of a dict').format(fname))
        for name, value in fdict['dimensions'].iteritems():
            if isinstance(value, list):
                if len(value) != 1 or not isinstance(value[0], int):
                    raise TypeError(('Unlimited dimension {!r} in file {!r} '
                                     'must be declared with a list of 1 '
                                     'integer').format(name, fname))
                fobj.dimensions[name] = [int(value[0])]
            elif isinstance(value, int):
                fobj.dimensions[name] = int(value)
            else:
                raise TypeError(('Dimension {!r} in file {!r} must be declared '
                                 'with an integer or a list containing only 1 '
                                 'integer').format(name, fname))

        # Parse file variables (required section)
        if 'variables' not in fdict:
            raise KeyError(('Dataset file {!r}: File dict must have variables '
                            'section').format(fname))
        if not isinstance(fdict['variables'], dict):
            raise TypeError(('Dataset file {!r}: File variables section must '
                             'be of a dict').format(fname))
        for name, value in fdict['variables'].iteritems():
            vobj = VariableInfo(name)
            if not isinstance(value, dict):
                raise TypeError(('Dataset file {!r}: File variable {!r} must '
                                 'be of a dict').format(fname, name))

            if 'type' not in value:
                raise KeyError(('Variable {!r} in file {!r} must have a '
                                'declared type').format(name, fname))
            vobj.dtype = str(value['type'])

            if 'dimensions' not in value:
                raise KeyError(('Variable {!r} in file {!r} must have a '
                                'declared dimensions list').format(name, fname))
            if not isinstance(value['dimensions'], list):
                raise TypeError('Variable dimensions must be a list')
            vobj.dimensions = tuple(value['dimensions'])

            if 'attributes' in value:
                if not isinstance(value['attributes'], dict):
                    raise TypeError(('Variable {!r} in file {!r} must declare '
                                     'attributes in a dict').format(name, fname))
                vobj.attributes = value['attributes']

            if 'definition' in value:
                if not isinstance(value['definition'], (str, unicode)):
                    raise TypeError(('Variable {!r} in file {!r} must declare '
                                     'definition with a string').format(name, fname))
                vobj.definition = str(value['definition'])

            fobj.variables[name] = vobj

        # Parse file attributes (optional section)
        if 'attributes' in fdict:
            if not isinstance(fdict['attributes'], dict):
                raise TypeError('Dataset file attributes must be of type dict')
            for name, value in fdict['attributes'].iteritems():
                fobj.attributes[name] = value

        files[fname] = fobj

    return files


#=========================================================================
# parse_dataset_filelist
#=========================================================================
def parse_dataset_filelist(filenames):
    """
    Parse a list of filenames and return a list of FileInfos

    Parameters:
        filenames (list): The complete list of NetCDF filenames in the dataset

    Returns:
        dict: A map of filenames to FileInfo objects
    """
    if not isinstance(filenames, list):
        raise TypeError('Dataset filenames must be of list type')

    files = OrderedDict()

    for fname in filenames:
        ncf = netCDF4.Dataset(fname)
        fobj = FileInfo(fname)
        for attr in ncf.ncattrs():
            fobj.attributes[attr] = ncf.getncattr(attr)
        for name, obj in ncf.dimensions.iteritems():
            if obj.isunlimited():
                fobj.dimensions[name] = [len(obj)]
            else:
                fobj.dimensions[name] = len(obj)
        for name, obj in ncf.variables.iteritems():
            vobj = VariableInfo(name)
            vobj.dtype = str(obj.dtype)
            for attr in obj.ncattrs():
                vobj.attributes[attr] = obj.getncattr(attr)
            vobj.dimensions = tuple(obj.dimensions)
            fobj.variables[name] = vobj
        ncf.close()
        files[fname] = fobj

    return files

#=========================================================================
# VariableInfo
#=========================================================================


class VariableInfo(object):

    def __init__(self, name):
        """
        Initializer

        Parameters:
            name (str): Name of the variable
        """
        self.name = str(name)
        self.dtype = None
        self.dimensions = tuple()
        self.attributes = OrderedDict()
        self.definition = None

    def __eq__(self, other):
        if self.name != other.name:
            print 'Names: {} != {}'.format(self.name, other.name)
            return False
        if self.dtype != other.dtype:
            print 'Data Type: {} != {}'.format(self.dtype, other.dtype)
            return False
        if self.dimensions != other.dimensions:
            print 'Dimensions: {} != {}'.format(self.dimensions, other.dimensions)
            return False
        if self.attributes != other.attributes:
            print 'Attributes: {} != {}'.format(self.attributes, other.attributes)
            return False
        if self.definition != other.definition:
            print 'Definition: {} != {}'.format(self.definition, other.definition)
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


#=========================================================================
# FileInfo
#=========================================================================
class FileInfo(object):

    def __init__(self, name):
        """
        Initializer

        Parameters:
            name (str): Name/path of the file
        """
        self.name = str(name)
        self.attributes = OrderedDict()
        self.dimensions = OrderedDict()
        self.variables = OrderedDict()

    def __eq__(self, other):
        if self.name != other.name:
            print 'Names: {} != {}'.format(self.name, other.name)
            return False
        if self.dimensions != other.dimensions:
            print 'Dimensions: {} != {}'.format(self.dimensions, other.dimensions)
            return False
        if self.attributes != other.attributes:
            print 'Attributes: {} != {}'.format(self.attributes, other.attributes)
            return False
        if self.variables != other.variables:
            print 'Variables: {} != {}'.format(self.variables, other.variables)
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


#=========================================================================
# Dataset
#=========================================================================
class Dataset(object):

    def __init__(self, name=''):
        """
        Initializer

        Parameters:
            name (str): String name to optionally give to a dataset
        """
        self.name = str(name)
        self.files = OrderedDict()
        self.dimensions = OrderedDict()
        self.variables = []

    def _analyze(self):
        file_1 = self.files.values()[0]
        self.dimensions = OrderedDict(file_1.dimensions)
        self.variables = list(file_1.variables.keys())

        dims_1 = set(self.dimensions.keys())
        vars_1 = set(self.variables)
        for fobj in self.files.values()[1:]:
            dims_i = set(fobj.dimensions.keys())
            dims_1mi = dims_1 - dims_i
            if len(dims_1mi) > 0:
                err_msg = ('Dimensions {} found in file {!r} but not in '
                           '{!r}').format(list(dims_1mi), file_1.name,
                                          fobj.name)
                raise KeyError(err_msg)
            dims_im1 = dims_i - dims_1
            if len(dims_im1) > 0:
                err_msg = ('Dimensions {} found in file {!r} but not in '
                           '{!r}').format(list(dims_im1), fobj.name,
                                          file_1.name)
                raise KeyError(err_msg)
            for dname, dvalue in fobj.dimensions.iteritems():
                if isinstance(dvalue, list):
                    if isinstance(self.dimensions[dname], list):
                        self.dimensions[dname] += dvalue
                    else:
                        err_msg = ('Dimension {!r} is unlimited in file '
                                   '{!r} but limited in file '
                                   '{!r}').format(dname, fobj.name, file_1.name)
                        raise TypeError(err_msg)
                elif isinstance(dvalue, int):
                    if (isinstance(self.dimensions[dname], int) and
                            dvalue != self.dimensions[dname]):
                        err_msg = ('Dimension {!r} in file {!r} has '
                                   'size {} but expected size '
                                   '{}').format(dname, fobj.name, dvalue,
                                                self.dimensions[dname])
                        raise ValueError(err_msg)
                    else:
                        err_msg = ('Dimension {!r} is limited in file '
                                   '{!r} but unlimited in file '
                                   '{!r}').format(dname, fobj.name, file_1.name)
                        raise TypeError(err_msg)

            vars_i = set(fobj.variables.keys())
            vars_1mi = vars_1 - vars_i
            if len(vars_1mi) > 0:
                err_msg = ('Variables {!r} found in file {!r} but not in '
                           '{!r}').format(list(vars_1mi), file_1.name,
                                          fobj.name)
                raise KeyError(err_msg)
            vars_im1 = vars_i - vars_1
            if len(vars_im1) > 0:
                err_msg = ('Variables {!r} found in file {!r} but not in '
                           '{!r}').format(list(vars_im1), fobj.name,
                                          file_1.name)
                raise KeyError(err_msg)
            for vname, vobj in fobj.variables.iteritems():
                if vobj.dtype != file_1.variables[vname].dtype:
                    err_msg = ('Variable {!r} in file {!r} has data type'
                               ' {} but expected '
                               '{}').format(vname, fobj.name, vobj.dtype,
                                            file_1.variables[vname].dtype)
                    raise ValueError(err_msg)
                if vobj.dimensions != file_1.variables[vname].dimensions:
                    err_msg = ('Variable {!r} in file {!r} has dimensions'
                               ' {} but expected '
                               '{}').format(vname, fobj.name, vobj.dimensions,
                                            file_1.variables[vname].dimensions)
                    raise ValueError(err_msg)
                units_1 = file_1.variables[vname].attributes.get('units')
                units_i = vobj.attributes.get('units')
                if units_1 != units_i:
                    err_msg = ('Variable {!r} units {!r} in file {!r} '
                               'does not match units {!r} of same '
                               'variable in file '
                               '{!r}').format(vname, units_i, fobj.name,
                                              units_1, file_1.name)
                    raise ValueError(err_msg)
                stdnm_1 = file_1.variables[
                    vname].attributes.get('standard_name')
                stdnm_i = vobj.attributes.get('standard_name')
                if stdnm_1 != stdnm_i:
                    err_msg = ('Variable {!r} standard name {!r} in file {!r} '
                               'does not match standard name {!r} of same '
                               'variable in file '
                               '{!r}').format(vname, stdnm_i, fobj.name,
                                              stdnm_1, file_1.name)
                    raise ValueError(err_msg)

#=========================================================================
# OutputDataset
#=========================================================================


class OutputDataset(Dataset):

    def __init__(self, name='output', dsdict=OrderedDict()):
        """
        Initializer

        Parameters:
            name (str): String name to optionally give to a dataset
            dsdict (dict): Dictionary describing the dataset, ordered by
                files, file attributes, file dimensions, and file variables.
        """
        super(OutputDataset, self).__init__(name)
        self.files = parse_dataset_dictionary(dsdict)
        self._analyze()


#=========================================================================
# InputDataset
#=========================================================================
class InputDataset(Dataset):

    def __init__(self, name='input', filenames=[]):
        """
        Initializer

        Parameters:
            name (str): String name to optionally give to a dataset
            filenames (list): List of filenames in the dataset
        """
        super(InputDataset, self).__init__(name)
        self.files = parse_dataset_filelist(filenames)
        self._analyze()
