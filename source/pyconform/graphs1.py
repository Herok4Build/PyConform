"""
Directed Graph Data Structures and Tools

This module contains the DiGraph directional graph generic data structure.

COPYRIGHT: 2016, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from copy import deepcopy
from os import linesep


#===============================================================================
# DiGraph - A directed Graph data structure
#===============================================================================
class DiGraph(object):
    """
    A rudimentary directed graph data structure
    """
    
    def __init__(self):
        """
        Initializer
        """
        self._vertices = set()
        self._edges = list()

    def __eq__(self, other):
        """
        Check if an other graph is equal to this graph
        
        Equality for the DiGraph is defined as when all of the vertex
        objects and edges in the other graph are in this graph.
        
        Parameters:
            other (DiGraph): the graph to compare against
            
        Returns:
            bool: True if equal, False if not equal
        """
        if isinstance(other, DiGraph):
            if (self._vertices == other._vertices and 
                self._edges == other._edges):
                return True
        return False
    
    def __ne__(self, other):
        """
        Check if an other graph is not equal to this graph
        
        Inquality for the DiGraph is defined as when the other graph is
        found to NOT equal this graph.
        
        Parameters:
            other (DiGraph): the graph to compare against        
            
        Returns:
            bool: True if not equal, False if equal
        """
        return not (self == other)

    def __contains__(self, vertex):
        """
        Check if a vertex is in the graph
            
        Returns:
            bool: True if vertex in graph, False otherwise
        """
        return vertex in self._vertices
    
    def __len__(self):
        """
        Returns the number of vertices in the graph
        
        Returns:
            int: The number of vertices in the graph
        """
        return len(self._vertices)

    def __str__(self):
        """
        String representation of the graph
        """
        connected_vertices = set(sum(self.edges, ()))
        unconnected_vertices = self.vertices - connected_vertices
        strverts = ''.join('{0}    {1}'.format(linesep, str(v))
                           for v in unconnected_vertices) 
        stredges = ''.join('{0}    {1[0]} --> {1[1]}'.format(linesep, e)
                           for e in self.edges)
        return 'DiGraph:{0}{1}'.format(strverts, stredges)

    def sinks(self):
        """
        Returns the set of vertices in the graph with only incoming edges
        
        Returns:
            set: The set of vertices in the graph with only incoming edges
        """
        w_outgoing, w_incoming = zip(*self._edges)
        return set(w_incoming) - set(w_outgoing)

    def sources(self):
        """
        Returns the set of vertices in the graph with only outgoing edges
        
        Returns:
            set: The set of vertices in the graph with only outgoing edges
        """
        w_outgoing, w_incoming = zip(*self._edges)
        return set(w_outgoing) - set(w_incoming)
                
    def clear(self):
        """
        Remove all vertices and edges from the graph
        """
        self._vertices.clear()
        self._edges = list()

    def copy(self):
        """
        Create a new graph by copying another
            
        Returns:
            DiGraph: A copy of this graph
        """
        return deepcopy(self)

    @property
    def vertices(self):
        """
        Return the list of vertices in the graph
        
        Returns:
            list: The list of vertices contained in this graph
        """
        return self._vertices

    @property
    def edges(self):
        """
        Return the list of edges (vertex 2-tuples) in the graph
        
        Returns:
            list: The list of edges contained in this graph
        """
        return self._edges
    
    def add(self, vertex):
        """
        Add a vertex to the graph

        Parameters:
            vertex: The vertex object to be added to the graph
        """
        self._vertices.add(vertex)

    def remove(self, vertex):
        """
        Remove a vertex from the graph
        
        Parameters:
            vertex: The vertex object to remove from the graph
        """
        if vertex in self._vertices:
            self._vertices.remove(vertex)
        for edge in self._edges:
            if vertex in edge:
                self._edges.remove(edge)
                
    def update(self, other):
        """
        Update this graph with the union of itself and another
        
        Parameters:
            other (DiGraph): the other graph to union with
        """
        if not isinstance(other, DiGraph):
            raise TypeError("Cannot for union between DiGraph and non-DiGraph")
        self._vertices.update(other._vertices)
        self._edges.extend(other._edges)

    def union(self, other):
        """
        Form the union of this graph with another
        
        Parameters:
            other (DiGraph): the other graph to union with
        
        Returns:
            DiGraph: A graph containing the union of this graph with another
        """
        if not isinstance(other, DiGraph):
            raise TypeError("Cannot for union between DiGraph and non-DiGraph")
        G = self.copy()
        G.update(other)
        return G

    def connect(self, start, stop):
        """
        Add an edge to the graph
        
        If the vertices specified are not in the graph, they will be added.

        Parameters:
            start: The starting point of the edge to be added to the graph
            stop: The ending point of the edge to be added to the graph
        """
        self.add(start)
        self.add(stop)
        edge = (start, stop)
        if edge not in self._edges:
            self._edges.append((start, stop))

    def disconnect(self, start, stop):
        """
        Remove an edge from the graph

        Parameters:
            start: The starting point of the edge to be removed from the graph
            stop: The ending point of the edge to be removed from the graph
        """
        edge = (start, stop)
        if edge in self._edges:
            self._edges.remove(edge)

    def neighbors_from(self, vertex):
        """
        Return the list of neighbors on edges pointing from the given vertex
        
        Parameters:
            vertex: The vertex object to query
        
        Returns:
            list: The list of vertices with incoming edges from vertex
        """
        return [v2 for (v1, v2) in self._edges if v1 == vertex]

    def neighbors_to(self, vertex):
        """
        Return the list of neighbors on edges pointing to the given vertex
        
        Parameters:
            vertex: The vertex object to query
        
        Returns:
            list: The list of vertices with outgoing edges to vertex
        """
        return [v1 for (v1,v2) in self._edges if v2 == vertex]

    def iter_bfs(self, start, reverse=False):
        """
        Breadth-First Search generator from the root node
        
        Parameters:
            start: The starting vertex of the search
            reverse (bool): Whether to perform the search "backwards"
                through the graph (True) or "forwards" (False)
                
        Yields:
            The next vertex found in the breadth-first search from start
        """
        if start not in self._vertices:
            raise KeyError('Root vertex not in graph')
        
        visited = []
        queue = [start]
        if reverse:
            neighbors = self.neighbors_to
        else:
            neighbors = self.neighbors_from
        while queue:
            vertex = queue.pop(0)
            if vertex not in visited:
                yield vertex
                visited.append(vertex)
                queue.extend(v for v in neighbors(vertex) if v not in visited)

    def iter_dfs(self, start, reverse=False):
        """
        Depth-First Search generator from the root node
        
        Parameters:
            start: The starting vertex of the search
            reverse (bool): Whether to perform the search "backwards"
                through the graph (True) or "forwards" (False)
        """
        if start not in self._vertices:
            raise KeyError('Root vertex not in graph')
        
        visited = []
        stack = [start]
        if reverse:
            neighbors = self.neighbors_to
        else:
            neighbors = self.neighbors_from
        while stack:
            vertex = stack.pop()
            if vertex not in visited:
                yield vertex
                visited.append(vertex)
                stack.extend(v for v in neighbors(vertex) if v not in visited)

    def toposort(self):
        """
        Return a topological ordering of the vertices using Kahn's algorithm
        
        Returns:
            list: If topological ordering is possible, then return the list of
                topologically ordered vertices
            None: If topological ordering is not possible (i.e., if the DiGraph
                is cyclic), then return None
        """
        G = self.copy()
        sorted_list = []
        stack = list(G._vertices - set(map(lambda edge: edge[1], G._edges)))
        while stack:
            vertex = stack.pop()
            sorted_list.append(vertex)
            for neighbor in G.neighbors_from(vertex):
                G.disconnect(vertex, neighbor)
                if len(G.neighbors_to(neighbor)) == 0:
                    stack.append(neighbor)
        if len(G._edges) > 0:
            return None
        else:
            return sorted_list
        
    def is_cyclic(self):
        """
        Returns whether the graph is cyclic or not
        """
        return self.toposort() is None

    def components(self):
        """
        Return the connected components of the graph
        
        Returns:
            list: A list of connected DiGraphs
        """
        unvisited = set(self.vertices)
        components = []
        while unvisited:
            start = unvisited.pop()
            comp = type(self)()
            stack = [start]
            while stack:
                vertex = stack.pop()
                # Forward
                neighbors = [v for v in self.neighbors_from(vertex) 
                             if v not in comp.vertices]
                for neighbor in neighbors:
                    comp.connect(vertex, neighbor)
                stack.extend(neighbors)
                # Backward
                neighbors = [v for v in self.neighbors_to(vertex) 
                             if v not in comp.vertices]
                for neighbor in neighbors:
                    comp.connect(neighbor, vertex)
                stack.extend(neighbors)
                # Mark vertex as visited
                if vertex in unvisited:
                    unvisited.remove(vertex)
            if len(comp.vertices) > 0:
                components.append(comp)
        return components
