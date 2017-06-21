"""
Data Flow Node Classes and Functions

This module contains the classes and functions needed to define nodes in Data Flows.

Copyright 2017, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyconform.indexing import index_str, join, align_index, index_tuple
from pyconform.physarray import PhysArray
from pyconform.datasets import VariableDesc, FileDesc
from pyconform.functions import Function
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

            # Get the attributes into a dictionary, for convenience
            attrs = {a:ncvar.getncattr(a) for a in ncvar.ncattrs()}
            
            # Read the variable units
            units_attr = attrs.get('units', 1)
            calendar_attr = attrs.get('calendar', None)
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

            # Align the second index on the intermediate dimensions
            index2 = align_index(index, dimensions1)

            # Get the dimensions after application of the second index
            dimensions2 = tuple(d for d, i in zip(dimensions1, index2) if isinstance(i, slice))

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
            
            # Read the positive attribute, if available
            pos = attrs.get('positive', None)

        return PhysArray(data, name=self.label, units=units, dimensions=dimensions2, positive=pos)


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

    def __init__(self, label, func, *args, **kwds):
        """
        Initializer
        
        Parameters:
            label: A label to give the FlowNode
            func (callable): A callable function associated with the FlowNode operation
            args (list): Arguments to the function given by 'func'
            kwds (dict): Keyword arguments to the function given by 'func'
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
        nargumnt = len(argspec.args)
        ndefault = 0 if argspec.defaults is None else len(argspec.defaults)
        min_args = nargumnt - ndefault
        max_args = nargumnt if argspec.varargs is None else None
        if len(args) < min_args:
            raise ValueError(('Too few arguments supplied for FlowNode function {!r}. '
                              '({} needed, {} supplied)').format(label, min_args, len(args)))
        elif max_args is not None and len(args) > max_args:
            raise ValueError(('Too many arguments supplied for FlowNode function {!r}. '
                              '({} needed, {} supplied)').format(label, max_args, len(args)))
        
        # Check the function keywords
        if argspec.keywords is None:
            valid_kwds = set(argspec.args[-ndefault:] if ndefault > 0 else [])
        else:
            valid_kwds = set(kwds)

        # Store the keyword argument values
        self._keywords = {}
        for kwd in kwds:
            if kwd in valid_kwds:
                self._keywords[kwd] = kwds[kwd]
            else:
                raise ValueError(('Unrecognized keyword argument {!r} for FlowNode function {!r}.').format(kwd, label))

        # Save the function reference
        self._function = func
        
        # Call the base class initialization
        super(EvalNode, self).__init__(label, *args)
    
    @property
    def sumlike_dimensions(self):
        """
        Return the set of sum-like dimensions registered by the node's function
        """
        if isinstance(self._function, Function):
            return self._function.sumlike_dimensions
        else:
            return set()

    def __getitem__(self, index):
        """
        Compute and retrieve the data associated with this FlowNode operation
        """
        kwds = {}
        for k in self._keywords:
            v = self._keywords[k]
            kwds[k] = v[index] if isinstance(v, (PhysArray, FlowNode)) else v

        if len(self.inputs) == 0:
            data = self._function(**kwds)
            return data[index] if isinstance(data, PhysArray) else data
        else:
            args = [d[index] if isinstance(d, (PhysArray, FlowNode)) else d for d in self.inputs]
            return self._function(*args, **kwds)


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
        if inp_dims == out_dims:
            name = inp_info.name
        else:
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
        self._dimensions = None
        if dimensions is not None:
            if isinstance(dimensions, (list, tuple)):
                self._dimensions = tuple(dimensions)
            else:
                raise TypeError('Dimensions must be a list or tuple')

        # Check for units
        if units is not None and not isinstance(units, Unit):
            raise TypeError('Units must be a Unit object')
        self._units = units

        # Store the attributes given to the FlowNode
        self._attributes = OrderedDict((k, v) for k, v in attributes.iteritems())
        
        # Initialize the history attribute
        info = self[None]
        if 'history' not in self.attributes:
            self.attributes['history'] = info.name

    @property
    def attributes(self):
        """
        Attributes dictionary of the variable returned by the ValidateNode
        """
        return self._attributes

    @property
    def dimensions(self):
        """
        Dimensions tuple of the variable returned by the ValidateNode
        """
        return self._dimensions

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
        if self.dimensions is not None and self.dimensions != indata.dimensions:
            indata = indata.transpose(self.dimensions)
        
        # Check the positive attribute, if specified
        positive = self.attributes.get('positive', None)
        if positive is not None and indata.positive != positive:
            indata.flip()

        # Do not validate if index is None (nothing to validate)
        if index is None:
            return indata

        # Testing parameters
        valid_min = self.attributes.get('valid_min', None)
        valid_max = self.attributes.get('valid_max', None)
        ok_min_mean_abs = self.attributes.get('ok_min_mean_abs', None)
        ok_max_mean_abs = self.attributes.get('ok_max_mean_abs', None)

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
            history (bool): Whether to write a history attribute generated during execution
                for each variable in the file
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

        # Initialize set of inverted dimensions
        self._idims = set()
        
        # Initialize set of unwritten attributes
        self._unwritten_attributes = {'_FillValue', 'direction', 'history'}
    
    def enable_history(self):
        """
        Enable writing of the history attribute to the file
        """
        if 'history' in self._unwritten_attributes:
            self._unwritten_attributes.remove('history')

    def disable_history(self):
        """
        Disable writing of the history attribute to the file
        """
        self._unwritten_attributes.add('history')

    def _open_(self):
        """
        Open the file for writing, if not open already
        """
        if self._file is None:

            # Make the necessary subdirectories to open the file
            fname = self.label
            fdir = dirname(fname)
            if len(fdir) > 0 and not exists(fdir):
                try:
                    makedirs(fdir)
                except:
                    raise IOError('Failed to create directory for output file {!r}'.format(fname))

            # Try to open the output file for writing
            try:
                self._file = Dataset(fname, 'w', format=self._filedesc.format)
            except:
                raise IOError('Failed to open output file {!r}'.format(fname))

            # Write the global attributes
            self._file.setncatts(self._filedesc.attributes)

            # Scan over variables for coordinates and dimension information
            req_dims = set()
            for vnode in self.inputs:
                vname = vnode.label
                vdesc = self._filedesc.variables[vname]

                # Get only dimension descriptors needed by the variables
                for dname in vdesc.dimensions:
                    if dname not in self._filedesc.dimensions:
                        raise KeyError(('Dimension {!r} needed by variable {!r} is not specified '
                                        'in file {!r}').format(dname, vname, fname))
                    req_dims.add(dname)

                # Determine coordinates and dimensions to invert
                if len(vdesc.dimensions) == 1 and 'axis' in vnode.attributes:
                    if 'direction' in vnode.attributes:                    
                        vdir_out = vnode.attributes['direction']
                        if vdir_out not in ['increasing', 'decreasing']:
                            raise ValueError(('Unrecognized direction in output coordinate variable '
                                              '{!r} when writing file {!r}').format(vname, fname))
                        vdir_inp = WriteNode._direction_(vnode[:])
                        if vdir_inp is None:
                            raise ValueError(('Output coordinate variable {!r} has no calculable '
                                              'direction').format(vname))
                        if vdir_inp != vdir_out:
                            self._idims.add(vdesc.dimensions.keys()[0])
            
            # Create the required dimensions in the file
            for dname in req_dims:
                ddesc = self._filedesc.dimensions[dname]
                if not ddesc.is_set():
                    raise RuntimeError(('Cannot create unset dimension {!r} in file '
                                        '{!r}').format(dname, fname))
                if ddesc.unlimited:
                    self._file.createDimension(dname)
                else:
                    self._file.createDimension(dname, ddesc.size)

            # Create the variables and write their attributes
            for vnode in self.inputs:
                vname = vnode.label
                vdesc = self._filedesc.variables[vname]
                vattrs = OrderedDict((k, v) for k, v in vnode.attributes.iteritems())

                vdtype = numpy.dtype(vdesc.datatype)
                fillval = vattrs.get('_FillValue', None)
                vdims = vdesc.dimensions.keys()
                ncvar = self._file.createVariable(vname, vdtype, vdims, fill_value=fillval)

                for aname in vattrs:
                    if aname not in self._unwritten_attributes:
                        avalue = vattrs[aname]
                        if aname == 'history':
                            idimstr = ','.join(d for d in vdesc.dimensions if d in self._idims)
                            if len(idimstr) > 0:
                                avalue = 'invdims({}, dims=[{}])'.format(avalue, idimstr)                            
                        ncvar.setncattr(aname, avalue)

    def _close_(self):
        """
        Close the file associated with the WriteNode
        """
        if self._file is not None:
            self._file.close()
            self._idims = set()
            self._file = None

    @staticmethod
    def _chunk_iter_(dsizes, chunks={}):
        if not isinstance(dsizes, OrderedDict):
            raise TypeError('Dimensions must be an ordered dictionary of names and sizes')
        if not isinstance(chunks, dict):
            raise TypeError('Dimension chunks must be a dictionary')

        chunks_ = {d:chunks[d] if d in chunks else dsizes[d] for d in dsizes}
        nchunks = {d:int(dsizes[d]//chunks_[d]) + int(dsizes[d]%chunks_[d]>0) for d in dsizes}
        ntotal = int(numpy.prod([nchunks[d] for d in nchunks]))
        
        idx = {d:0 for d in dsizes}
        for n in xrange(ntotal):
            for d in nchunks:
                n, idx[d] = divmod(n, nchunks[d])
            chunk = OrderedDict()
            for d in dsizes:
                lb = idx[d] * chunks_[d]
                ub = (idx[d] + 1) * chunks_[d]
                chunk[d] = slice(lb, ub if ub < dsizes[d] else None)    
            yield chunk
    
    @staticmethod
    def _invert_dims_(dsizes, chunk, idims=set()):
        if not isinstance(dsizes, OrderedDict):
            raise TypeError('Dimensions must be an ordered dictionary of names and sizes')
        if not isinstance(chunk, OrderedDict):
            raise TypeError('Chunk must be an ordered dictionary of names and slices')
        if not isinstance(idims, set):
            raise TypeError('Dimensions to invert must be a set')
        
        ichunk = OrderedDict()
        for d in dsizes:
            s = dsizes[d]
            c = chunk[d]
            if d in idims:
                ub = s if c.stop is None else c.stop
                ichunk[d] = slice(s - c.start - 1, s - ub - 1 if ub < s else None, -1)
            else:
                ichunk[d] = c
        return ichunk
           
    @staticmethod
    def _direction_(data):
        diff = numpy.diff(data)
        if numpy.all(diff > 0):
            return 'increasing'
        elif numpy.all(diff < 0):
            return 'decreasing'
        else:
            return None

    def execute(self, chunks={}):
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
        """

        # Open the file and write the header information
        self._open_()

        # Create data structure to keep track of which variable chunks we have written
        vchunks = {vnode.label:set() for vnode in self.inputs}
        
        # Compute the Global Dimension Sizes dictionary
        gdims = OrderedDict((d, self._filedesc.dimensions[d].size) for d in self._filedesc.dimensions)
        
        # Iterate over the global dimension space
        for chunk in WriteNode._chunk_iter_(gdims, chunks=chunks):
            
            # Invert the necessary dimensions to get the read-chunk
            rchunk = self._invert_dims_(gdims, chunk, idims=self._idims)
            
            # Loop over all variables and write the data, if necessary
            for vnode in self.inputs:
                vname = vnode.label
                vdesc = self._filedesc.variables[vname]
                ncvar = self._file.variables[vname]
                
                # Compute the write-chunk for the given variable
                wchunk = tuple(chunk[d] for d in vdesc.dimensions)
                
                # Write the data to the variable, if it hasn't already been written
                if repr(wchunk) not in vchunks[vname]:
                    ncvar[wchunk] = vnode[rchunk]
                    vchunks[vname].add(repr(wchunk))

        # Close the file after completion
        self._close_()
