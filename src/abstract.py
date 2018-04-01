import abc

class AbstractParser(abc.ABC):
    meta_list = set()
    mimetypes = set()

    def __init__(self, filename: str):
        self.filename = filename
        self.output_filename = filename + '.cleaned'

    @abc.abstractmethod
    def get_meta(self) -> dict:
        pass

    @abc.abstractmethod
    def remove_all(self) -> bool:
        pass
