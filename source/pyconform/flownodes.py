"""
Data Flow Node Classes and Functions

This module contains the classes and functions needed to define nodes in Data Flows.

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyconform.indexing import index_str, join, align_index, index_tuple
from pyconform.physarray import PhysArray
from pyconform.datasets import VariableDesc, FileDesc
from cf_units import Unit
from inspect import getargspec, ismethod, isfunction
from os.path import exists, dirname
from os import makedirs
from netCDF4 import Dataset
from collections import OrderedDict
from warnings import warn

import numpy


#===================================================================================================
# ValidationWarning
#===================================================================================================
class ValidationWarning(Warning):
    """Warning for validation errors"""

#===================================================================================================
# UnitsWarning
#===================================================================================================
class UnitsWarning(Warning):
    """Warning for units errors"""

#===================================================================================================
# FlowNode
#===================================================================================================
class FlowNode(object):
    """
    The base class for objects that can appear in a data flow
    
    The FlowNode object represents a point in the directed acyclic graph where multiple
    edges meet.  It represents a functional operation on the DataArrays coming into it from
    its adjacent DataNodes.  The FlowNode itself outputs the result of this operation
    through the __getitem__ interface (i.e., FlowNode[item]), returning a slice of a
    PhysArray.
    """

    def __init__(self, label, *inputs):
        """
        Initializer
        
        Parameters:
            label: A label to give the FlowNode
            inputs (list): DataNodes that provide input into this FlowNode
        """
        self._label = label
        self._inputs = list(inputs)

    @property
    def label(self):
        """The FlowNode's label"""
        return self._label

    @property
    def inputs(self):
        """Inputs into this FlowNode"""
        return self._inputs


#===================================================================================================
# DataNode
#===================================================================================================
class DataNode(FlowNode):
    """
    FlowNode class to create data in memory
    
    This is a "source" FlowNode.
    """

    def __init__(self, data):
        """
        Initializer
        
        Parameters:
            data (PhysArray): Data to store in this FlowNode
        """
        # Determine type and upcast, if necessary
        array = PhysArray(data)
        if issubclass(array.dtype.type, numpy.float) and array.dtype.itemsize < 8:
            array = array.astype(numpy.float64)

        # Store data
        self._data = array

        # Call base class initializer
        super(DataNode, self).__init__(self._data.name)

    def __getitem__(self, index):
        """
        Compute and retrieve the data associated with this FlowNode operation
        """
        return self._data[index]


#===================================================================================================
# ReadNode
#===================================================================================================
class ReadNode(FlowNode):
    """
    FlowNode class for reading data from a NetCDF file
    
    This is a "source" FlowNode.
    """

    def __init__(self, variable, index=slice(None)):
        """
        Initializer
        
        Parameters:
            variable (VariableDesc): A variable descriptor object
            index (tuple, slice, int, dict): A tuple of slices or ints, or a slice or int,
                specifying the range of data to read from the file (in file-local indices)
        """

        # Check variable descriptor type and existence in the file
        if not isinstance(variable, VariableDesc):
            raise TypeError('Unrecognized variable descriptor of type '
                            '{!r}: {!r}'.format(type(variable), variable.name))

        # Check for associated file
        if len(variable.files) == 0:
            raise ValueError('Variable descriptor {} has no associated files'.format(variable.name))
        self._filepath = None
        for fdesc in variable.files.itervalues():
            if fdesc.exists():
                self._filepath = fdesc.name
                break
        if self._filepath is None:
            raise OSError('File path not found for input variable: {!r}'.format(variable.name))

        # Check that the variable exists in the file
        with Dataset(self._filepath, 'r') as ncfile:
            if variable.name not in ncfile.variables:
                raise OSError('Variable {!r} not found in NetCDF file: '
                              '{!r}'.format(variable.name, self._filepath))
        self._variable = variable.name

        # Check if the index means "all"
        is_all = False
        if isinstance(index, slice) and index == slice(None):
            is_all = True
        elif isinstance(index, (list, tuple)) and all(i == slice(None) for i in index):
            is_all = True
        elif isinstance(index, dict) and all(v == slice(None) for v in index.itervalues()):
            is_all = True

        # Store the reading index
        self._index = index

        # Call the base class initializer
        if is_all:
            label = variable.name
        else:
            label = '{}[{}]'.format(variable.name, index_str(index))
        super(ReadNode, self).__init__(label)

    def __getitem__(self, index):
        """
        Read PhysArray from file
        """
        with Dataset(self._filepath, 'r') as ncfile:

            # Get a reference to the variable
            ncvar = ncfile.variables[self._variable]

            # Read the variable units
            attrs = ncvar.ncattrs()
            units_attr = ncvar.getncattr('units') if 'units' in attrs else 1
            calendar_attr = ncvar.getncattr('calendar') if 'calendar' in attrs else None
            try:
                units = Unit(units_attr, calendar=calendar_attr)
            except ValueError:
                msg = 'Units {!r} unrecognized in UDUNITS.  Assuming unitless.'.format(units_attr)
                warn(msg, UnitsWarning)
                units = Unit(1)
            except:
                raise

            # Read the original variable dimensions
            dimensions0 = ncvar.dimensions

            # Read the original variable shape
            shape0 = ncvar.shape

            # Align the read-indices on dimensions
            index1 = align_index(self._index, dimensions0)

            # Get the dimensions after application of the first index
            dimensions1 = tuple(d for d, i in zip(dimensions0, index1) if isinstance(i, slice))

            # Compute the original shape after potential dimension reduction
            shape1 = tuple(s for s, i in zip(shape0, index1) if isinstance(i, slice))

            # Align the second index on the intermediate dimensions
            index2 = align_index(index, dimensions1)

            # Get the dimensions after application of the second index
            dimensions2 = tuple(d for d, i in zip(dimensions1, index2) if isinstance(i, slice))

            # Compute the original shape after potential dimension reduction
            shape2 = tuple(s for s, i in zip(shape1, index2) if isinstance(i, slice))

            # Compute the joined index object
            index12 = join(shape0, index1, index2)

            # Retrieve the data from file, unpacking if necessary
            if 'scale_factor' in attrs or 'add_offset' in attrs:
                scale_factor = attrs.get('scale_factor', 1)
                add_offset = attrs.get('add_offset', 0)
                data = scale_factor * ncvar[index12] + add_offset
            else:
                data = ncvar[index12]

            # Upconvert, if possible
            if issubclass(ncvar.dtype.type, numpy.float) and ncvar.dtype.itemsize < 8:
                data = data.astype(numpy.float64)

        return PhysArray(data, name=self.label, units=units, dimensions=dimensions2, initshape=shape2)


