#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import logging
import argparse
import astroid
from pysemantic.search import SemanticSearcher

log = logging.getLogger(__name__)

def create_argparser():
    parser = argparse.ArgumentParser(description='PySemantic Query System',
                                     prog='pysemantic')
    parser.add_argument('search', nargs='+', help='search for something', metavar=('search'))
    parser.add_argument('--no-git', action='store_true', help='do not use git to find files')
    parser.add_argument('-f', '--file')
    parser.add_argument('-o', '--output-format', choices=['emacs', 'json', 'grep'], default='grep',
                        help="output format for the results")
    return parser


def make_search_query(query):
    ss = SemanticSearcher()
    ss.search(query)
def main():
    parser = create_argparser()
    args = parser.parse_args()
    args.search
if __name__ == "__main__":
    main()
