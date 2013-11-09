#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sona.parser import AssertionParser
import pyparsing

log = logging.getLogger(__name__)


class AssertionParserTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_string(self):
        ap = AssertionParser()
        pt = ap.String.parseString('"Test String"')
        self.assertEqual(pt.pop(), 'Test String')
        pt = ap.String.parseString("'Test String'")
        self.assertEqual(pt.pop(), 'Test String')

    def test_number(self):
        ap = AssertionParser()
        pt = ap.Number.parseString('100392')
        self.assertEqual(pt.pop(), 100392)

    def test_string_error(self):
        ap = AssertionParser()
        with self.assertRaises(pyparsing.ParseException):
            ap.String.parseString("'Test String\"")

    def test_field(self):
        ap = AssertionParser()
        pt = ap.Field.parseString("testfield:testattr")
        self.assertEqual(pt.pop(0), 'testfield')
        self.assertEqual(pt.pop(0), 'testattr')

    def test_field_error(self):
        ap = AssertionParser()
        # missing something : and second half
        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Field.parseString("testfield")
        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Field.parseString("testfield:")
        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Field.parseString(":foo")

    def test_conditional(self):
        ap = AssertionParser()
        pt = ap.Conditional.parseString("==")
        self.assertEqual(pt.pop(), '==')
        pt = ap.Conditional.parseString("!=")
        self.assertEqual(pt.pop(), '!=')

    def test_assertion(self):
        ap = AssertionParser()
        pt = ap.Assertion.parseString('fn:name == "hello"').asList()

        self.assertEqual(pt.pop(0), 'fn')
        self.assertEqual(pt.pop(0), 'name')
        self.assertEqual(pt.pop(0), '==')
        self.assertEqual(pt.pop(0), 'hello')

    def test_assertion_number(self):
        ap = AssertionParser()
        pt = ap.Assertion.parseString('fn:argcount == 3').asList()

        self.assertEqual(pt.pop(0), 'fn')
        self.assertEqual(pt.pop(0), 'argcount')
        self.assertEqual(pt.pop(0), '==')
        self.assertEqual(pt.pop(0), 3)

    def test_assertion_error(self):
        ap = AssertionParser()
        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Assertion.parseString('fn:name <> "hello"')
        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Assertion.parseString('fn:name ==')
        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Assertion.parseString('fn: ==')

    def test_expr(self):
        ap = AssertionParser()
        pt = ap.Expression.parseString('fn:name == "foo" , cls:name == "bar"')
        assertion1 = pt.asList()[0]
        assertion2 = pt.asList()[1]
        self.assertEqual(assertion1, ['fn', 'name', '==', 'foo'])
        self.assertEqual(assertion2, ['cls', 'name', '==', 'bar'])
        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Assertion.parseString('fn:name == , cls:name')

        pt = ap.Expression.parseString('fn:name, cls:name')
        self.assertEqual(pt.asList(), [['fn', 'name'], ['cls', 'name']])

    def test_query(self):
        ap = AssertionParser()
        pt = ap.Query.parseString('fn:name; cls:name == "foo"')
        self.assertEqual(pt.asList(), [[['fn', 'name']], [['cls', 'name', '==', 'foo']]])

        pt = ap.Query.parseString('fn:name == "hello", fn:name != "goodbye"; cls:name == "test"')
        self.assertEqual(pt.asList(), [[['fn', 'name', '==', 'hello'],
                                        ['fn', 'name', '!=', 'goodbye']],
                                       [['cls', 'name', '==', 'test']]])

        pt = ap.Query.parseString('fn:name; cls:name')
        self.assertEqual(pt.asList(), [[['fn', 'name']], [['cls', 'name']]])

        with self.assertRaises(pyparsing.ParseException):
            pt = ap.Query.parseString('fn:name cls:name, fn:name', parseAll=True)





