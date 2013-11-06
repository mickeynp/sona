#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import string
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

    # List of valid node types. Ideally this would be extended to all
    # conceivable node types Astroid/Python's AST support -- but in
    # praxis it's probably far less than that. Each entry must have a
    # string representation of the node type, and the equivalent
    # Astroid node class.
    NODE_TYPES = {
        'fn': Function,
        'cls': Class,
        }

    # Double-nested dictionary of each Astroid node class that exist
    # in NODE_TYPE and their respective node attributes. Each is
    # mapped to an equivalent attribute (as a string) on the Astroid
    # node class.
    NODE_ATTR = {
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

    def __init__(self, node_type, node_attr,
                 conditional, comp_value):
        self.node_type = self.NODE_TYPES[node_type]
        self.node_attr = self.NODE_ATTR[self.node_type][node_attr]
        self.conditional = self.CONDITIONALS[conditional]
        self.comp_value = comp_value

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

    _tree = []
    IDENTIFIER = printables

    String = QuotedString('"')
    Field = Word(alphas) + Suppress(Literal(':')) + Word(IDENTIFIER)
    Conditional = (Keyword("==") | Keyword("!="))
    Operator = Keyword("or") | Keyword("and")
    Negation = Keyword("not")
    Term = Group(Field + Conditional + String)
    Expression = Forward()
    Expression << Term + ZeroOrMore(Operator + Optional(Negation) + Expression)

    PrecExpr = operatorPrecedence(Expression, [(Negation, 1, opAssoc.RIGHT),
                                               (Operator, 2,opAssoc.LEFT),])

    def parse_Term(self, token):
        """Parses a Term token."""
        l = token.asList()[0]
        self._tree.append(SearchTerm(*l))

    def _apply_transformers(self):
        """Applies setParseActions to relevant tokens."""
        self.Term.setParseAction(self.parse_Term)

    def __init__(self):
        self._tree = []
        self._apply_transformers()
