#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import os

from pysemantic.parser import BooleanExpressionParser, SearchOperator, SearchTerm
from pysemantic.indexer import Indexer, NoNodeError

from astroid import builder, InferenceError, NotFoundError
from astroid.nodes import Module, Function
from astroid.bases import YES, BUILTINS, NodeNG
from astroid.manager import AstroidManager
from astroid.utils import ASTWalker
from astroid.as_string import AsStringVisitor
from collections import defaultdict

log = logging.getLogger(__name__)



class SemanticSearcherError(Exception):
    pass
class NoSemanticIndexerError(SemanticSearcherError):
    pass


class SemanticSearcher(object):

    def add_file(self, filepath):
        self.files.append(filepath)

    def __init__(self):
        self.files = []

    def _find_query_in_module(self, query, indexer):
        INDEXER_MAPS = {
            # <Node Class>, <Equiv Attr on Node Class>
            (Function, 'name'): Indexer.find_function_by_name,

            }
        bep = BooleanExpressionParser(query)
        matches = []
        # This is where we push the results (1 for True, 0 for False)
        # for the purpose of boolean evaluation, and at least one
        # operator. I cannot, at this time, conceive of a scenario in
        # which this stack will ever contain more than three eleents
        # at a time.
        stack = []
        # iterate over every search term and search operator after
        # parsing the string.
        for node in bep.iter_tree():
            assert len(stack) <= 3, 'SemanticSearcher stack length exceeds 3.\
 This should never occur!'
            # If the node is a SearchTerm we need to use the details
            # stored within it to query for the <node_type> with a
            # <node_attr> that is <conditional> to <node_value>.
            if isinstance(node, SearchTerm):
                try:
                    indexer_fn = INDEXER_MAPS[(node.search_type, node.search_attr)]

                    # This actually returns a list of nodes that matches the query.
                    nodes = indexer_fn(indexer, node.comp_value, comparator=node.conditional)

                    # Push False to the stack if we found no nodes, and True
                    # if we did find at least one.
                    stack.append(False if not nodes else True)
                    for node in nodes:
                        matches.append(node)

                except KeyError:
                    raise NoSemanticIndexerError('{0!r} does not have a valid locator assigned to it.'.format(node))
                except NoNodeError:
                    raise
            # If the node is a SearchOperator that means we must have
            if isinstance(node, SearchOperator):
                stack.append(node)
            # It's time to evaluate the items on the stack.
            if len(stack) == 3:
                # Stack should look like [bool, op, bool]
                left = stack.pop()
                operator = stack.pop()
                right = stack.pop()
                result = operator.operator(left, right)
                # Set the stack to the result
                stack = [result]
        return matches

    def search(self, query):
        for filename in self.files:
            indexer = Indexer.from_file(filename)
            for node in self._find_query_in_module(query, indexer):
                yield node

