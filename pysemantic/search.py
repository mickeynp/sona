#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import os

from pysemantic.parser import AssertionParser
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
class InvalidTermError(SemanticSearcherError):
    pass


INDEXER_MAPS = {
    # <Node type>, <Equiv Attr on Node Class>
    ('fn', 'name'): Indexer.find_function_by_name,

    }
# TODO: This should be in parser.py?
COMPARATOR_MAP = {
    '==': lambda a,b: a == b,
    '!=': lambda a,b: a != b,
    }

class SemanticSearcher(object):
    """Semantic Searcher class. Returns a list of matching nodes given a string query.


    aggressive_search - if True, an assertion that returns NoNodeError
    will not halt the evaluation of that expression. If False, any
    assertion that returns NoNodeError is instead halted, its results
    up until then kept, and the next expression is evaluated."""
    aggressive_search = False


    def add_file(self, filepath):
        self.files.append(filepath)

    def __init__(self):
        self.files = []
        self.aggressive_search = False

    def _find_query_in_module(self, query, indexer):
        ap = AssertionParser(query)
        matches = []

        # Iterate over the tree. A tree is made up of many nested
        # lists with the following pattern:
        #
        # [[[term], ...],
        #  [[term, ...], ...], ...]
        for expression in ap.iter_tree():
            nodes = None
            # Each expression, in turn, has N number of terms, which
            # in turn is made up of a field node type; a field
            # attribute; a conditional; and a value.
            for term in expression:
                if not len(term) in [2, 4]:
                    raise InvalidTermError('Term {0!r} contained {1} items instead of\
 the expected 2 or 4'.format(term, len(term)))
                try:
                    if len(term) == 2:
                        node_type, node_attr = term
                        # Blank these out if term only has two
                        # elements. That means it's of the form
                        # "type:attr" which is shorthand for "match
                        # everything".
                        conditional = None
                        comp_value = None
                    else:
                        node_type, node_attr, conditional, comp_value = term

                    comparator = COMPARATOR_MAP[conditional]
                    indexer_fn = INDEXER_MAPS[(node_type, node_attr)]

                    try:
                        # This actually returns a list of nodes that matches the query.
                        nodes = indexer_fn(indexer, comp_value, comparator=comparator, node_list=nodes)

                    except NoNodeError:
                        # It's perfectly OK if NoNodeError is raised
                        # -- all that means is one leg of the query
                        # failed to match.
                        nodes = None

                        # Break if aggressive_search is not True.
                        if not self.aggressive_search:
                            break

                    for node in nodes:
                        matches.append(node)

                except KeyError:
                    raise NoSemanticIndexerError('{0!r} does not have a valid locator assigned to it.'.format(node))
                except NoNodeError:
                    raise
        return matches

    def search(self, query):
        for filename in self.files:
            indexer = Indexer.from_file(filename)
            for node in self._find_query_in_module(query, indexer):
                yield node

