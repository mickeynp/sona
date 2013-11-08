#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import os
from astroid import builder, InferenceError, NotFoundError
from astroid.nodes import Module, Function
from astroid.bases import YES, BUILTINS, NodeNG
from astroid.manager import AstroidManager
from astroid.utils import ASTWalker
from astroid.as_string import AsStringVisitor
from collections import defaultdict

log = logging.getLogger(__name__)



# /class[name = 'foo', parent = 'object'], assignment[var = 'x']

class BaseSemanticError(Exception):
    pass

class NoNodeError(BaseSemanticError):
    def __init__(self, class_type, attr, query):
        msg = 'Cannot find a node {0!r} with attr {1!r} matching query {2!r}'\
            .format(class_type, attr, query)
        self.class_type = class_type
        self.query = query
        super(NoNodeError, self).__init__(self, msg)


class FunctionVisitor(AsStringVisitor, ASTWalker):

    def __init__(self):
        ASTWalker.__init__(self, self)
        self._visited = set()


    def visit(self, node):
        super(FunctionVisitor, self).visit(node)
        print node



# def autoyield(f):
#     """Takes a return value from the decorated function and iterates
#     over every item, yielding it."""
#     def function_wrapper(*args, **kwargs):
#         res = f(*args, **kwargs)
#     return function_wrapper


class LocalsVisitor(ASTWalker):
    """visit a project by traversing the locals dictionary"""

    def __init__(self):
        ASTWalker.__init__(self, self)
        self.string_visitor = AsStringVisitor()
        self._visited = {}
        self._nodemap = defaultdict(list)

    def visit(self, node):
        """launch the visit starting from the given node"""
        if node in self._visited:
            return
        self._visited[node] = 1 # FIXME: use set ?
        self._nodemap[node.__class__].append(node)

        methods = self.get_callbacks(node)
        if methods[0] is not None:
            methods[0](node)
        if 'locals' in node.__dict__: # skip Instance and other proxy
            for name, local_node in node.items():
                self.visit(local_node)
        if methods[1] is not None:
            return methods[1](node)

    @property
    def nodes(self):
        """Returns a list of Visited nodes."""
        return self._nodemap

class Indexer(object):
    """Indexer class that builds an AST using Astroid.

    The indexer exposes a selection of helper functions to find
    syntactic constructs along with, obviously, the AST itself. This
    is task is carried out by simple Visitor Patterns.
    """
    # TODO: Should break away the stuff that interacts with nodes to
    # another class.

    # Comparator function to use for comparisons
    @staticmethod
    def compare(a, b):
        """Case-sensitive comparison"""
        return a == b

    def __init__(self, s):
        """Builds an Indexer given s, a string object."""
        self._module_string = s
        tree = builder.AstroidBuilder().string_build(s)
        self.tree = tree

    @classmethod
    def from_file(cls, filename):
        """Builds an Indexer given f, a file-like object."""
        with open(filename) as f:
            return cls(f.read())

    def find(self, node_class):
        """Searches a Visitor's nodemap for a particular class.

        The class, node_class, must derive from astroid.nodes.BaseNG."""
        assert issubclass(node_class, NodeNG)
        visitor = LocalsVisitor()
        visitor.visit(self.tree)
        nodes = visitor.nodes
        return nodes.get(node_class, [])


    # Specific locators for various node classes.
    def _compare_by_attr(self, class_type, attr, expected_attr_value=None,
                         comparator=None, node_list=None):
        # If we are given an explicit list of nodes to search, use
        # that instead; otherwise, go find all the nodes matching
        # class_type.
        if node_list is None:
            nodes = self.find(class_type)
        else:
            nodes = node_list
        matches = []
        if comparator is None:
            comparator = self.compare
        for node in nodes:
            # If we are given a None value for expected_attr_value
            # then simply assume we want everything as a shorthand.
            if expected_attr_value is not None:
                result = comparator(getattr(node, attr), expected_attr_value)
            else:
                result = True
            if result:
                matches.append(node)
        if not matches:
            raise NoNodeError(class_type, attr, expected_attr_value)
        else:
            return matches

    def find_function_by_name(self, expected_attr_value=None, comparator=None, node_list=None):
        return self._compare_by_attr(Function, 'name', expected_attr_value, comparator, node_list)
