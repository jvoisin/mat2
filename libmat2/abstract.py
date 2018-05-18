import abc
import os


class AbstractParser(abc.ABC):
    meta_list = set()
    mimetypes = set()

    def __init__(self, filename: str):
        self.filename = filename
        fname, extension = os.path.splitext(filename)
        self.output_filename = fname + '.cleaned' + extension

    @abc.abstractmethod
    def get_meta(self) -> dict:
        pass

    @abc.abstractmethod
    def remove_all(self) -> bool:
        pass

    def remove_all_lightweight(self) -> bool:
        """ Remove _SOME_ metadata. """
        return self.remove_all()
