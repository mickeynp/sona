#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import functools
import itertools

from astroid import builder, InferenceError, NotFoundError
from astroid.nodes import Module, Function, Class, CallFunc, Assign, AssName, Name
from astroid.node_classes import Getattr
from astroid.bases import YES, BUILTINS, NodeNG
from astroid.manager import AstroidManager
from astroid.utils import ASTWalker
from astroid.as_string import AsStringVisitor

from sona.exceptions import NoNodeError


log = logging.getLogger(__name__)

def compare(a, b):
    """Case-sensitive comparison"""
    return a == b

DEFAULT_COMPARATOR = compare

def find_immediate_name(node):
    """Finds the immediate name of a CallFunc node."""
    try:
        if isinstance(node, CallFunc):
            # A function may turn out to be an attribute on
            # something else; quite possibly a class. If it's an
            # attribute that we "call" -- use its attrname instead
            # of just "name".
            if isinstance(node.func, Getattr):
                return node.func.attrname
            else:
                return node.func.name
        else:
            if isinstance(node, Getattr):
                return node.attrname
            return node.name
    except AttributeError:
        return ''

def get_all_parents(node):
    """Yields the entire parent hierarchy of node"""
    n = node
    while n.parent:
        try:
            parent = n.parent
            yield parent
            n = parent
        except AttributeError:
            break


# Specific locators for various node classes.
def compare_by_attr(indexer, class_types, attr=None, expected_attr_value=None,
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
        nodes = itertools.chain(indexer.find(class_types))
    else:
        nodes = node_list
    matches = []
    if comparator is None:
        comparator = DEFAULT_COMPARATOR
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


