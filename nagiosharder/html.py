# coding=utf8
"""
Convinience layer between `Parsable` object and parsing library
"""

import lxml.html
from lxml import etree


class Html(object):
    """Wrapper around raw html string"""
    def __init__(self, html_str):
        if isinstance(html_str, Html):
            self.html_str = etree.tostring(html_str.html)
            self.html = html_str.html
        else:
            self.html_str = html_str
            self.html = lxml.html.document_fromstring(html_str)

    def split_by(self, delim):
        return [ Html(html) for html in self.html_str.split(delim) ]

    def __getattr__(self, attr):
        return getattr(self.html, attr)

