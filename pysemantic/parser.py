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


class SearchOperator(object):

    # Dictionary of operator strings and equivalent lambdas that carry out
    # the actual boolean test.
    OPERATORS = {
        'and': lambda a,b: a and b,
        'or': lambda a,b: a or b,
        'not': lambda a: not a,
        }

    def __init__(self, node_operator):
        self.operator = self.OPERATORS[node_operator]

class BooleanExpressionParser(object):
    """Rudimentary Boolean Expression Parser

    Fairly rough-and-tumble EBNF:

    string = '"' , { printable characters sans '"'  }, '"' ;

    field = "fn" | "class" | ... , ":", "name" | "type" ... ;
    conditional = "==" | "!=" ;
    operator = "or" | "and" ;
    term = ( field , conditional , string ) ;
    expression =  term , { [ operator, term ] } ;
    """

    # A tree of all items pulled from the node
    _tree = []
    # A stack used for storing search terms until a suitable Operator
    # comes along.
    _stack = []
    IDENTIFIER = printables

    String = QuotedString('"')
    Field = Word(alphas) + Suppress(Literal(':')) + Word(IDENTIFIER)
    Conditional = (Keyword("==") | Keyword("!="))
    Operator = Keyword("or") | Keyword("and")
    Negation = Keyword("not")
    Term = Group(Field + Conditional + String)
    Expression = Forward()
    Expression << Term + ZeroOrMore(Group(Operator + Optional(Negation)) + Expression)

    PrecExpr = operatorPrecedence(Expression, [(Negation, 1, opAssoc.RIGHT),
                                               (Operator, 2,opAssoc.LEFT),])

    def parse_Term(self, token):
        """Parses a Term token."""
        l = token.asList()[0]
        st = SearchTerm(*l)
        self._tree.append(st)
        # TODO: We should not ever have more than two here.
        self._stack.append(st)

    def parse_Operator(self, token):
        l = token.asList()[0]
        op = SearchOperator(l)
        self._stack.append(op)

    def _apply_transformers(self):
        """Applies setParseActions to relevant tokens."""
        self.Term.setParseAction(self.parse_Term)
        self.Operator.setParseAction(self.parse_Operator)
        self.Negation.setParseAction(self.parse_Operator)

    def __init__(self, query=''):
        self._tree = []
        self._stack = []
        self._query = query
        self._apply_transformers()
        if query:
            self.PrecExpr.parseString(query)

    def iter_tree(self):
        for search_node in self._tree:
            yield search_node

if __name__ == '__main__':
    bep = BooleanExpressionParser()
    pt = bep.PrecExpr.parseString('fn:name == "mymethod" or cls:name != "myclass" and not cls:type != "type"')
