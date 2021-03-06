#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import tempfile
import logging
from StringIO import StringIO
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sona.indexer import Indexer
from sona.exceptions import NoNodeError

import astroid.nodes


log = logging.getLogger(__name__)


FUNCTIONS_STR = """
def fn1(a, b, c, *args, **kwargs):
    pass

def fn2(a, b):
    def fn3():
        pass

variable = fn2(fn1())
"""
class IndexerTest(unittest.TestCase):

    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.tmpfile.write(FUNCTIONS_STR)
        self.tmpfile.flush()
        self.index = Indexer(self.tmpfile.name)

    def tearDown(self):
        self.tmpfile = None

    def test_function_visitor(self):
        fns = set([fns.name for fns in self.index.find(astroid.nodes.Function)])
        self.assertEqual(fns, set(['fn1', 'fn2', 'fn3']))

    def test_find_function_by_name(self):
        node = self.index.find_function_by_name('fn2').pop()
        self.assertIsInstance(node, astroid.nodes.Function)
        self.assertEqual(node.name, 'fn2')

    def test_find_function_error(self):
        with self.assertRaises(NoNodeError):
            node = self.index.find_function_by_name('fn4')

    def test_find_function_by_argcount(self):
        nodes = self.index.find_function_by_argcount(2)
        self.assert_(len(nodes) == 1)
        node = nodes.pop()
        self.assertIsInstance(node, astroid.nodes.Function)
        self.assertEqual(node.name, 'fn2')
        nodes = self.index.find_function_by_argcount(5)
        self.assert_(len(nodes) == 1)
        node = nodes.pop()
        self.assertIsInstance(node, astroid.nodes.Function)
        self.assertEqual(node.name, 'fn1')

    def test_find_function_by_call(self):
        nodes = self.index.find_function_by_call('fn2')
        self.assert_(len(nodes) == 1)
        node = nodes.pop()
        self.assertEqual(node.func.name, 'fn2')


def mk_indexer(string):
    tmpfile = tempfile.NamedTemporaryFile()
    tmpfile.write(string)
    tmpfile.flush()
    return Indexer(tmpfile.name)

class ClassIndexerTest(unittest.TestCase):

    def test_class_find_parent(self):
        indexer = mk_indexer(r"""
class FooBase(object): pass
class FooActual(FooBase): pass
class FooMultipleParents(FooBase, list): pass

class OldClass: pass
""")

        nodes = indexer.find_class_by_parent('object')
        self.assert_(len(nodes), 1)
        # Error
        with self.assertRaises(NoNodeError):
            nodes = indexer.find_class_by_parent('wrongbase')
            self.assert_(len(nodes), 0)

        nodes = indexer.find_class_by_parent('FooBase')
        self.assert_(len(nodes), 2)

    def test_find_class_method(self):
        indexer = mk_indexer(r"""
class Foo(object):
    def method1(self): pass

class Bar(Foo):
    def method2(self): pass
""")

        # None finds all
        nodes = indexer.find_class_method('Foo')
        self.assert_(len(nodes), 1)
        # Error
        with self.assertRaises(NoNodeError):
            nodes = indexer.find_class_method('wrongname')
            self.assert_(len(nodes), 0)


    def test_find_variable_name(self):
        indexer = mk_indexer(r"""
a = 42
b = 0
def foo(a, b):
   b = a + a
   for a in [1,2,3]: pass
   print b

""")

        # None finds all
        nodes = indexer.find_variable_by_name('a')
        # assignment and for loop.
        self.assert_(len(nodes), 2)
        # Error
        with self.assertRaises(NoNodeError):
            nodes = indexer.find_variable_by_name('c')
            self.assert_(len(nodes), 0)
        nodes = indexer.find_variable_by_name('b')
        self.assert_(len(nodes), 2)
        
