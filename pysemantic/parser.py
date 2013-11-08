#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
# Terrible...
from pyparsing import *

log = logging.getLogger(__name__)


class AssertionParser(object):


    IDENTIFIER = alphanums + "_"

    BoolConstant = Keyword("True") | Keyword("False")
    String = QuotedString('"') | QuotedString("'")

    Field = Word(IDENTIFIER) + Suppress(Literal(':')) + Word(IDENTIFIER)
    Conditional = (Keyword("==") | Keyword("!="))

    Assertion = Field + Conditional + String

    Expression = Group(Assertion | Field) + ZeroOrMore(Suppress(",") + Group(Assertion | Field))

    Query = Group(Expression) + Group(ZeroOrMore(Suppress(";") + Expression))

    def __init__(self, query=''):
        self._tree = []
        self._query = query
        if query:
            self._tree = self.Query.parseString(query, parseAll=True)

    def iter_tree(self):
        for search_node in self._tree:
            yield search_node

