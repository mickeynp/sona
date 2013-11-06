#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
from StringIO import StringIO
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pysemantic.indexer import Indexer, NoNodeError
from pysemantic.parser import BooleanExpressionParser, SearchTerm, SearchOperator
import pyparsing
import astroid.nodes

log = logging.getLogger(__name__)

class BEPTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_string(self):
        bep = BooleanExpressionParser()
        pt = bep.String.parseString('"Test String"')
        self.assertEqual(pt.pop(), 'Test String')

    def test_string_error(self):
        bep = BooleanExpressionParser()
        with self.assertRaises(pyparsing.ParseException):
            bep.String.parseString("'Test String'")

    def test_field(self):
        bep = BooleanExpressionParser()
        pt = bep.Field.parseString("testfield:testattr")
        self.assertEqual(pt.pop(0), 'testfield')
        self.assertEqual(pt.pop(0), 'testattr')

    def test_field_error(self):
        bep = BooleanExpressionParser()
        # missing something : and second half
        with self.assertRaises(pyparsing.ParseException):
            pt = bep.Field.parseString("testfield")
        with self.assertRaises(pyparsing.ParseException):
            pt = bep.Field.parseString("testfield:")
        with self.assertRaises(pyparsing.ParseException):
            pt = bep.Field.parseString(":foo")

    def test_conditional(self):
        bep = BooleanExpressionParser()
        pt = bep.Conditional.parseString("==")
        self.assertEqual(pt.pop(), '==')
        pt = bep.Conditional.parseString("!=")
        self.assertEqual(pt.pop(), '!=')

    def test_operator(self):
        bep = BooleanExpressionParser()
        pt = bep.Operator.parseString("or")
        self.assertEqual(pt.pop(), 'or')
        pt = bep.Operator.parseString("and")
        self.assertEqual(pt.pop(), 'and')

    def test_term(self):
        bep = BooleanExpressionParser()
        pt = bep.Term.parseString('fn:name == "hello"').asList()[0]

        self.assertEqual(pt.pop(0), 'fn')
        self.assertEqual(pt.pop(0), 'name')
        self.assertEqual(pt.pop(0), '==')
        self.assertEqual(pt.pop(0), 'hello')
        st = bep._tree[0]
        self.assertIsInstance(st, SearchTerm)

    def test_term_error(self):
        bep = BooleanExpressionParser('')
        with self.assertRaises(pyparsing.ParseException):
            pt = bep.Term.parseString('fn:name <> "hello"')
        with self.assertRaises(pyparsing.ParseException):
            pt = bep.Term.parseString('fn:name ==')
        with self.assertRaises(pyparsing.ParseException):
            pt = bep.Term.parseString('fn: ==')

    def test_expression(self):
        bep = BooleanExpressionParser()
        pt = bep.PrecExpr.parseString('fn:name == "mymethod" or cls:name != "myclass" and not cls:type != "type"')
        expected = [['fn', 'name', '==', 'mymethod'], ['or'],
                    ['cls', 'name', '!=', 'myclass'], ['and', 'not'],
                    ['cls', 'type', '!=', 'type']]
        self.assertListEqual(pt.asList(), expected)



