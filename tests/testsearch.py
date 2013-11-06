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

    def test_find_function_by_name(self):
        self.searcher.add_file(self.tmpfile.name)
        self.assertEqual(self.searcher.files, [self.tmpfile.name])
        nodes = list(self.searcher.search('fn:name == "fn1"'))
        self.assert_(len(nodes) == 1)
        node = nodes.pop()
        self.assertIsInstance(node, Function)
