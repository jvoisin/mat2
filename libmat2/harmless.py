from typing import Dict
from . import abstract


class HarmlessParser(abstract.AbstractParser):
    """ This is the parser for filetypes that do not contain metadata. """
    mimetypes = {'application/xml', 'text/plain', 'text/xml', 'application/rdf+xml'}

    def __init__(self, filename: str) -> None:
        super().__init__(filename)
        self.filename = filename
        self.output_filename = filename

    def get_meta(self) -> Dict[str, str]:
        return dict()

    def remove_all(self) -> bool:
        return True
