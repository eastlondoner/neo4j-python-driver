#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2018 "Neo Technology,"
# Network Engine for Objects in Lund AB [http://neotechnology.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Graph data types
"""


__all__ = [
    "Graph",
    "Entity",
    "Node",
    "Relationship",
    "Path",
]


class Graph(object):

    def __init__(self):
        self.__nodes = {}
        self.__relationships = {}


class Entity(object):
    """ Base class for Node and Relationship.
    """
    graph = None
    id = None
    properties = None

    def __init__(self, properties=None, **kwproperties):
        properties = dict(properties or {}, **kwproperties)
        self.properties = dict((k, v) for k, v in properties.items() if v is not None)

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return len(self.properties)

    def __getitem__(self, name):
        return self.properties.get(name)

    def __contains__(self, name):
        return name in self.properties

    def __iter__(self):
        return iter(self.properties)

    def get(self, name, default=None):
        """ Get a property value by name, optionally with a default.
        """
        return self.properties.get(name, default)

    def keys(self):
        """ Return an iterable of all property names.
        """
        return self.properties.keys()

    def values(self):
        """ Return an iterable of all property values.
        """
        return self.properties.values()

    def items(self):
        """ Return an iterable of all property name-value pairs.
        """
        return self.properties.items()


class Node(Entity):
    """ Self-contained graph node.
    """
    labels = None

    @classmethod
    def hydrate(cls, id_, labels, properties=None):
        inst = cls(labels, properties)
        inst.id = id_
        return inst

    def __init__(self, labels=None, properties=None, **kwproperties):
        super(Node, self).__init__(properties, **kwproperties)
        self.labels = set(labels or set())

    def __repr__(self):
        return "<Node id=%r labels=%r properties=%r>" % \
               (self.id, self.labels, self.properties)


class Relationship(Entity):
    """ Self-contained graph relationship.
    """

    #: The start node of this relationship
    start = None

    #: The end node of this relationship
    end = None

    #: The type of this relationship
    type = None

    @classmethod
    def hydrate(cls, id_, start, end, type, properties=None):
        inst = cls(start, end, type, properties)
        inst.id = id_
        return inst

    @classmethod
    def hydrate_unbound(cls, id_, type, properties=None):
        return cls.hydrate(id_, None, None, type, properties)

    def __init__(self, start, end, type, properties=None, **kwproperties):
        super(Relationship, self).__init__(properties, **kwproperties)
        self.start = start
        self.end = end
        self.type = type

    def __repr__(self):
        return "<Relationship id=%r start=%r end=%r type=%r properties=%r>" % \
               (self.id, self.start, self.end, self.type, self.properties)

    @property
    def nodes(self):
        return self.start, self.end


class Path(object):
    """ Self-contained graph path.
    """
    nodes = None
    relationships = None

    @classmethod
    def hydrate(cls, nodes, rels, sequence):
        assert len(nodes) >= 1
        assert len(sequence) % 2 == 0
        last_node = nodes[0]
        entities = [last_node]
        for i, rel_index in enumerate(sequence[::2]):
            assert rel_index != 0
            next_node = nodes[sequence[2 * i + 1]]
            if rel_index > 0:
                r = rels[rel_index - 1]
                r.start = last_node.id
                r.end = next_node.id
                entities.append(r)
            else:
                r = rels[-rel_index - 1]
                r.start = next_node.id
                r.end = last_node.id
                entities.append(r)
            entities.append(next_node)
            last_node = next_node
        return cls(*entities)

    def __init__(self, start_node, *rels_and_nodes):
        self.nodes = (start_node,) + rels_and_nodes[1::2]
        self.relationships = rels_and_nodes[0::2]

    def __repr__(self):
        return "<Path start=%r end=%r size=%s>" % \
               (self.start.id, self.end.id, len(self))

    def __eq__(self, other):
        try:
            return self.start == other.start and self.relationships == other.relationships
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        value = hash(self.start)
        for relationship in self.relationships:
            value ^= hash(relationship)
        return value

    def __len__(self):
        return len(self.relationships)

    def __iter__(self):
        return iter(self.relationships)

    @property
    def start(self):
        return self.nodes[0]

    @property
    def end(self):
        return self.nodes[-1]


__hydration_functions = {
    b"N": Node.hydrate,
    b"R": Relationship.hydrate,
    b"r": Relationship.hydrate_unbound,
    b"P": Path.hydrate,
}

__dehydration_functions = {
    # There is no support for passing graph types into queries as parameters
}


def hydration_functions(graph):
    return __hydration_functions


def dehydration_functions():
    return __dehydration_functions
