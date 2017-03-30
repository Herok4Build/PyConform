"""
Data Flow Node Classes and Functions

This module contains the classes and functions needed to define nodes in Data Flows.

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyconform.indexing import index_str, join, align_index, index_tuple
from pyconform.physarray import PhysArray
from cf_units import Unit
from inspect import getargspec, ismethod, isfunction
from os.path import exists, dirname
from os import makedirs
from netCDF4 import Dataset
from collections import OrderedDict
from warnings import warn
# from datetime import datetime

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
            inputs (tuple): DataNodes that provide input into this FlowNode
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

    def __init__(self, label, data, units=None, dimensions=None):
        """
        Initializer
        
        Parameters:
            label: A label to give the FlowNode
            data (array): Data to store in this FlowNode
            units (Unit): Units to associate with the data
            dimensions: Dimensions to associate with the data 
        """
        # Determine type and upcast, if necessary
        array = numpy.asarray(data)
        if issubclass(array.dtype.type, numpy.float) and array.dtype.itemsize < 8:
            array = data.astype(numpy.float64)

        # Store data
        self._data = PhysArray(array, name=str(label), units=units, dimensions=dimensions)

        # Call base class initializer
        super(DataNode, self).__init__(label)

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

    def __init__(self, filepath, variable, index=slice(None)):
        """
        Initializer
        
        Parameters:
            filepath (str): A string filepath to a NetCDF file 
            variable (str): A string variable name to read
            index (tuple, slice, int, dict): A tuple of slices or ints, or a slice or int,
                specifying the range of data to read from the file (in file-local indices)
        """

        # Parse File Path
        if not isinstance(filepath, basestring):
            raise TypeError('Unrecognized file path object of type '
                            '{!r}: {!r}'.format(type(filepath), filepath))
        if not exists(filepath):
            raise OSError('File path not found: {!r}'.format(filepath))
        self._filepath = filepath

        # Check variable name type and existence in the file
        if not isinstance(variable, basestring):
            raise TypeError('Unrecognized variable name object of type '
                            '{!r}: {!r}'.format(type(variable), variable))
        with Dataset(self._filepath, 'r') as ncfile:
            if variable not in ncfile.variables:
                raise OSError('Variable {!r} not found in NetCDF file: '
                              '{!r}'.format(variable, self._filepath))
        self._variable = variable

        # Check if the index means "all"
        is_all = False
        if isinstance(index, slice) and index == slice(None):
            is_all = True
        elif isinstance(index, tuple) and all(i == slice(None) for i in index):
            is_all = True
        elif isinstance(index, dict) and all(v == slice(None) for v in index.itervalues()):
            is_all = True

        # Store the reading index
        self._index = index

        # Call the base class initializer
        if is_all:
            label = variable
        else:
            label = '{}[{}]'.format(variable, index_str(index))
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
            args (tuple): Arguments to the function given by 'func'
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
            dimensions (tuple): The output dimensions for the mapped variable
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

    def __init__(self, label, dnode, units=None, dimensions=None, dtype=None, attributes=OrderedDict()):
        """
        Initializer
        
        Parameters:
            label: The label associated with this FlowNode
            dnode (FlowNode): FlowNode that provides input into this FlowNode
            units (Unit): CF units to validate against
            dimensions (tuple): The output dimensions to validate against
            dtype (dtype): The Numpy dtype of the data to return
            attributes: Additional named arguments corresponding to additional attributes
                to which to associate with the new variable
        """
        # Check FlowNode type
        if not isinstance(dnode, FlowNode):
            raise TypeError('ValidateNode can only act on output from another FlowNode')

        # Call base class initializer
        super(ValidateNode, self).__init__(label, dnode)

        # Save the data type
        self._dtype = dtype

        # Check for dimensions
        if dimensions is not None and not isinstance(dimensions, tuple):
            raise TypeError('Dimensions must be a tuple')
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

    def __init__(self, filename, *inputs, **kwds):
        """
        Initializer
        
        Parameters:
            filename (str): Name of the file to write
            inputs (ValidateNode): A tuple of ValidateDataNodes providing input into the file
            unlimited (tuple): A tuple of dimensions that should be written as unlimited dimensions
                (This parameter is pulled from the 'kwds' argument, if given.)
            provenance (bool): Whether to write variable provenance information
                generated by PyConform.
            attributes (dict): Dictionary of global attributes to write to the file
                (This parameter is pulled from the 'kwds' argument, if given.)
        """
        # Check filename
        if not isinstance(filename, basestring):
            raise TypeError('Filename must be of string type')

        # Check and store input variables
        for inp in inputs:
            if not isinstance(inp, ValidateNode):
                raise TypeError(('WriteNode {!r} cannot accept input from type '
                                 '{}').format(filename, type(inp)))

        # Call base class (label is filename)
        super(WriteNode, self).__init__(filename, *inputs)

        # Grab the unlimited dimensions parameter and check type
        unlimited = kwds.pop('unlimited', ())
        if not isinstance(unlimited, tuple):
            raise TypeError('Unlimited dimensions must be given as a tuple')
        self._unlimited = unlimited

        # Save the global attributes
        self._attributes = {str(a): v for a, v in kwds.iteritems()}

        # Set the filehandle
        self._file = None
        
        # Initialize the variable information
        self._vinfos = {}
        self._idims = set()

    def open(self, history=False):
        """
        Open the file for writing, if not open already
        
        Parameters:
            provenance (bool): Whether to write a provenance attribute generated during execution
                for each variable in the file
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
                self._file = Dataset(fname, 'w')
            except:
                raise IOError('Failed to open output file {!r}'.format(fname))

            # Write the global attributes
            self._file.setncatts(self._attributes)

            # Scan over variables for coordinates and dimension information
            dim_sizes = {}
            for vnode in self.inputs:
                vname = vnode.label
                vinfo = vnode[None]

                # Get dimensions and their sizes
                for dname, dsize in zip(vinfo.dimensions, vinfo.initshape):
                    if dname not in dim_sizes:
                        dim_sizes[dname] = dsize
                    elif dim_sizes[dname] != dsize:
                        raise RuntimeError(('Dimension {!r} has inconsistent size: '
                                            '{}, {}').format(dname, dim_sizes[dname], dsize))

                # Determine coordinates and dimensions to invert
                if len(vinfo.dimensions) == 1 and 'axis' in vnode.attributes:
                    if 'direction' in vnode.attributes:                    
                        vdir_out = vnode.attributes.pop('direction')
                        if vdir_out not in ['increasing', 'decreasing']:
                            raise ValueError(('Unrecognized direction in output coordinate variable '
                                              '{!r} when writing file {!r}').format(vname, fname))
                        vdir_inp = WriteNode._direction_(vnode[:])
                        if vdir_inp is None:
                            raise ValueError(('Output coordinate variable {!r} has no calculable '
                                              'direction').format(vname))
                        if vdir_inp != vdir_out:
                            self._idims.add(vinfo.dimensions[0])

                # Store variable information object                
                self._vinfos[vname] = vinfo
            
            # Record dimension inversion information for history attributes
            if history:
                vhist = {}
                for vname in self._vinfos:
                    vinfo = self._vinfos[vname]
                    idimstr = ','.join(d for d in vinfo.dimensions if d in self._idims)
                    if len(idimstr) > 0:
                        vhist[vname] = 'invdims({},dims=({}))'.format(vinfo.name, idimstr)
                    else:
                        vhist[vname] = vinfo.name

            # Create the required dimensions in the file
            for dname in dim_sizes:
                dsize = dim_sizes[dname]
                if dname in self._unlimited:
                    self._file.createDimension(dname)
                else:
                    self._file.createDimension(dname, dsize)

            # Create the variables and write their attributes
            for vnode in self.inputs:
                vname = vnode.label
                vinfo = self._vinfos[vname]
                vattrs = OrderedDict((k, v) for k, v in vnode.attributes.iteritems())

                fill_value = vattrs.pop('_FillValue', None)
                ncvar = self._file.createVariable(vname, str(vinfo.dtype), vinfo.dimensions,
                                                  fill_value=fill_value)
                for aname in vattrs:
                    ncvar.setncattr(aname, vattrs[aname])
                if history:
                    ncvar.setncattr('history', vhist[vname])

    def close(self):
        """
        Close the file associated with the WriteNode
        """
        if self._file is not None:
            self._file.close()
            self._vinfos = {}
            self._idims = set()
            self._file = None

    @staticmethod
    def _chunk_iter_(dimsizes, chunks={}):
        if ((not isinstance(dimsizes, (tuple, list))) and
            (not all(isinstance(ds, tuple) and len(ds)==2 for ds in dimsizes))):
            raise TypeError('Dimensions must be a tuple or list of dimension-size pairs')
        if not isinstance(chunks, dict):
            raise TypeError('Dimension chunks must be a dictionary')

        dsizes = {d:s for d,s in dimsizes}
        chunks_ = {d:chunks[d] if d in chunks else dsizes[d] for d in dsizes}
        nchunks = {d:int(dsizes[d]//chunks_[d]) + int(dsizes[d]%chunks_[d]>0) for d in dsizes}
        ntotal = numpy.prod([nchunks[d] for d in nchunks])
        
        idx = {d:0 for d in dsizes}
        for n in xrange(ntotal):
            for d in nchunks:
                n, idx[d] = divmod(n, nchunks[d])
            chunk = []
            for d, _ in dimsizes:
                lb = idx[d] * chunks_[d]
                ub = (idx[d] + 1) * chunks_[d]
                chunk.append(slice(lb, ub if ub < dsizes[d] else None))    
            yield tuple(chunk) 
    
    @staticmethod
    def _invert_dims(dimsizechunks, idims=set()):
        if ((not isinstance(dimsizechunks, (list, tuple))) and
            (not all(isinstance(dsc, tuple) and len(dsc)==3 for dsc in dimsizechunks))):
            raise TypeError('Dimensions must be a tuple')
        if not isinstance(idims, set):
            raise TypeError('Dimensions to invert must be a set')
        
        ichunk = []
        for d,s,c in dimsizechunks:
            ub = s if c.stop is None else c.stop
            if d in idims:
                ilb = s - c.start - 1
                iub = s - ub - 1 if ub < s else None
                ist = -1
            else:
                ilb = c.start
                iub = c.stop
                ist = c.step                
            ichunk.append(slice(ilb,iub,ist))
        return tuple(ichunk)
           
    @staticmethod
    def _direction_(data):
        diff = numpy.diff(data)
        if numpy.all(diff > 0):
            return 'increasing'
        elif numpy.all(diff < 0):
            return 'decreasing'
        else:
            return None

    def execute(self, chunks={}, history=False, bounds={}):
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
            history (bool): Whether to write a provenance attribute generated during execution
                for each variable in the file
            bounds (dict):  Bounds on named variables specified in the output specification
                file.  Data will be written for values within these bounds inclusively.
        """

        # Open the file and write the header information (fills the _vinfos)
        self.open(history=history)

        # Loop over all variable nodes and write data
        for vnode in self.inputs:
            vname = vnode.label
            vinfo = self._vinfos[vname]
            ncvar = self._file.variables[vname]

            # Loop over all chunks for the given variable's dimensions
            vdimsizes = zip(vinfo.dimensions, vinfo.initshape)
            for chunk in WriteNode._chunk_iter_(vdimsizes, chunks=chunks):
                vdimsizechunks = zip(vinfo.dimensions, vinfo.initshape, chunk)
                ncvar[chunk] = vnode[self._invert_dims(vdimsizechunks, idims=self._idims)]

        # Close the file after completion
        self.close()
