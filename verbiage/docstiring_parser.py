#!/usr/bin/env python
"""Testing docstring processing"""
from pprint import pprint
from re import match
from copy import deepcopy

from sphinx.util.docstrings import prepare_docstring
from sphinxcontrib.napoleon.docstring import GoogleDocstring
from sphinxcontrib.napoleon.docstring import NumpyDocstring
from sphinxcontrib.napoleon import Config
from sphinxcontrib.napoleon.iterators import peek_iter


def a_rst_func(posarg1, posarg2, kwarg1=7, kwarg2='blah'):
    """Function for testing docstring parsing

    :param str posarg1: 1st positional argument
    :param int posarg2: 2nd positional argument with a long
                        multiline idented description
    :param int kwarg1: 1st keyword argument
    :param str kwarg2: 2sd keyword argument with a mutilined description

                       With a blank line
    :returns: Success or failure
    :rtype: bool
    """
    print "posarg1: {}\nposarg2: {}\nkwarg1: {}\nkwarg2: {}\n".format(
        posarg1, posarg2, kwarg1, kwarg2
    )
    return True


def a_google_func(posarg1, posarg2, kwarg1=7, kwarg2='blah'):
    """Function for testing google docstring parsing

    Just to test translation from Google style docstrings.

    Args:
        posarg1 (str): 1st positional argument
        posarg2 (int): 2nd positional argument with a long
                       multiline idented description
        kwarg1 (int): 1st keyword argument
        kwarg2 (str): 2sd keyword argument with a mutilined description

                      With a blank line

    Returns:
        bool: Success or failure
    """
    print "posarg1: {}\nposarg2: {}\nkwarg1: {}\nkwarg2: {}\n".format(
        posarg1, posarg2, kwarg1, kwarg2
    )
    return True


def a_numpy_func(posarg1, posarg2, kwarg1=7, kwarg2='blah'):
    """Function for testing numpy docstring parsing

    Just to test translation from NumPy style docstrings.

    Parameters
    ----------
    posarg1 : str
        1st positional argument
    posarg2 : int
        2nd positional argument with a long
        multiline idented description
    kwarg1 : int
        1st keyword argument
    kwarg2 : str
        2sd keyword argument with a miltilined description

        With a blank line

    Returns
    -------
    bool
        Success or failure
    """
    print "posarg1: {}\nposarg2: {}\nkwarg1: {}\nkwarg2: {}\n".format(
        posarg1, posarg2, kwarg1, kwarg2
    )
    return True


def parse_docstring(func):
    """Parse structured function metadata out of a function's docstring

    Args:
        func (function): The function for which to parse the docstring
    """
    return DocStringParser(func).as_hash()


class DocStringParser(object):
    def __init__(self, func):
        self._rst_lines = self._docstr2rst(func)
        self._rst_iter = peek_iter(self._rst_lines)
        self._text = []
        self._params = {}
        self._retuned = {
            'description': '',
            'type': None,
        }
        self._parse()

    def as_hash(self):
        return deepcopy(self._as_hash())

    def _as_hash(self):
        return {
            'parameters': self._params,
            'returned_value': self._retuned,
            'documentation_text': self._text,
        }

    def _docstr2rst(self, func):
        docstring = func.__doc__
        rst_lines = prepare_docstring(docstring)
        rst_lines = GoogleDocstring(
            docstring=rst_lines,
            what='function',
            config=Config(napoleon_use_param=True, napoleon_use_rtype=True)
        ).lines()
        rst_lines = NumpyDocstring(
            docstring=rst_lines,
            what='function',
            config=Config(napoleon_use_param=True, napoleon_use_rtype=True)
        ).lines()
        return rst_lines

    def _parse(self):
        while self._rst_iter.has_next():
            self._take_empty()
            self._take_content()

    def _take_empty(self):
        lines = []
        line = self._rst_iter.peek()
        while self._rst_iter.has_next() and not line:
            lines.append(line)
            self._rst_iter.next()
            line = self._rst_iter.peek()
        return lines

    def _take_content(self):
        if not self._rst_iter.has_next():
            return
        if not self._rst_iter.peek():
            return
        if self._is_param():
            self._take_param()
        elif self._is_type():
            self._take_type()
        elif self._is_returns():
            self._take_returns()
        elif self._is_rtype():
            self._take_rtype()
        else:
            self._take_text()

    def _is_param(self):
        return self._match(':param\s+(?:(\w+)\s+)?(\w+):\s*(.*)')

    def _is_type(self):
        return self._match(':type\s+(\w+):\s*(\w+)')

    def _is_returns(self):
        return self._match(':returns:\s*(.*)')

    def _is_rtype(self):
        return self._match(':rtype:\s*(\w+)')

    def _take_param(self):
        matcher = self._is_param()
        if not matcher:
            return
        self._rst_iter.next()
        ptype, name, description = matcher.groups()
        description = '\n'.join(
            [description] + self._take_indented_text()
        )
        param = self._get_param(name)
        param['description'] = description
        if ptype:
            param['type'] = ptype

    def _take_type(self):
        matcher = self._is_type()
        if not matcher:
            return
        self._rst_iter.next()
        name, ptype = matcher.groups()
        param = self._get_param(name)
        param['type'] = ptype

    def _take_returns(self):
        matcher = self._is_returns()
        if not matcher:
            return
        self._rst_iter.next()
        return_desc = matcher.group(1)
        return_desc = '\n'.join(
            [return_desc] + self._take_indented_text()
        )
        self._retuned['description'] = return_desc

    def _take_rtype(self):
        matcher = self._is_rtype()
        if not matcher:
            return
        self._rst_iter.next()
        rtype = matcher.group(1)
        self._retuned['type'] = rtype
        pass

    def _take_text(self):
        lines = []
        while (
            self._rst_iter.has_next()
            and self._rst_iter.peek()
            and not self._is_param()
            and not self._is_type()
            and not self._is_returns()
            and not self._is_rtype()
        ):
            lines.append(self._rst_iter.next())
        self._text.append('\n'.join(lines))

    def _take_indented_text(self):
        lines = []
        last_empty = self._take_empty()
        matcher = self._match('\s+')
        if not matcher:
            return lines
        indent = matcher.group(0)
        while(self._rst_iter.has_next() and self._startswith(indent)):
            lines.extend(last_empty)
            lines.append(self._rst_iter.next()[len(indent):])
            last_empty = self._take_empty()
        return lines

    def _get_param(self, name):
        param = self._params.setdefault(name, {
            'description': '',
            'type': None,
        })
        return param

    def _startswith(self, prefix):
        if not self._rst_iter.has_next():
            return None
        return self._rst_iter.peek().startswith(prefix)

    def _match(self, pattern):
        if not self._rst_iter.has_next():
            return None
        return match(pattern, self._rst_iter.peek())


if __name__ == '__main__':
    FUNCTIONS = [a_rst_func, a_google_func, a_numpy_func]
    for afunc in FUNCTIONS:
        pprint(parse_docstring(afunc))
