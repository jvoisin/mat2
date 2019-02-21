from html import parser
from typing import Dict, Any, List, Tuple
import re
import string

from . import abstract


class CSSParser(abstract.AbstractParser):
    """There is no such things as metadata in CSS files,
    only comments of the form `/* … */`, so we're removing the laters."""
    mimetypes = {'text/css', }
    flags = re.MULTILINE | re.DOTALL

    def remove_all(self) -> bool:
        with open(self.filename, encoding='utf-8') as f:
            cleaned = re.sub(r'/\*.+?\*/', '', f.read(), 0, self.flags)
        with open(self.output_filename, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        return True

    def get_meta(self) -> Dict[str, Any]:
        metadata = {}
        with open(self.filename, encoding='utf-8') as f:
            cssdoc = re.findall(r'/\*(.+?)\*/', f.read(), self.flags)
        for match in cssdoc:
            for line in match.splitlines():
                try:
                    k, v = line.split(':')
                    metadata[k.strip(string.whitespace + '*')] = v.strip()
                except ValueError:
                    metadata['harmful data'] = line.strip()
        return metadata


class HTMLParser(abstract.AbstractParser):
    mimetypes = {'text/html', 'application/x-dtbncx+xml', }
    def __init__(self, filename):
        super().__init__(filename)
        self.__parser = _HTMLParser(self.filename)
        with open(filename, encoding='utf-8') as f:
            self.__parser.feed(f.read())
        self.__parser.close()

    def get_meta(self) -> Dict[str, Any]:
        return self.__parser.get_meta()

    def remove_all(self) -> bool:
        return self.__parser.remove_all(self.output_filename)


class _HTMLParser(parser.HTMLParser):
    """Python doesn't have a validating html parser in its stdlib, so
    we're using an internal queue to track all the opening/closing tags,
    and hoping for the best.
    """
    tag_blacklist = {'doctitle', 'meta'}  # everything is lowercase
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.__textrepr = ''
        self.__meta = {}
        self.__validation_queue = []
        # We're using a counter instead of a boolean to handle nested tags
        self.__in_dangerous_tag = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        self.__validation_queue.append(tag)
        if tag in self.tag_blacklist:
            self.__in_dangerous_tag += 1
            return

        if self.__in_dangerous_tag == 0:
            self.__textrepr += self.get_starttag_text()

    def handle_endtag(self, tag: str):
        if not self.__validation_queue:
            raise ValueError("The closing tag %s doesn't have a corresponding "
                             "opening one in %s." % (tag, self.filename))

        previous_tag = self.__validation_queue.pop()
        if tag != previous_tag:
            raise ValueError("The closing tag %s doesn't match the previous "
                             "tag %s in %s" %
                             (tag, previous_tag, self.filename))
        elif tag in self.tag_blacklist:
            self.__in_dangerous_tag -= 1
            return

        if self.__in_dangerous_tag == 0:
            # There is no `get_endtag_text()` method :/
            self.__textrepr += '</' + tag + '>\n'

    def handle_data(self, data: str):
        if self.__in_dangerous_tag == 0 and data.strip():
            self.__textrepr += data

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, str]]):
        if tag in self.tag_blacklist:
            meta = {k:v for k, v in attrs}
            name = meta.get('name', 'harmful metadata')
            content = meta.get('content', 'harmful data')
            self.__meta[name] = content
        else:
            if self.__in_dangerous_tag == 0:
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
