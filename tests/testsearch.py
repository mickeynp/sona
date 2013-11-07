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
def fn1():
    pass

def fn2():
    def fn3():
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

    @unittest.SkipTest
    def test_find_function_by_name_simple(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])
        # Test '=='
        nodes = list(self.searcher.search('fn:name == "fn1"'))
        self.assert_(len(nodes) == 1)
        node = nodes.pop()
        self.assertEqual(node.name, 'fn1')
        self.assertIsInstance(node, Function)
        # Test '!='
        nodes = list(self.searcher.search('fn:name != "fn1"'))
        self.assert_(len(nodes) == 2)
        # Is this in any way guaranteed to be deterministic? It seems
        # fn2 is found first in the AST; but this may just be a quirk
        # of how the leaf nodes on the AST are ordered?
        node = nodes.pop()
        self.assertIsInstance(node, Function)
        self.assertEqual(node.name, 'fn3')

        node = nodes.pop()
        self.assertIsInstance(node, Function)
        self.assertEqual(node.name, 'fn2')

    @unittest.SkipTest
    def test_find_function_by_name_complex(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])

        nodes = list(self.searcher.search('fn:name == "fn1" or fn:name == "fn2"'))
        self.assert_(len(nodes) == 2)

        node = nodes.pop()
        self.assertIsInstance(node, Function)
        self.assertEqual(node.name, 'fn2')

        node = nodes.pop()
        self.assertIsInstance(node, Function)
        self.assertEqual(node.name, 'fn1')


    def test_find_function_by_name_invalid(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])

        # This conjunction is clearly impossible. There is no function named fn1 AND fn2.
        nodes = list(self.searcher.search('fn:name == "fn1" and fn:name == "fn2"'))
        self.assert_(len(nodes) == 0)
