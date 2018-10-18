import abc
import os
from typing import Set, Dict, Union

assert Set  # make pyflakes happy


class AbstractParser(abc.ABC):
    """ This is the base class of every parser.
    It might yield `ValueError` on instantiation on invalid files,
    and `RuntimeError` when something went wrong in `remove_all`.
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
        self.lightweight_cleaning = False

    @abc.abstractmethod
    def get_meta(self) -> Dict[str, Union[str, dict]]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def remove_all(self) -> bool:
        """
        :raises RuntimeError: Raised if the cleaning process went wrong.
        """
        pass  # pragma: no cover