#===================================================================================================
# EvalNode
#===================================================================================================
class EvalNode(FlowNode):
    """
    FlowNode class for evaluating a function on input from neighboring DataNodes
    
    The EvalNode is constructed with a function reference and any number of arguments to
    that function.  The number of arguments supplied must match the number of arguments accepted
    by the function.  The arguments can be any type, and the order of the arguments will be
    preserved in the call signature of the function.  If the arguments are of type FlowNode,
    then a reference to the FlowNode will be stored.  If the arguments are of any other type, the
    argument will be stored by the EvalNode.

    This is a "non-source"/"non-sink" FlowNode.
    """

    def __init__(self, label, func, *args):
        """
        Initializer
        
        Parameters:
            label: A label to give the FlowNode
            func (callable): A callable function associated with the FlowNode operation
            args (list): Arguments to the function given by 'func'
        """
        # Check func parameter
        fpntr = func
        if callable(func):
            if hasattr(func, '__call__') and (isfunction(func.__call__) or ismethod(func.__call__)):
                fpntr = func.__call__
            else:
                fpntr = func
        else:
            raise TypeError('Function argument to FlowNode {} is not callable'.format(label))

        argspec = getargspec(fpntr)
        if ismethod(fpntr) and 'self' in argspec.args:
            argspec.args.remove('self')

        # Check the function arguments
        max_len = len(argspec.args)
        if argspec.defaults is None:
            min_len = max_len
        else:
            min_len = max_len - len(argspec.defaults)
        if len(args) < min_len:
            raise ValueError(('Too few arguments supplied for FlowNode function. '
                              '({} needed, {} supplied)').format(min_len, len(args)))
        if len(args) > max_len:
            raise ValueError(('Too many arguments supplied for FlowNode function. '
                              '({} needed, {} supplied)').format(max_len, len(args)))

        # Save the function reference
        self._function = func

        # Call the base class initialization
        super(EvalNode, self).__init__(label, *args)

    def __getitem__(self, index):
        """
        Compute and retrieve the data associated with this FlowNode operation
        """
        if len(self.inputs) == 0:
            data = self._function()
            if isinstance(data, PhysArray):
                return data[index]
            else:
                return data
        else:
            args = [d[index] if isinstance(d, (PhysArray, FlowNode)) else d for d in self.inputs]
            return self._function(*args)


