#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
# Terrible...
from pyparsing import *

ParserElement.enablePackrat()

log = logging.getLogger(__name__)


class AssertionParser(object):


    IDENTIFIER = alphanums + "_"

    BoolConstant = Keyword("True") | Keyword("False")
    String = QuotedString('"') | QuotedString("'")
    Number = Word(nums).setParseAction(lambda s, l, t: [int(t[0])])
    Set = Group(Suppress('{') + delimitedList(String | Number, delim=',') + Suppress('}'))
    Identifier = Word(IDENTIFIER)

    Field = Identifier + Suppress(Literal(':')) + Identifier

    Conditional = (Keyword("==") | Keyword("!=") | Keyword("in") | (Keyword("not") + Keyword("in")).setParseAction(lambda s, l, t: 'not in'))

    Assertion = (Field + Conditional + (String | Number | Set))

    Expression = Group(Assertion | Field) + ZeroOrMore(Suppress(",") + Group(Assertion | Field))

    Query = Group(Expression) + Group(ZeroOrMore(Suppress(";") + Expression))

    def __init__(self, query=''):
        self._tree = []
        self._query = query
        if query:
            self._tree = self.Query.parseString(query, parseAll=True)

    @property
    def tree(self):
        return self._tree

    def iter_tree(self):
        for search_node in self._tree:
            yield search_node

