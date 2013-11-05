#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
from StringIO import StringIO
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pysemantic.indexer import Indexer, NoNodeError
import astroid.nodes


log = logging.getLogger(__name__)


FUNCTIONS_STR = """
def fn1():
    pass

def fn2():
    def fn3():
        pass
"""
class IndexerTest(unittest.TestCase):

    def setUp(self):
        self.index = Indexer(FUNCTIONS_STR)

    def test_function_visitor(self):
        fns = set([fns.name for fns in self.index.find(astroid.nodes.Function)])
        self.assertEqual(fns, set(['fn1', 'fn2', 'fn3']))

    def test_node_class_not_found(self):
        self.assertEqual(self.index.find(astroid.nodes.Pass), [])

    def test_find_function_by_name(self):
        node = self.index.find_function_by_name('fn2')
        self.assertIsInstance(node, astroid.nodes.Function)
        self.assertEqual(node.name, 'fn2')

    def test_find_function_error(self):
        with self.assertRaises(NoNodeError):
            node = self.index.find_function_by_name('fn4')

