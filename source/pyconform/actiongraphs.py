"""
ActionGraph Class

This module contains the ActionGraph class to be used with the Action 
classes and the DiGraph class to build an "graph of actions."  This graph
walks through a DiGraph of connected Actions performing the Action functions
in sequence, and using the output of each Action as input into the next. 

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from pyconform.graphs import DiGraph
from pyconform.parsing import (ParsedFunction, ParsedVariable, ParsedUniOp,
                               ParsedBinOp, parse_definition)
from pyconform.datasets import InputDataset, OutputDataset
from pyconform.actions import (Action, ReaderAction,
                               Evaluator, Handle)
from pyconform.functions import (find_function, find_operator, find,
                                 UnitsError, DimensionsError)
from itertools import cycle
from os import linesep


#===============================================================================
# ActionGraph
#===============================================================================
class ActionGraph(DiGraph):
    """
    Action Graph
    
    A directed graph defining a connected set of operations whose results
    are used as input to adjacent operators.
    """

    def __init__(self):
        """
        Initialize
        """
        super(ActionGraph, self).__init__()

    def __str__(self):
        """
        Display an ActionGraph as a string
        """
        output = []
        for h in self.handles():
            nodes = self._actions_by_depth_(h)
            houtput = []
            for i, u in nodes:
                indent = '    '*i
                if i > 0:
                    houtput.append('{0}|'.format(indent))
                houtput.append('{0}+-- {1!s}'.format(indent, u))
            for i in xrange(len(houtput)):
                for j in [j for j, c in enumerate(houtput[i]) if c == '|']:
                    k = i - 1
                    while k > 0:
                        if houtput[k][j] == ' ':
                            houtput[k] = houtput[k][:j] + '|' + houtput[k][j+1:]
                            k = k - 1
                        else:
                            k = 0
            output.extend(houtput)
            output.append('')
        return linesep.join(output)
    
    def _actions_by_depth_(self, v, depth=0, visited=None):
        if visited is None:
            visited = set()
        visited.add(v)
        nodes = [(depth, v)]
        for n in self.neighbors_to(v):
            if n not in visited:
                nodes.extend(self._actions_by_depth_(n, depth=depth+1,
                                                     visited=visited))
        return nodes
    
    def add(self, vertex):
        """
        Add a vertex to the graph
        
        Parameters:
            vertex (Action): An Action vertex to be added to the graph
        """
        if not isinstance(vertex, Action):
            raise TypeError('ActionGraph must consist only of Actions')
        super(ActionGraph, self).add(vertex)

    def __call__(self, root):
        """
        Perform the ActionGraph operations
        
        Parameters:
            root (Action): The root of the operation, from which data is
                requested from the operation graph
        """
        if root not in self:
            raise KeyError('Action {!r} not in ActionGraph'.format(root))
        def evaluate_from(op):
            return op(*map(evaluate_from, self.neighbors_to(op)))
        return evaluate_from(root)
    
    def handles(self):
        """
        Return a dictionary of output variable handles in the graph
        """
        return [op for op in self.vertices if isinstance(op, Handle)]


#===============================================================================
# GraphFiller
#===============================================================================
class GraphFiller(object):
    """
    Object that fills an ActionGraph
    """
    
    def __init__(self, inp, cyc=True):
        """
        Initializer
        
        Parameters:
            inp (InputDataset): The input dataset to use as reference when
                parsing variable definitions
            cyc (bool): If True, cycles which file to read metadata variables
                from (i.e., variables that exist in all input files).  If False,
                always reads metadata variables from the first input file.
        """
        # Input dataset
        if not isinstance(inp, InputDataset):
            raise TypeError('Input dataset must be of InputDataset type')
        self._inputds = inp

        # Maintain a database of slice readers
        self._readers = {}
        
        # Cyclic iterator over available input filenames
        fnames = [v.filename for v in self._inputds.variables.itervalues()]
        if cyc:
            self._infile_cycle = cycle(filter(None, fnames))
        else:
            self._infile_cycle = cycle([filter(None, fnames)[0]])

    def from_definitions(self, graph, outds):
        """
        Fill an ActionGraph from definitions in an output dataset
        """
        # Action Graph
        if not isinstance(graph, ActionGraph):
            raise TypeError('Graph must be an ActionGraph object')
            
        # Output dataset
        if not isinstance(outds, OutputDataset):
            raise TypeError('Output dataset must be of OutputDataset type')

        # Parse the output variable definitions
        for vname, vinfo in outds.variables.iteritems():
            obj = parse_definition(vinfo.definition)
            vtx = self._add_to_graph_(graph, obj)
            handle = Handle(vname)
            handle.units = vinfo.cfunits()
            handle.dimensions = vinfo.dimensions
            graph.connect(vtx, handle)
        
        # Check to make sure the graph is not cyclic
        if graph.is_cyclic():
            raise ValueError('Graph is cyclic.  Cannot continue.')
            
    def _add_to_graph_(self, graph, obj):
        vtx = self._convert_obj_(obj)
        graph.add(vtx)
        if isinstance(obj.args, tuple):
            for arg in obj.args:
                graph.connect(self._add_to_graph_(graph, arg), vtx)
        return vtx

    def _convert_obj_(self, obj):
        if isinstance(obj, ParsedVariable):
            vname = obj.key
            if vname not in self._inputds.variables:
                raise KeyError('Variable {0!r} not found'.format(vname))
            var = self._inputds.variables[vname]
            if var.filename:
                fname = var.filename
            else:
                fname = self._infile_cycle.next()
            return ReaderAction(fname, vname, slicetuple=obj.args)

        elif isinstance(obj, (ParsedUniOp, ParsedBinOp)):
            symbol = obj.key
            nargs = len(obj.args)
            func = find_operator(symbol, numargs=nargs)
            args = [o if isinstance(o, (int, float)) else None
                    for o in obj.args]
            if all(isinstance(o, (int, float)) for o in args):
                return func(*args)
            return Evaluator(symbol, str(obj), func, signature=args)

        elif isinstance(obj, ParsedFunction):
            name = obj.key
            nargs = len(obj.args)
            func = find_function(name, numargs=nargs)
            args = [o if isinstance(o, (int, float)) else None
                    for o in obj.args]
            if all(isinstance(o, (int, float)) for o in args):
                return func(*args)
            return Evaluator(name, str(obj), func, signature=args)
        
        else:
            return obj

    def match_units(self, graph):
        """
        Match units of connected Actions in an ActionGraph
        
        This will add new Actions to the ActionGraph, as necessary, to convert
        units to match the necessary units needed by each Action.
        
        Parameters:
            graph (ActionGraph): The ActionGraph in which to match units 
        """
        for handle in graph.handles():
            GraphFiller._compute_units_(graph, handle)

    @staticmethod
    def _compute_units_(graph, vtx):
        nbrs = graph.neighbors_to(vtx)
        to_units = [GraphFiller._compute_units_(graph, nbr) for nbr in nbrs]
        if isinstance(vtx, Evaluator):
            arg_units = [to_units.pop(0) if arg is None else arg
                         for arg in vtx.signature]
            func = find(vtx.key, numargs=len(arg_units))
            ret_unit, new_units = func.units(*arg_units)
            for i, new_unit in enumerate(new_units):
                if new_unit is not None:
                    if vtx.signature[i] is not None:
                        raise UnitsError(('Argument {0} in action {1} requires '
                                          'units {2}').format(i, vtx, new_unit))
                    else:
                        old_unit = arg_units[i]
                        name = 'convert(from={0!r}, to={1!r})'.format(old_unit,
                                                                      new_unit)
                        cfunc = find_function('convert', 3)
                        cvtx = Evaluator('convert', name, cfunc,
                                                 signature=(None, old_unit, new_unit))
                        cvtx.units = new_unit
                        nbr = nbrs[sum(map(lambda k: 1 if k is None else 0,
                                           vtx.signature)[:i])]
                        cvtx.dimensions = nbr.dimensions
                        graph.disconnect(nbr, vtx)
                        graph.connect(nbr, cvtx)
                        graph.connect(cvtx, vtx)
            vtx.units = ret_unit
                        
        elif isinstance(vtx, Handle):
            old_unit = to_units[0]
            if vtx.units != old_unit:
                if old_unit.is_convertible(vtx.units):
                    name = 'convert(from={0!r}, to={1!r})'.format(old_unit,
                                                                  vtx.units)
                    cfunc = find_function('convert', 3)
                    cvtx = Evaluator('convert', name, cfunc,
                                             signature=(None, old_unit, vtx.units))
                    cvtx.units = vtx.units
                    cvtx.dimensions = vtx.dimensions

                    graph.disconnect(nbrs[0], vtx)
                    graph.connect(nbrs[0], cvtx)
                    graph.connect(cvtx, vtx)
                else:
                    if old_unit.calendar != vtx.units.calendar:
                        raise UnitsError(('Cannot convert {0} units to {1} '
                                          'units.  Calendars must be '
                                          'same.').format(nbrs[0], vtx))
                    else:
                        raise UnitsError(('Cannot convert {0} units '
                                          '{1!r} to {2} units '
                                          '{3!r}').format(nbrs[0], old_unit,
                                                          vtx, vtx.units))
        
        else:
            if len(to_units) == 1:
                vtx.units = to_units[0]

        return vtx.units

    def match_dimensions(self, graph):
        """
        Match dimensions of connected Actions in an ActionGraph
        
        This will add new Actions to the ActionGraph, as necessary, to transpose
        dimensions to match the necessary dimensions needed by each Action.
        
        Parameters:
            graph (ActionGraph): The ActionGraph in which to match dimensions 
        """
        # Fill the graph with dimensions up to the OutputSliceHandles and
        # compute the map of input dataset dimensions to output dataset dims
        dmap = {}
        for handle in graph.handles():
            GraphFiller._compute_dimensions_(graph, handle, dmap)
        
        for handle in graph.handles():
            nbr = graph.neighbors_to(handle)[0]
            if not all(d in dmap for d in nbr.dimensions):
                unmapped_dims = tuple(d for d in nbr.dimensions if d not in dmap)
                raise DimensionsError(('Could not determine complete dimension '
                                       'map for input dimensions '
                                       '{0}').format(unmapped_dims))
            mapped_dims = tuple(dmap[d] for d in nbr.dimensions)
            if handle.dimensions != mapped_dims:
                if set(handle.dimensions) == set(mapped_dims):
                    neworder = [handle.dimensions.index(d) for d in mapped_dims]
                    name = 'transpose({0!r}, order={1!r})'.format(mapped_dims,
                                                                  neworder)
                    tfunc = find_function('transpose', 2)
                    tvtx = Evaluator('transpose', name, tfunc,
                                             signature=(None, neworder))
                    tvtx.dimensions = handle.dimensions
                    tvtx.units = nbr.units
                    graph.disconnect(nbr, handle)
                    graph.connect(nbr, tvtx)
                    graph.connect(tvtx, handle)

    @staticmethod
    def _compute_dimensions_(graph, vtx, dmap={}):
        nbrs = graph.neighbors_to(vtx)
        to_dims = [GraphFiller._compute_dimensions_(graph, nbr, dmap)
                   for nbr in nbrs]
        if isinstance(vtx, Evaluator):
            arg_dims = [to_dims.pop(0) if arg is None else arg
                        for arg in vtx.signature]
            func = find(vtx.key, numargs=len(arg_dims))
            ret_dims, new_dims = func.dimensions(*arg_dims)
            for i, new_dim in enumerate(new_dims):
                if new_dim is not None:
                    if vtx.signature[i] is not None:
                        raise DimensionsError(('Argument {0} in action {1} '
                                               'requires dimensions '
                                               '{2}').format(i, vtx, new_dim))
                    else:
                        old_dim = arg_dims[i]
                        neworder = [new_dim.index(d) for d in old_dim]
                        name = 'transpose({0!r}, order={1!r})'.format(old_dim,
                                                                      neworder)
                        tfunc = find_function('transpose', 2)
                        tvtx = Evaluator('transpose', name, tfunc,
                                                 signature=(None, neworder))
                        tvtx.dimensions = new_dim
                        nbr = nbrs[sum(map(lambda k: 1 if k is None else 0,
                                           vtx.signature)[:i])]
                        tvtx.units = nbr.units
                        graph.disconnect(nbr, vtx)
                        graph.connect(nbr, tvtx)
                        graph.connect(tvtx, vtx)
            vtx.dimensions = ret_dims

        if isinstance(vtx, Handle):
            nbr = nbrs[0]
            to_dim = to_dims[0]
            if len(to_dim) != len(vtx.dimensions):
                raise DimensionsError(('Action {0} with dimensions {1} '
                                       'inconsistent with required output '
                                       'variable {2} dimensions '
                                       '{3}').format(nbr, to_dim, vtx,
                                                     vtx.dimensions))
            elif len(to_dim) == 1:
                dmap[to_dim[0]] = vtx.dimensions[0]
                
        else:
            if len(to_dims) == 1:
                vtx.dimensions = to_dims[0]

        return vtx.dimensions
