#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import os
import subprocess
import logging
import argparse
import astroid
import fnmatch
from pysemantic.search import SemanticSearcher, GrepOutputFormatter
from pyparsing import ParseException

log = logging.getLogger('pysemantic')

def create_argparser():
    parser = argparse.ArgumentParser(description='PySemantic Query System',
                                     prog='pysemantic')
    parser.add_argument('search', nargs='+', help='search for something', metavar=('search'))
    parser.add_argument('--no-git', action='store_true', help='do not use git to find files [default: %(default)s]')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error', 'critical', 'none'],
                        help='show only logs from this level and above', default='error')
    parser.add_argument('-f', '--file')
    parser.add_argument('-o', '--output-format', choices=['emacs', 'json', 'grep'], default='grep',
                        help="output format for the results")
    return parser


FORMATTER_MAP = {
    'grep': GrepOutputFormatter,
    'emacs': None,
    'json': None,
    }

LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARN,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
    'none': logging.NOTSET,
    }

# Command to call git with. NOTE: Output must be null-terminated!
GIT_LS_FILES_COMMAND = ('git', 'ls-tree', '-r', '-z', '--full-tree', '--name-only', 'HEAD')

# Command to get the git root directory.
GIT_GET_ROOT = ('git', 'rev-parse', '--show-cdup')

class NotGitRepoError(Exception):
    pass

class PySemantic(object):
    """User-Interface Class for the commandline

    This class interfaces with the user through the commandline and
    with the backend that does the searching, parsing and indexing."""

    @staticmethod
    def iter_git_files(pattern='*.py'):
        """Yields every file matching pattern managed by Git.

        This raises an exception if it is invoked from outside a
        git-controlled directory. """
        def get_git_root():
            proc = subprocess.Popen(GIT_GET_ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            comms = proc.communicate()
            output = comms[0]
            # Hackish way of determining if we are in a git-controlled
            # (sub-)directory.
            # TODO: better way?
            err_output = comms[1]
            if 'Not a git repository'.upper() in err_output.upper():
                raise NotGitRepoError('This directory does not have a git repository')

            # Strip the newline from the shell output. If we are AT
            # the git root directory we just get a blank string;
            # replace that with a '.' to signify this directory.
            return output.strip() or '.'
        log.debug('Reading files from git repository...')
        old_cwd = os.curdir
        try:
            root_dir = get_git_root()

            proc = subprocess.Popen(GIT_LS_FILES_COMMAND, stdout=subprocess.PIPE)
            output = proc.communicate()[0]

            os.chdir(root_dir)
            files = output.split('\0')
            for filename in files:
                absfn = os.path.abspath(filename)
                if fnmatch.fnmatch(absfn, pattern):
                    yield filename
        finally:
            os.chdir(old_cwd)

    def make_search_query(self, query):
        ss = SemanticSearcher()
        # for fn in fnmatch.filter(os.listdir('.'), '*.py'):
        #     ss.add_file(fn)
        if not self.args.no_git:
            try:
                ss.add_files(self.iter_git_files())
            except NotGitRepoError:
                # Just do nothing. We need a fall through - such as
                # using the current directory?
                log.error('Not in a git repo. Specify file pattern instead.')
        results = ss.search(query)
        self.formatter.print_all_results(results)

    def go(self):
        """Figures out from the given CLI args what it needs to
        do."""
        logging.basicConfig(level=LOG_LEVELS[self.args.log_level],
                            format='%(levelname)s - %(message)s')
        log.debug('Starting up')
        if self.args.search:
            _, query = self.args.search
            try:
                self.make_search_query(query)
            except ParseException, err:
                log.critical('Parsing failed because...')
                log.critical(err.line)
                log.critical(" "*(err.column-1) + "^")
                log.critical(str(err))

    def __init__(self, args):
        self.args = args
        self.formatter = FORMATTER_MAP[args.output_format]()

def main():
    parser = create_argparser()
    args = parser.parse_args()
    pyse = PySemantic(args)
    pyse.go()

if __name__ == "__main__":
    main()
