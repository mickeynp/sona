#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import itertools

from astroid import builder, InferenceError, NotFoundError
from astroid.nodes import Module, Function, Class, CallFunc, Assign, AssName, Name
from astroid.node_classes import Getattr
from astroid.bases import YES, BUILTINS, NodeNG
from astroid.manager import AstroidManager
from astroid.utils import ASTWalker
from astroid.as_string import AsStringVisitor
from collections import defaultdict

log = logging.getLogger(__name__)

class BaseSemanticError(Exception):
    pass

class NoNodeError(BaseSemanticError):
    def __init__(self, class_types, attr, query):
        msg = 'Cannot find a node {0!r} with attr {1!r} matching query {2!r}'\
            .format(class_types, attr, query)
        self.class_types = class_types
        self.query = query
        super(NoNodeError, self).__init__(self, msg)


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

    def __init__(self, filename):
        """Builds an Indexer given s, a string object."""
        self._filename = filename
        self._visitor = None
        tree = builder.AstroidBuilder().file_build(filename)
        self.tree = tree

    # @classmethod
    # def from_file(cls, filename):
    #     """Builds an Indexer given f, a file-like object."""
    #     with open(filename) as f:
    #         return cls(f.read())

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

    # Specific locators for various node classes.
    def _compare_by_attr(self, class_types, attr=None, expected_attr_value=None,
                         comparator=None, node_list=None, closed_fn=None):
        """Handy generic method for querying the parse tree.

        class_types must be a valid Astroid node class or a tuple of
        node classes to find.

        attr is the string attribute (via getattr()) that you want to
        use for the comparison

        expected_attr_value is the expected attribute value. If it's
        None, it means \"always match\".

        comparator is the comparison function to use to compare the
        attribute value on each node against expected_attr_value. If
        it is None, use the default == comparison.

        node_list is an optional list of nodes to scan *instead* of
        the default parse tree. Note: node_list is expected to be a
        flat list and not a parse tree.

        closed_fn is an optional callable that is call and closed over
        the variables node and comparator. Its result is used to
        determine whether a node should be included in the matches
        list. """
        assert attr is not None or closed_fn is not None, \
            'Either closed_fn or attr must be non-None'
        # If we are given an explicit list of nodes to search, use
        # that instead; otherwise, go find all the nodes matching
        # class_types.
        if node_list is None:
            nodes = itertools.chain(self.find(class_types))
        else:
            nodes = node_list
        matches = []
        if comparator is None:
            comparator = self.compare
        for node in nodes:
            # We may not get a match against a particular node class;
            # skip those.
            if not node:
                continue
            # if we are given a closed_fn argument we must first make
            # sure it's callable. After that, we simply call it with
            # the pertinent arguments (node and attr) and store its
            # result. If only Python has defmacro. sigh.
            if (closed_fn is not None) and (expected_attr_value is not None):
                assert callable(closed_fn), 'closed_fn must be callable!'
                # Pass back in the comparator function, even though it
                # may be the same as what we were called with.
                result = closed_fn(node, comp=comparator)
            # If we are given a None value for expected_attr_value
            # then simply assume we want everything as a shorthand.
            if (closed_fn is None) and (expected_attr_value is not None):
                result = comparator(getattr(node, attr), expected_attr_value)
            elif expected_attr_value is None:
                result = True
            if result:
                matches.append(node)
        if not matches:
            raise NoNodeError(class_types, attr, expected_attr_value)
        else:
            return matches

    def _get_all_parents(self, node):
        """Yields the entire parent hierarchy of node"""
        n = node
        while n.parent:
            try:
                parent = n.parent
                yield parent
                n = parent
            except AttributeError:
                break

    def find_function_by_name(self, expected_attr_value=None,
                              comparator=None, node_list=None):
        return self._compare_by_attr(Function, 'name', expected_attr_value,
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
        return self._compare_by_attr(Function, None, expected_attr_value,
                                     comparator, node_list,
                                     closed_fn=argcounter)

    def find_class_by_name(self, expected_attr_value=None,
                              comparator=None, node_list=None):
        return self._compare_by_attr(Class, 'name', expected_attr_value,
                                     comparator, node_list)

    def find_parent_by_name(self, expected_attr_value=None,
                              comparator=None, node_list=None):
        def check_parent(node, comp):
            for parent_node in self._get_all_parents(node):
                try:
                    return comp(parent_node.name, expected_attr_value)
                except AttributeError:
                    pass
            # Fall-through.
            return False

        return self._compare_by_attr(Function, None, expected_attr_value,
                                     comparator, node_list,
                                     closed_fn=check_parent)

    @staticmethod
    def _find_immediate_name(n):
        """Finds the immediate name of a CallFunc node."""
        try:
            if isinstance(n, CallFunc):
                # A function may turn out to be an attribute on
                # something else; quite possibly a class. If it's an
                # attribute that we "call" -- use its attrname instead
                # of just "name".
                if isinstance(n.func, Getattr):
                    return n.func.attrname
                else:
                    return n.func.name
            else:
                return n.name
        except AttributeError:
            return ''

    def find_function_by_call(self, expected_attr_value=None,
                          comparator=None, node_list=None):

        def call_function(node, comp):
            return comp(
                self._find_immediate_name(node),
                expected_attr_value
                )
        return self._compare_by_attr(CallFunc, None, expected_attr_value,
                                     comparator, node_list,
                                     closed_fn=call_function)
