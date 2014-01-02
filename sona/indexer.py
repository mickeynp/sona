#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import itertools

from astroid import builder, InferenceError, NotFoundError
from astroid.nodes import (Module, Function, Class, CallFunc, Assign,
                           AssName, Name, Arguments, AssAttr)
from astroid.node_classes import Getattr
from astroid.bases import YES, BUILTINS, NodeNG
from astroid.manager import AstroidManager
from astroid.utils import ASTWalker
from astroid.as_string import AsStringVisitor
from collections import defaultdict

from sona.locators import compare_by_attr, get_all_parents, find_immediate_name

log = logging.getLogger(__name__)


class IndexVisitor(ASTWalker):

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
        if node.parent is not None:
            self.visit(node.parent)
        for child in node.get_children():
            self.visit(child)
        if methods[0] is not None:
            methods[0](node)
        # This is needed to avoid stuff like __div__, etc. from
        # appearing in our node list (unnecessarily.)
        if 'locals' in node.__dict__:
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

    def __init__(self, filename):
        """Builds an Indexer given s, a string object."""
        self._filename = filename
        self._visitor = None
        tree = builder.AstroidBuilder().file_build(filename)
        self.tree = tree

    def find(self, *node_classes):
        """Searches a Visitor's nodemap for particular classes.

        The class, node_class, must derive from astroid.nodes.BaseNG."""
        if self._visitor is None:
            self._visitor = IndexVisitor()
            self._visitor.visit(self.tree)
        nodes = self._visitor.nodes
        for cls in node_classes:
            assert issubclass(cls, NodeNG)
            matching_nodes = nodes.get(cls, [])
            for node in matching_nodes:
                yield node

    def find_function_by_name(self, expected_attr_value=None,
                              comparator=None, node_list=None):
        return compare_by_attr(self, Function, 'name', expected_attr_value,
                               comparator, node_list)

    def find_function_by_argcount(self, expected_attr_value=None,
                                  comparator=None, node_list=None):
        def argcounter(node, comp):
            # This is a bit grizzly: we basically rely on the side
            # effect that bool(), if given something that it can treat
            # as True, is equivalent to 1.
            return comp(len(node.args.args) +
                        bool(node.args.vararg) +
                        bool(node.args.kwarg),
                        expected_attr_value)

        return compare_by_attr(self, Function, None, expected_attr_value,
                               comparator, node_list,
                               closed_fn=argcounter)

    def find_parent_by_name(self, expected_attr_value=None,
                            comparator=None, node_list=None):
        def check_parent(node, comp):
            for parent_node in get_all_parents(node):
                try:
                    return comp(parent_node.name, expected_attr_value)
                except AttributeError:
                    pass
            # Fall-through.
            return False
        return compare_by_attr(self, Function, None, expected_attr_value,
                               comparator, node_list,
                               closed_fn=check_parent)
    
    def find_function_by_call(self, expected_attr_value=None,
                          comparator=None, node_list=None):
        def call_function(node, comp):
            return comp(
                find_immediate_name(node),
                expected_attr_value
                )
        return compare_by_attr(self, CallFunc, None, expected_attr_value,
                               comparator, node_list,
                               closed_fn=call_function)
    ###########
    # Classes #
    ###########

    def find_class_by_name(self, expected_attr_value=None,
                           comparator=None, node_list=None):
        return compare_by_attr(self, Class, 'name', expected_attr_value,
                               comparator, node_list)

    def find_class_by_parent(self, expected_attr_value=None,
                             comparator=None, node_list=None):
        def check_bases(node, comp):
            bases = set([comp(find_immediate_name(base), expected_attr_value) for base in node.bases])
            # node.bases might be empty so we also check that bases contains something.
            return all(bases) and bases
        return compare_by_attr(self, Class, None, expected_attr_value,
                               comparator, node_list,
                               closed_fn=check_bases)

    def find_class_method(self, expected_attr_value=None,
                          comparator=None, node_list=None):
        # This is functionally equivalent to:
        #    fn:name == <name>, fn:parent == <class>
        all_functions = self.find_function_by_name(None, comparator, node_list)
        return self.find_parent_by_name(expected_attr_value, comparator, all_functions)


    #############
    # Variables #
    #############

    def find_variable_by_name(self, expected_attr_value=None,
                              comparator=None, node_list=None):

        variables = compare_by_attr(self, AssName, 'name', expected_attr_value,
                                    comparator, node_list)
        # Filter out variables that are "assigned" in the function
        # arguments. It's technically an assignment but it is not what
        # people would expect.
        return [variable for variable in variables
                if not isinstance(variable.parent, Arguments) #and\
                    # not isinstance(variable.parent.parent, Function)
                ]

