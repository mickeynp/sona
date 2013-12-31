#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import os
import json

from sona.parser import AssertionParser
from sona.indexer import Indexer
from sona.exceptions import NoNodeError

from astroid import builder, InferenceError, NotFoundError
from astroid.nodes import Module, Function, Lambda, Class
from astroid.bases import NodeNG

log = logging.getLogger(__name__)

INDEXER_MAPS = {
    # <Node type>, <Equiv Attr on Node Class>
    ('fn', 'name'): Indexer.find_function_by_name,
    ('fn', 'argcount'): Indexer.find_function_by_argcount,
    ('fn', 'parent'): Indexer.find_parent_by_name,
    ('fn', 'call'): Indexer.find_function_by_call,
    ('cls', 'name'): Indexer.find_class_by_name,
    }

# TODO: This should be in parser.py?
COMPARATOR_MAP = {
    '==': lambda a,b: a == b,
    '!=': lambda a,b: a != b,
    'in': lambda a,b: a in b,
    'not in': lambda a,b: a not in b,
    }

class SemanticSearcher(object):
    """Semantic Searcher class. Returns a list of matching nodes given
    a string query.


    aggressive_search - if True, an assertion that returns NoNodeError
    will not halt the evaluation of that expression. If False, any
    assertion that returns NoNodeError is instead halted, its results
    up until then kept, and the next expression is evaluated."""
    aggressive_search = False


    def add_file(self, filepath):
        self.files.append(filepath)

    def add_files(self, iterable):
        self.files.extend(iterable)

    def __init__(self):
        self.files = []
        self.results = []
        self.aggressive_search = False

    @staticmethod
    def _find_query_in_module(tree, query, indexer,
                              aggressive_search=False):
        matches = set()
        global_matches = set()
        # Iterate over the tree. A tree is made up of many nested
        # lists with the following pattern:
        #
        # [[[assertion], ...],
        #  [[assertion, ...], ...], ...]
        for expression in tree:
            log.debug('Parsing expression %r', expression)
            nodes = None
            # Each expression, in turn, has N number of assertions,
            # which in turn is made up of at least a field node type
            # and a field attribute. Optionally, a conditional and a
            # value may also be there.
            for assertion in expression:
                log.debug('\tParsing assertion %r', assertion)
                if not len(assertion) in [2, 4]:
                    raise InvalidAssertionError(\
                        'Assertion {0!r} contained {1} items instead of\
 the expected 2 or 4'.format(assertion, len(assertion)))
                try:
                    if len(assertion) == 2:
                        node_type, node_attr = assertion
                        # Blank these out if assertion only has two
                        # elements. That means it's of the form
                        # "type:attr" which is shorthand for "match
                        # everything".
                        conditional = None
                        comp_value = None
                    else:
                        node_type, node_attr, conditional, comp_value = assertion
                    # We need to do this here - annoyingly - because
                    # the behaviour of the default ParseResults object
                    # is not consistent with standard Python
                    # containers.
                    if comp_value is not None:
                        # Just try and call asList() - if that fails,
                        # fall through and do nothing.
                        try:
                            comp_value = comp_value.asList()
                        except AttributeError:
                            pass

                    try:
                        comparator = COMPARATOR_MAP[conditional]
                    except KeyError:
                        comparator = None

                    indexer_fn = INDEXER_MAPS[(node_type, node_attr)]
                    try:
                        # This actually returns a list of nodes that
                        # matches the query.
                        nodes = indexer_fn(indexer, comp_value,
                                           comparator=comparator, node_list=nodes)
                        log.debug('\t\tFound %d new submatches (%d total)',
                                  len(nodes), len(matches))
                        # Override the old list with the new one. We
                        # don't want stale, and now invalid (as they
                        # failed the indexer check above), to remain.
                        # TODO: or do we? Add switch to support this.
                        matches = set(nodes)
                    except NoNodeError:
                        # It's perfectly OK if NoNodeError is raised
                        # -- all that means is one leg of the query
                        # failed to match.
                        nodes = None
                        matches = set()

                        log.debug('\t\tFound 0 matching nodes')
                        # Break if aggressive_search is not True.
                        if not aggressive_search:
                            break
                    for node in nodes:
                        matches.add(node)
                except KeyError:
                    raise NoSemanticIndexerError('{0!r} does not have a valid\
 locator assigned to it.'.format(assertion))
                except NoNodeError:
                    raise
            # Once we're done with one expression we need to shunt all
            # the nodes in the matches set into the set
            # global_matches. The filtering applied by assertions do
            # not cross "expressions".
            global_matches.update(matches)
            matches = set()
        return global_matches

    @staticmethod
    def _do_search(filename, query):
        """Actual method that does the search.

        This method is designed to operate on a single file ONLY for
        the purposes of enabling paralleism with multiprocessing."""
        tree = AssertionParser(query).tree
        log.info('Commencing with parsing of file %s', filename)
        try:
            indexer = Indexer(filename)
            all_nodes = SemanticSearcher._find_query_in_module(tree,
                                                               query,
                                                               indexer)
            for node in all_nodes:
                yield node
        except SyntaxError:
            log.critical('Syntax Error in %s. Skipping...', filename)


    def search(self, query):
        for filename in self.files:
            # There may be many nodes returned from each job, so we
            # need to iterate over them and, sigh, yield them again...
            # Also, this is as good a time as any to sort the items by
            # line number.
            results = SemanticSearcher._do_search(filename, query)
            for node in sorted(results, key=lambda n: n.lineno):
                yield node

    # def search(self, query):
    #     jobs = [gevent.spawn(SemanticSearcher._do_search, filename, query)
    #             for filename in self.files]
    #     gevent.joinall(jobs)
    #     for job in jobs:
    #         # There may be many nodes returned from each job, so we
    #         # need to iterate over them and, sigh, yield them again...
    #         # Also, this is as good a time as any to sort the items by
    #         # line number.
    #         for node in sorted(job.value, key=lambda n: n.lineno):
    #             yield node




