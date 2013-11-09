#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import tempfile
from StringIO import StringIO
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sona.search import SemanticSearcher, OutputFormatterBase, GrepOutputFormatter, return_sane_filepath
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

FUNCTIONS_WITH_ARGS_STR = """
def fn2(arg1, arg2):
    def fn3(*myargs, **mykwargs):
        pass

def fn1(a='hello'):
    pass

"""

class SearchTest(unittest.TestCase):

    def setUp(self):
        self.searcher = SemanticSearcher()
        self.tmpfile_simple = tempfile.NamedTemporaryFile()
        self.tmpfile_simple.write(FUNCTIONS_STR)
        self.tmpfile_simple.flush()
        self.tmpfile_args = tempfile.NamedTemporaryFile()
        self.tmpfile_args.write(FUNCTIONS_WITH_ARGS_STR)
        self.tmpfile_args.flush()

    def tearDown(self):
        self.tmpfile_simple = None
        self.tmpfile_args = None

    def test_find_function_by_name_simple(self):
        self.searcher.add_file(self.tmpfile_simple.name)
        self.assertEqual(self.searcher.files, [self.tmpfile_simple.name])
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
        self.searcher.add_file(self.tmpfile_simple.name)
        self.assertEqual(self.searcher.files, [self.tmpfile_simple.name])

        nodes = set(self.searcher.search('fn:name == "fn1", fn:name == "fn2"'))
        self.assert_(len(nodes) == 0)

    def test_find_function_by_name_invalid(self):
        self.searcher.add_file(self.tmpfile_simple.name)
        self.assertEqual(self.searcher.files, [self.tmpfile_simple.name])

        nodes = set(self.searcher.search('fn:name == "fn1", fn:name != "fn1"'))
        self.assert_(len(nodes) == 0)

    def test_multiple_expressions(self):
        self.searcher.add_file(self.tmpfile_simple.name)
        self.assertEqual(self.searcher.files, [self.tmpfile_simple.name])
        nodes = set(self.searcher.search('fn:name == "fn1"; fn:name == "fn2"'))
        self.assert_(len(nodes) == 2)
        self.assertEqual(set([node.name for node in nodes]), set(['fn1', 'fn2']))

    def test_membership_string(self):
        self.searcher.add_file(self.tmpfile_args.name)
        self.assertEqual(self.searcher.files, [self.tmpfile_args.name])
        nodes = set(self.searcher.search('fn:name in {"fn1", "fn2"}'))
        self.assert_(len(nodes) == 2)
        self.assertEqual(set([node.name for node in nodes]), set(['fn1', 'fn2']))

        nodes = set(self.searcher.search('fn:name not in {"fn3"}'))
        self.assert_(len(nodes) == 2)
        self.assertEqual(set([node.name for node in nodes]), set(['fn1', 'fn2']))

    def test_membership_number(self):
        self.searcher.add_file(self.tmpfile_args.name)
        self.assertEqual(self.searcher.files, [self.tmpfile_args.name])
        nodes = set(self.searcher.search('fn:argcount in {1, 2, 3}'))
        self.assert_(len(nodes) == 3)
        self.assertEqual(set([node.name for node in nodes]), set(['fn1', 'fn2', 'fn3']))

        nodes = set(self.searcher.search('fn:argcount in {2}'))
        self.assert_(len(nodes) == 2)
        self.assertEqual(set([node.name for node in nodes]), set(['fn2', 'fn3']))

        nodes = set(self.searcher.search('fn:argcount not in {2}'))
        self.assert_(len(nodes) == 1)
        self.assertEqual(set([node.name for node in nodes]), set(['fn1']))

    def test_simple_assertion(self):
        self.searcher.add_file(self.tmpfile_simple.name)
        self.assertEqual(self.searcher.files, [self.tmpfile_simple.name])
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


class TestOutputFormatter(unittest.TestCase):

    def setUp(self):
        self.searcher = SemanticSearcher()

        class OutputFormatterTest(OutputFormatterBase):

            _test_results = set()
            def print_single_result(self, result, formatted_result):
                 self._test_results.add(formatted_result)

            def post_output(self):
                pass

        self.output = OutputFormatterTest()
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.tmpfile.write(FUNCTIONS_WITH_ARGS_STR)
        self.tmpfile.flush()

    def tearDown(self):
        self.tmpfile = None

    def test_print_all_results(self):
        self.searcher.add_file(self.tmpfile.name)
        results = self.searcher.search('fn:name')
        expected = set([
                "def fn1(a='hello')",
                'def fn2(arg1, arg2)',
                'def fn3(*myargs, **mykwargs)',
                ]
            )
        self.output.print_all_results(results)
        self.assertSetEqual(self.output._test_results, expected)

class TestGrepOutputFormatter(unittest.TestCase):

    def setUp(self):
        self.searcher = SemanticSearcher()

        class OutputFormatterTest(GrepOutputFormatter):

            _test_results = set()

            def output(self, s):
                self._test_results.add(s)

            def post_output(self):
                pass

        self.output = OutputFormatterTest()
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.tmpfile.write(FUNCTIONS_WITH_ARGS_STR)
        self.tmpfile.flush()

    def tearDown(self):
        self.tmpfile = None

    def test_print_all_results(self):
        self.searcher.add_file(self.tmpfile.name)
        results = self.searcher.search('fn:name')
        expected = set([
                "%s:6:def fn1(a='hello')" % return_sane_filepath(self.tmpfile.name),
                '%s:2:def fn2(arg1, arg2)' % return_sane_filepath(self.tmpfile.name),
                '%s:3:def fn3(*myargs, **mykwargs)' % return_sane_filepath(self.tmpfile.name),
                ]
            )
        self.output.print_all_results(results)
        self.assertSetEqual(self.output._test_results, expected)

