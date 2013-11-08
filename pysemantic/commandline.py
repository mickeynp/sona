#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import os
import logging
import argparse
import astroid
import fnmatch
from pysemantic.search import SemanticSearcher, GrepOutputFormatter

log = logging.getLogger(__name__)
logging.basicConfig()
log.setLevel(logging.DEBUG)
def create_argparser():
    parser = argparse.ArgumentParser(description='PySemantic Query System',
                                     prog='pysemantic')
    parser.add_argument('search', nargs='+', help='search for something', metavar=('search'))
    parser.add_argument('--no-git', action='store_true', help='do not use git to find files')
    parser.add_argument('-f', '--file')
    parser.add_argument('-o', '--output-format', choices=['emacs', 'json', 'grep'], default='grep',
                        help="output format for the results")
    return parser


FORMATTER_MAP = {
    'grep': GrepOutputFormatter,
    'emacs': None,
    'json': None,
    }
class PySemantic(object):
    """User-Interface Class for the commandline

    This class interfaces with the user through the commandline and
    with the backend that does the searching, parsing and indexing."""

    def make_search_query(self, query):
        ss = SemanticSearcher()
        for fn in fnmatch.filter(os.listdir('.'), '*.py'):
            ss.add_file(fn)
        results = ss.search(query)
        self.formatter.print_all_results(results)

    def go(self):
        """Figures out from the given CLI args what it needs to
        do."""
        if self.args.search:
            _, query = self.args.search
            self.make_search_query(query)

    def __init__(self, args):
        self.args = args
        self.formatter = FORMATTER_MAP[args.output_format]()

def main():
    log.debug('Starting up')
    parser = create_argparser()
    args = parser.parse_args()
    pyse = PySemantic(args)
    pyse.go()

if __name__ == "__main__":
    main()
