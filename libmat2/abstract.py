import abc
import os
from typing import Set, Dict

assert Set  # make pyflakes happy


class AbstractParser(abc.ABC):
    """ This is the base class of every parser.
    It might yield `ValueError` on instantiation on invalid files.
    """
    meta_list = set()  # type: Set[str]
    mimetypes = set()  # type: Set[str]

    def __init__(self, filename: str) -> None:
        """
        :raises ValueError: Raised upon an invalid file
        """
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
        """ This method removes _SOME_ metadata.
        It might be useful to implement it for fileformats that do
        not support non-destructive cleaning.
        """
        return self.remove_all()
