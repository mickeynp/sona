#!/usr/bin/env python
#  -*- coding: utf-8 -*- 

class SonaError(Exception):
    pass

class BaseSemanticError(SonaError):
    pass

class NoNodeError(BaseSemanticError):
    def __init__(self, class_types, attr, query):
        msg = 'Cannot find a node {0!r} with attr {1!r} matching query {2!r}'\
            .format(class_types, attr, query)
        self.class_types = class_types
        self.query = query
        super(NoNodeError, self).__init__(self, msg)

class SemanticSearcherError(SonaError):
    pass

class NoSemanticIndexerError(SemanticSearcherError):
    pass

class InvalidAssertionError(SemanticSearcherError):
    pass

class FormatterError(SonaError):
    pass

