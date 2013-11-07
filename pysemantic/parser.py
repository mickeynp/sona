#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
from astroid.nodes import Function, Class
# Terrible...
from pyparsing import *

log = logging.getLogger(__name__)


class SearchTerm(object):

    # Complete dictionary of valid conditionals we support, and the lambda
    # we map them to. The lambda must take two arguments and return a bool
    # indicating whether the comparison succeeded or not.
    CONDITIONALS = {
        '==': lambda a,b: a == b,
        '!=': lambda a,b: a != b,
        }

    # Dict of valid search types. Ideally this would be extended to all
    # conceivable search types Astroid/Python's AST support -- but in
    # praxis it's probably far less than that. Each entry must have a
    # string representation of the search type, and the equivalent
    # Astroid search class.
    SEARCH_TYPES = {
        'fn': Function,
        'cls': Class,
        }

    # Double-nested dictionary of each Astroid search class that exist
    # in SEARCH_TYPE and their respective search attributes. Each is
    # mapped to an equivalent attribute (as a string) on the Astroid
    # search class.
    SEARCH_ATTR = {
        Function: {
            'name': 'name',
            'type': 'type',
            },
        Class: {
            'name': 'name',
            'type': 'type',     # TODO: This is not right. Should be
                                # ancestors/parent classes.

            },
        }

    def __init__(self, search_type, search_attr,
                 conditional, comp_value):
        self.search_type = self.SEARCH_TYPES[search_type]
        self.search_attr = self.SEARCH_ATTR[self.search_type][search_attr]
        self.conditional = self.CONDITIONALS[conditional]
        self.comp_value = comp_value


class AssertionParser(object):


    IDENTIFIER = alphanums + "_"

    BoolConstant = Keyword("True") | Keyword("False")
    String = QuotedString('"')

    Field = Word(IDENTIFIER) + Suppress(Literal(':')) + Word(IDENTIFIER)
    Conditional = (Keyword("==") | Keyword("!="))

    Term = Field + Conditional + String

    Expression = Group(Term | Field) + ZeroOrMore(Suppress(",") + Group(Term | Field))

    Query = Group(Expression) + Group(ZeroOrMore(Suppress(";") + Expression))

    def parse_Term(self, token):
        """Parses a Term token."""
        l = token.asList()[0]
        st = SearchTerm(*l)
        self._tree.append(st)

    def parse_Operator(self, token):
        l = token.asList()[0]
        op = SearchOperator(l)
        self._tree.append(op)

    def _apply_transformers(self):
        """Applies setParseActions to relevant tokens."""
        self.Term.setParseAction(self.parse_Term)
        # self.Operator.setParseAction(self.parse_Operator)
        # self.Negation.setParseAction(self.parse_Operator)

    def __init__(self, query=''):
        self._tree = []
        self._stack = []
        self._query = query
        #self._apply_transformers()
        if query:
            self.Query.parseString(query, parseAll=True)

    def iter_tree(self):
        for search_node in self._tree:
            yield search_node

