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
        result_stack = []

        # iterate over every search term and search operator after
        # parsing the string.
        for node in bep.iter_tree():
            # If the node is a SearchTerm we need to use the details
            # stored within it to query for the <node_type> with a
            # <node_attr> that is <conditional> to <node_value>.
            if isinstance(node, SearchTerm):
                try:
                    indexer_fn = INDEXER_MAPS[(node.search_type, node.search_attr)]
                    # This actually returns a list of nodes that matches the query.
                    nodes = indexer_fn(indexer, node.comp_value, comparator=node.conditional)
                    for node in nodes:
                        result_stack.append(node)
                except KeyError:
                    raise NoSemanticIndexerError('{0!r} does not have a valid locator assigned to it.'.format(node))
                except NoNodeError:
                    raise
        return result_stack

    def search(self, query):
        for filename in self.files:
            indexer = Indexer.from_file(filename)
            for node in self._find_query_in_module(query, indexer):
                yield node

