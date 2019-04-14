from html import parser, escape
from typing import Dict, Any, List, Tuple, Set
import re
import string

from . import abstract

assert Set

# pylint: disable=too-many-instance-attributes

class CSSParser(abstract.AbstractParser):
    """There is no such things as metadata in CSS files,
    only comments of the form `/* … */`, so we're removing the laters."""
    mimetypes = {'text/css', }
    flags = re.MULTILINE | re.DOTALL

    def remove_all(self) -> bool:
        with open(self.filename, encoding='utf-8') as f:
            cleaned = re.sub(r'/\*.*?\*/', '', f.read(), 0, self.flags)
        with open(self.output_filename, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        return True

    def get_meta(self) -> Dict[str, Any]:
        metadata = {}
        with open(self.filename, encoding='utf-8') as f:
            cssdoc = re.findall(r'/\*(.*?)\*/', f.read(), self.flags)
        for match in cssdoc:
            for line in match.splitlines():
                try:
                    k, v = line.split(':')
                    metadata[k.strip(string.whitespace + '*')] = v.strip()
                except ValueError:
                    metadata['harmful data'] = line.strip()
        return metadata


class AbstractHTMLParser(abstract.AbstractParser):
    tags_blocklist = set()  # type: Set[str]
    # In some html/xml-based formats some tags are mandatory,
    # so we're keeping them, but are discarding their content
    tags_required_blocklist = set()  # type: Set[str]

    def __init__(self, filename):
        super().__init__(filename)
        self.__parser = _HTMLParser(self.filename, self.tags_blocklist,
                                    self.tags_required_blocklist)
        with open(filename, encoding='utf-8') as f:
            self.__parser.feed(f.read())
        self.__parser.close()

    def get_meta(self) -> Dict[str, Any]:
        return self.__parser.get_meta()

    def remove_all(self) -> bool:
        return self.__parser.remove_all(self.output_filename)


class HTMLParser(AbstractHTMLParser):
    mimetypes = {'text/html', 'application/xhtml+xml'}
    tags_blocklist = {'meta', }
    tags_required_blocklist = {'title', }


class DTBNCXParser(AbstractHTMLParser):
    mimetypes = {'application/x-dtbncx+xml', }
    tags_required_blocklist = {'title', 'doctitle', 'meta'}


class _HTMLParser(parser.HTMLParser):
    """Python doesn't have a validating html parser in its stdlib, so
    we're using an internal queue to track all the opening/closing tags,
    and hoping for the best.

    Moreover, the parser.HTMLParser call doesn't provide a get_endtag_text
    method, so we have to use get_starttag_text instead, put its result in a
    LIFO, and transform it in a closing tag when needed.

    Also, gotcha: the `tag` parameters are always in lowercase.
    """
    def __init__(self, filename, blocklisted_tags, required_blocklisted_tags):
        super().__init__()
        self.filename = filename
        self.__textrepr = ''
        self.__meta = {}
        self.__validation_queue = []  # type: List[str]

        # We're using counters instead of booleans, to handle nested tags
        self.__in_dangerous_but_required_tag = 0
        self.__in_dangerous_tag = 0

        if required_blocklisted_tags & blocklisted_tags:  # pragma: nocover
            raise ValueError("There is an overlap between %s and %s" % (
                required_blocklisted_tags, blocklisted_tags))
        self.tag_required_blocklist = required_blocklisted_tags
        self.tag_blocklist = blocklisted_tags

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        original_tag = self.get_starttag_text()
        self.__validation_queue.append(original_tag)

        if tag in self.tag_blocklist:
            self.__in_dangerous_tag += 1

        if self.__in_dangerous_tag == 0:
            if self.__in_dangerous_but_required_tag == 0:
                self.__textrepr += original_tag

        if tag in self.tag_required_blocklist:
            self.__in_dangerous_but_required_tag += 1

    def handle_endtag(self, tag: str):
        if not self.__validation_queue:
            raise ValueError("The closing tag %s doesn't have a corresponding "
                             "opening one in %s." % (tag, self.filename))

        previous_tag = self.__validation_queue.pop()
        previous_tag = previous_tag[1:-1]  # remove < and >
        previous_tag = previous_tag.split(' ')[0]  # remove attributes
        if tag != previous_tag.lower():
            raise ValueError("The closing tag %s doesn't match the previous "
                             "tag %s in %s" %
                             (tag, previous_tag, self.filename))

        if tag in self.tag_required_blocklist:
            self.__in_dangerous_but_required_tag -= 1

        if self.__in_dangerous_tag == 0:
            if self.__in_dangerous_but_required_tag == 0:
                # There is no `get_endtag_text()` method :/
                self.__textrepr += '</' + previous_tag + '>'

        if tag in self.tag_blocklist:
            self.__in_dangerous_tag -= 1

    def handle_data(self, data: str):
        if self.__in_dangerous_but_required_tag == 0:
            if self.__in_dangerous_tag == 0:
                if data.strip():
                    self.__textrepr += escape(data)

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, str]]):
        if tag in self.tag_required_blocklist | self.tag_blocklist:
            meta = {k:v for k, v in attrs}
            name = meta.get('name', 'harmful metadata')
            content = meta.get('content', 'harmful data')
            self.__meta[name] = content

            if self.__in_dangerous_tag == 0:
                if tag in self.tag_required_blocklist:
                    self.__textrepr += '<' + tag + ' />'
                return

        if self.__in_dangerous_tag == 0:
            if self.__in_dangerous_but_required_tag == 0:
                self.__textrepr += self.get_starttag_text()

    def remove_all(self, output_filename: str) -> bool:
        if self.__validation_queue:
            raise ValueError("Some tags (%s) were left unclosed in %s" % (
                ', '.join(self.__validation_queue),
                self.filename))
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(self.__textrepr)
        return True

    def get_meta(self) -> Dict[str, Any]:
        if self.__validation_queue:
            raise ValueError("Some tags (%s) were left unclosed in %s" % (
                ', '.join(self.__validation_queue),
                self.filename))
        return self.__meta