#===================================================================================================
# MapNode
#===================================================================================================
class MapNode(FlowNode):
    """
    FlowNode class to map input data from a neighboring FlowNode to new dimension names and units
    
    The MapNode can rename the dimensions of a FlowNode's output data.  It does not change the
    data itself, however.  The input dimension names will be changed according to the dimension
    map given.  If an input dimension name is not referenced by the map, then the input dimension
    name does not change.
    
    This is a "non-source"/"non-sink" FlowNode.
    """

    def __init__(self, label, dnode, dmap={}):
        """
        Initializer
        
        Parameters:
            label: The label given to the FlowNode
            dnode (FlowNode): FlowNode that provides input into this FlowNode
            dmap (dict): A dictionary mapping dimension names of the input data to
                new dimensions names for the output variable
        """
        # Check FlowNode type
        if not isinstance(dnode, FlowNode):
            raise TypeError('MapNode can only act on output from another FlowNode')

        # Check dimension map type
        if not isinstance(dmap, dict):
            raise TypeError('Dimension map must be a dictionary')

        # Store the dimension input-to-output map
        self._i2omap = dmap

        # Construct the reverse mapping
        self._o2imap = dict((v, k) for k, v in dmap.iteritems())

        # Call base class initializer
        super(MapNode, self).__init__(label, dnode)

    def __getitem__(self, index):
        """
        Compute and retrieve the data associated with this FlowNode operation
        """

        # Request the input information without pulling data
        inp_info = self.inputs[0][None]

        # Get the input data dimensions
        inp_dims = inp_info.dimensions

        # The input/output dimensions will be the same
        # OR should be contained in the input-to-output dimension map
        out_dims = tuple(self._i2omap.get(d, d) for d in inp_dims)

        # Compute the input index in terms of input dimensions
        if index is None:
            inp_index = None

        elif isinstance(index, dict):
            inp_index = dict((self._o2imap.get(d, d), i) for d, i in index.iteritems())

        else:
            out_index = index_tuple(index, len(inp_dims))
            inp_index = dict((self._o2imap.get(d, d), i) for d, i in zip(out_dims, out_index))

        # Return the mapped data
        idims_str = ','.join(inp_dims)
        odims_str = ','.join(out_dims)
        name = 'map({}, from=[{}], to=[{}])'.format(inp_info.name, idims_str, odims_str)
        return PhysArray(self.inputs[0][inp_index], name=name, dimensions=out_dims)


