#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import os
import subprocess
import logging
import argparse
import astroid
import fnmatch
from sona.search import SemanticSearcher, GrepOutputFormatter, JSONOutputFormatter
from pyparsing import ParseException

log = logging.getLogger('sona')

def create_argparser():
    parser = argparse.ArgumentParser(prog=r"""
 ____
/ ___|  ___  _ __   __ _
\___ \ / _ \| '_ \ / _` |
 ___) | (_) | | | | (_| |
|____/ \___/|_| |_|\__,_|

    Query System
""")
    parser.add_argument('search', nargs='+', help='search for something (default)', metavar='search')
    parser.add_argument('--no-git', action='store_true', help='do not use git to find files [default: %(default)s]')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error', 'critical', 'none'],
                        help='show only logs from this level and above', default='error')
    parser.add_argument('-o', '--output-format', choices=['emacs', 'json', 'grep'], default='grep',
                        help="output format for the results")
    return parser


FORMATTER_MAP = {
    'grep': GrepOutputFormatter,
    'emacs': None,
    'json': JSONOutputFormatter,
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

class Sona(object):
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
            log.debug('Stderr Output from Git: %s', err_output)
            if 'Not a git repository'.upper() in err_output.upper():
                raise NotGitRepoError('This directory does not have a git repository')
            else:
                log.info('It would appear we are in a git directory')

            # Strip the newline from the shell output. If we are AT
            # the git root directory we just get a blank string;
            # replace that with a '.' to signify this directory.
            return output.strip() or '.'
        log.debug('Reading files from git repository...')
        old_cwd = os.curdir
        try:
            root_dir = get_git_root()

            log.debug('Calling Git ls files command: "%s"', ','.join(GIT_LS_FILES_COMMAND))
            proc = subprocess.Popen(GIT_LS_FILES_COMMAND, stdout=subprocess.PIPE)
            output = proc.communicate()[0]

            os.chdir(root_dir)
            files = output.split('\0')
            log.debug('\tFound %d files', len(files))
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
                log.error('Not in a git repository. Specify file pattern instead.')
                return
        results = ss.search(query)
        self.formatter.print_all_results(results)

    def go(self):
        """Figures out from the given CLI args what it needs to
        do."""
        logging.basicConfig(level=LOG_LEVELS[self.args.log_level],
                            format='%(levelname)s - %(message)s')
        log.debug('Starting up')
        if self.args.search:
            if self.args.search[0] == 'search':
                query = self.args.search[1:]
            else:
                query = self.args.search
            try:
                self.make_search_query(' '.join(query))
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
    pyse = Sona(args)
    pyse.go()

if __name__ == "__main__":
    main()