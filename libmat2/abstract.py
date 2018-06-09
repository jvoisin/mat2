import abc
import os
from typing import Set, Dict

assert Set  # make pyflakes happy


class AbstractParser(abc.ABC):
    meta_list = set()  # type: Set[str]
    mimetypes = set()  # type: Set[str]

    def __init__(self, filename: str) -> None:
        self.filename = filename
        fname, extension = os.path.splitext(filename)
        self.output_filename = fname + '.cleaned' + extension

    @abc.abstractmethod
    def get_meta(self) -> Dict[str, str]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def remove_all(self) -> bool:
        pass  # pragma: no cover

    def remove_all_lightweight(self) -> bool:
        """ Remove _SOME_ metadata. """
        return self.remove_all()