#===================================================================================================
# ValidateNode
#===================================================================================================
class ValidateNode(FlowNode):
    """
    FlowNode class to validate input data from a neighboring FlowNode
    
    The ValidateNode takes additional attributes in its initializer that can effect the 
    behavior of its __getitem__ method.  The special attributes are:
    
        'valid_min': The minimum value the data should have, if valid
        'valid_max': The maximum value the data should have, if valid
        'min_mean_abs': The minimum acceptable value of the mean of the absolute value of the data
        'max_mean_abs': The maximum acceptable value of the mean of the absolute value of the data
    
    If these attributes are supplied to the ValidateNode at construction time, then the
    associated validation checks will be made on the data when __getitem__ is called.
    
    Additional attributes may be added to the ValidateNode that do not affect functionality.
    These attributes may be named however the user wishes and can be retrieved from the FlowNode
    as a dictionary with the 'attributes' property.

    This is a "non-source"/"non-sink" FlowNode.
    """

    def __init__(self, label, dnode, units=None, dimensions=None, dtype=None, attributes={}):
        """
        Initializer
        
        Parameters:
            label: The label associated with this FlowNode
            dnode (FlowNode): FlowNode that provides input into this FlowNode
            units (Unit): CF units to validate against
            dimensions (tuple): The output dimensions to validate against
            dtype (dtype): The NumPy dtype of the data to return
            attributes (dict): Attributes to associate with the new variable
        """
        # Check FlowNode type
        if not isinstance(dnode, FlowNode):
            raise TypeError('ValidateNode can only act on output from another FlowNode')

        # Call base class initializer
        super(ValidateNode, self).__init__(label, dnode)

        # Save the data type
        self._dtype = dtype

        # Check for dimensions
        if dimensions is not None and not isinstance(dimensions, (list, tuple)):
            raise TypeError('Dimensions must be a list or tuple')
        self._dimensions = dimensions

        # Check for units
        if units is not None and not isinstance(units, Unit):
            raise TypeError('Units must be a Unit object')
        self._units = units

        # Store the attributes given to the FlowNode
        self._attributes = OrderedDict((k, v) for k, v in attributes.iteritems())

    @property
    def attributes(self):
        """
        Attributes dictionary of the variable returned by the ValidateNode
        """
        return self._attributes

    def __getitem__(self, index):
        """
        Compute and retrieve the data associated with this FlowNode operation
        """

        # Get the data to validate
        indata = self.inputs[0][index]

        # Check datatype, and cast as necessary
        if self._dtype is None:
            odtype = indata.dtype
        else:
            odtype = self._dtype
        if numpy.can_cast(indata.dtype, odtype, casting='same_kind'):
            indata = indata.astype(odtype)
        else:
            raise TypeError('Cannot cast datatype {!s} to {!s} in ValidateNode '
                            '{!r}').format(indata.dtype, odtype, self.label)

        # Check that units match as expected
        if self._units is not None and self._units != indata.units:
            if index is None:
                indata.units = self._units
            else:
                indata = indata.convert(self._units)

        # Check that the dimensions match as expected
        if self._dimensions is not None and self._dimensions != indata.dimensions:
            indata = indata.transpose(self._dimensions)

        # Do not validate if index is None (nothing to validate)
        if index is None:
            return indata

        # Testing parameters
        valid_min = self._attributes.get('valid_min', None)
        valid_max = self._attributes.get('valid_max', None)
        ok_min_mean_abs = self._attributes.get('ok_min_mean_abs', None)
        ok_max_mean_abs = self._attributes.get('ok_max_mean_abs', None)

        # Validate minimum
        if valid_min:
            dmin = numpy.min(indata)
            if dmin < valid_min:
                msg = 'valid_min: {} < {} ({!r})'.format(dmin, valid_min, self.label)
                warn(msg, ValidationWarning)

        # Validate maximum
        if valid_max:
            dmax = numpy.max(indata)
            if dmax > valid_max:
                msg = 'valid_max: {} > {} ({!r})'.format(dmax, valid_max, self.label)
                warn(msg, ValidationWarning)

        # Compute mean of the absolute value, if necessary
        if ok_min_mean_abs or ok_max_mean_abs:
            mean_abs = numpy.mean(numpy.abs(indata))

        # Validate minimum mean abs
        if ok_min_mean_abs:
            if mean_abs < ok_min_mean_abs:
                msg = 'ok_min_mean_abs: {} < {} ({!r})'.format(mean_abs, ok_min_mean_abs, self.label)
                warn(msg, ValidationWarning)

        # Validate maximum mean abs
        if ok_max_mean_abs:
            if mean_abs > ok_max_mean_abs:
                msg = 'ok_max_mean_abs: {} > {} ({!r})'.format(mean_abs, ok_max_mean_abs, self.label)
                warn(msg, ValidationWarning)

        return indata


