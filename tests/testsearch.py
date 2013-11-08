#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import tempfile
from StringIO import StringIO
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pysemantic.search import SemanticSearcher
from astroid.nodes import Function
import astroid.nodes


log = logging.getLogger(__name__)


FUNCTIONS_STR = """
def fn2():
    def fn3():
        pass

def fn1():
    pass

"""
class SearchTest(unittest.TestCase):

    def setUp(self):
        self.searcher = SemanticSearcher()
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.tmpfile.write(FUNCTIONS_STR)
        self.tmpfile.flush()

    def tearDown(self):
        self.tmpfile = None

    def test_find_function_by_name_simple(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])
        # Test '=='
        nodes = set(self.searcher.search('fn:name == "fn1"'))
        self.assert_(len(nodes) == 1)
        node = nodes.pop()
        self.assertEqual(node.name, 'fn1')
        self.assertIsInstance(node, Function)
        # Test '!='
        nodes = set(self.searcher.search('fn:name != "fn1"'))
        self.assert_(len(nodes) == 2)

    def test_find_function_by_name_complex(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])

        nodes = set(self.searcher.search('fn:name == "fn1", fn:name == "fn2"'))
        self.assert_(len(nodes) == 1)

        node = nodes.pop()
        self.assertIsInstance(node, Function)
        self.assertEqual(node.name, 'fn1')


    def test_find_function_by_name_invalid(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])

        # Should be 1 because the first assertion limits the search
        # set to just functions named "fn1", and the second tries to
        # find all the ones not named "fn1" -- which obviously fails.
        nodes = set(self.searcher.search('fn:name == "fn1", fn:name != "fn1"'))
        self.assert_(len(nodes) == 1)

    def test_multiple_expressions(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])
        nodes = set(self.searcher.search('fn:name == "fn1"; fn:name == "fn2"'))
        self.assert_(len(nodes) == 2)
        self.assertEqual(set([node.name for node in nodes]), set(['fn1', 'fn2']))

    def test_simple_assertion(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])
        nodes = set(self.searcher.search('fn:name'))
        self.assert_(len(nodes) == 3)
        self.assertSetEqual(set([node.name for node in nodes]), set(['fn2', 'fn3', 'fn1']))

        # doubling the number of assertions in the same expression
        # should still give the same result -- we simply aren't
        # filtering anything.
        nodes = set(self.searcher.search('fn:name, fn:name'))
        self.assert_(len(nodes) == 3)
        self.assertEqual(set([node.name for node in nodes]), set(['fn2', 'fn3', 'fn1']))

        # doubling the number of assertions in two different
        # expressions should still give the same result -- we simply
        # aren't filtering anything.
        nodes = set(self.searcher.search('fn:name; fn:name'))
        self.assert_(len(nodes) == 3)
        self.assertEqual(set([node.name for node in nodes]), set(['fn2', 'fn3', 'fn1']))


