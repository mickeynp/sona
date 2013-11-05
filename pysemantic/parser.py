#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging

# Terrible...
from pyparsing import *

log = logging.getLogger(__name__)




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

