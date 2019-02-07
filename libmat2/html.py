from html import parser
from typing import Dict, Any, List, Tuple

from . import abstract


class HTMLParser(abstract.AbstractParser):
    mimetypes = {'text/html', }
    def __init__(self, filename):
        super().__init__(filename)
        self.__parser = _HTMLParser()
        with open(filename) as f:
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
    def __init__(self):
        super().__init__()
        self.__textrepr = ''
        self.__meta = {}
        self.__validation_queue = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        self.__textrepr += self.get_starttag_text()
        self.__validation_queue.append(tag)

    def handle_endtag(self, tag: str):
        if not self.__validation_queue:
            raise ValueError
        elif tag != self.__validation_queue.pop():
            raise ValueError
        # There is no `get_endtag_text()` method :/
        self.__textrepr += '</' + tag + '>\n'

    def handle_data(self, data: str):
        if data.strip():
            self.__textrepr += data

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, str]]):
        if tag == 'meta':
            meta = {k:v for k, v in attrs}
            name = meta.get('name', 'harmful metadata')
            content = meta.get('content', 'harmful data')
            self.__meta[name] = content
        else:
            self.__textrepr += self.get_starttag_text()

    def remove_all(self, output_filename: str) -> bool:
        if self.__validation_queue:
            raise ValueError
        with open(output_filename, 'w') as f:
            f.write(self.__textrepr)
        return True

    def get_meta(self) -> Dict[str, Any]:
        if self.__validation_queue:
            raise ValueError
        return self.__meta