class OutputFormatterBase(object):
    """Base Class for formatting a SemanticSearcher's results for
    display on the screen.

    This class contains formatters for each supported node class,
    along with helper methods to iterate over, and display, each node
    result."""


    def __init__(self, results=None, **settings):
        """Creates an Output Formatter class.

        The optional argument, results, is a list of result sets the
        formatter should do its work on.

        The **settings argument is a kv-pair of optional settings you
        wish to store against the formatter object."""
        self.results = results
        self.settings = settings

    def output(self, text):
        """Outputs text to a device or object.

        By default it is stdout (via print)"""
        print text

    def post_output(self):
        """Called post facto after a print_all_results run has
        completed."""
        raise NotImplementedError

    def print_single_result(self, result, formatted_result):
        """Abstract method. Called for every result by
        print_all_results with the original result object and
        formatted_result, a string-formatted version of the result."""
        raise NotImplementedError

    def print_all_results(self, results=None):
        """Enumerates each result in results and calls
        print_single_result for each one of them, passing in the
        original result along with a string-formatted version of the
        result."""
        results = results or self.results
        for result in results:
            self.print_single_result(result, self.format_single_result(result))
        self.post_output()

    def format_single_result(self, result):
        """Dispatcher method that formats result based on its node type.

        This is done by, in turn, calling another method named
        _format_<Node Class> with the result."""
        # Use dispatching to get the method name of the formatter
        try:
            name = '_format_{0}'.format(result.__class__.__name__)
            formatter = getattr(self, name)
            assert callable(formatter)
            return formatter(result)
        except AttributeError:
            raise FormatterError('Cannot format {0!r}. Method {1} does \
not exist on class {2!r}'.format(result, name, self))

    def _format_Function(self, node):
        """Formats a Function node to make it look like it would in
        Python."""
        assert isinstance(node, Function)
        fmt = 'def {0}({1})'.format(
            node.name,
            node.args.format_args() or ''
            )
        return fmt

    def _format_CallFunc(self, node):
        fmt = 'call -> {0}'.format(node.as_string())
        return fmt

    def _format_Class(self, node):
        """Formats a Class node to make it look like it would in
        Python."""
        assert isinstance(node, Class)
        fmt = 'class {0}({1})'.format(
            node.name,
            ', '.join(node.basenames),
            )
        return fmt


def return_sane_filepath(filepath, root_dir='.'):
    """Re-assembles a filepath so that it is relative to a particular
    root directory."""
    old_dir = os.curdir
    try:
        os.chdir(root_dir)
        return os.path.relpath(filepath)
    finally:
        os.chdir(old_dir)


class GrepOutputFormatter(OutputFormatterBase):

    GREP_OUTPUT_FORMAT = './{filename}:{lineno}:{result}'

    def print_single_result(self, result, formatted_result):
        output = self.GREP_OUTPUT_FORMAT.format(
            filename=return_sane_filepath(result.root().file),
            lineno=result.lineno,
            result=formatted_result)
        self.output(output)

    def post_output(self):
        pass

class JSONOutputFormatter(OutputFormatterBase):

    _store = []

    def output(self, text):
        """Outputs text in JSON format to stdout."""
        self._store.append(text)

    def print_single_result(self, result, formatted_result):
        self.output({'filename': return_sane_filepath(result.root().file),
                     'lineno': result.lineno,
                     'result': formatted_result,})

    def post_output(self):
        print json.dumps(self._store)