#===================================================================================================
# WriteNode
#===================================================================================================
class WriteNode(FlowNode):
    """
    FlowNode that writes validated data to a file.
    
    This is a "sink" node, meaning that the __getitem__ (i.e., [index]) interface does not return
    anything.  Rather, the data "retrieved" through the __getitem__ interface is sent directly to
    file.
    
    For this reason, it is possible to "retrieve" data multiple times, resulting in writing and
    overwriting of data.  To eliminate this inefficiency, it is advised that you use the 'execute'
    method to write data efficiently once (and only once).
    """

    def __init__(self, filedesc, inputs=()):
        """
        Initializer
        
        Parameters:
            filedesc (FileDesc): File descriptor for the file to write
            inputs (tuple): A tuple of ValidateNodes providing input into the file
        """
        # Check filename
        if not isinstance(filedesc, FileDesc):
            raise TypeError('File descriptor must be of FileDesc type')

        # Check and store input variables nodes
        if not isinstance(inputs, (list, tuple)):
            raise TypeError(('WriteNode {!r} inputs must be given as a list or '
                             'tuple').format(filedesc.name))
        for inp in inputs:
            if not isinstance(inp, ValidateNode):
                raise TypeError(('WriteNode {!r} cannot accept input from type {}, must be a '
                                 'ValidateNode').format(filedesc.name, type(inp)))

        # Call base class (label is filename)
        super(WriteNode, self).__init__(filedesc.name, *inputs)

        # Store the file descriptor for use later
        self._filedesc = filedesc

        # Check that inputs are contained in the file descriptor
        for inp in inputs:
            if inp.label not in self._filedesc.variables:
                raise ValueError(('WriteNode {!r} takes input from variable {!r} that is not '
                                  'contained in the descibed file').format(filedesc.name, inp.label))

        # Set the filehandle
        self._file = None

        # Initialize the variable information
        self._vinfos = {}

    def open(self, provenance=False):
        """
        Open the file for writing, if not open already
        
        Parameters:
            provenance (bool): Whether to write a provenance attribute generated during execution
                for each variable in the file
        """
        if self._file is None:

            # Make the necessary subdirectories to open the file
            labeldir = dirname(self.label)
            if len(labeldir) > 0 and not exists(labeldir):
                try:
                    makedirs(labeldir)
                except:
                    raise IOError('Failed to create directory for output file {!r}'.format(self.label))

            # Try to open the output file for writing
            try:
                self._file = Dataset(self.label, 'w')
            except:
                raise IOError('Failed to open output file {!r}'.format(self.label))

            # Write the global attributes
            self._file.setncatts(self._filedesc.attributes)

            # Create the required dimensions for the variable
            for dname, ddesc in self._filedesc.dimensions.iteritems():
                if not ddesc.is_set():
                    raise RuntimeError(('Cannot create unset dimension {!r} in file '
                                        '{!r}').format(dname, self.label))
                if ddesc.unlimited:
                    self._file.createDimension(dname)
                else:
                    self._file.createDimension(dname, ddesc.size)

            # Create the variables and write their attributes
            for vnode in self.inputs:
                vname = vnode.label
                vdesc = self._filedesc.variables[vname]
                vattrs = OrderedDict((k, v) for k, v in vnode.attributes.iteritems())
                fill_value = vattrs.pop('_FillValue', None)
                ncvar = self._file.createVariable(vname, vdesc.datatype, vdesc.dimensions.keys(),
                                                  fill_value=fill_value)
                for aname, avalue in vattrs.iteritems():
                    ncvar.setncattr(aname, avalue)
                if provenance:
                    ncvar.setncattr('conform_prov', vnode[None].name)

    def close(self):
        """
        Close the file associated with the WriteNode
        """
        if self._file is not None:
            self._file.close()
            self._file = None

    @staticmethod
    def _chunk_iter_(dims, sizes, chunks={}):
        if not isinstance(dims, (list, tuple)):
            raise TypeError('Dimensions must be a tuple')
        if not isinstance(sizes, (list, tuple)):
            raise TypeError('Dimension sizes must be a tuple')
        if not isinstance(chunks, dict):
            raise TypeError('Dimension chunks must be a dictionary')
        if len(dims) != len(sizes):
            raise ValueError('Dimensions and sizes must be same length')

        chunks_ = {d:c for d, c in chunks.iteritems() if d in dims}
        if len(chunks_) == 0:
            yield slice(None)
        else:
            dsizes = OrderedDict((d, s) for d, s in zip(dims, sizes))
            nchunks = OrderedDict((d, s) for d, s in dsizes.iteritems() if d in chunks_)
            for d in chunks_:
                nchunks[d] = dsizes[d] / chunks_[d] + int(dsizes[d] % chunks_[d] > 0)
            ntotal = numpy.prod(nchunks.values())
            index = {d: 0 for d in sizes}
            for n in xrange(ntotal):
                for d, m in nchunks.iteritems():
                    n, index[d] = divmod(n, m)
                bnds = {d: (index[d] * c, (index[d] + 1) * c) for d, c in chunks_.iteritems()}
                yield {d: (slice(lb, ub) if ub < dsizes[d] else slice(lb, None))
                       for d, (lb, ub) in bnds.iteritems()}

    def execute(self, chunks={}, provenance=False, bounds={}):
        """
        Execute the writing of the WriteNode file at once
        
        This method efficiently writes all of the data for each file only once, chunking
        the data according to the 'chunks' parameter, as needed.
        
        Parameters:
            chunks (dict): A dictionary of output dimension names and chunk sizes for each
                dimension given.  Output dimensions not included in the dictionary will not be
                chunked.  (Use OrderedDict to preserve order of dimensions, where the first
                dimension will be assumed to correspond to the fastest-varying index and the last
                dimension will be assumed to correspond to the slowest-varying index.)
            provenance (bool): Whether to write a provenance attribute generated during execution
                for each variable in the file
            bounds (dict):  Bounds on named variables specified in the output specification
                file.  Data will be written for values within these bounds inclusively.
        """

        # Open the file and write the header information (fills the _vinfos)
        self.open(provenance=provenance)

        # Loop over all variable nodes
        for vnode in self.inputs:

            # Get the name of the variable node
            vname = vnode.label

            # Get the header information for this variable node
            vdesc = self._filedesc.variables[vname]
            vdims = vdesc.dimensions.keys()
            vshape = [d.size for d in vdesc.dimensions.itervalues()]

            # Get the NetCDF variable object
            ncvar = self._file.variables[vname]

            # Loop over all chunks for the given variable's dimensions
            for chunk in WriteNode._chunk_iter_(vdims, vshape, chunks):
                ncvar[align_index(chunk, ncvar.dimensions)] = vnode[chunk]

        # Close the file after completion
        self.close()
